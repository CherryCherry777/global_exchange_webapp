# webapp/services/fs_proxy.py
from django.db import connection, connections, transaction
import base64, os, requests

FS_PROXY_WEB_URL = os.getenv("FS_PROXY_WEB_URL")
KUDE_USER = os.getenv("FS_PROXY_KUDE_USER")
KUDE_PASS = os.getenv("FS_PROXY_KUDE_PASS")

def _cursor():
    return connections["fs_proxy"].cursor()

def esi_exists() -> bool:
    with _cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM public.esi;")
        return cur.fetchone()[0] > 0

def delete_all_esi() -> None:
    with transaction.atomic(using="fs_proxy"):
        with _cursor() as cur:
            cur.execute("DELETE FROM public.esi;")

def insert_esi(*, ruc: str, ruc_dv: str, nombre: str, descripcion: str,
               esi_email: str, esi_passwd: str, ambiente: str) -> None:
    ambiente = ambiente.strip().upper()
    if ambiente not in ("TEST", "PROD"):
        raise ValueError("Ambiente debe ser TEST o PROD")
    esi_url = "https://apitest.facturasegura.com.py" if ambiente == "TEST" else "https://api.facturasegura.com.py"
    with transaction.atomic(using="fs_proxy"):
        with _cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.esi
                (ruc, ruc_dv, nombre, descripcion, estado, esi_email, esi_passwd, esi_token, esi_url)
                VALUES (%s, %s, %s, %s, 'ACTIVO', %s, %s, '', %s);
                """,
                [ruc, ruc_dv, nombre, descripcion, esi_email, esi_passwd, esi_url],
            )

def get_de_status(de_id: int):
    with _cursor() as cur:
        cur.execute("SELECT id, estado, dNumDoc, dFeEmiDE FROM public.de WHERE id = %s;", [de_id])
        row = cur.fetchone()
        if not row:
            return None
        return {"id": row[0], "estado": row[1], "dNumDoc": row[2], "dFeEmiDE": row[3]}

def fetch_kude_index_html() -> str:
    if not (FS_PROXY_WEB_URL and KUDE_USER and KUDE_PASS):
        raise RuntimeError("Faltan FS_PROXY_WEB_URL/KUDE_USER/KUDE_PASS")
    auth = base64.b64encode(f"{KUDE_USER}:{KUDE_PASS}".encode()).decode()
    r = requests.get(f"{FS_PROXY_WEB_URL}/kude/", headers={"Authorization": f"Basic {auth}"}, timeout=15)
    r.raise_for_status()
    return r.text

def _c1(val, default='0'):
    v = (val or '').strip()
    return v[:1] if v else default

def _s(val, maxlen=255):
    return ((val or '')[:maxlen]).strip()

def insert_de(params):
    timb, emi, rec = params.timbrado, params.emisor, params.receptor

    iNatRec  = _c1(rec.nat_rec, '2')
    iTiOpe   = _c1(rec.ti_ope, '2') if iNatRec == '2' else _c1(rec.ti_ope, '1')
    cPaisRec = 'PRY'

    if iNatRec == '1':  # contribuyente
        iTiContRec = _c1(rec.ti_cont_rec, '1')   # 1 PF / 2 PJ
        dRucRec = _s(rec.ruc, 20)
        dDVRec  = _c1(rec.dv, '0')
        iTipIDRec = '0'
        dDTipIDRec = ''
        dNumIDRec = ''
    else:               # no contribuyente
        iTiContRec = ''                      # NO None
        dRucRec = ''                         # NO None
        dDVRec  = ''                         # NO None
        iTipIDRec  = _c1(rec.tip_id, '1')
        dDTipIDRec = ''
        dNumIDRec  = _s(rec.num_id, 20) or '0'

    with _cursor() as cur:
        cur.execute("""
            INSERT INTO public.de (
              iTiDE, dFeEmiDE, dEst, dPunExp, dNumDoc, CDC, dSerieNum, estado,
              estado_sifen, desc_sifen, error_sifen, fch_sifen, estado_can, desc_can, error_can, fch_can,
              estado_inu, desc_inu, error_inu, fch_inu,
              iTipEmi, dNumTim, dFeIniT, iTipTra, iTImp, cMoneOpe, dTiCam, dInfoFisc, dRucEm, dDVEmi,
              iTipCont, dNomEmi, dDirEmi, dNumCas, cDepEmi, dDesDepEmi, cCiuEmi, dDesCiuEmi, dTelEmi, dEmailE,
              iNatRec, iTiOpe, cPaisRec, iTiContRec, dRucRec, dDVRec, iTipIDRec, dDTipIDRec, dNumIDRec,
              dNomRec, dEmailRec, dDirRec, dNumCasRec, cDepRec, dDesDepRec, cCiuRec, dDesCiuRec,
              iIndPres, iCondOpe, dPlazoCre, dSisFact, dInfAdic,
              fch_ins, fch_upd
            ) VALUES (
              %s, CURRENT_DATE, %s, %s, %s, %s, %s, %s,
              %s, %s, %s, %s, %s, %s, %s, %s,
              %s, %s, %s, %s,
              %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
              %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
              %s, %s, %s, %s, %s, %s, %s, %s, %s,
              %s, %s, %s, %s, %s, %s, %s, %s,
              %s, %s, %s, %s, %s,
              CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
            RETURNING id;
        """, (
            timb.iTiDE, timb.est, timb.pun_exp, timb.num_doc, '0', '', 'Confirmado',
            '', '', '', '', '', '', '', '',
            '', '', '', '',
            '1', timb.num_tim, timb.fe_ini_t, '1', '1', 'PYG', '1', emi.info_fisc, emi.ruc, emi.dv,
            '2', emi.nombre, emi.dir, emi.num_casa, emi.dep_cod, emi.dep_desc, emi.ciu_cod, emi.ciu_desc, emi.tel, emi.email,
            iNatRec, iTiOpe, cPaisRec, iTiContRec, dRucRec, dDVRec, iTipIDRec, dDTipIDRec, dNumIDRec,
            _s(rec.nombre,255), _s(rec.email,200), _s(rec.dir,255), '', '1','CAPITAL','1','ASUNCION (DISTRITO)',
            _c1(params.ind_pres,'1'), _c1(params.cond_ope,'1'), _s(params.plazo_cre,60), '1', _s(getattr(params, 'inf_adic', ''), 500),
        ))
        de_id = cur.fetchone()[0]
    return de_id