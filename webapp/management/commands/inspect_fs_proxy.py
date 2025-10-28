# webapp/management/commands/inspect_fs_proxy.py
from django.core.management.base import BaseCommand
from django.db import connections
import csv
from pathlib import Path

COLUMNS_SQL = """
SELECT
    c.table_schema,
    c.table_name,
    c.column_name,
    c.data_type,
    c.character_maximum_length,
    c.numeric_precision,
    c.numeric_scale,
    c.is_nullable,
    c.column_default,
    c.ordinal_position
FROM information_schema.columns c
WHERE c.table_schema = %s
ORDER BY c.table_name, c.ordinal_position;
"""

TABLES_SQL = """
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_schema = %s AND table_type='BASE TABLE'
ORDER BY table_name;
"""

CONSTRAINTS_SQL = """
SELECT
    t.table_schema,
    t.table_name,
    c.conname AS constraint_name,
    CASE c.contype
        WHEN 'p' THEN 'PRIMARY KEY'
        WHEN 'u' THEN 'UNIQUE'
        WHEN 'f' THEN 'FOREIGN KEY'
        WHEN 'c' THEN 'CHECK'
        WHEN 'x' THEN 'EXCLUDE'
        ELSE c.contype::text
    END AS constraint_type,
    pg_get_constraintdef(c.oid, true) AS definition
FROM pg_constraint c
JOIN pg_class r      ON r.oid = c.conrelid
JOIN information_schema.tables t
  ON t.table_name = r.relname AND t.table_schema = %s
ORDER BY t.table_name, constraint_type, constraint_name;
"""

class Command(BaseCommand):
    help = "Inspecciona el esquema de la base fs_proxy y exporta columnas y constraints."

    def add_arguments(self, parser):
        parser.add_argument("--schema", default="public", help="Esquema a inspeccionar (default: public)")
        parser.add_argument("--out", default="fs_proxy_schema", help="Prefijo/carpeta de salida (default: fs_proxy_schema)")
        parser.add_argument("--format", choices=["txt","md"], default="txt", help="Imprime resumen en consola en txt/md")

    def handle(self, *args, **opts):
        schema = opts["schema"]
        out_dir = Path(opts["out"])
        out_dir.mkdir(parents=True, exist_ok=True)

        with connections["fs_proxy"].cursor() as cur:
            # Tablas
            cur.execute(TABLES_SQL, [schema])
            tables = cur.fetchall()

            # Columnas
            cur.execute(COLUMNS_SQL, [schema])
            columns = cur.fetchall()

            # Constraints
            cur.execute(CONSTRAINTS_SQL, [schema])
            constraints = cur.fetchall()

        # Guardar tablas
        (out_dir / "tables.txt").write_text(
            "\n".join(f"{sch}.{tbl}" for sch, tbl in tables),
            encoding="utf-8"
        )

        # Guardar columnas
        cols_path = out_dir / "columns.csv"
        with cols_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([
                "table_schema","table_name","column_name","data_type","char_max_len",
                "numeric_precision","numeric_scale","is_nullable","column_default","ordinal_position"
            ])
            for row in columns:
                w.writerow(row)

        # Guardar constraints
        cons_path = out_dir / "constraints.csv"
        with cons_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["table_schema","table_name","constraint_name","constraint_type","definition"])
            for row in constraints:
                w.writerow(row)

        # Resumen por consola
        if opts["format"] == "md":
            self._print_markdown(tables, columns, constraints)
        else:
            self._print_text(tables, columns, constraints)

        self.stdout.write(self.style.SUCCESS(f"OK. Archivos generados en: {out_dir.resolve()}"))
        self.stdout.write(f"- {cols_path.name}\n- {cons_path.name}\n- tables.txt")

    # ---- helpers de impresión ----
    def _print_text(self, tables, columns, constraints):
        tbls = [t[1] for t in tables]
        self.stdout.write("== Tablas ==\n" + ", ".join(tbls) + "\n")

        self.stdout.write("== Resumen columnas (primeras por tabla) ==")
        by_tbl = {}
        for (sch, tbl, col, dt, cmax, nprec, nsc, nul, dflt, ordpos) in columns:
            by_tbl.setdefault(tbl, []).append((col, dt, cmax, nul, dflt))
        for tbl in by_tbl:
            self.stdout.write(f"\n[{tbl}]")
            for (col, dt, cmax, nul, dflt) in by_tbl[tbl][:8]:
                self.stdout.write(f"  - {col}: {dt}({cmax or ''}) NULL={nul} DEFAULT={dflt}")

        self.stdout.write("\n== Constraints por tabla ==")
        for (sch, tbl, cname, ctype, defn) in constraints:
            self.stdout.write(f"  [{tbl}] {ctype} {cname} :: {defn}")

    def _print_markdown(self, tables, columns, constraints):
        self.stdout.write("# Tablas\n")
        for sch, tbl in tables:
            self.stdout.write(f"- `{sch}.{tbl}`")
        self.stdout.write("\n\n# Columnas (primeras por tabla)\n")
        by_tbl = {}
        for (sch, tbl, col, dt, cmax, nprec, nsc, nul, dflt, ordpos) in columns:
            by_tbl.setdefault(tbl, []).append((col, dt, cmax, nul, dflt))
        for tbl in by_tbl:
            self.stdout.write(f"\n## {tbl}\n")
            self.stdout.write("| Columna | Tipo | MaxLen | NULL | Default |\n|---|---|---:|:-:|---|\n")
            for (col, dt, cmax, nul, dflt) in by_tbl[tbl][:12]:
                self.stdout.write(f"| `{col}` | `{dt}` | {cmax or ''} | {nul} | `{dflt or ''}` |\n")
        self.stdout.write("\n\n# Constraints\n")
        self.stdout.write("| Tabla | Tipo | Nombre | Definición |\n|---|---|---|---|\n")
        for (sch, tbl, cname, ctype, defn) in constraints:
            self.stdout.write(f"| `{tbl}` | {ctype} | `{cname}` | `{defn}` |\n")
