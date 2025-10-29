# webapp/services/invoice_sync.py
import os
import re
import base64
import requests
from datetime import datetime
from typing import Optional, Tuple
from django.conf import settings
from django.core.files import File
from django.db import transaction
from webapp.models import Factura
from webapp.services import fs_proxy as sql  # tu wrapper DB del proxy
from django.utils import timezone
from django.core.files.base import ContentFile
from django.contrib import messages
from celery import current_app as celery_app
from django.core.cache import cache



# --- HTTP helpers (proxy en proyecto separado) ---

def _auth_header() -> dict:
    user = settings.KUDE_USER if hasattr(settings, "KUDE_USER") else None
    pwd  = settings.KUDE_PASS if hasattr(settings, "KUDE_PASS") else None
    if not (user and pwd):
        # también intentamos por variables env con prefijo FS_PROXY_
        user = getattr(settings, "FS_PROXY_KUDE_USER", None)
        pwd  = getattr(settings, "FS_PROXY_KUDE_PASS", None)
    if not (user and pwd):
        raise RuntimeError("Faltan KUDE_USER/KUDE_PASS o FS_PROXY_KUDE_USER/FS_PROXY_KUDE_PASS en settings.")
    token = base64.b64encode(f"{user}:{pwd}".encode()).decode()
    return {"Authorization": f"Basic {token}"}

def _proxy_base_url() -> str:
    url = getattr(settings, "FS_PROXY_WEB_URL", None)
    if not url:
        raise RuntimeError("Falta FS_PROXY_WEB_URL en settings.")
    return url.rstrip("/")

def _yyyymm_from_fch_sifen(fch_sifen: Optional[str]) -> str:
    # fch_sifen esperado: 'YYYY-MM-DD HH:MM:SS'
    try:
        dt = datetime.strptime((fch_sifen or ""), "%Y-%m-%d %H:%M:%S")
    except Exception:
        dt = datetime.now()
    return f"{dt.year:04d}{dt.month:02d}"

def _prefijo_kude(est: str, pun: str, dnumdoc: str) -> str:
    return f"{str(est).zfill(3)}-{str(pun).zfill(3)}-{str(dnumdoc).zfill(7)}-"

def _http_list_kude_month(yyyymm: str) -> str:
    """
    Devuelve el HTML de índice de /kude/YYYYMM/ para parsear los nombres de archivo.
    """
    url = f"{_proxy_base_url()}/kude/{yyyymm}/"
    r = requests.get(url, headers=_auth_header(), timeout=15)
    r.raise_for_status()
    return r.text

def _find_kude_files_in_index(html: str, prefix: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Busca enlaces <a href="..."> que contengan el prefijo y terminen en .xml / .pdf
    Retorna (xml_name, pdf_name) si encuentra, sino None.
    """
    # Match muy permisivo sobre href="filename"
    hrefs = re.findall(r'href=["\']([^"\']+)["\']', html, flags=re.IGNORECASE)
    xml = next((h for h in hrefs if h.lower().endswith(".xml") and h.startswith(prefix)), None)
    pdf = next((h for h in hrefs if h.lower().endswith(".pdf") and h.startswith(prefix)), None)
    return xml, pdf

def _http_download_to_filefield(yyyymm: str, filename: str, dst_field, save_instance=False):
    """
    Descarga /kude/YYYYMM/filename y graba en un FileField (xml_file o pdf_file).
    """
    url = f"{_proxy_base_url()}/kude/{yyyymm}/{filename}"
    r = requests.get(url, headers=_auth_header(), timeout=20)
    r.raise_for_status()
    # guardamos sin tocar el filesystem local
    dst_field.save(filename, File(io.BytesIO(r.content)), save=save_instance)

# Necesitamos io para envolver bytes en File
import io

# --- Sincronización ---

@transaction.atomic
def sync_factura_de(factura: Factura) -> dict:
    """
    Sincroniza ESTADO y adjunta XML/PDF desde el PROXY (proyecto separado) vía HTTP.
    Requiere en settings:
      FS_PROXY_WEB_URL, FS_PROXY_KUDE_USER, FS_PROXY_KUDE_PASS
    Y en Factura: de_id, d_num_doc, est, pun, xml_file, pdf_file
    """
    if not getattr(factura, "de_id", None):
        if not _try_backfill_de_id(factura):
            return {"ok": False, "reason": "Factura sin de_id."}


    estatus = sql.get_de_status(factura.de_id)
    if not estatus:
        return {"ok": False, "reason": "DE no encontrado en proxy."}

    estado_sifen = estatus.get("estado_sifen")
    desc_sifen   = estatus.get("desc_sifen")
    fch_sifen    = estatus.get("fch_sifen")

    # map a estados locales
    if estado_sifen == "Aprobado":
        nuevo_estado = "aprobada"
    elif estado_sifen == "Rechazado":
        nuevo_estado = "rechazada"
    else:
        nuevo_estado = "emitida"

    # Actualizar estado si cambió
    if factura.estado != nuevo_estado:
        Factura.objects.filter(id=factura.id).update(estado=nuevo_estado)
        factura.estado = nuevo_estado

    xml_saved = False
    pdf_saved = False
    xml_name = None
    pdf_name = None

    # Si Aprobado: bajar archivos por HTTP
    if nuevo_estado == "aprobada":
        yyyymm = _yyyymm_from_fch_sifen(fch_sifen)
        pref = _prefijo_kude(factura.est, factura.pun, factura.d_num_doc)

        try:
            index_html = _http_list_kude_month(yyyymm)
            xml_name, pdf_name = _find_kude_files_in_index(index_html, pref)
        except Exception as e:
            return {
                "ok": True,
                "estado_app": nuevo_estado,
                "estado_sifen": estado_sifen,
                "desc_sifen": desc_sifen,
                "fch_sifen": fch_sifen,
                "warn": f"No se pudo listar /kude/{yyyymm}/: {e!r}",
            }

        # Descargar y adjuntar si corresponde
        if xml_name and not factura.xml_file:
            try:
                _http_download_to_filefield(yyyymm, xml_name, factura.xml_file, save_instance=False)
                xml_saved = True
            except Exception as e:
                xml_name = None  # falló
        if pdf_name and not factura.pdf_file:
            try:
                _http_download_to_filefield(yyyymm, pdf_name, factura.pdf_file, save_instance=False)
                pdf_saved = True
            except Exception as e:
                pdf_name = None

        if xml_saved or pdf_saved:
            factura.save(update_fields=["xml_file", "pdf_file"])

    return {
        "ok": True,
        "factura_id": factura.id,
        "de_id": factura.de_id,
        "estado_app": factura.estado,
        "estado_sifen": estado_sifen,
        "desc_sifen": desc_sifen,
        "fch_sifen": fch_sifen,
        "xml_saved": xml_saved,
        "pdf_saved": pdf_saved,
        "xml_name": xml_name,
        "pdf_name": pdf_name,
    }

def _is_numdoc_aprobado_case(de_status: dict) -> bool:
    """
    Detecta el caso de número ya aprobado, según los datos reales del proxy:
      - estado == 'Verificar datos (Rech.Apr.)'
      - o error_sifen contiene 'NUMDOC_APROBADO'
    """
    estado = (de_status.get("estado") or "").strip()
    err = (de_status.get("error_sifen") or "").upper()
    return estado == "Verificar datos (Rech.Apr.)" or ("NUMDOC_APROBADO" in err)

def _attach_if_approved(factura: Factura, de_status: dict) -> tuple[bool, bool, str | None, str | None]:
    """
    Si está Aprobado, adjunta XML/PDF desde el KUDE. Devuelve flags y nombres.
    """
    from webapp.services.invoice_sync import attach_kude_files_to_factura, _to_yyyymm

    if (de_status.get("estado_sifen") or "").strip() != "Aprobado" and (de_status.get("estado") or "").strip() != "Aprobado":
        return (False, False, None, None)

    yyyymm = None
    # preferimos fch_sifen
    if de_status.get("fch_sifen"):
        yyyymm = _to_yyyymm(de_status["fch_sifen"])

    res = attach_kude_files_to_factura(factura, yyyymm=yyyymm)
    if res.get("ok"):
        return (bool(res["attached"].get("xml")), bool(res["attached"].get("pdf")),
                res["attached"].get("xml"), res["attached"].get("pdf"))
    return (False, False, None, None)

def sync_facturas_pendientes(
    limit: int = 200,
    *,
    fetch_files: bool | None = None,
    attach_docs: bool | None = None,
    fetch_files_on_approved: bool | None = None,
    **kwargs,
) -> dict:
    """
    Sincroniza facturas (emitida/rechazada) contra el proxy SIFEN y, si quedan 'Aprobadas',
    puede adjuntar automáticamente XML/PDF.

    Parámetros compatibles (backward-compatible):
      - fetch_files
      - attach_docs
      - fetch_files_on_approved
    Cualquiera de ellos activa el adjunto de archivos si es True.
    """

    # --- Normalización de flags de adjunto (compatibilidad hacia atrás) ---
    # Prioridad: fetch_files > attach_docs > fetch_files_on_approved
    if fetch_files is None:
        if attach_docs is not None:
            fetch_files = bool(attach_docs)
        elif fetch_files_on_approved is not None:
            fetch_files = bool(fetch_files_on_approved)
        else:
            # Valor por defecto: adjuntar archivos cuando la factura quede aprobada
            fetch_files = True
            
    qs = (Factura.objects
          .filter(estado__in=["emitida", "rechazada"])
          .exclude(de_id__isnull=True)
          .order_by("id"))

    if limit:
        qs = qs[:limit]

    detalles = []
    aprobadas = rechazadas = con_archivos = procesadas = 0

    for fac in qs:
        try:
            de = sql.get_de_status(fac.de_id)  # {id, dRucEm, dEst, dPunExp, dNumDoc, estado, estado_sifen, desc_sifen, error_sifen, fch_sifen}
            if not de:
                detalles.append({"factura_id": fac.id, "ok": False, "reason": "DE no encontrado en proxy."})
                continue

            # Actualizar dNumDoc/est/pun locales si vienen del proxy
            d_est = (de.get("dEst") or fac.est or "").strip() or "001"
            d_pun = (de.get("dPunExp") or fac.pun or "").strip() or "003"
            d_num = (de.get("dNumDoc") or fac.d_num_doc or "").strip()
            if d_num and (fac.est != d_est or fac.pun != d_pun or fac.d_num_doc != d_num):
                Factura.objects.filter(id=fac.id).update(est=d_est, pun=d_pun, d_num_doc=d_num)
                fac.est, fac.pun, fac.d_num_doc = d_est, d_pun, d_num

            estado_sifen = (de.get("estado_sifen") or "").strip()
            estado = (de.get("estado") or "").strip()
            desc_sifen = (de.get("desc_sifen") or "").strip()
            fch_sifen = de.get("fch_sifen")

            xml_saved = pdf_saved = False
            xml_name = pdf_name = None

            # Caso aprobado
            if estado_sifen == "Aprobado" or estado == "Aprobado":
                if fac.estado != "aprobada":
                    Factura.objects.filter(id=fac.id).update(estado="aprobada")
                    fac.estado = "aprobada"
                    aprobadas += 1
                # intentar adjuntar XML/PDF
                x_ok, p_ok, x_name, p_name = _attach_if_approved(fac, de)
                xml_saved, pdf_saved = x_ok, p_ok
                xml_name, pdf_name = x_name, p_name
                if x_ok or p_ok:
                    con_archivos += 1

            else:
                # Detectar caso NUMDOC_APROBADO tal como se da en tu proxy
                if _is_numdoc_aprobado_case(de):
                    # evitar encolar muchas veces en poco tiempo para la misma factura
                    lock_key = f"retry_numdoc_lock:{fac.id}"
                    if cache.add(lock_key, "1", timeout=300):  # 5 minutos
                        try:
                            # import interno para evitar circular
                            from webapp.tasks import reintentar_factura_numdoc_task
                            reintentar_factura_numdoc_task.delay(fac.id)
                        except Exception as e:
                            detalles.append({"factura_id": fac.id, "ok": False, "reason": f"no se pudo encolar retry: {e!r}"})
                    # marcar como rechazada localmente para que el usuario vea el estado transitorio
                    if fac.estado != "rechazada":
                        Factura.objects.filter(id=fac.id).update(estado="rechazada")
                        fac.estado = "rechazada"
                        rechazadas += 1
                else:
                    # Otros estados → solo reflejar si vino 'Rechazado' en estado_sifen
                    if estado_sifen == "Rechazado" and fac.estado != "rechazada":
                        Factura.objects.filter(id=fac.id).update(estado="rechazada")
                        fac.estado = "rechazada"
                        rechazadas += 1

            detalles.append({
                "factura_id": fac.id,
                "ok": True,
                "de_id": fac.de_id,
                "estado_app": fac.estado,
                "estado_sifen": estado_sifen or estado or None,
                "desc_sifen": desc_sifen or None,
                "fch_sifen": fch_sifen,
                "xml_saved": xml_saved,
                "pdf_saved": pdf_saved,
                "xml_name": xml_name,
                "pdf_name": pdf_name,
            })
            procesadas += 1

        except Exception as e:
            detalles.append({"factura_id": fac.id, "ok": False, "error": repr(e)})

    return {
        "ok": True,
        "procesadas": procesadas,
        "aprobadas": aprobadas,
        "rechazadas": rechazadas,
        "con_archivos": con_archivos,
        "detalles": detalles,
    }


def _try_backfill_de_id(factura: Factura) -> bool:
    """
    Intenta rellenar de_id/est/pun/d_num_doc para facturas antiguas.
    Heurística: usa dEmailRec (correo del cliente) y toma el DE más reciente.
    """
    email_rec = getattr(factura.cliente, "correo", None)
    if not email_rec:
        return False

    hit = sql.find_recent_de_by_email(email_rec, around_date=factura.fechaEmision or timezone.now().date())
    if not hit:
        return False

    Factura.objects.filter(id=factura.id).update(
        de_id=hit["id"],
        est=str(hit["est"]).zfill(3),
        pun=str(hit["pun"]).zfill(3),
        d_num_doc=str(hit["dnumdoc"]).zfill(7),
    )
    # refrescamos el objeto en memoria
    factura.de_id = hit["id"]
    factura.est = str(hit["est"]).zfill(3)
    factura.pun = str(hit["pun"]).zfill(3)
    factura.d_num_doc = str(hit["dnumdoc"]).zfill(7)
    return True


def _to_yyyymm(dt) -> Optional[str]:
    if not dt:
        return None
    # dt puede venir como str 'YYYY-mm-dd HH:MM:SS' o como date/datetime
    try:
        if isinstance(dt, str):
            return dt[:7].replace("-", "")
        return dt.strftime("%Y%m")
    except Exception:
        return None

def attach_kude_files_to_factura(factura, yyyymm: str | None = None):
    """
    Busca XML/PDF del KUDE y los adjunta a la Factura.
    - Si 'yyyymm' no se pasa, se intenta con: fch_sifen (DE) -> fechaEmision -> ahora.
    - Acepta nombres con '-' o '_' después del d_num_doc.
    - Devuelve dict con flags, meses probados y nombres adjuntados.
    """
    import os
    import requests
    from django.utils import timezone
    from django.core.files.base import ContentFile
    from webapp.services import fs_proxy as sql  # por si el import no está en el módulo

    def _name_matches(name: str, est: str, pun: str, d_num_doc: str) -> bool:
        pref_dash = f"{est}-{pun}-{d_num_doc}-"
        pref_und  = f"{est}-{pun}-{d_num_doc}_"
        return name.startswith(pref_dash) or name.startswith(pref_und)

    if not (getattr(factura, "est", None) and getattr(factura, "pun", None) and getattr(factura, "d_num_doc", None)):
        return {"ok": False, "reason": "Factura sin est/pun/d_num_doc."}
    if not getattr(factura, "de_id", None):
        return {"ok": False, "reason": "Factura sin de_id."}

    # 1) Mes desde SIFEN (DE)
    de_status = sql.get_de_status(factura.de_id) or {}
    yyyymm_sifen = _to_yyyymm(de_status.get("fch_sifen"))

    # 2) Mes desde la fecha de emisión local
    yyyymm_emision = _to_yyyymm(getattr(factura, "fechaEmision", None))

    # 3) Mes actual
    yyyymm_now = timezone.now().strftime("%Y%m")

    tried = []
    candidates = []
    if yyyymm:
        candidates.append(yyyymm)
    for cand in (yyyymm_sifen, yyyymm_emision, yyyymm_now):
        if cand and cand not in candidates:
            candidates.append(cand)

    found = []
    last_cand = None
    listed_samples = []

    for cand in candidates:
        tried.append(cand)
        last_cand = cand
        try:
            files = sql.fetch_kude_files(factura.est, factura.pun, factura.d_num_doc, yyyymm=cand)
        except requests.HTTPError as e:
            # Si el índice del mes no existe, probamos el siguiente mes candidato
            if e.response is not None and e.response.status_code == 404:
                continue
            # 401/403/5xx u otros: error claro
            code = e.response.status_code if e.response is not None else "N/A"
            return {"ok": False, "reason": f"Error HTTP {code} al listar {cand}."}

        # Guardamos una muestra para depuración
        listed_samples = [f["name"] for f in (files or [])][:10]

        # Filtrar por nombre que empiece con est-pun-d_num_doc- o con _
        matches = [f for f in files if _name_matches(f["name"], factura.est, factura.pun, factura.d_num_doc)]
        if matches:
            found = matches
            break

    if not found:
        return {
            "ok": False,
            "reason": f"No se encontraron archivos en meses {tried}.",
            "listed_samples": listed_samples
        }

    # Elegir XML y/o PDF (case-insensitive)
    xml = next((f for f in found if f["name"].lower().endswith(".xml")), None)
    pdf = next((f for f in found if f["name"].lower().endswith(".pdf")), None)

    if not xml and not pdf:
        return {
            "ok": False,
            "reason": f"Se listaron archivos en {last_cand} pero no hubo .xml/.pdf para el prefijo.",
            "listed_samples": [f["name"] for f in found][:10]
        }

    # Descarga + guarda en FileField(s)
    auth_user = os.getenv("FS_PROXY_KUDE_USER") or ""
    auth_pass = os.getenv("FS_PROXY_KUDE_PASS") or ""
    auth = (auth_user, auth_pass) if (auth_user or auth_pass) else None

    updated = {}
    if xml:
        rx = requests.get(xml["url"], auth=auth, timeout=20)
        rx.raise_for_status()
        factura.xml_file.save(xml["name"], ContentFile(rx.content), save=False)
        updated["xml"] = xml["name"]

    if pdf:
        rp = requests.get(pdf["url"], auth=auth, timeout=20)
        rp.raise_for_status()
        factura.pdf_file.save(pdf["name"], ContentFile(rp.content), save=False)
        updated["pdf"] = pdf["name"]

    factura.save(update_fields=["xml_file", "pdf_file"])
    return {"ok": True, "yyyymm": last_cand, "attached": updated, "tried": tried}



def _name_matches(name: str, est: str, pun: str, d_num_doc: str) -> bool:
    pref_dash = f"{est}-{pun}-{d_num_doc}-"
    pref_und  = f"{est}-{pun}-{d_num_doc}_"
    return name.startswith(pref_dash) or name.startswith(pref_und)


def _enqueue_retry_numdoc(factura_id: int) -> bool:
    try:
        celery_app.send_task(
            "webapp.tasks.reintentar_factura_numdoc_task",
            args=[factura_id],
            countdown=2,
        )
        return True
    except Exception as e:
        print(f"[sync_facturas] No pude encolar reintento NUMDOC: {e!r}")
        return False