# signals.py
from datetime import date
import traceback
from django.conf import settings
from django.db.models.signals import post_migrate, post_save
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from django.contrib.sessions.models import Session

from webapp.services.esi_bootstrap import ensure_esi_global_exchange
from .models import Billetera, BilleteraCobro, ClienteUsuario, CuentaBancariaCobro, Currency, CurrencyDenomination, Entidad, LimiteIntercambioConfig, Categoria, LimiteIntercambioCliente, LimiteIntercambioLog, MedioCobro, Role, MedioPago, TarjetaInternacional, TarjetaNacional, Tauser, TipoCobro, TipoPago, CuentaBancariaNegocio, Transaccion, Cliente, TransaccionAuditoria
from django.contrib.auth.models import Group, Permission
from django.apps import apps
from django.db import connections, transaction
from decimal import Decimal
import logging

from datetime import timedelta

import hashlib
from django.utils import timezone

from django.db.models import Q
from django.core.files.base import ContentFile
import requests

User = get_user_model()
# ================================================================
# CONFIGURACIONES POR DEFECTO
# ================================================================

ROLES_POR_DEFECTO = ["Usuario", "Empleado", "Administrador", "Analista"]

USUARIOS_POR_DEFECTO = [
    {"username": "superadmin2", "password": "password12345", "email": "admin2@example.com", "grupo": "Administrador"},
    {"username": "usuario1", "password": "password12345", "email": "usuario1@example.com", "grupo": "Usuario"},
    {"username": "analista1", "password": "password12345", "email": "analista1@example.com", "grupo": "Analista"},
]

CATEGORIAS_POR_DEFECTO = [
    {"nombre": "Minorista", "descuento": 0},
    {"nombre": "Corporativo", "descuento": 0.05},
    {"nombre": "VIP", "descuento": 0.1},
]

CATEGORIAS_POR_DEFECTO_DESCUENTOS = {
    "Minorista": 0,
    "Corporativo": 0.05,
    "VIP": 0.1
}

CLIENTES_POR_DEFECTO = [
    {
        "tipoCliente": "persona_fisica",
        "nombre": "Cliente Persona",
        "documento": "1234567",
        "correo": "clientep@ejemplo.com",
        "telefono": "123456789",
        "direccion": "Dirección Cliente Persona",
        "categoria": "Minorista",
    },
    {
        "tipoCliente": "persona_juridica",
        "nombre": "Cliente Jurídico Corporativo",
        "razonSocial": "Cliente Corporativo",
        "documento": "5666888",
        "ruc": "5666888-9",
        "correo": "clientej@ejemplo.com",
        "telefono": "123456789",
        "direccion": "Dirección Cliente Jurídico",
        "categoria": "Corporativo",
    },
    {
        "tipoCliente": "persona_juridica",
        "nombre": "Cliente Jurídico VIP",
        "razonSocial": "Cliente VIP",
        "documento": "5666888",
        "ruc": "5666888-9",
        "correo": "clientevip@ejemplo.com",
        "telefono": "123456789",
        "direccion": "Dirección Cliente VIP",
        "categoria": "VIP",
    },
]

DEFAULT_DENOMINATIONS = {
    "PYG": {"bills": [100000, 50000], "coins": []},
    "USD": {"bills": [100, 50], "coins": []},
    "EUR": {"bills": [500, 200, 100, 50], "coins": []},
    "BRL": {"bills": [200, 100], "coins": []},
    "ARS": {"bills": [20000, 10000, 2000, 1000], "coins": []},
}


VALORES_POR_MONEDA = {"PYG": 100000000, "USD": 50000, "EUR": 50000, "BRL": 200000, "ARS": 20000000}
DEFAULT_NO_LISTADA = 0

@receiver(post_migrate)
def clear_sessions(sender, **kwargs):
    Session.objects.all().delete()
    print("✅ All sessions cleared after migration")


# ================================================================
# HELPERS
# ================================================================

def safe_run(title, func):
    """Runs a setup block safely and prints error traceback if any."""
    print(f"\n---- {title} ----")
    try:
        func()
    except Exception as e:
        print(f"❌ Error en {title}: {e}")
        traceback.print_exc()


# ================================================================
# MAIN SIGNAL
# ================================================================

@receiver(post_migrate)
def setup_database(sender, **kwargs):
    if sender.name != "webapp":
        return

    # Import models here (lazy import avoids circulars)
    Categoria = apps.get_model("webapp", "Categoria")
    Cliente = apps.get_model("webapp", "Cliente")
    ClienteUsuario = apps.get_model("webapp", "ClienteUsuario")
    Entidad = apps.get_model("webapp", "Entidad")
    Currency = apps.get_model("webapp", "Currency")
    CurrencyDenomination = apps.get_model("webapp", "CurrencyDenomination")
    LimiteIntercambioConfig = apps.get_model("webapp", "LimiteIntercambioConfig")
    MedioPago = apps.get_model("webapp", "MedioPago")
    MedioCobro = apps.get_model("webapp", "MedioCobro")
    TipoPago = apps.get_model("webapp", "TipoPago")
    TipoCobro = apps.get_model("webapp", "TipoCobro")
    CuentaBancariaNegocio = apps.get_model("webapp", "CuentaBancariaNegocio")
    TarjetaNacional = apps.get_model("webapp", "TarjetaNacional")
    TarjetaInternacional = apps.get_model("webapp", "TarjetaInternacional")
    Billetera = apps.get_model("webapp", "Billetera")
    BilleteraCobro = apps.get_model("webapp", "BilleteraCobro")
    CuentaBancariaCobro = apps.get_model("webapp", "CuentaBancariaCobro")
    Tauser = apps.get_model("webapp", "Tauser")

    # -------------------------------------------------------------
    # BLOQUES DE CONFIGURACIÓN
    # -------------------------------------------------------------

    def setup_roles_y_usuarios():
        for role_name in ROLES_POR_DEFECTO:
            group, _ = Group.objects.get_or_create(name=role_name)
            print(f"✅ Rol '{role_name}' listo.")

        # Permisos del administrador
        admin_group = Group.objects.get(name="Administrador")
        admin_group.permissions.set(Permission.objects.all())

        # Permisos del analista
        analyst_group = Group.objects.get(name="Analista")
        nombres_permisos = [
            "Can change Moneda", "Can view Moneda",
            "Can access analyst panel",
            "Can change Límite de Intercambio", "Can view Límite de Intercambio",
            "Can change Método de Cobro", "Can view Método de Cobro",
            "Can change Medio de Pago", "Can view Medio de Pago",
            "Puede ver los reportes de la empresa"
        ]
        analyst_group.permissions.set(Permission.objects.filter(name__in=nombres_permisos))
        #print(f"✅ Asignados permisos al analista: {Permission.objects.filter(name__in=nombres_permisos)}")

        for data in USUARIOS_POR_DEFECTO:
            user, created = User.objects.get_or_create(username=data["username"], defaults={"email": data["email"]})
            if created:
                user.set_password(data["password"])
                user.is_active = True
                user.save()
                user.groups.add(Group.objects.get(name=data["grupo"]))
                print(f"✅ Usuario '{user.username}' creado.")

    def setup_clientes():
        for cat in CATEGORIAS_POR_DEFECTO:
            Categoria.objects.get_or_create(nombre=cat["nombre"])
            categoria = Categoria.objects.get(nombre=cat["nombre"])
            categoria.descuento = CATEGORIAS_POR_DEFECTO_DESCUENTOS[cat["nombre"]]
            categoria.save()
            print(f"El descuento para la categoria {cat["nombre"]} es {cat["descuento"]}")
        usuario = User.objects.filter(username="usuario1").first()
        if not usuario:
            print("⚠️ Usuario base 'usuario1' no existe todavía.")
            return
        for data in CLIENTES_POR_DEFECTO:
            categoria = Categoria.objects.get(nombre=data["categoria"])
            data["categoria"] = categoria
            cliente, _ = Cliente.objects.get_or_create(nombre=data["nombre"], defaults=data)
            ClienteUsuario.objects.get_or_create(cliente=cliente, usuario=usuario)
            print(f"✅ Cliente '{cliente.nombre}' asignado a '{usuario.username}'.")

    def setup_entidades_y_monedas():
        # -----------------------------
        # ENTIDADES
        # -----------------------------
        bancos = ["Banco Nacional de Paraguay", "Banco Regional", "Banco Continental"]
        billeteras = ["Bancard Wallet", "Tigo Money", "Personal Wallet"]

        for nombre in bancos:
            Entidad.objects.get_or_create(
                nombre=nombre,
                defaults={"tipo": "banco", "activo": True}
            )

        for nombre in billeteras:
            Entidad.objects.get_or_create(
                nombre=nombre,
                defaults={"tipo": "telefono", "activo": True}
            )

        # -----------------------------
        # MONEDAS
        # -----------------------------
        monedas = [
            {"code": "PYG", "name": "Guaraní Paraguayo", "symbol": "G", "base_price": 1.0, "comision_venta": 1.0,
            "comision_compra": 1.0, "decimales_cotizacion": 2, "decimales_monto": 0},
            {"code": "USD", "name": "Dólar Estadounidense", "symbol": "$", "base_price": 7500, "comision_venta": 200,
            "comision_compra": 300, "decimales_cotizacion": 4, "decimales_monto": 2},
            {"code": "EUR", "name": "Euro", "symbol": "€", "base_price": 8000, "comision_venta": 200,
            "comision_compra": 300, "decimales_cotizacion": 4, "decimales_monto": 2},
            {"code": "BRL", "name": "Real Brasileño", "symbol": "R$", "base_price": 1500, "comision_venta": 100,
            "comision_compra": 200, "decimales_cotizacion": 4, "decimales_monto": 2},
            {"code": "ARS", "name": "Peso Argentino", "symbol": "$", "base_price": 5, "comision_venta": 1,
            "comision_compra": 2, "decimales_cotizacion": 4, "decimales_monto": 2},
        ]

        for moneda_data in monedas:
            currency, created = Currency.objects.get_or_create(
                code=moneda_data["code"],
                defaults=moneda_data
            )
            if not created:
                # Update only missing fields
                updated = False
                for key, value in moneda_data.items():
                    if getattr(currency, key, None) in [None, ""]:
                        setattr(currency, key, value)
                        updated = True
                if updated:
                    currency.save()

            # -----------------------------
            # DENOMINACIONES
            # -----------------------------
            for tipo, valores in DEFAULT_DENOMINATIONS.get(currency.code, {}).items():
                tipo_final = tipo[:-1]  # "bills" -> "bill", "coins" -> "coin"
                for v in valores:
                    value = Decimal(str(v))  # normalize
                    try:
                        denom = CurrencyDenomination.objects.get(currency=currency, value=value)
                        updated = False
                        if denom.type != tipo_final:
                            denom.type = tipo_final
                            updated = True
                        if not denom.is_active:
                            denom.is_active = True
                            updated = True
                        if updated:
                            denom.save()
                    except CurrencyDenomination.DoesNotExist:
                        CurrencyDenomination.objects.create(
                            currency=currency,
                            value=value,
                            type=tipo_final,
                            is_active=True
                        )

    def setup_limites():
        for categoria in Categoria.objects.all():
            for moneda in Currency.objects.all():
                limite_dia = limite_mes = Decimal(VALORES_POR_MONEDA.get(moneda.code, DEFAULT_NO_LISTADA))
                
                # Try to get existing config
                obj, created = LimiteIntercambioConfig.objects.get_or_create(
                    categoria=categoria,
                    moneda=moneda,
                    defaults={"limite_dia_max": limite_dia, "limite_mes_max": limite_mes},
                )

                # Only update if the fields are empty / zero
                needs_save = False
                if obj.limite_dia_max == 0:
                    obj.limite_dia_max = limite_dia
                    needs_save = True
                if obj.limite_mes_max == 0:
                    obj.limite_mes_max = limite_mes
                    needs_save = True
                if needs_save:
                    obj.save()


    def setup_tipos_pago_cobro():
        for model, tipos in [
            (TipoPago, ["Billetera", "Cuenta Bancaria", "Tauser", "Tarjeta Nacional", "Tarjeta Internacional"]),
            (TipoCobro, ["Billetera", "Cuenta Bancaria", "Tauser"]),
        ]:
            for nombre in tipos:
                comision = 0.0
                if model == TipoPago:
                    if "Tarjeta" in nombre:
                        comision = 3  # 3% for any card
                    elif "Billetera" in nombre:
                        comision = 2  # 2% for wallets
                else:
                    if "Billetera" in nombre:
                        comision = 2

                model.objects.get_or_create(
                    nombre=nombre,
                    defaults={"activo": True, "comision": comision},
                )

        print("✅ Tipos de pago y cobro listos (con comisiones asignadas).")

    def setup_tauser():
        tipo_pago = TipoPago.objects.filter(nombre__icontains="tauser").first()
        tipo_cobro = TipoCobro.objects.filter(nombre__icontains="tauser").first()
        if tipo_pago and tipo_cobro:
            Tauser.objects.filter(tipo_pago__isnull=True).update(tipo_pago=tipo_pago)
            Tauser.objects.filter(tipo_cobro__isnull=True).update(tipo_cobro=tipo_cobro)
            print("✅ Tipos de pago/cobro asignados a TAUSERs.")

    def setup_cuenta_negocio():
        def create_account():
            moneda = Currency.objects.filter(code="PYG").first()
            banco, _ = Entidad.objects.get_or_create(nombre="Banco Continental", tipo="banco")
            if not CuentaBancariaNegocio.objects.exists():
                CuentaBancariaNegocio.objects.create(
                    numero_cuenta="000100000001",
                    alias_cbu="CUENTA_NEGOCIO_DEFECTO",
                    entidad=banco,
                    moneda=moneda,
                )
                print("✅ Cuenta bancaria del negocio creada.")
        transaction.on_commit(create_account)


    def crear_medios_pago_por_defecto():
        # === Moneda base ===
        moneda_pyg = Currency.objects.filter(code="PYG").first()

        # === Entidades ===
        proveedor_wallet = Entidad.objects.filter(nombre__iexact="Personal Wallet").first()
        banco_continental = Entidad.objects.filter(nombre__iexact="Banco Continental").first()

        # === Clientes por defecto ===
        clientes = Cliente.objects.filter(
            nombre__in=[
                "Cliente Persona",
                "Cliente Jurídico Corporativo",
                "Cliente Jurídico VIP",
            ]
        )

        for cliente in clientes:
            sufijo = cliente.nombre.replace(" ", "_")

            # --- Billetera ---
            nombre_billetera = f"Billetera_{sufijo}"
            if not MedioPago.objects.filter(cliente=cliente, nombre=nombre_billetera).exists():
                medio_billetera = MedioPago.objects.create(
                    cliente=cliente,
                    tipo="billetera",
                    nombre=nombre_billetera,
                    moneda=moneda_pyg,
                    activo=True
                )
                Billetera.objects.create(
                    medio_pago=medio_billetera,
                    numero_celular="123456789",
                    entidad=proveedor_wallet,
                    moneda=moneda_pyg,

                )
                print(f"✅ Billetera creada para {cliente.nombre}")

            # --- Tarjeta Nacional ---
            nombre_tarjeta_nac = f"Tarjeta_Nacional_{sufijo}"
            if not MedioPago.objects.filter(cliente=cliente, nombre=nombre_tarjeta_nac).exists():
                medio_tarjeta_nat = MedioPago.objects.create(
                    cliente=cliente,
                    tipo="tarjeta_nacional",
                    nombre=nombre_tarjeta_nac,
                    moneda=moneda_pyg,
                    activo=True
                )
                TarjetaNacional.objects.create(
                    medio_pago=medio_tarjeta_nat,
                    numero_tokenizado="1234567",
                    fecha_vencimiento=date(2029, 2, 4),
                    ultimos_digitos="4567",
                    entidad=banco_continental,
                    moneda=moneda_pyg,
                )
                print(f"✅ Tarjeta Nacional creada para {cliente.nombre}")

            # --- Tarjeta Internacional ---
            nombre_tarjeta_int = f"Tarjeta_Internacional_{sufijo}"
            if not MedioPago.objects.filter(cliente=cliente, nombre=nombre_tarjeta_int).exists():
                medio_tarjeta_int = MedioPago.objects.create(
                    cliente=cliente,
                    tipo="tarjeta_internacional",
                    nombre=nombre_tarjeta_int,
                    moneda=moneda_pyg,
                    activo=True
                )
                TarjetaInternacional.objects.create(
                    medio_pago=medio_tarjeta_int,
                    stripe_payment_method_id="pm_card_visa",
                    ultimos_digitos="4242",
                    exp_month=4,
                    exp_year=2029,
                )
                print(f"✅ Tarjeta Internacional creada para {cliente.nombre}")

        print("\n🎉 Medios de pago por defecto creados correctamente.\n")

    def crear_medios_cobro_por_defecto():
        tipo_cobro_map = {
            "billetera": "Billetera",
            "cuenta_bancaria": "Cuenta Bancaria",
            "tauser": "Tauser",
        }
        # === Monedas ===
        moneda_pyg = Currency.objects.filter(code="PYG").first()
        moneda_usd = Currency.objects.filter(code="USD").first()

        # === Entidades ===
        proveedor_tigo = Entidad.objects.filter(nombre__iexact="Tigo Money").first()
        banco_nacional = Entidad.objects.filter(nombre__iexact="Banco Nacional de Paraguay").first()

        # === Clientes por defecto ===
        clientes = Cliente.objects.filter(
            nombre__in=[
                "Cliente Persona",
                "Cliente Jurídico Corporativo",
                "Cliente Jurídico VIP",
            ]
        )

        for cliente in clientes:
            sufijo = cliente.nombre.replace(" ", "_")

            # --- Billetera ---
            nombre_billetera = f"Billetera_Cobro_{sufijo}"
            if not MedioCobro.objects.filter(cliente=cliente, nombre=nombre_billetera).exists():
                medio_billetera = MedioCobro.objects.create(
                    cliente=cliente,
                    tipo="billetera",
                    nombre=nombre_billetera,
                    moneda=moneda_pyg,
                    activo=True,
                    tipo_cobro=TipoCobro.objects.filter(nombre__iexact=tipo_cobro_map["billetera"]).first()
                )
                BilleteraCobro.objects.create(
                    medio_cobro=medio_billetera,
                    numero_celular="123456788",
                    entidad=proveedor_tigo,
                    moneda=moneda_pyg,
                )
                print(f"✅ Billetera de cobro creada para {cliente.nombre}")

            # --- Cuenta Bancaria PYG ---
            nombre_cbu_pyg = f"Cuenta_Bancaria_PYG_{sufijo}"
            if not MedioCobro.objects.filter(cliente=cliente, nombre=nombre_cbu_pyg).exists():
                medio_cbu_pyg = MedioCobro.objects.create(
                    cliente=cliente,
                    tipo="cuenta_bancaria",
                    nombre=nombre_cbu_pyg,
                    moneda=moneda_pyg,
                    activo=True,
                    tipo_cobro=TipoCobro.objects.filter(nombre__iexact=tipo_cobro_map["cuenta_bancaria"]).first()
                )
                CuentaBancariaCobro.objects.create(
                    medio_cobro=medio_cbu_pyg,
                    numero_cuenta="123456789",
                    alias_cbu="1354544444",
                    entidad=banco_nacional,
                    moneda=moneda_pyg,
                )
                print(f"✅ Cuenta Bancaria PYG creada para {cliente.nombre}")

            # --- Cuenta Bancaria USD ---
            nombre_cbu_usd = f"Cuenta_Bancaria_USD_{sufijo}"
            if not MedioCobro.objects.filter(cliente=cliente, nombre=nombre_cbu_usd).exists():
                medio_cbu_usd = MedioCobro.objects.create(
                    cliente=cliente,
                    tipo="cuenta_bancaria",
                    nombre=nombre_cbu_usd,
                    moneda=moneda_usd,
                    activo=True,
                    tipo_cobro=TipoCobro.objects.filter(nombre__iexact=tipo_cobro_map["cuenta_bancaria"]).first()
                )
                CuentaBancariaCobro.objects.create(
                    medio_cobro=medio_cbu_usd,
                    numero_cuenta="112233445",
                    alias_cbu="1212121212",
                    entidad=banco_nacional,
                    moneda=moneda_usd,
                )
                print(f"✅ Cuenta Bancaria USD creada para {cliente.nombre}")

        print("\n🎉 Medios de cobro por defecto creados correctamente.\n")

    def setup_tauser_stock():
        Tauser = apps.get_model("webapp", "Tauser")
        CurrencyDenomination = apps.get_model("webapp", "CurrencyDenomination")
        TauserCurrencyStock = apps.get_model("webapp", "TauserCurrencyStock")

        tausers = Tauser.objects.filter(activo=True)
        if not tausers.exists():
            print("⚠️ No hay Tausers activos aún, stock no inicializado.")
            return

        # Solo billetes
        denominations = CurrencyDenomination.objects.filter(is_active=True, type="bill")
        if not denominations.exists():
            print("⚠️ No hay denominaciones activas, stock no inicializado.")
            return

        INITIAL_QTY = 1000

        for tauser in tausers:
            for denom in denominations:
                stock, created = TauserCurrencyStock.objects.get_or_create(
                    tauser=tauser,
                    denomination=denom,
                    defaults={
                        "currency": denom.currency,  # ✅ FIX OBLIGADO
                        "quantity": INITIAL_QTY
                    }
                )

                # Si ya existía pero no tiene moneda asignada (defensive fix)
                if stock.currency_id is None:
                    stock.currency = denom.currency

                # Si existe pero tiene 0
                if stock.quantity == 0:
                    stock.quantity = INITIAL_QTY

                stock.save()

        print(f"✅ Stock inicial cargado: {INITIAL_QTY} billetes por denominación")

    def setup_tauser_names():
        Tauser = apps.get_model("webapp", "Tauser")

        tausers = Tauser.objects.filter(activo=True)
        if not tausers.exists():
            print("⚠️ No hay Tausers activos aún, nombres no inicializados.")
            return
        
        """
        i = 1
        for name in default_names:
        Tauser.objects.create(
            nombre=name,
            activo=True,
            ubicacion=f"Sucursal {i}",
            # No asignamos tipo_pago ni tipo_cobro
        )
        i += 1"""

        default_names = [
        "Tauser 1", "Tauser 2", "Tauser 3", "Tauser 4", "Tauser 5",
        "Tauser 6", "Tauser 7", "Tauser 8", "Tauser 9", "Tauser 10"
        ]

        # OJO si se agregan mas sucursales, agregar a esta lista

        sucursales = [
            "Casa Central", "Sucursal Pinedo", "Sucursal Villamorra", "Sucursal Multiplaza", "Sucursal Mariano Roque Alonso",
            "Sucursal Ciudad del Este", "Sucursal Encarnación", "Sucursal Mercado San Lorenzo", "Sucursal Itaugua", "Sucursal Capiata", "Sucursal Lambaré"
        ]
        largo = len(sucursales)

        i = 0

        for tauser in tausers:
            if tauser.ubicacion != f"Sucursal {i+1}":
                print("✅ Nombres ya asignados a los Tausers")
                return
            
            if i+1 == largo:
                #En caso de que hayan mas tausers para los que hay asignados nombres
                print("Observacion: Puede haber algun Tauser sin ubicacion asignada")
                return
            
            tauser.ubicacion=sucursales[i]
            tauser.save()
            i += 1

        print("✅ Nombres de Tausers establecidos")
        
    def setup_imagenes_monedas():
        Currency = apps.get_model("webapp", "Currency")

        monedas = Currency.objects.filter(Q(flag_image__isnull=True) | Q(flag_image=''))

        if not monedas.exists():
            print("✅ Todas las monedas ya tienen imagenes de banderas asignadas")
            return

        """
        banderas = [
            "https://file.garden/aTR_tQRLDge8swJl/banderas_paises/pyg.png", "https://file.garden/aTR_tQRLDge8swJl/banderas_paises/usd.png",
            "https://file.garden/aTR_tQRLDge8swJl/banderas_paises/ars.png", "https://file.garden/aTR_tQRLDge8swJl/banderas_paises/eur.png", 
            "https://file.garden/aTR_tQRLDge8swJl/banderas_paises/brl.png"
        ]

        Todas las monedas tienen imagenes en mi repositorio de filegarden, si quieren agregar alguna contactar a Raquel para que suba la imagen correspondiente
        """

        for moneda in monedas:
            """
            if moneda.code == "EUR":
                url = "https://file.garden/aTR_tQRLDge8swJl/banderas_paises/eur.png"
                response = requests.get(url)

                if response.status_code == 200:
                    file_name = "eur.png"
                    moneda.flag_image.save(file_name, ContentFile(response.content), save=True)
            """
            url = "https://file.garden/aTR_tQRLDge8swJl/banderas_paises/" + str(moneda.code).lower() + ".png"
            #print("url: " + url)

            response = requests.get(url)
            if response.status_code == 200:
                print(f"✅ Asignando imagen a la moneda {moneda.name}")
                file_name = str(moneda.code).lower() + ".png"
                moneda.flag_image.save(file_name, ContentFile(response.content), save=True)
            else:
                print(f"❌ No hay imagen establecida para la moneda {moneda.name}")

        print("✅ Imagenes de banderas asignadas a las monedas")

    def backfill_currency_history():
        """
        Generate up to 1 year of historical FX prices using base_price.

        TODAY is always equal to currency.base_price (no simulation).
        Historical values are simulated backwards.

        - compra = price * (1 - spread)
        - venta  = price * (1 + spread)

        - PYG stays constant.
        - Runs only once.
        """
        Currency = apps.get_model("webapp", "Currency")
        CurrencyHistory = apps.get_model("webapp", "CurrencyHistory")

        # If any history exists, assume already created → do nothing
        if CurrencyHistory.objects.exists():
            print("✅ Ya existen datos historicos de tasas (ambiente de pruebas)")
            return

        today = timezone.localdate()
        days_back = 365
        histories = []

        currencies = list(Currency.objects.filter(is_active=True))

        for currency in currencies:
            code = currency.code.upper()
            base_price = Decimal(currency.base_price)
            com_com = Decimal(currency.comision_compra)
            com_ven = Decimal(currency.comision_venta)

            # ---- BASE CURRENCY PYG (flat, including today) --------------------------
            if code == "PYG":
                for i in range(0, days_back + 1):
                    date = today - timedelta(days=i)
                    histories.append(
                        CurrencyHistory(
                            currency=currency,
                            date=date,
                            compra=base_price-com_com,
                            venta=base_price+com_ven,
                        )
                    )
                continue

            # ---- OTHER CURRENCIES --------------------------------------------------
            # Today's price is exactly the base_price
            histories.append(
                CurrencyHistory(
                    currency=currency,
                    date=today,
                    compra=base_price-com_com,           # compra today based on base_price
                    venta=base_price+com_ven,            # venta today same (or you may want a spread)
                )
            )

            # Start the simulation from today’s base_price
            current_price = base_price

            for i in range(1, days_back + 1):  # 1..365 (skip today simulation)
                date = today - timedelta(days=i)

                # price random walk for historical days
                delta = _daily_variation(code, i)
                current_price = current_price * (Decimal("1") + delta)

                # daily spread
                spread = _daily_spread_variation(code, i)

                compra = (current_price * (Decimal("1") - spread)) - com_com
                venta = current_price * (Decimal("1") + spread) + com_ven

                if compra <= 0:
                    compra = Decimal("0.01")
                if venta <= 0:
                    venta = Decimal("0.01")

                histories.append(
                    CurrencyHistory(
                        currency=currency,
                        date=date,
                        compra=compra,
                        venta=venta,
                    )
                )

        CurrencyHistory.objects.bulk_create(histories, ignore_conflicts=True)
        print("✅ Datos historicos de tasas generados (ambiente de pruebas)")



    # -------------------------------------------------------------
    # EXECUTION ORDER
    # -------------------------------------------------------------
    safe_run("Roles y usuarios", setup_roles_y_usuarios)
    safe_run("Entidades, Monedas y Denominaciones", setup_entidades_y_monedas)
    safe_run("Clientes", setup_clientes)
    safe_run("Límites de Intercambio", setup_limites)
    safe_run("Tipos de Pago/Cobro", setup_tipos_pago_cobro)
    safe_run("Asignar tipos a TAUSER", setup_tauser)
    safe_run("Cuenta Bancaria del Negocio", setup_cuenta_negocio)
    safe_run("Medios de Pago para usuario1 por defecto", crear_medios_pago_por_defecto)
    safe_run("Medios de Cobro para usuario1 por defecto", crear_medios_cobro_por_defecto)
    safe_run("Stock inicial de Tauser", setup_tauser_stock)
    safe_run("Asignacion de nombres a los Tauser", setup_tauser_names)
    safe_run("Asignacion de banderas a las monedas", setup_imagenes_monedas)
    safe_run("Generacion de datos historicos de tasas (ambiente de pruebas)", backfill_currency_history)

def _daily_spread_variation(code: str, day_index: int) -> Decimal:
    """
    Small ± variation applied to the buy/sell spread.
    """
    spread_map = {
        "USD": Decimal("0.01"),   # 1% spread
        "EUR": Decimal("0.012"),
        "BRL": Decimal("0.015"),
        "ARS": Decimal("0.03"),
    }
    base_spread = spread_map.get(code.upper(), Decimal("0.01"))

    key = f"{code}-{day_index}-spread"
    h = int(hashlib.sha256(key.encode()).hexdigest(), 16)
    frac = Decimal(h % 10001) / Decimal("5000") - Decimal("1")

    # ± 10% variation of the spread
    variation = base_spread * Decimal("0.10") * frac
    return base_spread + variation

def _daily_variation(code: str, day_index: int) -> Decimal:
    """
    Deterministic pseudo-random variation in [-max_change, max_change],
    so results are realistic but reproducible.
    """
    # Volatility per currency (roughly daily % max change)
    vol_map = {
        "USD": Decimal("0.004"),  # ±0.4% per day
        "EUR": Decimal("0.004"),  # ±0.4%
        "BRL": Decimal("0.008"),  # ±0.8%
        "ARS": Decimal("0.020"),  # ±2%
    }
    default_vol = Decimal("0.003")  # ±0.3%

    max_change = vol_map.get(code.upper(), default_vol)

    # Turn (code, day_index) into a deterministic "random" number
    key = f"{code}-{day_index}-base"
    h = int(hashlib.sha256(key.encode()).hexdigest(), 16)

    # Map hash → [-1, 1]
    frac = Decimal(h % 10001) / Decimal("5000") - Decimal("1")  # [-1, 1]

    # Scale to [-max_change, max_change]
    return frac * max_change

"""
@receiver(post_migrate)
def crear_medios_pago_por_defecto(sender, **kwargs):
    if sender.name != "webapp":
        return

    try:
        # === Moneda base ===
        moneda_pyg = Currency.objects.filter(code="PYG").first()
        if not moneda_pyg:
            print("⚠️ No se encontró la moneda PYG. Se omite la creación de medios de pago.")
            return

        # === Entidades ===
        proveedor_wallet = Entidad.objects.filter(nombre__iexact="Personal Wallet").first()
        banco_continental = Entidad.objects.filter(nombre__iexact="Banco Continental").first()

        if not proveedor_wallet or not banco_continental:
            print("⚠️ No se encontraron las entidades requeridas (Personal Wallet o Banco Continental).")
            return

        # === Clientes por defecto ===
        clientes = Cliente.objects.filter(
            nombre__in=[
                "Cliente Persona",
                "Cliente Juridico Corporativo",
                "Cliente Juridico VIP",
            ]
        )

        for cliente in clientes:
            sufijo = cliente.nombre.replace(" ", "_")

            # --- Billetera ---
            nombre_billetera = f"Billetera_{sufijo}"
            if not MedioPago.objects.filter(cliente=cliente, nombre=nombre_billetera).exists():
                medio_billetera = MedioPago.objects.create(
                    cliente=cliente,
                    tipo="billetera",
                    nombre=nombre_billetera,
                    moneda=moneda_pyg,
                )
                Billetera.objects.create(
                    medio_pago=medio_billetera,
                    numero_celular="123456789",
                    entidad=proveedor_wallet,
                    moneda=moneda_pyg,
                )
                print(f"✅ Billetera creada para {cliente.nombre}")

            # --- Tarjeta Nacional ---
            nombre_tarjeta_nac = f"Tarjeta_Nacional_{sufijo}"
            if not MedioPago.objects.filter(cliente=cliente, nombre=nombre_tarjeta_nac).exists():
                medio_tarjeta_nat = MedioPago.objects.create(
                    cliente=cliente,
                    tipo="tarjeta_nacional",
                    nombre=nombre_tarjeta_nac,
                    moneda=moneda_pyg,
                )
                TarjetaNacional.objects.create(
                    medio_pago=medio_tarjeta_nat,
                    numero_tokenizado="1234567",
                    fecha_vencimiento="2029-02-04",
                    ultimos_digitos="4567",
                    entidad=banco_continental,
                    moneda=moneda_pyg,
                )
                print(f"✅ Tarjeta Nacional creada para {cliente.nombre}")

            # --- Tarjeta Internacional ---
            nombre_tarjeta_int = f"Tarjeta_Internacional_{sufijo}"
            if not MedioPago.objects.filter(cliente=cliente, nombre=nombre_tarjeta_int).exists():
                medio_tarjeta_int = MedioPago.objects.create(
                    cliente=cliente,
                    tipo="tarjeta_internacional",
                    nombre=nombre_tarjeta_int,
                    moneda=moneda_pyg,
                )
                TarjetaInternacional.objects.create(
                    medio_pago=medio_tarjeta_int,
                    stripe_payment_method_id="pm_card_visa",
                    ultimos_digitos="4242",
                    exp_month=4,
                    exp_year=2029,
                )
                print(f"✅ Tarjeta Internacional creada para {cliente.nombre}")

        print("\n🎉 Medios de pago por defecto creados correctamente.\n")

    except Exception as e:
        print(f"\n❌ Error al crear los medios de pago por defecto: {e}")
        traceback.print_exc()
"""
"""
@receiver(post_migrate)
def crear_medios_cobro_por_defecto(sender, **kwargs):
    if sender.name != "webapp":
        return

    try:
        # === Monedas ===
        moneda_pyg = Currency.objects.filter(code="PYG").first()
        moneda_usd = Currency.objects.filter(code="USD").first()
        if not moneda_pyg or not moneda_usd:
            print("⚠️ No se encontraron las monedas PYG o USD. Se omite la creación de medios de cobro.")
            return

        # === Entidades ===
        proveedor_tigo = Entidad.objects.filter(nombre__iexact="Tigo Money").first()
        banco_nacional = Entidad.objects.filter(nombre__iexact="Banco Nacional de Paraguay").first()
        if not proveedor_tigo or not banco_nacional:
            print("⚠️ No se encontraron las entidades necesarias para medios de cobro.")
            return

        # === Clientes por defecto ===
        clientes = Cliente.objects.filter(
            nombre__in=[
                "Cliente Persona",
                "Cliente Juridico Corporativo",
                "Cliente Juridico VIP",
            ]
        )

        for cliente in clientes:
            sufijo = cliente.nombre.replace(" ", "_")

            # --- Billetera ---
            nombre_billetera = f"Billetera_Cobro_{sufijo}"
            if not MedioCobro.objects.filter(cliente=cliente, nombre=nombre_billetera).exists():
                medio_billetera = MedioCobro.objects.create(
                    cliente=cliente,
                    tipo="billetera",
                    nombre=nombre_billetera,
                    moneda=moneda_pyg,
                )
                BilleteraCobro.objects.create(
                    medio_cobro=medio_billetera,
                    numero_celular="123456788",
                    entidad=proveedor_tigo,
                    moneda=moneda_pyg,
                )
                print(f"✅ Billetera de cobro creada para {cliente.nombre}")

            # --- Cuenta Bancaria PYG ---
            nombre_cbu_pyg = f"Cuenta_Bancaria_PYG_{sufijo}"
            if not MedioCobro.objects.filter(cliente=cliente, nombre=nombre_cbu_pyg).exists():
                medio_cbu_pyg = MedioCobro.objects.create(
                    cliente=cliente,
                    tipo="cuenta_bancaria",
                    nombre=nombre_cbu_pyg,
                    moneda=moneda_pyg,
                )
                CuentaBancariaCobro.objects.create(
                    medio_cobro=medio_cbu_pyg,
                    numero_cuenta="123456789",
                    alias_cbu="1354544444",
                    entidad=banco_nacional,
                    moneda=moneda_pyg,
                )
                print(f"✅ Cuenta Bancaria PYG creada para {cliente.nombre}")

            # --- Cuenta Bancaria USD ---
            nombre_cbu_usd = f"Cuenta_Bancaria_USD_{sufijo}"
            if not MedioCobro.objects.filter(cliente=cliente, nombre=nombre_cbu_usd).exists():
                medio_cbu_usd = MedioCobro.objects.create(
                    cliente=cliente,
                    tipo="cuenta_bancaria",
                    nombre=nombre_cbu_usd,
                    moneda=moneda_usd,
                )
                CuentaBancariaCobro.objects.create(
                    medio_cobro=medio_cbu_usd,
                    numero_cuenta="112233445",
                    alias_cbu="1212121212",
                    entidad=banco_nacional,
                    moneda=moneda_usd,
                )
                print(f"✅ Cuenta Bancaria USD creada para {cliente.nombre}")

        print("\n🎉 Medios de cobro por defecto creados correctamente.\n")

    except Exception as e:
        print(f"\n❌ Error al crear los medios de cobro por defecto: {e}")
        traceback.print_exc()

"""
"""
@receiver(post_migrate)
def setup_roles_and_users(sender, **kwargs):
    if sender.name != "webapp":
        return

    try:
        roles = ["Usuario", "Empleado", "Administrador", "Analista"]
        for role_name in roles:
            group, _ = Group.objects.get_or_create(name=role_name)
            Role.objects.get_or_create(group=group)
            print(f"Creado rol {role_name}")

        # Asignar todos los permisos disponibles al grupo Administrador
        admin_group = Group.objects.get(name="Administrador")
        all_permissions = Permission.objects.all()
        admin_group.permissions.set(all_permissions)
        print("Todos los permisos asignados al Administrador")

        # Asignar todos los permisos correspondientes a Analista
        analyst_group = Group.objects.get(name="Analista")
        nombres_permisos = ["Can change Moneda", "Can view Moneda", "Can access analyst panel", "Can change Límite de Intercambio", "Can view Límite de Intercambio", "Can change Método de Cobro", "Can view Método de Cobro", "Can change Medio de Pago", "Can view Medio de Pago"]

        permisos_analista = Permission.objects.filter(name__in=nombres_permisos)

        analyst_group.permissions.set(permisos_analista)
        analyst_group.save()
        print("Permisos concedidos al Analista")

        for data in USUARIOS_POR_DEFECTO:
            user, created = User.objects.get_or_create(username=data["username"], defaults={
                "email": data["email"]
            })
            if created:
                user.set_password(data["password"])
                user.is_active = True
                user.save()
                grupo = Group.objects.get(name=data["grupo"])
                user.groups.add(grupo)
                print(f"✅ Usuario '{data['username']}' creado y asignado a '{data['grupo']}'")

    except Exception as e:
        print(f"❌ Error creando roles o usuarios: {e}")
        traceback.print_exc()

"""
"""
@receiver(post_migrate)
def setup_client_categories_and_clients(sender, **kwargs):
    if sender.name != "webapp":
        return

    try:
        for cat in CATEGORIAS_POR_DEFECTO:
            Categoria.objects.get_or_create(nombre=cat["nombre"], defaults={"descuento": cat["descuento"]})

        usuario = User.objects.filter(username="usuario1").first()
        if not usuario:
            print("⚠️ Usuario 'usuario1' no existe aún. Los clientes no se asignarán.")
            return

        for data in CLIENTES_POR_DEFECTO:
            categoria = Categoria.objects.get(nombre=data["categoria"])
            data["categoria"] = categoria
            cliente, _ = Cliente.objects.get_or_create(nombre=data["nombre"], defaults=data)
            ClienteUsuario.objects.get_or_create(cliente=cliente, usuario=usuario)
            print(f"✅ Cliente '{cliente.nombre}' creado/asignado a '{usuario.username}'")

    except Exception as e:
        print(f"❌ Error creando clientes: {e}")
        traceback.print_exc()"""
"""
@receiver(post_migrate)
def setup_entities_and_currencies(sender, **kwargs):
    if sender.name != "webapp":
        return

    bancos = ["Banco Nacional de Paraguay", "Banco Regional", "Banco Continental"]
    billeteras = ["Bancard Wallet", "Tigo Money", "Personal Wallet"]

    monedas = [
    {
        "code": "PYG",
        "name": "Guaraní Paraguayo",
        "symbol": "G",
        "base_price": 1.0,
        "comision_venta": 1.0,
        "comision_compra": 1.0,
        "decimales_cotizacion": 2,
        "decimales_monto": 0,
        "is_active": True
    },
    {
        "code": "USD",
        "name": "Dólar Estadounidense",
        "symbol": "$",
        "base_price": 7500,
        "comision_venta": 200,
        "comision_compra": 300,
        "decimales_cotizacion": 4,
        "decimales_monto": 2,
        "is_active": True
    },
    {
        "code": "EUR",
        "name": "Euro",
        "symbol": "€",
        "base_price": 8000,
        "comision_venta": 200,
        "comision_compra": 300,
        "decimales_cotizacion": 4,
        "decimales_monto": 2,
        "is_active": True
    },
    {
        "code": "BRL",
        "name": "Real Brasileño",
        "symbol": "R$",
        "base_price": 1500,
        "comision_venta": 100,
        "comision_compra": 200,
        "decimales_cotizacion": 4,
        "decimales_monto": 2,
        "is_active": True
    },
    {
        "code": "ARS",
        "name": "Peso Argentino",
        "symbol": "$",
        "base_price": 5,
        "comision_venta": 1,
        "comision_compra": 2,
        "decimales_cotizacion": 4,
        "decimales_monto": 2,
        "is_active": True
    }
]

    denominaciones = {
        "USD": [1, 5, 10, 20, 50, 100],
        "EUR": [5, 10, 20, 50, 100, 200],
        "PYG": [1000, 2000, 5000, 10000, 20000, 50000, 100000],
        "BRL": [2, 5, 10, 20, 50, 100],
        "ARS": [100, 200, 500, 1000, 2000],
    }

    try:
        for nombre in bancos:
            Entidad.objects.get_or_create(nombre=nombre, defaults={"tipo": "banco", "activo": True})
        for nombre in billeteras:
            Entidad.objects.get_or_create(nombre=nombre, defaults={"tipo": "telefono", "activo": True})

        for moneda in monedas:
            currency, _ = Currency.objects.get_or_create(
                code=moneda["code"],
                defaults={
                "name": moneda["name"],
                "symbol": moneda["symbol"],
                "base_price": moneda["base_price"],
                "comision_venta": moneda["comision_venta"],
                "comision_compra": moneda["comision_compra"],
                "decimales_cotizacion": moneda["decimales_cotizacion"],
                "decimales_monto": moneda["decimales_monto"],
                "is_active": moneda["is_active"]
                }
            )
            for valor in denominaciones[currency.code]:
                CurrencyDenomination.objects.get_or_create(currency=currency, valor=valor)

    except Exception as e:
        print(f"❌ Error creando entidades o monedas: {e}")
        traceback.print_exc()"""

        

@receiver(post_save, sender=User)
def assign_default_role(sender, instance, created, **kwargs):
    if created:
        try:
            default_group = Group.objects.get(name="Usuario")
            Role.objects.get_or_create(group=default_group)
            instance.groups.add(default_group)
        except Group.DoesNotExist:
            pass

"""
@receiver(post_migrate)
def create_default_payment_types(sender, **kwargs):
    # Asegurarse de que solo se ejecute para nuestra app
    if sender.name != "webapp":
        return

    TipoPago = apps.get_model("webapp", "TipoPago")
    defaults = {"activo": True, "comision": 0.0}
    
    # Lista de tipos de pago fijos
    tipos = ["Billetera", "Cuenta Bancaria", "Tauser", "Tarjeta Nacional", "Tarjeta Internacional"]
    
    for nombre in tipos:
        TipoPago.objects.get_or_create(nombre=nombre, defaults=defaults)
"""
@receiver(post_save, sender=MedioPago)
def asignar_tipo_pago(sender, instance, created, **kwargs):
    if created and not instance.tipo_pago:
        nombre_tipo_pago = " ".join([palabra.capitalize() for palabra in instance.tipo.split("_")])
        tipo_pago, _ = TipoPago.objects.get_or_create(nombre=nombre_tipo_pago)
        instance.tipo_pago = tipo_pago
        instance.save()



#crear limites de intercambio por defecto
@receiver(post_migrate)
def seed_limite_config(sender, **kwargs):
    if sender.label != "webapp":
        return
    Currency = apps.get_model("webapp", "Currency")
    Categoria = apps.get_model("webapp", "Categoria")
    LimiteIntercambioConfig = apps.get_model("webapp", "LimiteIntercambioConfig")

    for categoria in Categoria.objects.all():
        for moneda in Currency.objects.all():
            valor = VALORES_POR_MONEDA.get(moneda.code, DEFAULT_NO_LISTADA)
            LimiteIntercambioConfig.objects.get_or_create(
                categoria=categoria, moneda=moneda,
                defaults={
                    "limite_dia_max": valor,
                    "limite_mes_max": valor,
                }
            )


@receiver(post_save, sender="webapp.Currency")
def crear_config_al_crear_moneda(sender, instance, created, **kwargs):
    if not created:
        return
    Categoria = apps.get_model("webapp", "Categoria")
    LimiteIntercambioConfig = apps.get_model("webapp", "LimiteIntercambioConfig")

    valor = VALORES_POR_MONEDA.get(instance.code, DEFAULT_NO_LISTADA)
    for categoria in Categoria.objects.all():
        LimiteIntercambioConfig.objects.get_or_create(
            categoria=categoria, moneda=instance,
            defaults={"limite_dia_max": valor, "limite_mes_max": valor}
        )


@receiver(post_save, sender="webapp.Cliente")
def crear_saldos_cliente(sender, instance, created, **kwargs):
    LimiteIntercambioCliente = apps.get_model("webapp", "LimiteIntercambioCliente")
    LimiteIntercambioConfig = apps.get_model("webapp", "LimiteIntercambioConfig")

    if not instance.categoria_id:
        return

    configs = LimiteIntercambioConfig.objects.filter(categoria=instance.categoria)

    for cfg in configs:
        LimiteIntercambioCliente.objects.get_or_create(
            cliente=instance,
            config=cfg,  # ✅ AQUÍ SE CAMBIA
            defaults={
                "limite_dia_actual": cfg.limite_dia_max,
                "limite_mes_actual": cfg.limite_mes_max,
            }
        )

@receiver(post_save, sender=TipoPago)
def sync_medios_pago(sender, instance, **kwargs):
    # Sincroniza el estado de todos los MedioPago vinculados
    MedioPago.objects.filter(tipo_pago=instance).update(activo=instance.activo)

@receiver(post_save, sender=TipoCobro)
def sync_medios_cobro(sender, instance, **kwargs):
    # Sincroniza el estado de todos los MedioPago vinculados
    MedioCobro.objects.filter(tipo_cobro=instance).update(activo=instance.activo)

"""
@receiver(post_migrate)
def create_default_cobro_types(sender, **kwargs):
    # Asegurarse de que solo se ejecute para nuestra app
    if sender.name != "webapp":
        return

    TipoCobro = apps.get_model("webapp", "TipoCobro")
    defaults = {"activo": True, "comision": 0.0}
    
    # Lista de tipos de pago fijos
    tipos = ["Billetera", "Cuenta Bancaria", "Tauser"]
    
    for nombre in tipos:
        TipoCobro.objects.get_or_create(nombre=nombre, defaults=defaults)"""


        
"""
@receiver(post_migrate)
def asignar_tipos_tauser(sender, **kwargs):
    Tauser = apps.get_model("webapp", "Tauser")
    TipoPago = apps.get_model("webapp", "TipoPago")
    TipoCobro = apps.get_model("webapp", "TipoCobro")

    # Obtener los tipos "Tauser" existentes
    tipo_pago = TipoPago.objects.filter(nombre__icontains="tauser", activo=True).first()
    tipo_cobro = TipoCobro.objects.filter(nombre__icontains="tauser", activo=True).first()

    if not tipo_pago or not tipo_cobro:
        # Si no existen, no hacemos nada
        return

    # Actualizar solo los Tauser que aún no tienen asignado el tipo
    Tauser.objects.filter(tipo_pago__isnull=True).update(tipo_pago=tipo_pago)
    Tauser.objects.filter(tipo_cobro__isnull=True).update(tipo_cobro=tipo_cobro)"""

"""@receiver(post_migrate)
def crear_cuenta_bancaria_negocio(sender, **kwargs):

    #Crea una cuenta bancaria por defecto para el negocio
    #solo si no existe aún, y después de que la moneda PYG esté disponible.

    if sender.name != "webapp":
        return

    # Usamos transaction.on_commit para asegurar que se ejecute
    # después de todas las migraciones y commits
    def crear_si_corresponde():
        try:
            moneda = Currency.objects.filter(code="PYG").first()
            if not moneda:
                print("⚠️ No se creó la cuenta bancaria del negocio porque la moneda PYG aún no existe.")
                return

            banco, _ = Entidad.objects.get_or_create(
                nombre="Banco Continental",
                tipo="banco",
            )

            cuenta_existente = CuentaBancariaNegocio.objects.first()
            if cuenta_existente:
                print("ℹ️ Ya existe una cuenta bancaria del negocio, no se creó otra.")
                return

            CuentaBancariaNegocio.objects.create(
                numero_cuenta="000100000001",
                alias_cbu="CUENTA_NEGOCIO_DEFECTO",
                entidad=banco,
                moneda=moneda,
            )
            print("✅ Se creó la cuenta bancaria del negocio por defecto.")

        except Exception as e:
            print(f"❌ Error al crear cuenta bancaria del negocio: {e}")

    transaction.on_commit(crear_si_corresponde)"""

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Transaccion)
def actualizar_limite_post_transaccion(sender, instance, **kwargs):
    """
    Lógica bancaria profesional:
    - Si llega a PENDIENTE, PAGADA o COMPLETADA → DESCUENTA SOLO 1 VEZ (reserva cupo)
    - Si luego pasa a CANCELADA o ANULADA → DEVUELVE EXACTAMENTE lo reservado
    - Usa LimiteIntercambioLog como tracking persistente para evitar dobles descuentos
    """

    ESTADOS_DESCUENTAN = [
        Transaccion.Estado.PENDIENTE,
        Transaccion.Estado.PAGADA,
        Transaccion.Estado.COMPLETA,
    ]
    ESTADOS_RESTAURAN = [
        Transaccion.Estado.CANCELADA,
        Transaccion.Estado.ANULADA,
    ]

    # Solo aplica a operaciones de VENTA → origen PYG
    if instance.moneda_origen.code != "PYG":
        return

    try:
        # Traemos el tracking (si ya existía)
        log = LimiteIntercambioLog.objects.filter(transaccion=instance).first()

        # 1) Si es estado que DESCUNTA y aún *NO* se descontó antes → descontar
        if instance.estado in ESTADOS_DESCUENTAN and (not log or log.monto_descontado == 0):
            with transaction.atomic():
                config = LimiteIntercambioConfig.objects.get(
                    categoria=instance.cliente.categoria,
                    moneda=instance.moneda_destino
                )
                limite_cliente = LimiteIntercambioCliente.objects.select_for_update().get(
                    cliente=instance.cliente,
                    config=config
                )

                monto = instance.monto_destino
                limite_cliente.descontar(monto)

                # Guardar log
                LimiteIntercambioLog.objects.create(
                    transaccion=instance,
                    monto_descontado=monto
                )

        # 2) Si pasa a cancelado/anulado y ya tenía descuento → restaurar exactamente
        elif instance.estado in ESTADOS_RESTAURAN and log and log.monto_descontado > 0:
            with transaction.atomic():
                config = LimiteIntercambioConfig.objects.get(
                    categoria=instance.cliente.categoria,
                    moneda=instance.moneda_destino
                )
                limite_cliente = LimiteIntercambioCliente.objects.select_for_update().get(
                    cliente=instance.cliente,
                    config=config
                )

                # Devolver
                limite_cliente.limite_dia_actual += log.monto_descontado
                limite_cliente.limite_mes_actual += log.monto_descontado
                limite_cliente.save(update_fields=["limite_dia_actual", "limite_mes_actual"])

                # Marcar log como ya restaurado
                log.monto_descontado = Decimal("0")
                log.save()

    except (LimiteIntercambioConfig.DoesNotExist, LimiteIntercambioCliente.DoesNotExist):
        # No hay configuración de límite para esta combinación de categoría/moneda
        # Esto es válido - no todas las combinaciones tienen límites configurados
        pass
    except Exception as e:
        logger.exception(f"Error en actualización de límite post transacción: {e}")

   
@receiver(post_save, sender=Transaccion)
def crear_snapshot_transaccion(sender, instance: Transaccion, created: bool, **kwargs):
    """
    Crea un snapshot de la transacción cada vez que se hace save().
    Guarda el estado actual (después de guardar).
    """
    # Usuario y origen pueden ser fijados desde la vista/tarea opcionalmente:
    usuario = getattr(instance, "_usuario_accion", None)
    origen = getattr(instance, "_origen_accion", "sistema")

    TransaccionAuditoria.objects.create(
        transaccion=instance,
        usuario=usuario,
        origen=origen,

        tipo=instance.tipo,
        estado=instance.estado,

        moneda_origen=instance.moneda_origen.code,
        moneda_destino=instance.moneda_destino.code,

        tasa_cambio=instance.tasa_cambio,
        monto_origen=instance.monto_origen,
        monto_destino=instance.monto_destino,

        medio_pago_type=instance.medio_pago_type,
        medio_pago_id=instance.medio_pago_id,
        medio_cobro_type=instance.medio_cobro_type,
        medio_cobro_id=instance.medio_cobro_id,

        medio_pago_porc=instance.medio_pago_porc,
        medio_cobro_porc=instance.medio_cobro_porc,
        desc_cliente=instance.desc_cliente,
        monto_base_moneda=instance.monto_base_moneda,
        comision_vta_com=instance.comision_vta_com,
    )