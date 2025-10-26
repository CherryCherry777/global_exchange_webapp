from django.db import connections
from datetime import datetime

def generar_factura_sqlproxy(numero_doc: str, cliente: dict, items: list):
    """
    Genera una factura electrónica en el SQL-Proxy de FacturaSegura.
    Usa la conexión 'facturasegura' definida en settings.DATABASES.
    """
    numero_doc = numero_doc.zfill(7)
    fecha_emision = datetime.now().strftime("%Y-%m-%d")

    try:
        with connections["facturasegura"].cursor() as cursor:
            # 1️⃣ Insertar DE (Documento Electrónico)
            cursor.execute(f"""
                INSERT INTO public.de
                (iTiDE, dFeEmiDE, dEst, dPunExp, dNumDoc, estado,
                 iTipEmi, dNumTim, dFeIniT, iTipTra, iTImp,
                 cMoneOpe, dTiCam, dInfoFisc, dRucEm, dDVEmi,
                 iTipCont, dNomEmi, dDirEmi, dNumCas,
                 cDepEmi, dDesDepEmi, cCiuEmi, dDesCiuEmi,
                 dTelEmi, dEmailE, iNatRec, iTiOpe, cPaisRec,
                 dNomRec, dEmailRec,
                 fch_ins, fch_upd)
                VALUES (
                    '1', %s, '001', '001', %s, 'Borrador',
                    '1', '80143335', '2024-04-17', '2', '5',
                    'PYG', '1', '', '80143335', '5',
                    '2', 'AGASE E.A.S.', 'RADIO OPERADORES DEL CHACO CASI JULIANA INSFRAN', '0',
                    '1', 'CAPITAL', '1', 'ASUNCION (DISTRITO)',
                    '(0981)446544', 'soporte@facturasegura.com.py',
                    '1', '1', 'PRY',
                    %s, %s,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
                RETURNING id;
            """, [fecha_emision, numero_doc, cliente["nombre"], cliente["email"]])

            de_id = cursor.fetchone()[0]

            # 2️⃣ Insertar Actividades Económicas (fijas)
            cursor.execute(f"""
                INSERT INTO public.gActEco (cActEco, dDesActEco, fch_ins, fch_upd, de_id)
                VALUES
                ('62010','Actividades de programación informática',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP,{de_id}),
                ('46510','Comercio al por mayor de equipos informáticos y software',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP,{de_id});
            """)

            # 3️⃣ Insertar ítems dinámicos
            for item in items:
                cursor.execute(f"""
                    INSERT INTO public.gCamItem
                    (dCodInt, dDesProSer, dCantProSer, dPUniProSer, dDescItem,
                     iAfecIVA, dPropIVA, dTasaIVA, fch_ins, fch_upd, de_id)
                    VALUES
                    ('1', %s, %s, %s, '0', '1', '100', %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, %s);
                """, [item["descripcion"], item["cantidad"], item["precio"], item["iva"], de_id])

            # 4️⃣ Insertar condiciones de pago (contado)
            cursor.execute(f"""
                INSERT INTO public.gPaConEIni
                (iTiPago, dMonTiPag, cMoneTiPag, dTiCamTiPag, fch_ins, fch_upd, de_id)
                VALUES('1', '0', 'PYG', '1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, {de_id});
            """)

            # 5️⃣ Actualizar a Confirmado
            cursor.execute(f"""
                UPDATE public.de
                SET estado = 'Confirmado'
                WHERE id = {de_id};
            """)

            connections["facturasegura"].commit()

            print(f"Factura generada correctamente en SQL-Proxy (ID={de_id})")
            return de_id

    except Exception as e:
        print(f"❌ Error generando factura en FacturaSegura: {e}")
        return None
