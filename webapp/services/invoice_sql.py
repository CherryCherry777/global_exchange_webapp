# webapp/services/invoice_sql.py
from datetime import datetime
from django.db import connections

# -----------------------------------------------------------
# DE (cabecera) — usa el esquema real de tu tabla public.de
# -----------------------------------------------------------



# -----------------------------------------------------------
# Actividades económicas (gActEco)
# -----------------------------------------------------------
def insert_acteco(de_id: int, actividades=None):
    """
    Inserta actividades económicas en gActEco para el DE.
    `actividades` es lista de tuplas [(cActEco, dDesActEco), ...]
    """
    if not actividades:
        actividades = [("46510", "COMERCIO AL POR MAYOR DE EQUIPOS INFORMÁTICOS Y SOFTWARE")]

    conn = connections["fs_proxy"]
    with conn.cursor() as cur:
        cur.executemany("""
            INSERT INTO public.gActEco
                (cActEco, dDesActEco, fch_ins, fch_upd, de_id)
            VALUES
                (%s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, %s);
        """, [(c, d, de_id) for (c, d) in actividades])
        conn.commit()


# -----------------------------------------------------------
# Ítems (gCamItem)
# -----------------------------------------------------------
def insert_items(de_id: int, items):
    """
    Inserta líneas de ítems en gCamItem.
    Espera `items` como lista de ItemDTO con:
      cod_int, descripcion, cantidad, precio_unit, desc_item, iAfecIVA, dPropIVA, dTasaIVA
    """
    if not items:
        return

    # Campos adicionales (opcionales) que dejaremos vacíos
    vacio = ""

    rows = []
    for it in items:
        rows.append((
            it.cod_int,
            it.descripcion,
            str(it.cantidad),
            str(it.precio_unit),
            str(getattr(it, "desc_item", "0") or "0"),
            str(it.iAfecIVA), str(it.dPropIVA), str(it.dTasaIVA),
            vacio, vacio, vacio, vacio, vacio, vacio,
            de_id,
        ))

    conn = connections["fs_proxy"]
    with conn.cursor() as cur:
        cur.executemany("""
            INSERT INTO public.gCamItem
                (dCodInt, dDesProSer, dCantProSer, dPUniProSer, dDescItem,
                 iAfecIVA, dPropIVA, dTasaIVA,
                 dParAranc, dNCM, dDncpG, dDncpE, dGtin, dGtinPq,
                 fch_ins, fch_upd, de_id)
            VALUES
                (%s, %s, %s, %s, %s,
                 %s, %s, %s,
                 %s, %s, %s, %s, %s, %s,
                 CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, %s);
        """, rows)
        conn.commit()


# -----------------------------------------------------------
# Pago contado (gPaConEIni)
# -----------------------------------------------------------
def insert_pago_contado(de_id: int, monto_total: str = "0", moneda: str = "PYG", tipo_cambio: str = "1"):
    """
    Inserta condición de pago contado en gPaConEIni.
    Por defecto monto 0, moneda PYG, tipo de cambio 1.
    """
    conn = connections["fs_proxy"]
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO public.gPaConEIni
                (iTiPago, dMonTiPag, cMoneTiPag, dTiCamTiPag,
                 dNumCheq, dBcoEmi, iDenTarj, iForProPa,
                 fch_ins, fch_upd, de_id)
            VALUES
                ('1', %s, %s, %s,
                 '', '', '', '',
                 CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, %s);
        """, [str(monto_total), moneda, tipo_cambio, de_id])
        conn.commit()


# -----------------------------------------------------------
# Confirmar borrador → “Confirmado”
# -----------------------------------------------------------
def confirmar_borrador(de_id: int) -> int:
    """
    Pasa el DE de 'Borrador' a 'Confirmado'.
    Devuelve la cantidad de filas afectadas.
    """
    conn = connections["fs_proxy"]
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE public.de
               SET estado = 'Confirmado'
             WHERE estado = 'Borrador'
               AND id = %s;
        """, [de_id])
        rowcount = cur.rowcount
        conn.commit()
    return rowcount

_VARCHAR_LIMITS_CACHE = {}

def _get_varchar_limits(table: str, alias: str = "fs_proxy"):
    key = (alias, table)
    if key not in _VARCHAR_LIMITS_CACHE:
        with connections[alias].cursor() as c:
            c.execute("""
                SELECT column_name, character_maximum_length
                FROM information_schema.columns
                WHERE table_schema='public' AND table_name=%s
                  AND data_type='character varying' AND character_maximum_length IS NOT NULL
            """, [table])
            _VARCHAR_LIMITS_CACHE[key] = dict(c.fetchall())
    return _VARCHAR_LIMITS_CACHE[key]

def _truncate_by_limits(values: dict, table: str, alias: str = "fs_proxy"):
    limits = _get_varchar_limits(table, alias)
    fixed = {}
    for k, v in values.items():
        if v is None:
            fixed[k] = None
            continue
        s = str(v)
        maxlen = limits.get(k)
        if maxlen and len(s) > maxlen:
            # logea qué truncaste
            from datetime import datetime
            with open("error.txt", "a") as f:
                f.write(f"[{datetime.now()}] WARN: Truncating {k} to {maxlen} chars. Original len={len(s)}\n")
            fixed[k] = s[:maxlen]
        else:
            fixed[k] = s
    return fixed
