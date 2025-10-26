# webapp/services/dto.py
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class EmisorDTO:
    ruc: str
    dv: str
    nombre: str
    dir: str
    num_casa: str
    dep_cod: str
    dep_desc: str
    ciu_cod: str
    ciu_desc: str
    tel: str
    email: str
    tip_cont: str = "2"
    cTipReg: str = "3"      # <- NUEVO: tipo de registro del emisor (p.ej. 3 = Contribuyente)
    info_fisc: str = ""

@dataclass
class ReceptorDTO:
    nat_rec: str
    ti_ope: str
    pais: str
    ti_cont_rec: str
    ruc: Optional[str] = ""
    dv: Optional[str] = ""
    tip_id: str = "0"
    dtipo_id: str = ""
    num_id: str = ""
    nombre: str = ""
    dir: str = ""
    num_casa: str = ""
    dep_cod: str = ""
    dep_desc: str = ""
    ciu_cod: str = ""
    ciu_desc: str = ""
    email: str = ""
    tel: str = ""

@dataclass
class TimbradoDTO:
    iTiDE: str
    num_tim: str
    est: str
    pun_exp: str
    num_doc: str
    serie: str = ""
    fe_ini_t: str = "2024-04-17"

@dataclass
class ItemDTO:
    cod_int: str
    descripcion: str
    cantidad: str
    precio_unit: str
    desc_item: str
    iAfecIVA: str
    dPropIVA: str
    dTasaIVA: str

@dataclass
class InvoiceParams:
    timbrado: TimbradoDTO
    emisor: EmisorDTO
    receptor: ReceptorDTO
    items: List[ItemDTO]
    fecha_emision: datetime
    tip_emi: str = "1"
    tip_tra: str = "1"
    t_imp: str = "1"
    moneda: str = "PYG"
    ind_pres: str = "1"
    cond_ope: str = "1"
    plazo_cre: str = ""
