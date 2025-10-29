import os   # <-- NUEVO
from datetime import datetime
from django.conf import settings
from django.db import transaction
from webapp.models import Transaccion, Factura, DetalleFactura
from webapp.services import fs_proxy as sql
from webapp.services.dto import InvoiceParams, TimbradoDTO, EmisorDTO, ReceptorDTO, ItemDTO
import re
from typing import Optional, Tuple
from django.contrib import messages

# --- NUEVO: helper de entorno ---
def _env_true(name: str) -> bool:
    return str(os.getenv(name, "")).strip().lower() in ("1", "true", "yes", "on")

def _int_py(value) -> str:
    return str(int(round(float(value))))  # PYG sin decimales

def _mod11_py(num: str) -> str:
    nums = list(map(int, re.findall(r"\d", num)))
    if not nums:
        return "0"
    factors = [2,3,4,5,6,7,8,9,10,11]
    acc = 0
    for i, d in enumerate(reversed(nums)):
        acc += d * factors[i % len(factors)]
    dv = 11 - (acc % 11)
    if dv in (10, 11):
        return "0"
    return str(dv)

def _parse_ruc(raw: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    if not raw:
        return None, None
    s = str(raw).strip()
    parts = re.split(r"\D+", s)
    parts = [p for p in parts if p]
    if not parts:
        return None, None
    if len(parts) >= 2:
        base, dv = parts[0], parts[1]
    else:
        base, dv = parts[0], _mod11_py(parts[0])  # si no vino DV, calculamos
    base = base.lstrip("0") or "0"
    return base, dv

def _ensure_len(val: str, min_len: int, max_len: int, default: str) -> str:
    v = (val or "").strip()
    if len(v) < min_len:
        v = default
    return v[:max_len]


def generate_invoice_for_transaccion(transaccion: Transaccion) -> dict:
    """
    Genera una factura y crea el DE en el proxy fs_proxy.

    Reglas para dNumDoc:
      - Si FS_TEST_OVERWRITE_151=true => fuerza dNumDoc=0000151 (pruebas).
      - Si NO está forzado: busca en fs_proxy.public.de un dNumDoc entre
        '0000151'..'0000200' cuyo estado != 'Aprobado' y usa ese número.
      - Si no encuentra, usa el secuenciador local (DocSequence 001/003).

    También:
      - IVA exento (0%) para casas de cambio.
      - Guarda/actualiza Factura con de_id, d_num_doc, est, pun y la asocia a la Transaccion.
    """
    import os
    from django.db import transaction

    if transaccion.factura_asociada_id:
        return {"already": True, "factura_id": transaccion.factura_asociada_id}

    # force_151 = str(os.getenv("FS_TEST_OVERWRITE_151", "")).lower() in ("1", "true", "yes")
    force_numdoc = os.getenv("FS_TEST_OVERWRITE_NUMDOC", "False")

    with transaction.atomic():
        # --- Documento fiscal (Est y Pun fijos a 001/003) ---

        if force_numdoc:
            dNumDoc = "0000154"  # no consumimos secuencia cuando se fuerza
        else:
            # Intentar reutilizar un dNumDoc del proxy (rechazado/pendiente/etc.)
            reuse = sql.find_reusable_dnumdoc(est="001", pun="003",
                                              start="0000151", end="0000200")
            if reuse:
                dNumDoc = reuse
            else:
                messages.error("No se ha podido generar factura.")

        timb = TimbradoDTO(
            iTiDE="1",
            num_tim=str(getattr(settings, "TIMBRADO_NUM", "02595733")),
            est="001", pun_exp="003", num_doc=dNumDoc,
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

        # --- Receptor normalizado ---
        cli = transaccion.cliente
        es_juridica = (cli.tipoCliente == "persona_juridica")

        if es_juridica:
            # Persona jurídica → RUC fijo
            ruc_base, ruc_dv = "2175460", "8"
            is_contrib = True
        else:
            # Persona física → cédula fija
            cli.documento = "1234567"
            is_contrib = False  # normalmente no contribuyente en este caso
            ruc_base, ruc_dv = None, None

        iNatRec = "1" if is_contrib else "2"
        iTiOpe  = "1" if is_contrib else "2"
        cPaisRec = "PRY"

        nom_base = cli.razonSocial if es_juridica and cli.razonSocial else cli.nombre
        nom_rec = _ensure_len(nom_base, 4, 255, "Sin Nombre")
        dir_rec = _ensure_len(cli.direccion, 0, 255, "")

        if is_contrib:
            iTiContRec = "2" if es_juridica else "1"
            dRucRec = ruc_base
            dDVRec  = ruc_dv or _mod11_py(ruc_base)
            iTipIDRec = "0"
            dDTipIDRec = ""
            dNumIDRec = ""
        else:
            iTiContRec = None
            dRucRec = None
            dDVRec  = None
            iTipIDRec = "1"   # CI PY
            dDTipIDRec = ""
            if not cli.documento:
                raise ValueError("Cliente sin RUC válido ni documento de identidad.")
            dNumIDRec = _ensure_len(cli.documento, 1, 20, "0")

        receptor = ReceptorDTO(
            nat_rec=iNatRec, ti_ope=iTiOpe, pais=cPaisRec,
            ti_cont_rec=iTiContRec,
            ruc=dRucRec, dv=dDVRec,
            tip_id=iTipIDRec, dtipo_id=dDTipIDRec, num_id=dNumIDRec,
            nombre=nom_rec,
            dir=dir_rec, num_casa="",
            dep_cod="1", dep_desc="CAPITAL", ciu_cod="1", ciu_desc="ASUNCION (DISTRITO)",
            email=cli.correo, tel=cli.telefono
        )

        # --- Base imponible en PYG (monto informado) ---
        if transaccion.moneda_origen.code == "PYG":
            base_pyg = transaccion.monto_origen
        elif transaccion.moneda_destino.code == "PYG":
            base_pyg = transaccion.monto_destino
        else:
            base_pyg = transaccion.monto_destino

        # --- Ítem con IVA 0% (exento) para cambio de divisas ---
        items = [ItemDTO(
            cod_int="CAM/DIV",
            descripcion=f"Servicio de cambio de divisas ({transaccion.tipo})",
            cantidad="1",
            precio_unit=_int_py(base_pyg),
            desc_item="0",
            iAfecIVA="3",    # exento
            dPropIVA="0",
            dTasaIVA="0",
        )]

        params = InvoiceParams(
            timbrado=timb, emisor=emisor, receptor=receptor, items=items,
            fecha_emision=datetime.now(),
            tip_emi="1", tip_tra="1", t_imp="1", moneda="PYG",
            ind_pres="1", cond_ope="1", plazo_cre=""
        )

        # --- Persistimos Factura y Detalle (APP) ---
        detalle = DetalleFactura.objects.create(
            transaccion=transaccion,
            content_type=transaccion.medio_pago_type,
            object_id=transaccion.medio_pago_id,
            descripcion=items[0].descripcion
        )
        factura = Factura.objects.create(
            timbrado=int(timb.num_tim),
            usuario=transaccion.usuario,
            cliente=transaccion.cliente,
            fechaEmision=datetime.now().date(),
            detalleFactura=detalle,
            estado="emitida"
        )

        # --- Insertamos en proxy y actualizamos la Factura con datos del DE ---
        try:
            de_id = sql.insert_de(params)
            # Actividad económica fija para este programa
            sql.insert_acteco(de_id, actividades=[("62010", "Actividades de programación informática")])
            sql.insert_items(de_id, params.items)
            if params.cond_ope == "1":
                sql.insert_pago_contado(de_id, items=params.items)

            # Si estamos forzando numdoc, reseteamos el estado SIFEN del DE antes de confirmar
            if force_numdoc:
                sql.reset_sifen_by_de_id(de_id)
                # (opcional) también podrías hacerlo por doc:
                # sql.reset_sifen_by_doc("001", "003", dNumDoc)

            # Guardamos vínculo y datos fiscales en nuestra Factura
            Factura.objects.filter(id=factura.id).update(
                de_id=de_id,
                d_num_doc=dNumDoc,
                est=timb.est,
                pun=timb.pun_exp,
            )
            transaccion.factura_asociada = factura
            transaccion.save(update_fields=["factura_asociada"])

            # Confirmamos para que el proxy procese
            sql.confirmar_borrador(de_id)

        except Exception as e:
            # Marcamos la factura como rechazada en la app si falló la preparación del DE
            Factura.objects.filter(id=factura.id).update(estado="rechazada")
            # Log mínimo (puedes integrar con Sentry/logger real)
            print(f"[invoice_from_tx] Error preparando DE: {e!r}")
            raise

    return {"already": False, "de_id": de_id, "factura_id": factura.id, "dNumDoc": dNumDoc}

