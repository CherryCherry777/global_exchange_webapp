# webapp/management/commands/fix_rejected_de.py
from django.core.management.base import BaseCommand
from django.db import connections, transaction
from django.conf import settings
from datetime import datetime
import re, logging, os

# === Configuración de logging ===
LOG_DIR = os.path.join(settings.BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOG_DIR, "fix_rejected_de.log")

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# === Utilidades auxiliares ===
def _cursor():
    return connections["fs_proxy"].cursor()

def _s(val, maxlen):
    return (val or "")[:maxlen].strip()

def _c1(val, default='0'):
    v = (val or '')
    v = str(v).strip()
    return v[:1] if v else default

def _pad_left(num_str: str, total: int) -> str:
    return str(num_str or "").strip().zfill(total)

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

def _parse_ruc_force_zero(raw):
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
        base, dv = parts[0], "0"
    base = base.lstrip("0") or "0"
    return base, dv

def _ensure_datetime_iso(dt):
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%dT%H:%M:%S")
    s = str(dt or "").strip()
    if "T" in s:
        return s.split(".")[0]
    if " " in s:
        return s.split(".")[0].replace(" ", "T")
    return s + "T00:00:00" if re.match(r"^\d{4}-\d{2}-\d{2}$", s) else s

def _valid_timbrado(num):
    return isinstance(num, str) and num.isdigit() and len(num) == 8


class Command(BaseCommand):
    help = "Corrige y reintenta una DE rechazada en fs_proxy. Crea log detallado en logs/fix_rejected_de.log"

    def add_arguments(self, parser):
        parser.add_argument("--id", type=int, help="ID de la tabla public.de a reparar")
        parser.add_argument("--cdc", type=str, help="CDC de la DE a reparar en vez de id")
        parser.add_argument("--apply", action="store_true", help="Si se pasa, aplica los cambios; si no, solo dry-run")

    def handle(self, *args, **opts):
        de_id = opts.get("id")
        cdc = opts.get("cdc")
        apply_changes = opts.get("apply", False)

        if not de_id and not cdc:
            raise SystemExit("Debes pasar --id o --cdc")

        try:
            # === Paso 1: Obtener DE ===
            with _cursor() as cur:
                if de_id:
                    cur.execute("SELECT * FROM public.de WHERE id = %s;", [de_id])
                else:
                    cur.execute("SELECT * FROM public.de WHERE cdc = %s;", [cdc])
                row = cur.fetchone()
                if not row:
                    raise SystemExit("No se encontró la DE indicada en fs_proxy.public.de")

                cur.execute("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_schema='public' AND table_name='de'
                    ORDER BY ordinal_position;
                """)
                cols = [r[0] for r in cur.fetchall()]
                de = dict(zip(cols, row))

            msg_header = f"[DE #{de.get('id')}] Estado={de.get('estado')} CDC={de.get('cdc')}"
            self.stdout.write(self.style.NOTICE(msg_header))
            logger.info(f"=== INICIO REPARACIÓN {msg_header} ===")

            updates = {}
            notes = []

            # === Paso 2: Normalizaciones ===
            base, dv = _parse_ruc_force_zero(de.get("drucrec"))
            if base:
                updates["drucrec"] = base
                updates["ddvrec"] = dv
                notes.append(f"Normalizado RUC receptor: {base}-{dv}")
            else:
                notes.append("No hay RUC receptor válido")

            feini = de.get("dfeinit") or de.get("dFeIniT")
            femi_iso = _ensure_datetime_iso(de.get("dfeemide") or datetime.now())
            updates["dfeemide"] = femi_iso
            notes.append(f"Fecha emisión ajustada: {femi_iso}")

            dnumtim = de.get("dnumtim")
            if not _valid_timbrado(str(dnumtim or "")):
                tim = getattr(settings, "SIFEN_TIMBRADO_TEST_NUM", "80143335")
                updates["dnumtim"] = tim
                notes.append(f"Timbrado inválido -> reemplazado por {tim}")

            dirrec = de.get("ddirrec") or ""
            dirrec_cut = _s(dirrec, 20)
            updates["ddirrec"] = dirrec_cut
            if dirrec != dirrec_cut:
                notes.append(f"Truncado dDirRec a '{dirrec_cut}'")

            updates["desc_sifen"] = ""
            updates["error_sifen"] = ""
            updates["fch_sifen"] = ""

            # === Paso 3: Mostrar plan ===
            self.stdout.write("\n--- Plan de cambios ---")
            for k, v in updates.items():
                self.stdout.write(f"  {k} => {v}")
            for n in notes:
                self.stdout.write("  * " + n)
            logger.info("Cambios planificados: %s", updates)
            logger.info("Notas: %s", notes)

            if not apply_changes:
                self.stdout.write(self.style.WARNING("Dry-run: no se aplicaron cambios. Usa --apply para confirmar."))
                logger.info("Dry-run finalizado sin aplicar cambios.")
                return

            # === Paso 4: Aplicar cambios ===
            with transaction.atomic(using="fs_proxy"):
                with _cursor() as cur:
                    # a) update DE
                    if updates:
                        set_clause = ", ".join(f"{col} = %s" for col in updates.keys())
                        params = list(updates.values()) + [de["id"]]
                        cur.execute(f"UPDATE public.de SET {set_clause} WHERE id = %s;", params)
                        logger.info("Actualizado public.de con %d campos", len(updates))

                    # b) reemplazar gActEco
                    cur.execute("DELETE FROM public.gActEco WHERE de_id = %s;", [de["id"]])
                    cur.execute("""
                        INSERT INTO public.gActEco (cActEco, dDesActEco, fch_ins, fch_upd, de_id)
                        VALUES (%s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, %s);
                    """, ("66190", "Actividades auxiliares de servicios financieros n.c.p. (casa de cambios)", de["id"]))
                    logger.info("gActEco actualizado con 66190")

                    # c) ítems exentos
                    cur.execute("UPDATE public.gCamItem SET iAfecIVA='3', dPropIVA='0', dTasaIVA='0' WHERE de_id=%s;", [de["id"]])
                    logger.info("gCamItem actualizado (IVA exento)")

                    # d) recalcular pago contado
                    cur.execute("SELECT SUM(CAST(dPUniProSer AS INTEGER)) FROM public.gCamItem WHERE de_id=%s;", [de["id"]])
                    total = cur.fetchone()[0] or 0
                    cur.execute("UPDATE public.gPaConEIni SET dMonTiPag=%s WHERE de_id=%s;", (str(total), de["id"]))
                    logger.info("gPaConEIni total=%s", total)

                    # e) marcar confirmada
                    cur.execute("UPDATE public.de SET estado='Confirmado', fch_upd=CURRENT_TIMESTAMP WHERE id=%s;", [de["id"]])
                    logger.info("DE marcada como Confirmado para reintento.")

            self.stdout.write(self.style.SUCCESS("Cambios aplicados correctamente. Revisar logs/fix_rejected_de.log"))
            logger.info("Reparación completada exitosamente para DE #%s", de["id"])

        except Exception as e:
            logger.exception("Error procesando DE #%s: %s", de_id or cdc, e)
            self.stderr.write(self.style.ERROR(f"ERROR: {e}"))
            self.stderr.write(self.style.WARNING(f"Revisar {LOG_PATH} para más detalles."))
