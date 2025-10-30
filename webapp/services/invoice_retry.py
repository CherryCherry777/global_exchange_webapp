# webapp/services/invoice_retry.py
from datetime import datetime
from django.db import transaction
from django.conf import settings
from webapp.models import Factura
from webapp.services import fs_proxy as sql
from webapp.services.invoice_from_tx import (
    _int_py, _parse_ruc, _mod11_py, _ensure_len,
    InvoiceParams, TimbradoDTO, EmisorDTO, ReceptorDTO, ItemDTO
)

RETRY_MSG = "NUMDOC_APROBADO"

def _build_params_from_tx(transaccion, dNumDoc: str) -> InvoiceParams:
    # Emisor / timbrado según settings vigentes
    timb = TimbradoDTO(
        iTiDE="1",
        num_tim=str(getattr(settings, "TIMBRADO_NUM", "02595733")),
        est="001", pun_exp="003", num_doc=dNumDoc,
        serie="", fe_ini_t=str(getattr(settings, "TIMBRADO_FE_INI", "2025-03-27")),
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
    es_juridica = (cli.tipoCliente == "persona_juridica")

    # Reglas especiales de tests que definiste:
    if es_juridica:
        ruc_base, ruc_dv = "2175460", "8"
        is_contrib = True
    else:
        # persona física con CI alterno
        ruc_base, ruc_dv = None, None
        is_contrib = False
        cli.documento = "1234567"

    iNatRec = "1" if is_contrib else "2"
    iTiOpe  = "1" if is_contrib else "2"

    nom_base = cli.razonSocial if es_juridica and cli.razonSocial else cli.nombre
    nom_rec  = _ensure_len(nom_base, 4, 255, "Sin Nombre")
    dir_rec  = _ensure_len(cli.direccion, 0, 255, "")

    if is_contrib:
        iTiContRec, dRucRec, dDVRec = ("2" if es_juridica else "1"), ruc_base, ruc_dv
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
        iAfecIVA="3", dPropIVA="0", dTasaIVA="0",
    )]

    return InvoiceParams(
        timbrado=timb, emisor=emisor, receptor=receptor, items=items,
        fecha_emision=datetime.now(),
        tip_emi="1", tip_tra="1", t_imp="1", moneda="PYG",
        ind_pres="1", cond_ope="1", plazo_cre=""
    )


def retry_factura_numdoc(factura_id: int,
                         est="001", pun="003",
                         start="0000151", end="0000200") -> dict:
    """
    Reintenta una Factura con nuevo dNumDoc cuando fue rechazada con NUMDOC_APROBADO.
    - No crea Factura nueva: actualiza de_id, d_num_doc y estado a 'emitida'.
    """
    factura: Factura = (Factura.objects
                        .select_related("cliente", "usuario", "detalleFactura__transaccion")
                        .get(id=factura_id))
    tx = factura.detalleFactura.transaccion

    # Buscar el siguiente dNumDoc utilizable
    dnumdoc = sql.find_reusable_dnumdoc(est, pun, start, end)
    if not dnumdoc:
        return {"ok": False, "reason": "No hay dNumDoc reutilizable en rango."}

    params = _build_params_from_tx(tx, dnumdoc)

    with transaction.atomic():
        # Insertar nuevo DE en proxy
        new_de_id = sql.insert_de(params)
        sql.insert_acteco(new_de_id, actividades=[("62010", "Actividades de programación informática")])
        sql.insert_items(new_de_id, params.items)
        if params.cond_ope == "1":
            sql.insert_pago_contado(new_de_id, items=params.items)

        # Actualizar Factura con nuevo DE/Num y volver a 'emitida'
        Factura.objects.filter(id=factura.id).update(
            de_id=new_de_id,
            d_num_doc=dnumdoc,
            est=params.timbrado.est,
            pun=params.timbrado.pun_exp,
            estado="emitida",
            # Opcional: limpiar adjuntos si querés re-descargar tras aprobar
            # xml_file=None, pdf_file=None
        )

        # Confirmar el nuevo borrador para que el proxy procese
        sql.confirmar_borrador(new_de_id)

    return {"ok": True, "factura_id": factura.id, "new_de_id": new_de_id, "d_num_doc": dnumdoc}
