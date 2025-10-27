# app/services/sifen_repo.py
from django.db import connections, transaction
from datetime import datetime
from typing import Optional

EST = "001"
PUNEXP = "003"
RANGO_INI = 151
RANGO_FIN = 200
TIMBRADO = "02595733"    # ajusta si corresponde
FE_INI_TIM = "2025-03-27"

def _fetchone(cur):
    row = cur.fetchone()
    return row[0] if row else None

def _sig_numdoc(cur) -> str:
    """
    Calcula el próximo dNumDoc como string 7 dígitos, entre 151..200.
    Busca el máximo actual para Est/Px, lo incrementa y valida rango.
    """
    cur.execute("""
        SELECT MAX(dNumDoc) 
        FROM public.de 
        WHERE dEst=%s AND dPunExp=%s
          AND dNumDoc ~ '^[0-9]{7}$';
    """, [EST, PUNEXP])
    max_str = _fetchone(cur)
    if max_str is None:
        nxt = RANGO_INI
    else:
        try:
            nxt = int(max_str) + 1
        except ValueError:
            nxt = RANGO_INI
        if nxt < RANGO_INI:
            nxt = RANGO_INI
    if nxt > RANGO_FIN:
        raise ValueError("Rango de facturación agotado (151–200).")
    return f"{nxt:07d}"

def _calc_base_iva10(total_pyg: int) -> tuple[int,int]:
    base = round(total_pyg / 1.1)
    iva  = total_pyg - base
    return base, iva

def emitir_de_simple(*, 
    total_pyg: int,
    descripcion_item: str,
    receptor_ruc: Optional[str],
    receptor_dv: Optional[str],
    receptor_nombre: str,
    email_receptor: Optional[str] = None,
) -> dict:
    """
    Inserta filas en de, gCamItem, gActEco, gPaConEIni y confirma el DE.
    Devuelve dict con {id_de, dNumDoc, numero, estado}.
    Nota: CDC lo generará tu backend/daemon cuando procese 'Confirmado' (si aplica).
    """
    if total_pyg <= 0:
        raise ValueError("total_pyg debe ser > 0")

    with transaction.atomic(using="sifen"):
        con = connections["sifen"]
        cur = con.cursor()

        dNumDoc = _sig_numdoc(cur)
        dFeEmiDE = datetime.now().strftime("%Y-%m-%d")

        # === INSERT DE (estado=Borrador) ===
        cur.execute("""
        INSERT INTO public.de
        (iTiDE, dFeEmiDE, dEst, dPunExp, dNumDoc, CDC, dSerieNum, estado,
         estado_sifen, desc_sifen, error_sifen, fch_sifen, estado_can, desc_can, error_can, fch_can, estado_inu, desc_inu, error_inu, fch_inu,
         iTipEmi, dNumTim, dFeIniT, iTipTra, iTImp, cMoneOpe, dTiCam, dInfoFisc, dRucEm, dDVEmi,
         iTipCont, dNomEmi, dDirEmi, dNumCas,
         cDepEmi, dDesDepEmi, cCiuEmi, dDesCiuEmi, dTelEmi, dEmailE,
         iNatRec, iTiOpe, cPaisRec, iTiContRec, dRucRec, dDVRec, iTipIDRec, dDTipIDRec, dNumIDRec,
         dNomRec, dEmailRec,
         fch_ins, fch_upd)
        VALUES (
         %s, %s, %s, %s, %s, '0', '', 'Borrador',
         '','','','','','','','','','','',
         %s, %s, %s, %s, %s, 'PYG', '1', '', '2595733', '3',
         '1', 'DE generado en ambiente de prueba - sin valor comercial ni fiscal', 'YVAPOVO C/ TOBATI', '1543',
         '1','CAPITAL','1','ASUNCION (DISTRITO)','(0961)988439','ggonzar@gmail.com',
         '1','1','PRY','1', %s, %s, '0','', '0',
         %s, %s,
         CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        )
        RETURNING id;
        """, [
            '1', dFeEmiDE, EST, PUNEXP, dNumDoc,
            '1', TIMBRADO, FE_INI_TIM, '2', '5',
            receptor_ruc or None, receptor_dv or None,
            receptor_nombre, email_receptor or None
        ])
        de_id = _fetchone(cur)

        # === Actividades económicas (mínimo 1) ===
        cur.execute("""
        INSERT INTO public.gActEco
        (cActEco, dDesActEco, fch_ins, fch_upd, de_id) VALUES
        ('62010','Actividades de programación informática', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, %s);
        """, [de_id])

        # === Ítem único, gravado 10% ===
        base, iva = _calc_base_iva10(total_pyg)
        cur.execute("""
        INSERT INTO public.gCamItem
        (dCodInt, dDesProSer, dCantProSer, dPUniProSer, dDescItem,
         iAfecIVA, dPropIVA, dTasaIVA,
         fch_ins, fch_upd, de_id)
        VALUES
        (%s, %s, '1', %s, '0',
         '1', '100', '10',
         CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, %s);
        """, ['1', descripcion_item, str(total_pyg), de_id])

        # === Forma de pago contado PYG ===
        cur.execute("""
        INSERT INTO public.gPaConEIni
        (iTiPago, dMonTiPag, cMoneTiPag, dTiCamTiPag,
         dNumCheq, dBcoEmi,
         iDenTarj, iForProPa,
         fch_ins, fch_upd, de_id)
        VALUES('1', %s, 'PYG', '1', '', '', '', '',
               CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, %s);
        """, [str(total_pyg), de_id])

        # === Confirmar DE ===
        cur.execute("""
        UPDATE public.de
        SET estado='Confirmado', fch_upd=CURRENT_TIMESTAMP
        WHERE id=%s AND estado='Borrador';
        """, [de_id])

        # número “visual”: 001-003-0000xxx
        numero = f"{EST}-{PUNEXP}-{dNumDoc}"

        return {"id_de": de_id, "dNumDoc": dNumDoc, "numero": numero, "estado": "Confirmado"}
