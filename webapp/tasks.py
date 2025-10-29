from datetime import datetime, timedelta
from decimal import Decimal
import secrets
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError, Ignore
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import  F, OuterRef, Subquery

from webapp.services.invoice_retry import retry_factura_numdoc
from webapp.services.invoice_sync import sync_facturas_pendientes

from .models import Currency, ClienteUsuario, CustomUser, EmailScheduleConfig, ExpiracionTransaccionConfig, LimiteIntercambioCliente, LimiteIntercambioConfig, LimiteIntercambioScheduleConfig, MFACode, SyncLog, Tauser, Transaccion, CuentaBancariaNegocio
from .views.payments.pagos_simulados_a_clientes import pagar_al_cliente

from django.utils import timezone

from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

import logging
import calendar
from django.core.cache import cache

logger = logging.getLogger(__name__)

LOCK_EXPIRE = 60  # seconds — one minute, since this runs every minute


@shared_task
def check_and_send_exchange_rates():
    """
    Runs every minute. Checks EmailScheduleConfig and decides
    if exchange rate emails should be sent.
    Includes safety lock, validation, and logging.
    """
    # ---- Lock to prevent duplicate runs ----
    if cache.get("check_and_send_exchange_rates_lock"):
        logger.warning("Skipping run — another check_and_send_exchange_rates task is still active.")
        return
    cache.set("check_and_send_exchange_rates_lock", True, timeout=LOCK_EXPIRE)

    try:
        config = EmailScheduleConfig.objects.first()
        if not config:
            logger.warning("No EmailScheduleConfig found. Task skipped.")
            return

        now = timezone.localtime()
        should_send = False

        # ---- Validate necessary config fields ----
        if config.frequency in ["daily", "weekly"] and (config.hour is None or config.minute is None):
            logger.error(f"Invalid schedule configuration: hour or minute missing for {config.frequency}")
            return

        # ---- Frequency checks ----
        if config.frequency == "daily":
            should_send = now.hour == config.hour and now.minute == config.minute

        elif config.frequency == "weekly":
            # allow configurable weekday (0=Mon, 6=Sun)
            weekday = getattr(config, "weekday", 0)  # defaults to Monday if field doesn’t exist
            should_send = (
                now.weekday() == weekday
                and now.hour == config.hour
                and now.minute == config.minute
            )

        elif config.frequency == "custom" and config.interval_minutes:
            should_send = now.minute % config.interval_minutes == 0

        # ---- Action ----
        if should_send:
            logger.info(f"✅ Sending exchange rate emails at {now}.")
            _send_to_all_users.delay()
        else:
            logger.debug(f"No send scheduled at {now}. Frequency={config.frequency}")

    except Exception as e:
        logger.exception(f"Error in check_and_send_exchange_rates: {e}")

    finally:
        cache.delete("check_and_send_exchange_rates_lock")


@shared_task
def _send_to_all_users():
    """
    Dispatches one subtask per user, staggered to avoid rate limits.
    """
    users = CustomUser.objects.filter(is_active=True, receive_exchange_emails=True).exclude(email="")
    for i, user in enumerate(users):
        # space out each email by 2 seconds
        send_exchange_rates_email.apply_async(args=[user.id], countdown=i * 2)


@shared_task
def send_exchange_rates_email(user_id):
    """
    Sends one email with exchange rates to a single user.
    """
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return

    # generate persistent unsubscribe token
    if not getattr(user, "unsubscribe_token", None):
        user.unsubscribe_token = secrets.token_urlsafe(32)
        user.save(update_fields=["unsubscribe_token"])

    uidb64 = urlsafe_base64_encode(force_bytes(user.id))
    unsubscribe_url = f"{settings.SITE_URL}/unsubscribe/{uidb64}/{user.unsubscribe_token}/"

    cliente_usuarios = (
        ClienteUsuario.objects.select_related("cliente__categoria").filter(usuario=user)
    )
    if not cliente_usuarios.exists():
        cliente_usuarios = [None]

    currencies = Currency.objects.filter(is_active=True).exclude(code="PYG")
    clientes_data = []

    for cu in cliente_usuarios:
        if cu:
            cliente = cu.cliente
            descuento = getattr(getattr(cliente, "categoria", None), "descuento", None) or Decimal("0")
        else:
            cliente = None
            descuento = Decimal("0")

        monedas_info = []
        for c in currencies:
            precio_compra = c.base_price - (c.comision_compra * (Decimal("1") - descuento))
            precio_venta = c.base_price + (c.comision_venta * (Decimal("1") - descuento))
            monedas_info.append({
                "name": c.name,
                "code": c.code,
                "precio_compra": f"{precio_compra:.2f}",
                "precio_venta": f"{precio_venta:.2f}",
            })

        clientes_data.append({
            "cliente": cliente,
            "descuento": f"{(descuento * 100):.0f}%" if descuento else "0%",
            "monedas": monedas_info,
        })

    context = {
        "user": user,
        "clientes_data": clientes_data,
        "unsubscribe_url": unsubscribe_url,
    }

    text_content = render_to_string("emails/exchange_rates.txt", context)
    html_content = render_to_string("emails/exchange_rates.html", context)

    subject = "Simulador - Tasas de cambio"
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@simulador.com")
    email = EmailMultiAlternatives(subject, text_content, from_email, [user.email])
    email.attach_alternative(html_content, "text/html")

    try:
        email.send(fail_silently=False)
    except Exception as e:
        print(f"Error sending email to {user.email}: {e}")

@shared_task
def send_welcome_email(user_email):
    send_mail(
        'Welcome!',
        'Thanks for signing up!',
        'from@example.com',
        [user_email],
        fail_silently=False,
    )


@shared_task
def cleanup_expired_mfa_codes():
    """Elimina códigos MFA vencidos (más de 1 hora de antigüedad)."""
    MFACode.objects.filter(created_at__lt=timezone.now() - timedelta(hours=1)).delete()


@shared_task
def cancelar_transacciones_vencidas_cbn():
    """Expira transacciones con medio 'Transferencia' según la config definida en el panel."""
    try:
        config = ExpiracionTransaccionConfig.objects.get(medio="cuenta_bancaria_negocio")
        limite_min = config.minutos_expiracion
    except ExpiracionTransaccionConfig.DoesNotExist:
        print("[WARN] No existe configuración para 'Transferencia'. No se ejecuta.")
        return

    limite_tiempo = timezone.now() - timedelta(minutes=limite_min)
    tipo_cb = ContentType.objects.get_for_model(CuentaBancariaNegocio)

    vencidas = Transaccion.objects.filter(
        estado=Transaccion.Estado.PENDIENTE,
        medio_pago_type=tipo_cb,
        fecha_creacion__lt=limite_tiempo,
    )

    cantidad = vencidas.update(estado=Transaccion.Estado.CANCELADA)
    print(f"[INFO] {cantidad} transacciones con Transferencia canceladas automáticamente (> {limite_min} min).")


@shared_task
def cancelar_transacciones_vencidas_tauser():
    """Expira transacciones con medio 'Tauser' según la config definida en el panel."""
    try:
        config = ExpiracionTransaccionConfig.objects.get(medio="tauser")
        limite_min = config.minutos_expiracion
    except ExpiracionTransaccionConfig.DoesNotExist:
        print("[WARN] No existe configuración para 'Tauser'. No se ejecuta.")
        return

    limite_tiempo = timezone.now() - timedelta(minutes=limite_min)
    tipo_tauser = ContentType.objects.get_for_model(Tauser)

    vencidas = Transaccion.objects.filter(
        estado=Transaccion.Estado.PENDIENTE,
        medio_pago_type=tipo_tauser,
        fecha_creacion__lt=limite_tiempo,
    )

    cantidad = vencidas.update(estado=Transaccion.Estado.CANCELADA)
    print(f"[INFO] {cantidad} transacciones con Tauser canceladas automáticamente (> {limite_min} min).")


# Resetear límites de intercambio
LOCK_KEY = "check_and_reset_limites_intercambio_lock"

@shared_task
def check_and_reset_limites_intercambio():
    """
    Ejecuta el reset GLOBAL con tolerancia de ±3 minutos:
      - DAILY   → resetea limite_dia_actual
      - MONTHLY → resetea limite_mes_actual
    Cada uno se ejecuta solo si:
      - is_active=True
      - estamos dentro del minuto exacto o los 2 siguientes (tolerancia)
      - no fue ejecutado ya en este mismo día/mes (anti doble ejecución)
    """

    if cache.get(LOCK_KEY):
        logger.warning("⏭️  Reset ya en ejecución. Omitiendo este tick.")
        return
    cache.set(LOCK_KEY, True, timeout=LOCK_EXPIRE)

    try:
        now = timezone.localtime()
        now_minute_key = now.strftime("%Y-%m-%d %H:%M")  # resolución minuto

        # ---------- DAILY ----------
        config_daily = LimiteIntercambioScheduleConfig.get_by_frequency("daily")
        if config_daily.is_active:
            target_time = now.replace(hour=config_daily.hour, minute=config_daily.minute, second=0, microsecond=0)
            diff_seconds = abs((now - target_time).total_seconds())

            # <= 180 segundos de tolerancia (3 minutos)
            if diff_seconds <= 180:
                # Evitar repetir si ya se ejecutó este mismo día
                if not config_daily.last_executed_at or config_daily.last_executed_at.strftime("%Y-%m-%d") != now.strftime("%Y-%m-%d"):
                    with transaction.atomic():
                        tope_dia_subq = LimiteIntercambioConfig.objects.filter(
                            id=OuterRef("config_id")
                        ).values("limite_dia_max")[:1]

                        updated = LimiteIntercambioCliente.objects.update(
                            limite_dia_actual=Subquery(tope_dia_subq)
                        )
                        config_daily.last_executed_at = now
                        config_daily.save(update_fields=["last_executed_at"])

                    logger.info(f"✅ Reset DIARIO aplicado. {updated} filas afectadas.")
                else:
                    logger.info("⏭️ Reset diario ya se ejecutó hoy. Ignorando.")

        # ---------- MONTHLY ----------
        config_monthly = LimiteIntercambioScheduleConfig.get_by_frequency("monthly")
        if config_monthly.is_active and config_monthly.month_day:
            last_day = calendar.monthrange(now.year, now.month)[1]
            run_day = min(config_monthly.month_day, last_day)
            if now.day == run_day:
                target_time = now.replace(hour=config_monthly.hour, minute=config_monthly.minute, second=0, microsecond=0)
                diff_seconds = abs((now - target_time).total_seconds())

                if diff_seconds <= 180:
                    if not config_monthly.last_executed_at or config_monthly.last_executed_at.strftime("%Y-%m") != now.strftime("%Y-%m"):
                        with transaction.atomic():
                            tope_mes_subq = LimiteIntercambioConfig.objects.filter(
                                id=OuterRef("config_id")
                            ).values("limite_mes_max")[:1]

                            updated = LimiteIntercambioCliente.objects.update(
                                limite_mes_actual=Subquery(tope_mes_subq)
                            )
                            config_monthly.last_executed_at = now
                            config_monthly.save(update_fields=["last_executed_at"])

                        logger.info(f"✅ Reset MENSUAL aplicado. {updated} filas afectadas.")
                    else:
                        logger.info("⏭️ Reset mensual ya se ejecutó este mes. Ignorando.")

    except Exception as e:
        logger.exception(f"💥 Error en check_and_reset_limites_intercambio: {e}")

    finally:
        cache.delete(LOCK_KEY)
        

@shared_task(bind=True, max_retries=4, default_retry_delay=5)
def pagar_al_cliente_task(self, transaccion_id: int) -> None:
    """
    Acredita al cliente el monto de una transacción *solo si* la transacción
    ya está en estado PAGADA. Reintenta ante fallos transitorios.

    Flujo:
      - Precondición: estado == PAGADA → continúa; si no, finaliza sin reintentos.
      - Éxito: estado := COMPLETA.
      - Fracaso tras agotar reintentos: estado := AC_FALLIDA + avisos.

    Args:
        transaccion_id: PK de la transacción a acreditar.

    Raises:
        Ignore: si la transacción no está en estado PAGADA (no reintentar).
    """
    # Traer la transacción con un lock corto para evitar carreras de estado.
    # Si no te interesa el lock, podés quitar el atomic/select_for_update.
    with transaction.atomic():
        transaccion: Transaccion = (
            Transaccion.objects.select_for_update(skip_locked=True)
            .select_related("usuario")
            .get(pk=transaccion_id)
        )

        # ✅ Pre-condición: solo cuando esté PAGADA
        if transaccion.estado != Transaccion.Estado.PAGADA:
            logger.info(
                "Tarea de acreditación omitida: transacción %s en estado %s (se requiere PAGADA).",
                transaccion.id, transaccion.estado
            )
            # No reintentar ni marcar error: simplemente se ignora.
            raise Ignore()

    try:
        exito: bool = pagar_al_cliente(transaccion)

        if exito:
            transaccion.estado = Transaccion.Estado.COMPLETA
            transaccion.save(update_fields=["estado"])
            logger.info("Acreditación completada para transacción %s.", transaccion.id)
            return

        # Forzar excepción para activar retry
        raise RuntimeError("No se pudo pagar al cliente")

    except Exception as e:
        # ¿Quedan reintentos?
        if self.request.retries < self.max_retries:
            try:
                # Celery lanzará Retry; no continúa el flujo
                raise self.retry(exc=e)
            except MaxRetriesExceededError:
                # Si justo se excedió aquí, caemos al manejo final más abajo
                pass

        # 🔻 Agotados los reintentos: marcar fallo de acreditación
        transaccion.estado = Transaccion.Estado.AC_FALLIDA
        transaccion.save(update_fields=["estado"])

        # ---------------------------------------------
        # Notificación al usuario responsable y soporte
        # ---------------------------------------------
        try:
            usuario_email = getattr(transaccion.usuario, "email", None)
            soporte_email = getattr(settings, "SUPPORT_EMAIL", "soporte@tuempresa.com")
            project_name = getattr(settings, "PROJECT_NAME", "Global Exchange")
            from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@tuempresa.com")

            subject_usuario = "Error en la acreditación de la transacción"
            message_usuario = (
                f"Estimado/a {transaccion.usuario},\n\n"
                f"Se recibió el pago de la transacción correctamente, pero hubo problemas "
                f"para acreditar el monto correspondiente.\n\n"
                f"Detalles:\n"
                f"- ID de transacción: {transaccion.id}\n"
                f"- Monto: {transaccion.monto_destino} {transaccion.moneda_destino}\n\n"
                f"Por favor, revise la operación y tome las acciones necesarias.\n\n"
                f"Atentamente,\n"
                f"El equipo de soporte de {project_name}"
            )

            subject_admin = "⚠️ Error crítico: no se pudo acreditar la transacción"
            message_admin = (
                "No se pudo completar la acreditación tras varios intentos.\n\n"
                f"Detalles de la transacción:\n"
                f"- ID: {transaccion.id}\n"
                f"- Usuario responsable: {transaccion.usuario}\n"
                f"- Monto: {transaccion.monto_destino} {transaccion.moneda_destino}\n"
                f"- Error final: {str(e)}\n\n"
                "Por favor, revise manualmente la operación."
            )

            if usuario_email:
                send_mail(
                    subject=subject_usuario,
                    message=message_usuario,
                    from_email=from_email,
                    recipient_list=[usuario_email],
                    fail_silently=True,
                )

            send_mail(
                subject=subject_admin,
                message=message_admin,
                from_email=from_email,
                recipient_list=[soporte_email],
                fail_silently=True,
            )

        except Exception as mail_error:
            logger.warning("Error enviando notificaciones: %s", mail_error)

        logger.error("[ACREDITACION_FALLIDA] Transacción %s: %s", transaccion.id, e)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def generate_invoice_task(self, transaccion_id: int):
    from webapp.models import Transaccion
    from webapp.services.invoice_from_tx import generate_invoice_for_transaccion
    try:
        tx = Transaccion.objects.get(id=transaccion_id)
        return generate_invoice_for_transaccion(tx)
    except Exception as e:
        raise self.retry(exc=e)


@shared_task(name="webapp.tasks.sync_facturas_sifen_task")
def sync_facturas_sifen_task(limit=200):
    """
    Sincroniza facturas con SIFEN y adjunta XML/PDF cuando quedan aprobadas.
    """
    resumen = sync_facturas_pendientes(limit=limit, fetch_files=True)
    SyncLog.objects.create(resumen=resumen)
    return resumen


LOCK_KEY = "sync_facturas_lock"
LOCK_TTL = 60 * 5  # 5 minutos

@shared_task(bind=True, max_retries=2)
def sync_facturas_pendientes_task(self, limit=200):
    """
    (Opcional) Variante con lock local si querés correrla manualmente o desde otra agenda.
    """
    if not cache.add(LOCK_KEY, "1", LOCK_TTL):
        return {"ok": False, "skipped": "locked"}

    try:
        resumen = sync_facturas_pendientes(limit=limit, fetch_files=True)
        return {"ok": True, **resumen}
    except Exception as e:
        return {"ok": False, "error": repr(e)}
    finally:
        cache.delete(LOCK_KEY)


@shared_task(name="webapp.tasks.reintentar_factura_numdoc_task")
def reintentar_factura_numdoc_task(factura_id: int):
    """
    Reintenta una factura que fue rechazada con el error 'NUMDOC_APROBADO',
    generando un nuevo dNumDoc válido y reenviándola al proxy SIFEN.

    - Busca el siguiente número libre en public.de.
    - Inserta un nuevo DE en el proxy con ese número.
    - Actualiza la factura con el nuevo de_id y la marca como 'emitida'.
    - Llama a confirmar_borrador() para que el proxy procese el nuevo DE.
    """

    from webapp.models import Factura
    from webapp.services import fs_proxy as sql
    from webapp.services.invoice_from_tx import (
        _int_py, _parse_ruc, _mod11_py, _ensure_len,
        InvoiceParams, TimbradoDTO, EmisorDTO, ReceptorDTO, ItemDTO
    )
    from django.conf import settings

    try:
        factura = (Factura.objects
                   .select_related("cliente", "usuario", "detalleFactura__transaccion")
                   .get(id=factura_id))
        tx = factura.detalleFactura.transaccion

        # Buscar el siguiente dNumDoc disponible
        dnumdoc = sql.find_reusable_dnumdoc(est=factura.est, pun=factura.pun,
                                            start="0000151", end="0000200")
        if not dnumdoc:
            return {"ok": False, "reason": "No hay dNumDoc reutilizable en rango."}

        # Construir parámetros del nuevo DE
        timb = TimbradoDTO(
            iTiDE="1",
            num_tim=str(getattr(settings, "TIMBRADO_NUM", "02595733")),
            est=factura.est or "001", pun_exp=factura.pun or "003", num_doc=dnumdoc,
            serie="", fe_ini_t=str(getattr(settings, "TIMBRADO_FE_INI", "2025-03-27"))
        )
        emisor = EmisorDTO(
            ruc="2595733", dv="3",
            nombre="Global Exchange",
            dir="SIN DIRECCIÓN DEFINIDA",
            num_casa="0",
            dep_cod="1", dep_desc="CAPITAL",
            ciu_cod="1", ciu_desc="ASUNCION (DISTRITO)",
            tel="021000000",
            email="equipo8.globalexchange@gmail.com",
            tip_cont="2",
            info_fisc="Documento emitido por Global Exchange"
        )

        cli = factura.cliente
        es_juridica = (cli.tipoCliente == "persona_juridica")

        # Valores de prueba fijos
        if es_juridica:
            ruc_base, ruc_dv = "2175460", "8"
            is_contrib = True
        else:
            ruc_base, ruc_dv = None, None
            is_contrib = False
            cli.documento = "1234567"

        iNatRec = "1" if is_contrib else "2"
        iTiOpe = "1" if is_contrib else "2"

        nom_base = cli.razonSocial if es_juridica and cli.razonSocial else cli.nombre
        nom_rec = _ensure_len(nom_base, 4, 255, "Sin Nombre")
        dir_rec = _ensure_len(cli.direccion, 0, 255, "")

        if is_contrib:
            iTiContRec = "2" if es_juridica else "1"
            dRucRec = ruc_base
            dDVRec = ruc_dv
            iTipIDRec, dDTipIDRec, dNumIDRec = "0", "", ""
        else:
            iTiContRec, dRucRec, dDVRec = None, None, None
            iTipIDRec, dDTipIDRec, dNumIDRec = "1", "", "1234567"

        receptor = ReceptorDTO(
            nat_rec=iNatRec, ti_ope=iTiOpe, pais="PRY",
            ti_cont_rec=iTiContRec,
            ruc=dRucRec, dv=dDVRec,
            tip_id=iTipIDRec, dtipo_id=dDTipIDRec, num_id=dNumIDRec,
            nombre=nom_rec,
            dir=dir_rec, num_casa="",
            dep_cod="1", dep_desc="CAPITAL", ciu_cod="1", ciu_desc="ASUNCION (DISTRITO)",
            email=cli.correo, tel=cli.telefono
        )

        # Determinar base imponible
        if tx.moneda_origen.code == "PYG":
            base_pyg = tx.monto_origen
        elif tx.moneda_destino.code == "PYG":
            base_pyg = tx.monto_destino
        else:
            base_pyg = tx.monto_destino

        items = [ItemDTO(
            cod_int="CAM/DIV",
            descripcion=f"Servicio de cambio de divisas ({tx.tipo})",
            cantidad="1",
            precio_unit=_int_py(base_pyg),
            desc_item="0",
            iAfecIVA="3", dPropIVA="0", dTasaIVA="0"
        )]

        params = InvoiceParams(
            timbrado=timb, emisor=emisor, receptor=receptor, items=items,
            fecha_emision=datetime.now(),
            tip_emi="1", tip_tra="1", t_imp="1", moneda="PYG",
            ind_pres="1", cond_ope="1", plazo_cre=""
        )

        with transaction.atomic():
            new_de_id = sql.insert_de(params)
            sql.insert_acteco(new_de_id, actividades=[("62010", "Actividades de programación informática")])
            sql.insert_items(new_de_id, params.items)
            sql.insert_pago_contado(new_de_id, items=params.items)
            sql.confirmar_borrador(new_de_id)

            # Actualizar factura en la app
            factura.de_id = new_de_id
            factura.d_num_doc = dnumdoc
            factura.estado = "emitida"
            factura.save(update_fields=["de_id", "d_num_doc", "estado"])

        return {
            "ok": True,
            "factura_id": factura.id,
            "new_de_id": new_de_id,
            "d_num_doc": dnumdoc
        }

    except Exception as e:
        return {"ok": False, "error": repr(e)}