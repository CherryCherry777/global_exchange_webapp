# webapp/services/invoice_from_tx.py
from datetime import datetime
from django.conf import settings
from django.db import transaction
from webapp.models import DocSequence, Transaccion, Factura, DetalleFactura
from webapp.services import fs_proxy as sql
from webapp.services.dto import InvoiceParams, TimbradoDTO, EmisorDTO, ReceptorDTO, ItemDTO

def _int_py(value) -> str:
    return str(int(round(float(value))))  # PYG sin decimales

import re
from datetime import datetime
from typing import Optional, Tuple

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
    if transaccion.factura_asociada_id:
        return {"already": True, "factura_id": transaccion.factura_asociada_id}

    with transaction.atomic():
        seq = DocSequence.objects.select_for_update().get(est="001", pun="003")
        if seq.current_num >= seq.max_num:
            raise RuntimeError("Rango de documentos agotado (151–200).")
        seq.current_num += 1
        dNumDoc = str(seq.current_num).zfill(7)
        seq.save(update_fields=["current_num"])

        timb = TimbradoDTO(
            iTiDE="1",
            num_tim=str(getattr(settings, "TIMBRADO_NUM", "12345678")),
            est="001", pun_exp="003", num_doc=dNumDoc,
            serie="", fe_ini_t="2024-04-17"
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

        cli = transaccion.cliente

        # Determinar PF/PJ desde tu modelo:
        es_juridica = (cli.tipoCliente == "persona_juridica")

        # Normalizar RUC
        ruc_base, ruc_dv = _parse_ruc(cli.ruc)
        is_contrib = bool(ruc_base)  # tratamos como contribuyente si hay base

        # Naturaleza y tipo de operación
        iNatRec = "1" if is_contrib else "2"         # 1 contribuyente / 2 no contribuyente
        iTiOpe  = "1" if is_contrib else "2"         # B2B si contribuyente, B2C si no
        cPaisRec = "PRY"

        # Nombre/dirección (aprovechando razón social para PJ)
        nom_base = cli.razonSocial if es_juridica and cli.razonSocial else cli.nombre
        nom_rec = _ensure_len(nom_base, 4, 255, "Sin Nombre")
        dir_rec = _ensure_len(cli.direccion, 0, 255, "")

        if is_contrib:
            # Contribuyente: iTiContRec 1=PF, 2=PJ; se envía RUC/DV; NO doc alterno
            iTiContRec = "2" if es_juridica else "1"
            dRucRec = ruc_base
            dDVRec  = ruc_dv or _mod11_py(ruc_base)
            iTipIDRec = "0"
            dDTipIDRec = ""
            dNumIDRec = ""
        else:
            # No contribuyente: NO iTiContRec/RUC/DV; SÍ documento alterno
            iTiContRec = None    # si luego lo persistís al proxy, ponelo como '' en SQL para no mandar None
            dRucRec = None
            dDVRec  = None
            iTipIDRec = "1"      # p.ej. 1=CI PY (ajusta al catálogo que uses)
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
        # --- FIN NORMALIZACIÓN ---

        if transaccion.moneda_origen.code == "PYG":
            base_pyg = transaccion.monto_origen
        elif transaccion.moneda_destino.code == "PYG":
            base_pyg = transaccion.monto_destino
        else:
            base_pyg = transaccion.monto_destino

        items = [ItemDTO(
            cod_int="CAM/DIV",
            descripcion=f"Servicio de cambio de divisas ({transaccion.tipo})",
            cantidad="1",
            precio_unit=_int_py(base_pyg),
            desc_item="0",
            iAfecIVA="1", dPropIVA="100", dTasaIVA="10"
        )]

        params = InvoiceParams(
            timbrado=timb, emisor=emisor, receptor=receptor, items=items,
            fecha_emision=datetime.now(),
            tip_emi="1", tip_tra="1", t_imp="1", moneda="PYG",
            ind_pres="1", cond_ope="1", plazo_cre=""
        )

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
        transaccion.factura_asociada = factura
        transaccion.save(update_fields=["factura_asociada"])

    # proxy (fs_proxy)
    de_id = sql.insert_de(params)
    sql.insert_acteco(de_id, actividades=[("46510", "COMERCIO AL POR MAYOR DE EQUIPOS INFORMÁTICOS Y SOFTWARE")])
    sql.insert_items(de_id, params.items)
    if params.cond_ope == "1":
        sql.insert_pago_contado(de_id)
    sql.confirmar_borrador(de_id)

    Factura.objects.filter(id=factura.id).update(estado="aprobada")

    return {"already": False, "de_id": de_id, "factura_id": factura.id, "dNumDoc": dNumDoc}
