# webapp/services/invoice_from_tx.py
from datetime import datetime
from django.conf import settings
from django.db import transaction
from webapp.models import DocSequence, Transaccion, Factura, DetalleFactura
from webapp.services import invoice_sql as sql
from webapp.services.dto import InvoiceParams, TimbradoDTO, EmisorDTO, ReceptorDTO, ItemDTO

def _int_py(value) -> str:
    return str(int(round(float(value))))  # PYG sin decimales

def generate_invoice_for_transaccion(transaccion: Transaccion) -> dict:
    if transaccion.factura_asociada_id:
        return {"already": True, "factura_id": transaccion.factura_asociada_id}

    # 1) Todo el flujo bajo una transacción del default (incluye tomar número)
    with transaction.atomic():
        # 1.1) Tomar número con lock
        seq = DocSequence.objects.select_for_update().get(est="001", pun="003")
        if seq.current_num >= seq.max_num:
            raise RuntimeError("Rango de documentos agotado (151–200).")
        seq.current_num += 1
        dNumDoc = str(seq.current_num).zfill(7)
        seq.save(update_fields=["current_num"])

        # 1.2) Armar timbrado/emisor/receptor/ítems (igual que antes)
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
        tiene_ruc = bool(cli.ruc)
        receptor = ReceptorDTO(
            nat_rec="1", ti_ope="1", pais="PRY",
            ti_cont_rec="2" if tiene_ruc else "1",
            ruc=(cli.ruc or ""), dv="0",
            tip_id="0", dtipo_id="", num_id=(cli.documento or ""),
            nombre=(cli.razonSocial or cli.nombre),
            dir=(cli.direccion or ""), num_casa="",
            dep_cod="1", dep_desc="CAPITAL",
            ciu_cod="1", ciu_desc="ASUNCION (DISTRITO)",
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
            iAfecIVA="1", dPropIVA="100", dTasaIVA="10"
        )]
        params = InvoiceParams(
            timbrado=timb, emisor=emisor, receptor=receptor, items=items,
            fecha_emision=datetime.now(),
            tip_emi="1", tip_tra="1", t_imp="1", moneda="PYG",
            ind_pres="1", cond_ope="1", plazo_cre=""
        )

        # 1.3) Crear tu Factura/Detalle en la misma transacción del default
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
            estado="emitida"  # vamos a aprobar luego si sale bien el proxy
        )
        transaccion.factura_asociada = factura
        transaccion.save(update_fields=["factura_asociada"])

    # 2) Ahora hacemos los INSERTS al SQL-Proxy con su propio atomic (db fs_proxy)
    de_id = sql.insert_de(params)
    sql.insert_acteco(de_id, actividades=[("46510", "COMERCIO AL POR MAYOR DE EQUIPOS INFORMÁTICOS Y SOFTWARE")])
    sql.insert_items(de_id, params.items)
    if params.cond_ope == "1":
        sql.insert_pago_contado(de_id)
    sql.confirmar_borrador(de_id)

    # 3) Si todo bien en el proxy, aprobamos tu Factura (default DB)
    Factura.objects.filter(id=factura.id).update(estado="aprobada")

    return {"already": False, "de_id": de_id, "factura_id": factura.id, "dNumDoc": dNumDoc}