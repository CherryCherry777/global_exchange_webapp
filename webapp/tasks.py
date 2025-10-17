from datetime import timedelta
from decimal import Decimal
import secrets
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.contrib.contenttypes.models import ContentType

from .models import Currency, ClienteUsuario, CustomUser, EmailScheduleConfig, MFACode, Transaccion, CuentaBancariaNegocio
from .views.payments.pagos_simulados_a_clientes import pagar_al_cliente

from django.utils import timezone

from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

@shared_task
def check_and_send_exchange_rates():
    """
    Runs every minute. Checks config and decides if emails should be sent.
    """
    config = EmailScheduleConfig.objects.first()
    if not config:
        return

    now = timezone.localtime()

    should_send = False
    if config.frequency == "daily":
        should_send = now.hour == config.hour and now.minute == config.minute
    elif config.frequency == "weekly":
        # e.g., Monday at configured time
        should_send = now.weekday() == 0 and now.hour == config.hour and now.minute == config.minute
    elif config.frequency == "custom" and config.interval_minutes:
        should_send = now.minute % config.interval_minutes == 0

    if should_send:
        _send_to_all_users.delay()  # ✅ Run as background task


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
def cancelar_transacciones_vencidas():
    """
    Cancela automáticamente las transacciones pendientes que usan una CuentaBancariaNegocio
    y que excedieron el tiempo límite.
    """
    limite_tiempo = timezone.now() - timedelta(minutes=2)

    # Obtener ContentType de CuentaBancariaNegocio
    tipo_cuenta_bancaria = ContentType.objects.get_for_model(CuentaBancariaNegocio)

    # Filtrar solo las transacciones PENDIENTES y con ese tipo de medio de pago
    vencidas = Transaccion.objects.filter(
        estado=Transaccion.Estado.PENDIENTE,
        medio_pago_type=tipo_cuenta_bancaria,
        fecha_creacion__lt=limite_tiempo,
    )

    cantidad = vencidas.update(estado=Transaccion.Estado.CANCELADA)
    print(f"[INFO] {cantidad} transacciones con CuentaBancariaNegocio canceladas automáticamente por vencimiento.")


@shared_task(bind=True, max_retries=4, default_retry_delay=5)
def pagar_al_cliente_task(self, transaccion_id: int) -> None:
    transaccion = Transaccion.objects.get(pk=transaccion_id)

    try:
        exito = pagar_al_cliente(transaccion)

        if exito:
            transaccion.estado = Transaccion.Estado.COMPLETA
            transaccion.save(update_fields=["estado"])
            return

        # Forzar excepción para retry
        raise Exception("No se pudo pagar al cliente")

    except Exception as e:
        # Verificar si aún podemos reintentar
        if self.request.retries < self.max_retries:
            try:
                raise self.retry(exc=e)
            except MaxRetriesExceededError:
                # Esto nunca debería ejecutarse aquí, solo como fallback
                pass

        # Si llegamos aquí, significa que ya se agotaron los reintentos
        transaccion.estado = Transaccion.Estado.AC_FALLIDA
        transaccion.save(update_fields=["estado"])

        # ---------------------------------------------
        # Notificación al cliente y soporte
        # ---------------------------------------------
        try:
            # Solo necesitamos el correo del usuario responsable y del soporte
            usuario_email = getattr(transaccion.usuario, "email", None)
            soporte_email = getattr(settings, "SUPPORT_EMAIL", "soporte@tuempresa.com")

            # Este correo antes iba al cliente, ahora lo recibe el usuario responsable
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
                f"El equipo de soporte de {getattr(settings, 'PROJECT_NAME', 'Global Exchange')}"
            )

            # Correo “admin” sigue igual, para soporte
            subject_admin = "⚠️ Error crítico: no se pudo acreditar la transacción"
            message_admin = (
                f"No se pudo completar la acreditación tras varios intentos.\n\n"
                f"Detalles de la transacción:\n"
                f"- ID: {transaccion.id}\n"
                f"- Usuario responsable: {transaccion.usuario}\n"
                f"- Monto: {transaccion.monto_destino} {transaccion.moneda_destino}\n"
                f"- Error final: {str(e)}\n\n"
                f"Por favor, revise manualmente la operación."
            )

            # Enviar correo al usuario responsable
            if usuario_email:
                send_mail(
                    subject=subject_usuario,
                    message=message_usuario,
                    from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@tuempresa.com"),
                    recipient_list=[usuario_email],
                    fail_silently=True,
                )

            # Enviar correo a soporte
            admin_recipients = [soporte_email]
            send_mail(
                subject=subject_admin,
                message=message_admin,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@tuempresa.com"),
                recipient_list=admin_recipients,
                fail_silently=True,
            )

        except Exception as mail_error:
            print(f"[WARN] Error enviando notificación de fallo: {mail_error}")

        print(f"[ACREDITACION_FALLIDA] Transacción {transaccion.id}: {e}")
