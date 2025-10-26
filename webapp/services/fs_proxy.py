# webapp/services/fs_proxy.py
from django.db import connections, transaction
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
