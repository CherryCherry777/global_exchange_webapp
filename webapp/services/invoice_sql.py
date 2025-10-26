# webapp/services/invoice_sql.py
from django.db import connections, transaction
from webapp.services.dto import InvoiceParams, ItemDTO

def _cur():
    return connections["fs_proxy"].cursor()

def insert_de(params: InvoiceParams) -> int:
    """
    Inserta un registro de documento electrónico (DE) en la base del SQL-Proxy.
    Devuelve el ID del registro creado.
    """
    conn = connections["fs_proxy"]
    with conn.cursor() as cur:
        t = params.timbrado
        e = params.emisor
        r = params.receptor

        # Fecha actual (o la de emisión si se pasa explícita)
        fecha_emision = params.fecha_emision.strftime("%Y-%m-%dT%H:%M:%S")

        sql = """
        INSERT INTO public.de (
            dnumtim, dest, dpunexp, dnumdoc,
            dsisfact,
            iTipEmi, dDesTipEmi, dCodSeg,
            iTiDE, dDesTiDE, dFeEmiDE,
            iTipTra, dDesTipTra, iTImp, dDesTImp, cMoneOpe, dDesMoneOpe,
            dRucEm, dDVEmi, iTipCont, cTipReg, dNomEmi, dDirEmi, dNumCas,
            cDepEmi, dDesDepEmi, cCiuEmi, dDesCiuEmi, dTelEmi, dEmailE,
            cActEco, dDesActEco,
            iNatRec, iTiOpe, cPaisRec, dDesPaisRe, iTiContRec,
            dRucRec, dDVRec, dNomRec, dEmailRec, dDirRec, dNumCasRec,
            cDepRec, dDesDepRec, cCiuRec, dDesCiuRec,
            iIndPres, iCondOpe, dPlazoCre, dSisFact, dInfAdic, dSerieNum
        )
        VALUES (
            '150', %s, %s, %s, %s,
            %s, '1',
            %s, %s, '000000001',
            %s, %s, %s,
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s,
            %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, '1', '', %s
        )
        RETURNING id;
        """

        cur.execute(
            sql,
            [
                # --- Datos del timbrado ---
                t.num_tim, t.est, t.pun_exp, t.num_doc,
                fecha_emision,
                # --- Datos generales ---
                params.tip_emi, "Normal",  # iTipEmi / dDesTipEmi
                t.iTiDE, "Factura electrónica", fecha_emision,
                params.tip_tra, "Venta de mercadería",
                params.t_imp, "IVA",
                params.moneda, "Guaraní" if params.moneda == "PYG" else params.moneda,
                # --- Emisor ---
                e.ruc, e.dv, e.tip_cont, e.cTipReg,
                e.nombre, e.dir, e.num_casa,
                e.dep_cod, e.dep_desc, e.ciu_cod, e.ciu_desc,
                e.tel, e.email,
                "46510", "COMERCIO AL POR MAYOR DE EQUIPOS INFORMÁTICOS Y SOFTWARE",
                # --- Receptor ---
                r.nat_rec, r.ti_ope, r.pais, "Paraguay", r.ti_cont_rec,
                r.ruc, r.dv, r.nombre, r.email,
                r.dir, r.num_casa, r.dep_cod, r.dep_desc, r.ciu_cod, r.ciu_desc,
                # --- Operación ---
                params.ind_pres, params.cond_ope, (params.plazo_cre or ""), t.serie
            ],
        )

        de_id = cur.fetchone()[0]
        conn.commit()

    print(f"✅ Documento electrónico insertado (ID={de_id})")
    return de_id

def insert_acteco(de_id: int, actividades: list[tuple[str,str]]):
    if not actividades:
        actividades = [("46510", "COMERCIO AL POR MAYOR DE EQUIPOS INFORMÁTICOS Y SOFTWARE")]
    with transaction.atomic(using="fs_proxy"):
        with _cur() as cur:
            vals = []
            for (c, d) in actividades:
                vals.extend([c, d, de_id])
            placeholders = ",".join(["(%s,%s,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP,%s)"] * (len(vals)//3))
            cur.execute(f"""
                INSERT INTO public.gActEco (cActEco, dDesActEco, fch_ins, fch_upd, de_id)
                VALUES {placeholders};
            """, vals)

def insert_items(de_id: int, items: list[ItemDTO]):
    with transaction.atomic(using="fs_proxy"):
        with _cur() as cur:
            rows = []
            for it in items:
                rows.extend([
                    it.cod_int, it.descripcion, it.cantidad, it.precio_unit, it.desc_item,
                    it.iAfecIVA, it.dPropIVA, it.dTasaIVA,
                    "", "", "", "", "", "",
                    de_id
                ])
            placeholders = ",".join(["(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP,%s)"] * (len(rows)//17))
            cur.execute(f"""
                INSERT INTO public.gCamItem
                (dCodInt, dDesProSer, dCantProSer, dPUniProSer, dDescItem,
                 iAfecIVA, dPropIVA, dTasaIVA,
                 dParAranc, dNCM, dDncpG, dDncpE, dGtin, dGtinPq,
                 fch_ins, fch_upd, de_id)
                VALUES {placeholders};
            """, rows)

def insert_pago_contado(de_id: int):
    with transaction.atomic(using="fs_proxy"):
        with _cur() as cur:
            cur.execute("""
                INSERT INTO public.gPaConEIni
                (iTiPago, dMonTiPag, cMoneTiPag, dTiCamTiPag, dNumCheq, dBcoEmi, iDenTarj, iForProPa, fch_ins, fch_upd, de_id)
                VALUES ('1','0','PYG','1','','','','',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP,%s);
            """, [de_id])

def confirmar_borrador(de_id: int):
    with transaction.atomic(using="fs_proxy"):
        with _cur() as cur:
            cur.execute("UPDATE public.de SET estado='Confirmado' WHERE id=%s AND estado='Borrador';", [de_id])
