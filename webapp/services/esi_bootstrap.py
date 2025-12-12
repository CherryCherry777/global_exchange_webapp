# webapp/services/esi_bootstrap.py
from webapp.services import fs_proxy as db

def ensure_esi_global_exchange():
    if db.esi_exists():
        db.delete_all_esi()
    db.insert_esi(
        ruc="2595733",
        ruc_dv="3",
        nombre="Global Exchange",
        descripcion="Casa de Cambios",
        esi_email="equipo8.globalexchange@gmail.com",
        esi_passwd="CAMBIA_ESTA_CLAVE",
        ambiente="TEST"   # o "PROD"
    )
