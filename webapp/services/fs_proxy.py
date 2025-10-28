# webapp/services/fs_proxy.py
import os, base64, requests, logging
from datetime import datetime
from django.db import connections, transaction
import os

logger = logging.getLogger(__name__)

FS_PROXY_WEB_URL = os.getenv("FS_PROXY_WEB_URL")
KUDE_USER = os.getenv("FS_PROXY_KUDE_USER")
KUDE_PASS = os.getenv("FS_PROXY_KUDE_PASS")

def _cursor():
    return connections["fs_proxy"].cursor()

def _env_true(name: str) -> bool:
    return str(os.getenv(name, "")).strip().lower() in ("1", "true", "yes", "on")

# === Helpers de formato/longitud ===
def _c1(val, default='0'):
    v = (val or '').strip()
    return v[:1] if v else default

def _s(val, maxlen):
    return ((val or '')[:maxlen]).strip()

def _pad_left(num_str: str, total: int) -> str:
    return (str(num_str or '').strip()).zfill(total)

# === ESI helpers (sin cambios) ===
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
            cur.execute("""
                INSERT INTO public.esi
                (ruc, ruc_dv, nombre, descripcion, estado, esi_email, esi_passwd, esi_token, esi_url)
                VALUES (%s, %s, %s, %s, 'ACTIVO', %s, %s, '', %s);
            """, [ruc, ruc_dv, nombre, descripcion, esi_email, esi_passwd, esi_url])

# === Lecturas rápidas ===
def get_de_status(de_id: int):
    with _cursor() as cur:
        cur.execute("SELECT id, estado, dNumDoc, dFeEmiDE FROM public.de WHERE id = %s;", [de_id])
        row = cur.fetchone()
        if not row:
            return None
        return {"id": row[0], "estado": row[1], "dNumDoc": row[2], "dFeEmiDE": row[3]}

def get_dnumdoc(de_id: int):
    with _cursor() as cur:
        cur.execute("SELECT dNumDoc FROM public.de WHERE id = %s;", [de_id])
        r = cur.fetchone()
        return r[0] if r else None

# === KUDE (sin cambios) ===
def fetch_kude_index_html() -> str:
    if not (FS_PROXY_WEB_URL and KUDE_USER and KUDE_PASS):
        raise RuntimeError("Faltan FS_PROXY_WEB_URL/KUDE_USER/KUDE_PASS")
    auth = base64.b64encode(f"{KUDE_USER}:{KUDE_PASS}".encode()).decode()
    r = requests.get(f"{FS_PROXY_WEB_URL}/kude/", headers={"Authorization": f"Basic {auth}"}, timeout=15)
    r.raise_for_status()
    return r.text

# === INSERT principal (ajustes según aprobado) ===
def insert_de(params):
    timb = params.timbrado
    emi  = params.emisor
    rec  = params.receptor

    # FECHA como YYYY-MM-DD (tu aprobado muestra '2025-10-26')
    dFeEmiDE  = datetime.now().strftime("%Y-%m-%d")       # varchar(20), solo fecha
    dNumDoc   = _pad_left(timb.num_doc, 7)
    dNumTim   = _pad_left(timb.num_tim, 8)
    dFeIniT   = _s(timb.fe_ini_t, 20)
    dTiCam    = _s('1', 20)
    dRucEm    = _s(emi.ruc, 20)
    dDVEmi    = _c1(emi.dv, '0')

    # Receptor
    iNatRec   = _c1(rec.nat_rec, '2')
    iTiOpe    = _c1(rec.ti_ope, '2' if iNatRec == '2' else '1')
    cPaisRec  = 'PRY'

    if iNatRec == '1':  # contribuyente
        iTiContRec = _c1(rec.ti_cont_rec, '1')  # 1 PF / 2 PJ
        dRucRec    = _s(rec.ruc, 20)
        dDVRec     = _c1(rec.dv, '0')
        iTipIDRec  = '0'
        dDTipIDRec = None
        dNumIDRec  = None
    else:
        iTiContRec = ''
        dRucRec    = ''
        dDVRec     = ''
        iTipIDRec  = _c1(rec.tip_id, '1')
        dDTipIDRec = ''
        dNumIDRec  = _s(rec.num_id, 20) or '0'

    dNomRec   = _s(rec.nombre, 255)
    dEmailRec = _s(rec.email, 200)
    dDirRec   = _s(rec.dir, 20)  # tu BD lo limita a 20

    # Emisor/demás (calce con aprobado)
    iTipCont  = '2'
    iTipTra   = _c1(getattr(params, "tip_tra", "1"), '1')  # aprobado usa 1
    iTImp     = _c1(getattr(params, "t_imp", "1"), '1')    # aprobado usa 1
    cMoneOpe  = 'PYG'

    with _cursor() as cur:
        cur.execute("""
            INSERT INTO public.de (
              iTiDE, dFeEmiDE, dEst, dPunExp, dNumDoc, CDC, dSerieNum, estado,
              estado_sifen, desc_sifen, error_sifen, fch_sifen, estado_can, desc_can, error_can, fch_can,
              estado_inu, desc_inu, error_inu, fch_inu,
              iTipEmi, dNumTim, dFeIniT, iTipTra, iTImp, cMoneOpe, dTiCam, dInfoFisc, dRucEm, dDVEmi,
              iTipCont, dNomEmi, dDirEmi, dNumCas,
              cDepEmi, dDesDepEmi, cCiuEmi, dDesCiuEmi, dTelEmi, dEmailE,
              iNatRec, iTiOpe, cPaisRec, iTiContRec, dRucRec, dDVRec, iTipIDRec, dDTipIDRec, dNumIDRec,
              dNomRec, dEmailRec, dDirRec, dNumCasRec, cDepRec, dDesDepRec, cCiuRec, dDesCiuRec,
              iIndPres, iCondOpe, dPlazoCre, dSisFact, dInfAdic,
              dSecCont, dFeCodCont, dIniTras, dFinTras, dTiVehTras, dMarVeh, dRucTrans,
              fch_ins, fch_upd
            )
            VALUES (
              %s, %s, %s, %s, %s, %s, %s, %s,
              %s, %s, %s, %s, %s, %s, %s, %s,
              %s, %s, %s, %s,
              %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
              %s, %s, %s, %s,
              %s, %s, %s, %s, %s, %s,
              %s, %s, %s, %s, %s, %s, %s, %s, %s,
              %s, %s, %s, %s, %s, %s, %s, %s,
              %s, %s, %s, %s, %s,
              %s, %s, %s, %s, %s, %s, %s,
              CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
            RETURNING id;
        """, (
            timb.iTiDE, dFeEmiDE, timb.est, timb.pun_exp, dNumDoc, '0', '', 'Confirmado',
            '', '', '', '', '', '', '', '',
            '', '', '', '',
            '1', dNumTim, dFeIniT, iTipTra, iTImp, cMoneOpe, dTiCam, emi.info_fisc, dRucEm, dDVEmi,
            iTipCont, emi.nombre, emi.dir, emi.num_casa,
            emi.dep_cod, emi.dep_desc, emi.ciu_cod, emi.ciu_desc, emi.tel, emi.email,
            iNatRec, iTiOpe, cPaisRec, iTiContRec, dRucRec, dDVRec, iTipIDRec, dDTipIDRec, dNumIDRec,
            dNomRec, dEmailRec, dDirRec, '', '1', 'CAPITAL', '1', 'ASUNCION (DISTRITO)',
            _c1(params.ind_pres, '1'), _c1(params.cond_ope, '1'), _s(params.plazo_cre, 20), '1', _s(getattr(params, 'inf_adic', ''), 500),
            '', None, None, None, None, None, None,
        ))
        de_id = cur.fetchone()[0]
    return de_id

def insert_acteco(de_id: int, actividades):
    if not actividades:
        return True
    with _cursor() as cur:
        for cod, desc in actividades:
            cur.execute("""
                INSERT INTO public.gActEco (cActEco, dDesActEco, fch_ins, fch_upd, de_id)
                VALUES (%s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, %s);
            """, (_s(cod, 10), _s(desc, 255), de_id))
    return True

def _to_int(s, default=0):
    try:
        return int(str(s).strip())
    except Exception:
        return default

def insert_items(de_id: int, items):
    if not items:
        return True
    with _cursor() as cur:
        for it in items:
            dCodInt     = _s(getattr(it, "cod_int", "CAM/DIV"), 60)
            dDesProSer  = _s(getattr(it, "descripcion", "Servicio"), 500)
            dCantProSer = _s(str(getattr(it, "cantidad", "1")), 20)
            dPUniProSer = _s(str(getattr(it, "precio_unit", "0")), 20)
            dDescItem   = _s(str(getattr(it, "desc_item", "0")), 20)

            # EXENTO 100% (override por seguridad)
            iAfecIVA    = '3'
            dPropIVA    = '0'
            dTasaIVA    = '0'

            cur.execute("""
                INSERT INTO public.gCamItem (
                  dCodInt, dDesProSer, dCantProSer, dPUniProSer, dDescItem,
                  iAfecIVA, dPropIVA, dTasaIVA,
                  dParAranc, dNCM, dDncpG, dDncpE, dGtin, dGtinPq,
                  fch_ins, fch_upd, de_id
                ) VALUES (
                  %s, %s, %s, %s, %s,
                  %s, %s, %s,
                  %s, %s, %s, %s, %s, %s,
                  CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, %s
                );
            """, (
                dCodInt, dDesProSer, dCantProSer, dPUniProSer, dDescItem,
                iAfecIVA, dPropIVA, dTasaIVA,
                '', '', '', '', '', '',
                de_id
            ))
    return True

def _calc_total_items(items) -> int:
    if not items:
        return 0
    total = 0
    for it in items:
        cant = _to_int(getattr(it, "cantidad", 1), 1)
        pun  = _to_int(getattr(it, "precio_unit", 0), 0)
        desc = _to_int(getattr(it, "desc_item", 0), 0)
        total += max(cant * pun - desc, 0)
    return total

def insert_pago_contado(de_id: int, items=None, moneda="PYG", ti_cam="1"):
    total = _calc_total_items(items) if items else 0
    with _cursor() as cur:
        cur.execute("""
            INSERT INTO public.gPaConEIni (
              iTiPago, dMonTiPag, cMoneTiPag, dTiCamTiPag,
              dNumCheq, dBcoEmi, iDenTarj, iForProPa,
              fch_ins, fch_upd, de_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s,
                      CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, %s);
        """, ('1', _s(str(total), 20), _s(moneda, 10), _s(str(ti_cam), 20), '', '', '', '', de_id))
    return True

def confirmar_borrador(de_id: int):
    with _cursor() as cur:
        cur.execute("""
            UPDATE public.de
            SET estado = 'Confirmado', fch_upd = CURRENT_TIMESTAMP
            WHERE id = %s;
        """, (de_id,))
    return True

# === Utilidades para reintentos (traer/actualizar como en tu JSON aprobado) ===

def get_de_payload(de_id: int):
    """
    Devuelve dict con 'de', 'items', 'pagos', 'actividades' similar a tu JSON aprobado.
    """
    with _cursor() as cur:
        cur.execute("SELECT * FROM public.de WHERE id = %s;", [de_id])
        de_row = cur.fetchone()
        if not de_row:
            return None
        de_cols = [d[0] for d in cur.description]
        de = dict(zip(de_cols, de_row))

        cur.execute("SELECT * FROM public.gCamItem WHERE de_id = %s ORDER BY id;", [de_id])
        items = [dict(zip([d[0] for d in cur.description], r)) for r in cur.fetchall()]

        cur.execute("SELECT * FROM public.gPaConEIni WHERE de_id = %s ORDER BY id;", [de_id])
        pagos = [dict(zip([d[0] for d in cur.description], r)) for r in cur.fetchall()]

        cur.execute("SELECT * FROM public.gActEco WHERE de_id = %s ORDER BY id;", [de_id])
        acts = [dict(zip([d[0] for d in cur.description], r)) for r in cur.fetchall()]

    # Normaliza claves a minúsculas como tu JSON de ejemplo
    norm = lambda d: {k.lower(): v for k, v in d.items()}
    return {"de": norm(de), "items": [norm(x) for x in items], "pagos": [norm(x) for x in pagos], "actividades": [norm(x) for x in acts]}

def update_de_for_retry(
    de_id: int, *,
    ruc_rec: str = None, dv_rec: str = None,
    cActEco: str = None, dDesActEco: str = None,
    set_items_exentos: bool = True,
):
    """
    Aplica cambios mínimos para reintentar: RUC/DV receptor, ActEco y exención en ítems.
    """
    with transaction.atomic(using="fs_proxy"):
        with _cursor() as cur:
            if ruc_rec is not None:
                cur.execute("""
                    UPDATE public.de
                    SET dRucRec = %s
                    WHERE id = %s;
                """, (ruc_rec, de_id))
            if dv_rec is not None:
                cur.execute("""
                    UPDATE public.de
                    SET dDVRec = %s
                    WHERE id = %s;
                """, (dv_rec, de_id))
            if set_items_exentos:
                cur.execute("""
                    UPDATE public.gCamItem
                    SET iAfecIVA = '3', dTasaIVA = '0', dPropIVA = '0'
                    WHERE de_id = %s;
                """, (de_id,))
            if cActEco and dDesActEco:
                cur.execute("DELETE FROM public.gActEco WHERE de_id = %s;", (de_id,))
                cur.execute("""
                    INSERT INTO public.gActEco (cActEco, dDesActEco, fch_ins, fch_upd, de_id)
                    VALUES (%s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, %s);
                """, (cActEco, dDesActEco, de_id))
    return True

def reset_sifen_and_confirm(de_id: int):
    with transaction.atomic(using="fs_proxy"):
        with _cursor() as cur:
            cur.execute("""
                UPDATE public.de
                SET estado_sifen = NULL, desc_sifen = NULL, error_sifen = NULL, fch_sifen = NULL
                WHERE id = %s;
            """, (de_id,))
            cur.execute("""
                UPDATE public.de
                SET estado = 'Confirmado', fch_upd = CURRENT_TIMESTAMP
                WHERE id = %s;
            """, (de_id,))
    return True
