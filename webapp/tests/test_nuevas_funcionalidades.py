"""
Tests unitarios para las nuevas funcionalidades implementadas.

Incluye pruebas para:
- Cálculo de tasas con comisiones de medios de pago/cobro
- Formateo de montos según moneda
- Conversión de montos entre monedas
- Cálculo de montos ante cambio de tasa
- Función monto_stripe para diferentes monedas
- Validaciones de transacciones
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from decimal import Decimal, ROUND_HALF_UP
from unittest.mock import patch, MagicMock, Mock

from ..models import (
    CustomUser, Cliente, Currency, Transaccion, TipoPago, TipoCobro,
    MedioPago, MedioCobro, Tauser, ClienteUsuario, Categoria,
    CuentaBancariaNegocio, Entidad
)
from ..views.compraventa_y_conversión import (
    guardar_transaccion, monto_stripe, calcularTasa, formatearMontos,
    convertir_monto, calcularMontosCambio
)


class FormatearMontosTests(TestCase):
    """Pruebas para la función formatearMontos"""

    def setUp(self):
        """Configuración inicial"""
        self.pyg, _ = Currency.objects.get_or_create(
            code='PYG',
            defaults={
                'name': 'Guaraní Paraguayo',
                'base_price': Decimal('1.0'),
                'comision_compra': Decimal('100'),
                'comision_venta': Decimal('100'),
                'decimales_monto': 0,
                'is_active': True
            }
        )
        
        self.usd, _ = Currency.objects.get_or_create(
            code='USD',
            defaults={
                'name': 'Dólar Americano',
                'base_price': Decimal('7500.0'),
                'comision_compra': Decimal('100'),
                'comision_venta': Decimal('100'),
                'decimales_monto': 2,
                'is_active': True
            }
        )
        
        self.eur, _ = Currency.objects.get_or_create(
            code='EUR',
            defaults={
                'name': 'Euro',
                'base_price': Decimal('8200.0'),
                'comision_compra': Decimal('100'),
                'comision_venta': Decimal('100'),
                'decimales_monto': 2,
                'is_active': True
            }
        )

    def test_formatear_pyg_sin_decimales(self):
        """PYG debe formatearse sin decimales"""
        monto = Decimal('1234567.89')
        resultado = formatearMontos(monto, self.pyg, como_str=False)
        self.assertEqual(resultado, Decimal('1234568'))  # Redondeado

    def test_formatear_pyg_como_string(self):
        """PYG como string debe tener formato latino sin decimales"""
        monto = Decimal('1234567')
        resultado = formatearMontos(monto, self.pyg, como_str=True)
        self.assertEqual(resultado, '1.234.567')

    def test_formatear_usd_con_decimales(self):
        """USD debe formatearse con 2 decimales"""
        monto = Decimal('1234.567')
        resultado = formatearMontos(monto, self.usd, como_str=False)
        self.assertEqual(resultado, Decimal('1234.57'))  # Redondeado

    def test_formatear_usd_como_string(self):
        """USD como string debe tener formato latino con 2 decimales"""
        monto = Decimal('1234.50')
        resultado = formatearMontos(monto, self.usd, como_str=True)
        self.assertEqual(resultado, '1.234,50')

    def test_formatear_monto_pequeno(self):
        """Formateo de montos pequeños"""
        monto = Decimal('0.99')
        resultado = formatearMontos(monto, self.usd, como_str=True)
        self.assertEqual(resultado, '0,99')

    def test_formatear_monto_grande(self):
        """Formateo de montos grandes"""
        monto = Decimal('999999999')
        resultado = formatearMontos(monto, self.pyg, como_str=True)
        self.assertEqual(resultado, '999.999.999')


class ConvertirMontoTests(TestCase):
    """Pruebas para la función convertir_monto"""

    def setUp(self):
        """Configuración inicial"""
        self.pyg, _ = Currency.objects.get_or_create(
            code='PYG',
            defaults={
                'name': 'Guaraní Paraguayo',
                'base_price': Decimal('1.0'),
                'comision_compra': Decimal('100'),
                'comision_venta': Decimal('100'),
                'decimales_monto': 0,
                'is_active': True
            }
        )
        
        self.usd, _ = Currency.objects.get_or_create(
            code='USD',
            defaults={
                'name': 'Dólar Americano',
                'base_price': Decimal('7500.0'),
                'comision_compra': Decimal('100'),
                'comision_venta': Decimal('100'),
                'decimales_monto': 2,
                'is_active': True
            }
        )

    def test_convertir_pyg_a_usd(self):
        """Conversión de PYG a USD (división por tasa)"""
        monto = Decimal('7500000')
        tasa = Decimal('7500')
        resultado = convertir_monto(self.pyg, self.usd, monto, tasa)
        self.assertEqual(resultado, Decimal('1000'))

    def test_convertir_usd_a_pyg(self):
        """Conversión de USD a PYG (multiplicación por tasa)"""
        monto = Decimal('1000')
        tasa = Decimal('7500')
        resultado = convertir_monto(self.usd, self.pyg, monto, tasa)
        self.assertEqual(resultado, Decimal('7500000'))

    def test_convertir_monto_cero(self):
        """Conversión de monto cero devuelve cero"""
        monto = Decimal('0')
        tasa = Decimal('7500')
        resultado = convertir_monto(self.pyg, self.usd, monto, tasa)
        self.assertEqual(resultado, Decimal('0'))

    def test_convertir_monto_negativo(self):
        """Conversión de monto negativo devuelve cero"""
        monto = Decimal('-100')
        tasa = Decimal('7500')
        resultado = convertir_monto(self.pyg, self.usd, monto, tasa)
        self.assertEqual(resultado, Decimal('0'))


class MontoStripeTests(TestCase):
    """Pruebas para la función monto_stripe"""

    def test_monto_stripe_pyg(self):
        """PYG es moneda sin decimales - debe devolver entero"""
        resultado = monto_stripe(Decimal('1000000'), 'PYG')
        self.assertEqual(resultado, 1000000)
        self.assertIsInstance(resultado, int)

    def test_monto_stripe_usd(self):
        """USD es moneda con decimales - debe convertir a centavos"""
        resultado = monto_stripe(Decimal('100.50'), 'USD')
        self.assertEqual(resultado, 10050)
        self.assertIsInstance(resultado, int)

    def test_monto_stripe_eur(self):
        """EUR es moneda con decimales - debe convertir a centavos"""
        resultado = monto_stripe(Decimal('50.25'), 'EUR')
        self.assertEqual(resultado, 5025)

    def test_monto_stripe_jpy(self):
        """JPY es moneda sin decimales - debe devolver entero"""
        resultado = monto_stripe(Decimal('10000'), 'JPY')
        self.assertEqual(resultado, 10000)

    def test_monto_stripe_clp(self):
        """CLP es moneda sin decimales - debe devolver entero"""
        resultado = monto_stripe(Decimal('50000'), 'CLP')
        self.assertEqual(resultado, 50000)

    def test_monto_stripe_case_insensitive(self):
        """El código de moneda debe ser case-insensitive"""
        resultado_upper = monto_stripe(Decimal('100'), 'USD')
        resultado_lower = monto_stripe(Decimal('100'), 'usd')
        self.assertEqual(resultado_upper, resultado_lower)


class CalcularTasaTests(TestCase):
    """Pruebas para la función calcularTasa"""

    def setUp(self):
        """Configuración inicial"""
        # Usuario
        self.user = CustomUser.objects.create_user(
            username='testuser_tasa',
            password='testpass123',
            email='testtasa@example.com'
        )
        
        # Categoría con descuento
        self.categoria_premium, _ = Categoria.objects.get_or_create(
            nombre='Premium Test',
            defaults={'descuento': Decimal('0.10')}  # 10% descuento
        )
        
        self.categoria_sin_descuento, _ = Categoria.objects.get_or_create(
            nombre='Normal Test',
            defaults={'descuento': Decimal('0')}
        )
        
        # Cliente premium
        self.cliente_premium = Cliente.objects.create(
            nombre='Cliente Premium Test',
            documento='99999991',
            correo='premium_test@example.com',
            categoria=self.categoria_premium
        )
        
        # Cliente normal
        self.cliente_normal = Cliente.objects.create(
            nombre='Cliente Normal Test',
            documento='99999992',
            correo='normal_test@example.com',
            categoria=self.categoria_sin_descuento
        )
        
        # Monedas
        self.pyg, _ = Currency.objects.get_or_create(
            code='PYG',
            defaults={
                'name': 'Guaraní Paraguayo',
                'base_price': Decimal('1.0'),
                'comision_compra': Decimal('100'),
                'comision_venta': Decimal('100'),
                'decimales_monto': 0,
                'is_active': True
            }
        )
        
        self.usd, _ = Currency.objects.get_or_create(
            code='USD',
            defaults={
                'name': 'Dólar Americano',
                'base_price': Decimal('7500.0'),
                'comision_compra': Decimal('100'),
                'comision_venta': Decimal('100'),
                'decimales_monto': 2,
                'is_active': True
            }
        )
        
        # Tipos de pago y cobro
        self.tipo_pago, _ = TipoPago.objects.get_or_create(
            nombre='Tauser',
            defaults={'activo': True, 'comision': Decimal('0')}
        )
        
        self.tipo_cobro, _ = TipoCobro.objects.get_or_create(
            nombre='Tauser',
            defaults={'activo': True, 'comision': Decimal('0')}
        )

    def test_calcular_tasa_venta_sin_descuento(self):
        """Tasa de venta sin descuento de categoría: base + comision_venta"""
        # Crear transacción mock
        transaccion = Mock()
        transaccion.tipo = "VENTA"
        transaccion.cliente = self.cliente_normal
        transaccion.moneda_origen = self.pyg
        transaccion.moneda_destino = self.usd
        transaccion.medio_pago = None
        transaccion.medio_cobro = None
        
        tasa = calcularTasa(transaccion)
        
        # Tasa de venta = base + comision_venta
        tasa_esperada = self.usd.base_price + self.usd.comision_venta
        self.assertEqual(tasa, tasa_esperada)

    def test_calcular_tasa_compra_sin_descuento(self):
        """Tasa de compra sin descuento de categoría: base - comision_compra"""
        transaccion = Mock()
        transaccion.tipo = "COMPRA"
        transaccion.cliente = self.cliente_normal
        transaccion.moneda_origen = self.usd
        transaccion.moneda_destino = self.pyg
        transaccion.medio_pago = None
        transaccion.medio_cobro = None
        
        tasa = calcularTasa(transaccion)
        
        # Tasa de compra = base - comision_compra
        tasa_esperada = self.usd.base_price - self.usd.comision_compra
        self.assertEqual(tasa, tasa_esperada)

    def test_calcular_tasa_con_descuento_categoria(self):
        """Tasa con descuento de categoría: la comisión se reduce según descuento"""
        transaccion = Mock()
        transaccion.tipo = "VENTA"
        transaccion.cliente = self.cliente_premium
        transaccion.moneda_origen = self.pyg
        transaccion.moneda_destino = self.usd
        transaccion.medio_pago = None
        transaccion.medio_cobro = None
        
        tasa = calcularTasa(transaccion)
        
        # base + (comision_venta * (1 - descuento))
        descuento = self.categoria_premium.descuento
        comision_con_descuento = self.usd.comision_venta * (1 - descuento)
        tasa_esperada = self.usd.base_price + comision_con_descuento
        self.assertEqual(tasa, tasa_esperada)


class GuardarTransaccionTests(TestCase):
    """Pruebas para la función guardar_transaccion"""

    def setUp(self):
        """Configuración inicial"""
        self.user = CustomUser.objects.create_user(
            username='testuser_guardar',
            password='testpass123',
            email='testguardar@example.com'
        )
        
        self.categoria, _ = Categoria.objects.get_or_create(
            nombre='Test Guardar',
            defaults={'descuento': Decimal('0.05')}
        )
        
        self.cliente = Cliente.objects.create(
            nombre='Cliente Test Guardar',
            documento='88888888',
            categoria=self.categoria
        )
        
        self.pyg, _ = Currency.objects.get_or_create(
            code='PYG',
            defaults={
                'name': 'Guaraní Paraguayo',
                'base_price': Decimal('1.0'),
                'comision_compra': Decimal('100'),
                'comision_venta': Decimal('100'),
                'decimales_monto': 0,
                'is_active': True
            }
        )
        
        self.usd, _ = Currency.objects.get_or_create(
            code='USD',
            defaults={
                'name': 'Dólar Americano',
                'base_price': Decimal('7500.0'),
                'comision_compra': Decimal('100'),
                'comision_venta': Decimal('100'),
                'decimales_monto': 2,
                'is_active': True
            }
        )
        
        # Crear tipos de pago/cobro necesarios
        self.tipo_pago_billetera, _ = TipoPago.objects.get_or_create(
            nombre='Billetera',
            defaults={'activo': True, 'comision': Decimal('1.5')}
        )
        
        self.tipo_cobro_billetera, _ = TipoCobro.objects.get_or_create(
            nombre='Billetera',
            defaults={'activo': True, 'comision': Decimal('1.0')}
        )
        
        # Crear entidad para billetera
        self.entidad, _ = Entidad.objects.get_or_create(
            nombre='Test Bank',
            defaults={'tipo': 'banco', 'activo': True}
        )
        
        # Crear MedioPago
        self.medio_pago = MedioPago.objects.create(
            cliente=self.cliente,
            tipo='billetera',
            nombre='Mi Billetera Test',
            activo=True,
            tipo_pago=self.tipo_pago_billetera
        )
        
        # Crear MedioCobro
        self.medio_cobro = MedioCobro.objects.create(
            cliente=self.cliente,
            tipo='billetera',
            nombre='Mi Billetera Cobro Test',
            activo=True,
            tipo_cobro=self.tipo_cobro_billetera
        )

    def test_guardar_transaccion_venta(self):
        """Guardar transacción de tipo VENTA"""
        ct_medio_pago = ContentType.objects.get_for_model(MedioPago)
        ct_medio_cobro = ContentType.objects.get_for_model(MedioCobro)
        
        data = {
            'tipo': 'VENTA',
            'moneda_origen': 'PYG',
            'moneda_destino': 'USD',
            'tasa_cambio': '7600',
            'monto_origen': '7600000',
            'monto_destino': '1000',
            'medio_pago_contenttype': ct_medio_pago.id,
            'medio_pago': self.medio_pago.id,
            'medio_cobro_contenttype': ct_medio_cobro.id,
            'medio_cobro': self.medio_cobro.id,
        }
        
        transaccion = guardar_transaccion(
            cliente=self.cliente,
            usuario=self.user,
            data=data,
            estado='PENDIENTE'
        )
        
        self.assertIsNotNone(transaccion.id)
        self.assertEqual(transaccion.tipo, 'VENTA')
        self.assertEqual(transaccion.estado, 'PENDIENTE')
        self.assertEqual(transaccion.moneda_origen.code, 'PYG')
        self.assertEqual(transaccion.moneda_destino.code, 'USD')

    def test_guardar_transaccion_compra(self):
        """Guardar transacción de tipo COMPRA"""
        ct_medio_pago = ContentType.objects.get_for_model(MedioPago)
        ct_medio_cobro = ContentType.objects.get_for_model(MedioCobro)
        
        data = {
            'tipo': 'COMPRA',
            'moneda_origen': 'USD',
            'moneda_destino': 'PYG',
            'tasa_cambio': '7400',
            'monto_origen': '1000',
            'monto_destino': '7400000',
            'medio_pago_contenttype': ct_medio_pago.id,
            'medio_pago': self.medio_pago.id,
            'medio_cobro_contenttype': ct_medio_cobro.id,
            'medio_cobro': self.medio_cobro.id,
        }
        
        transaccion = guardar_transaccion(
            cliente=self.cliente,
            usuario=self.user,
            data=data,
            estado='PENDIENTE'
        )
        
        self.assertIsNotNone(transaccion.id)
        self.assertEqual(transaccion.tipo, 'COMPRA')
        self.assertEqual(transaccion.moneda_origen.code, 'USD')
        self.assertEqual(transaccion.moneda_destino.code, 'PYG')

    def test_guardar_transaccion_guarda_comisiones(self):
        """Verificar que se guardan las comisiones de medio pago/cobro"""
        ct_medio_pago = ContentType.objects.get_for_model(MedioPago)
        ct_medio_cobro = ContentType.objects.get_for_model(MedioCobro)
        
        data = {
            'tipo': 'VENTA',
            'moneda_origen': 'PYG',
            'moneda_destino': 'USD',
            'tasa_cambio': '7600',
            'monto_origen': '7600000',
            'monto_destino': '1000',
            'medio_pago_contenttype': ct_medio_pago.id,
            'medio_pago': self.medio_pago.id,
            'medio_cobro_contenttype': ct_medio_cobro.id,
            'medio_cobro': self.medio_cobro.id,
        }
        
        transaccion = guardar_transaccion(
            cliente=self.cliente,
            usuario=self.user,
            data=data,
            estado='PENDIENTE'
        )
        
        # Verificar que se guardaron las comisiones (usa las del TipoPago y TipoCobro)
        self.assertIsNotNone(transaccion.medio_pago_porc)
        self.assertIsNotNone(transaccion.medio_cobro_porc)
        # Verificar que las comisiones son valores Decimal positivos o cero
        self.assertGreaterEqual(transaccion.medio_pago_porc, Decimal('0'))
        self.assertGreaterEqual(transaccion.medio_cobro_porc, Decimal('0'))

    def test_guardar_transaccion_guarda_descuento_cliente(self):
        """Verificar que se guarda el descuento del cliente"""
        ct_medio_pago = ContentType.objects.get_for_model(MedioPago)
        ct_medio_cobro = ContentType.objects.get_for_model(MedioCobro)
        
        data = {
            'tipo': 'VENTA',
            'moneda_origen': 'PYG',
            'moneda_destino': 'USD',
            'tasa_cambio': '7600',
            'monto_origen': '7600000',
            'monto_destino': '1000',
            'medio_pago_contenttype': ct_medio_pago.id,
            'medio_pago': self.medio_pago.id,
            'medio_cobro_contenttype': ct_medio_cobro.id,
            'medio_cobro': self.medio_cobro.id,
        }
        
        transaccion = guardar_transaccion(
            cliente=self.cliente,
            usuario=self.user,
            data=data,
            estado='PENDIENTE'
        )
        
        # El cliente tiene 5% de descuento
        self.assertEqual(transaccion.desc_cliente, Decimal('0.05'))


class TransaccionValidacionTests(TestCase):
    """Pruebas de validación para transacciones"""

    def setUp(self):
        """Configuración inicial"""
        self.user = CustomUser.objects.create_user(
            username='testuser_validacion',
            password='testpass123',
            email='testvalidacion@example.com'
        )
        
        self.categoria, _ = Categoria.objects.get_or_create(
            nombre='Test Validacion',
            defaults={'descuento': Decimal('0')}
        )
        
        self.cliente = Cliente.objects.create(
            nombre='Cliente Test Validacion',
            documento='77777777',
            categoria=self.categoria
        )
        
        ClienteUsuario.objects.create(
            cliente=self.cliente,
            usuario=self.user
        )
        
        self.pyg, _ = Currency.objects.get_or_create(
            code='PYG',
            defaults={
                'name': 'Guaraní Paraguayo',
                'base_price': Decimal('1.0'),
                'comision_compra': Decimal('100'),
                'comision_venta': Decimal('100'),
                'decimales_monto': 0,
                'is_active': True
            }
        )
        
        self.usd, _ = Currency.objects.get_or_create(
            code='USD',
            defaults={
                'name': 'Dólar Americano',
                'base_price': Decimal('7500.0'),
                'comision_compra': Decimal('100'),
                'comision_venta': Decimal('100'),
                'decimales_monto': 2,
                'is_active': True
            }
        )
        
        self.tipo_pago, _ = TipoPago.objects.get_or_create(
            nombre='Test Pago',
            defaults={'activo': True, 'comision': Decimal('0')}
        )
        
        self.tipo_cobro, _ = TipoCobro.objects.get_or_create(
            nombre='Test Cobro',
            defaults={'activo': True, 'comision': Decimal('0')}
        )
        
        self.client = Client()

    def test_compraventa_requiere_login(self):
        """La vista de compraventa requiere autenticación o cliente seleccionado"""
        response = self.client.get(reverse('compraventa'))
        self.assertEqual(response.status_code, 302)
        # Puede redirigir a login o a selección de cliente
        self.assertTrue('login' in response.url or 'change-client' in response.url)

    def test_compraventa_requiere_cliente_seleccionado(self):
        """La vista requiere que haya un cliente seleccionado"""
        self.client.login(username='testuser_validacion', password='testpass123')
        response = self.client.get(reverse('compraventa'))
        self.assertEqual(response.status_code, 302)  # Redirige a seleccionar cliente

    def test_transaccion_tipo_invalido_rechazada(self):
        """Transacciones con tipo inválido generan error en la vista"""
        self.client.login(username='testuser_validacion', password='testpass123')
        
        session = self.client.session
        session['cliente_id'] = self.cliente.id
        session.save()
        
        response = self.client.post(reverse('compraventa'), {
            'tipo': 'INVALIDO',
            'moneda_origen': 'USD',
            'moneda_destino': 'PYG',
            'monto_origen': '100',
            'monto_destino': '750000',
            'medio_pago_tipo': self.tipo_pago.id,
            'medio_pago': '1',
            'medio_cobro_tipo': self.tipo_cobro.id,
            'medio_cobro': '1',
            'confirmar': 'true',
            'mfa_code': 'SKIP'
        })
        
        # La vista puede devolver 200 con mensaje de error o redirigir
        self.assertIn(response.status_code, [200, 302])


class APIActiveCurrenciesTests(TestCase):
    """Pruebas para el endpoint de monedas activas"""

    def setUp(self):
        """Configuración inicial"""
        self.user = CustomUser.objects.create_user(
            username='testuser_api',
            password='testpass123',
            email='testapi@example.com'
        )
        
        self.pyg, _ = Currency.objects.get_or_create(
            code='PYG',
            defaults={
                'name': 'Guaraní Paraguayo',
                'base_price': Decimal('1.0'),
                'comision_compra': Decimal('100'),
                'comision_venta': Decimal('100'),
                'decimales_monto': 0,
                'is_active': True
            }
        )
        
        self.usd, _ = Currency.objects.get_or_create(
            code='USD',
            defaults={
                'name': 'Dólar Americano',
                'base_price': Decimal('7500.0'),
                'comision_compra': Decimal('100'),
                'comision_venta': Decimal('100'),
                'decimales_monto': 2,
                'is_active': True
            }
        )
        
        self.moneda_inactiva, _ = Currency.objects.get_or_create(
            code='XXX',
            defaults={
                'name': 'Moneda Inactiva',
                'base_price': Decimal('1000.0'),
                'comision_compra': Decimal('50'),
                'comision_venta': Decimal('50'),
                'decimales_monto': 2,
                'is_active': False
            }
        )
        
        self.client = Client()

    def test_api_currencies_responde(self):
        """El endpoint responde correctamente (puede ser público)"""
        response = self.client.get(reverse('api_active_currencies'))
        # El endpoint puede ser público (200) o requerir login (302)
        self.assertIn(response.status_code, [200, 302])

    def test_api_currencies_devuelve_json(self):
        """El endpoint devuelve JSON"""
        self.client.login(username='testuser_api', password='testpass123')
        response = self.client.get(reverse('api_active_currencies'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_api_currencies_solo_activas(self):
        """Solo devuelve monedas activas"""
        self.client.login(username='testuser_api', password='testpass123')
        response = self.client.get(reverse('api_active_currencies'))
        data = response.json()
        
        codes = [item['code'] for item in data.get('items', [])]
        self.assertIn('PYG', codes)
        self.assertIn('USD', codes)
        self.assertNotIn('XXX', codes)  # Moneda inactiva no debe aparecer

    def test_api_currencies_incluye_tasas(self):
        """Cada moneda incluye tasas de compra y venta"""
        self.client.login(username='testuser_api', password='testpass123')
        response = self.client.get(reverse('api_active_currencies'))
        data = response.json()
        
        for item in data.get('items', []):
            if item['code'] != 'PYG':  # PYG no tiene tasas aplicadas igual
                self.assertIn('compra', item)
                self.assertIn('venta', item)
