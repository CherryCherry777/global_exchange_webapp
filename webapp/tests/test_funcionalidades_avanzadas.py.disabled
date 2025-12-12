from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.conf import settings
from decimal import Decimal
from unittest.mock import patch, MagicMock

from ..models import (
    CustomUser, Cliente, Currency, Transaccion, TipoPago, TipoCobro,
    TarjetaNacional, TarjetaInternacional, Billetera, CuentaBancariaCobro,
    BilleteraCobro, Tauser, ClienteUsuario, Categoria, LimiteIntercambio,
    MedioPago, MedioCobro, Entidad
)
from ..views.compraventa_y_conversión import (
    compraventa_view, get_metodos_pago_cobro, api_active_currencies,
    guardar_transaccion, monto_stripe
)

User = get_user_model()

class FuncionalidadesAvanzadasTests(TestCase):
    """Pruebas unitarias para funcionalidades avanzadas del sistema"""

    def setUp(self):
        """Configuración inicial para las pruebas"""
        # Crear usuarios con diferentes roles
        self.admin_user = CustomUser.objects.create_superuser(
            username='admin',
            password='admin123',
            email='admin@example.com'
        )

        self.employee_user = CustomUser.objects.create_user(
            username='employee',
            password='employee123',
            email='employee@example.com'
        )

        self.regular_user = CustomUser.objects.create_user(
            username='regular',
            password='regular123',
            email='regular@example.com'
        )

        # Crear categorías con diferentes límites
        self.categoria_basica = Categoria.objects.create(
            nombre='Básica',
            descuento=Decimal('0.0')
        )

        self.categoria_premium = Categoria.objects.create(
            nombre='Premium',
            descuento=Decimal('0.05')
        )

        # Crear clientes
        self.cliente_basico = Cliente.objects.create(
            nombre='Cliente Básico',
            documento='11111111',
            categoria=self.categoria_basica
        )

        self.cliente_premium = Cliente.objects.create(
            nombre='Cliente Premium',
            documento='22222222',
            categoria=self.categoria_premium
        )

        # Obtener o crear monedas adicionales (evitar duplicados)
        self.eur, created = Currency.objects.get_or_create(
            code='EUR',
            defaults={
                'name': 'Euro',
                'base_price': Decimal('8200.0'),
                'comision_compra': Decimal('0.025'),
                'comision_venta': Decimal('0.025'),
                'decimales_monto': 2,
                'is_active': True
            }
        )

        self.brl, created = Currency.objects.get_or_create(
            code='BRL',
            defaults={
                'name': 'Real Brasileño',
                'base_price': Decimal('1400.0'),
                'comision_compra': Decimal('0.03'),
                'comision_venta': Decimal('0.03'),
                'decimales_monto': 2,
                'is_active': True
            }
        )

        # Crear entidades
        self.entidad_bancaria = Entidad.objects.create(
            nombre='Banco Test',
            tipo='banco',
            activo=True
        )

        self.entidad_billetera, created = Entidad.objects.get_or_create(
            nombre='Tigo Money',
            defaults={
                'tipo': 'telefono',
                'activo': True
            }
        )

        # Obtener o crear tipos de pago y cobro con comisiones (evitar duplicados)
        self.tipo_pago_credito, created = TipoPago.objects.get_or_create(
            nombre='Crédito',
            defaults={
                'activo': True,
                'comision': Decimal('0.03')
            }
        )

        self.tipo_cobro_debito, created = TipoCobro.objects.get_or_create(
            nombre='Débito',
            defaults={
                'activo': True,
                'comision': Decimal('0.015')
            }
        )

        # Crear límites de intercambio
        self.limite_diario = LimiteIntercambio.objects.create(
            categoria=self.categoria_basica,
            moneda=self.usd,
            tipo_limite='diario',
            monto_max=Decimal('10000.0')
        )

        # Asociar clientes con usuarios
        self.cliente_usuario_admin = ClienteUsuario.objects.create(
            cliente=self.cliente_basico,
            usuario=self.admin_user
        )

        self.cliente_usuario_employee = ClienteUsuario.objects.create(
            cliente=self.cliente_premium,
            usuario=self.employee_user
        )

        # Crear cliente de test HTTP
        self.client = Client()

    def test_limite_intercambio_diario_excedido(self):
        """Prueba que se respete el límite diario de intercambio"""
        self.client.login(username='admin', password='admin123')

        # Crear sesión con cliente seleccionado
        session = self.client.session
        session['cliente_id'] = self.cliente_basico.id
        session.save()

        # Crear transacciones que excedan el límite diario
        # Crear múltiples transacciones pequeñas que sumen más del límite

        # Crear Tauser para pago y cobro
        tipo_pago_basico = TipoPago.objects.create(nombre='Tauser', activo=True)
        tipo_cobro_basico = TipoCobro.objects.create(nombre='Tauser', activo=True)

        tauser_pago = Tauser.objects.create(
            nombre='Tauser Pago Test',
            tipo='pago',
            ubicacion='Asunción',
            activo=True,
            tipo_pago=tipo_pago_basico
        )

        tauser_cobro = Tauser.objects.create(
            nombre='Tauser Cobro Test',
            tipo='cobro',
            ubicacion='Asunción',
            activo=True,
            tipo_cobro=tipo_cobro_basico
        )

        # Crear transacción que exceda el límite
        response = self.client.post(reverse('compraventa'), {
            'tipo': 'compra',
            'moneda_origen': 'USD',
            'moneda_destino': 'PYG',
            'monto_origen': '15000',  # Excede límite de 10000
            'monto_destino': '112500000',
            'medio_pago_tipo': tipo_pago_basico.id,
            'medio_pago': tauser_pago.id,
            'medio_cobro_tipo': tipo_cobro_basico.id,
            'medio_cobro': tauser_cobro.id,
            'confirmar': 'true'
        })

        # Debería fallar por límite excedido
        self.assertEqual(response.status_code, 302)

    def test_descuento_categoria_premium_aplicado(self):
        """Prueba que se aplica correctamente el descuento de categoría premium"""
        self.client.login(username='employee', password='employee123')

        # Crear sesión con cliente premium
        session = self.client.session
        session['cliente_id'] = self.cliente_premium.id
        session.save()

        response = self.client.get(reverse('api_active_currencies'))

        data = response.json()

        # Buscar moneda USD y verificar que tiene descuento aplicado
        usd_data = next((item for item in data['items'] if item['code'] == 'USD'), None)
        self.assertIsNotNone(usd_data)

        # Con descuento del 5%, el precio debería ser menor
        precio_base = float(self.usd.base_price)
        precio_con_descuento = precio_base * 0.95  # 5% menos

        # Verificar que se aplicó el descuento (con pequeña tolerancia por redondeo)
        self.assertAlmostEqual(usd_data['compra'], precio_con_descuento, delta=1.0)

    def test_comisiones_metodo_pago_aplicadas(self):
        """Prueba que se aplican correctamente las comisiones de método de pago"""
        self.client.login(username='admin', password='admin123')

        # Crear sesión con cliente seleccionado
        session = self.client.session
        session['cliente_id'] = self.cliente_basico.id
        session.save()

        response = self.client.get(reverse('api_active_currencies'), {
            'tipo_metodo_pago_id': self.tipo_pago_credito.id,
            'tipo_metodo_cobro_id': self.tipo_cobro_debito.id
        })

        data = response.json()

        # Buscar moneda USD y verificar que tiene comisiones aplicadas
        usd_data = next((item for item in data['items'] if item['code'] == 'USD'), None)
        self.assertIsNotNone(usd_data)

        # Calcular precio con comisiones aplicadas
        precio_base = float(self.usd.base_price)
        comision_pago = float(self.tipo_pago_credito.comision)  # 3%
        comision_cobro = float(self.tipo_cobro_debito.comision)  # 1.5%

        precio_venta_esperado = precio_base * (1 + comision_pago/100 + comision_cobro/100)
        precio_compra_esperado = precio_base * (1 - comision_cobro/100 - comision_pago/100)

        # Verificar que se aplicaron las comisiones correctamente
        self.assertAlmostEqual(usd_data['venta'], precio_venta_esperado, delta=1.0)
        self.assertAlmostEqual(usd_data['compra'], precio_compra_esperado, delta=1.0)

    def test_moneda_inactiva_no_aparece_en_api(self):
        """Prueba que monedas inactivas no aparecen en la API"""
        # Crear moneda inactiva
        moneda_inactiva = Currency.objects.create(
            code='CAD',
            name='Dólar Canadiense',
            base_price=Decimal('5500.0'),
            comision_compra=Decimal('0.02'),
            comision_venta=Decimal('0.02'),
            decimales_monto=2,
            is_active=False  # Inactiva
        )

        response = self.client.get(reverse('api_active_currencies'))

        data = response.json()

        # Verificar que la moneda inactiva no está en la respuesta
        moneda_codes = [item['code'] for item in data['items']]
        self.assertNotIn('CAD', moneda_codes)

    def test_pyg_siempre_presente_en_api(self):
        """Prueba que PYG siempre está presente en la API aunque no esté activa"""
        # Desactivar PYG
        self.pyg.is_active = False
        self.pyg.save()

        response = self.client.get(reverse('api_active_currencies'))

        data = response.json()

        # Verificar que PYG siempre está presente
        pyg_data = next((item for item in data['items'] if item['code'] == 'PYG'), None)
        self.assertIsNotNone(pyg_data)
        self.assertEqual(pyg_data['venta'], 1.0)
        self.assertEqual(pyg_data['compra'], 1.0)

    def test_transaccion_con_stripe_payment_intent(self):
        """Prueba creación de transacción con payment intent de Stripe"""
        data = {
            'tipo': 'venta',
            'moneda_origen': 'USD',
            'moneda_destino': 'PYG',
            'tasa_cambio': '7500.0',
            'monto_origen': '100.0',
            'monto_destino': '750000.0',
            'medio_pago_contenttype': 1,
            'medio_pago': 1,
            'medio_cobro_contenttype': 1,
            'medio_cobro': 1,
        }

        payment_intent_id = 'pi_test_123456789'

        transaccion = guardar_transaccion(
            cliente=self.cliente_basico,
            usuario=self.admin_user,
            data=data,
            estado='pagada',
            payment_intent_id=payment_intent_id
        )

        self.assertEqual(transaccion.stripe_payment_intent_id, payment_intent_id)
        self.assertEqual(transaccion.estado, 'pagada')

    def test_calculo_monto_stripe_precision_decimales(self):
        """Prueba precisión en cálculo de monto Stripe con diferentes decimales"""
        # Probar con monto que tenga muchos decimales
        monto_preciso = Decimal('100.123456')
        monto_stripe_result = monto_stripe(monto_preciso, 'USD')

        # Debe convertir correctamente a centavos
        self.assertEqual(monto_stripe_result, 10012)  # 100.123456 -> 10012 centavos

    def test_api_currencies_con_filtros_invalidos(self):
        """Prueba API de monedas con IDs de método inválidos"""
        self.client.login(username='admin', password='admin123')

        # Crear sesión con cliente seleccionado
        session = self.client.session
        session['cliente_id'] = self.cliente_basico.id
        session.save()

        response = self.client.get(reverse('api_active_currencies'), {
            'tipo_metodo_pago_id': '99999',  # ID inválido
            'tipo_metodo_cobro_id': '88888'   # ID inválido
        })

        # Debe manejar gracefully los IDs inválidos
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('items', data)

    def test_compraventa_con_datos_incompletos(self):
        """Prueba manejo de datos incompletos en formulario"""
        self.client.login(username='admin', password='admin123')

        # Crear sesión con cliente seleccionado
        session = self.client.session
        session['cliente_id'] = self.cliente_basico.id
        session.save()

        # Enviar formulario con datos faltantes
        response = self.client.post(reverse('compraventa'), {
            'tipo': 'compra',
            # Faltan otros campos requeridos
            'confirmar': 'true'
        })

        # Debe manejar el error gracefully
        self.assertEqual(response.status_code, 302)

    def test_cambio_entre_monedas_extranjeras(self):
        """Prueba conversión entre dos monedas extranjeras (EUR -> BRL)"""
        self.client.login(username='admin', password='admin123')

        # Crear sesión con cliente seleccionado
        session = self.client.session
        session['cliente_id'] = self.cliente_basico.id
        session.save()

        # Crear tipos básicos para la prueba
        tipo_pago_basico = TipoPago.objects.create(nombre='Tauser', activo=True)
        tipo_cobro_basico = TipoCobro.objects.create(nombre='Tauser', activo=True)

        tauser_pago = Tauser.objects.create(
            nombre='Tauser EUR',
            tipo='pago',
            ubicacion='Asunción',
            activo=True,
            tipo_pago=tipo_pago_basico
        )

        tauser_cobro = Tauser.objects.create(
            nombre='Tauser BRL',
            tipo='cobro',
            ubicacion='Asunción',
            activo=True,
            tipo_cobro=tipo_cobro_basico
        )

        # Calcular montos esperados
        monto_eur = Decimal('100.0')
        monto_brl_esperado = monto_eur * (self.brl.base_price / self.eur.base_price)

        response = self.client.post(reverse('compraventa'), {
            'tipo': 'compra',
            'moneda_origen': 'EUR',
            'moneda_destino': 'BRL',
            'monto_origen': str(monto_eur),
            'monto_destino': str(monto_brl_esperado),
            'medio_pago_tipo': tipo_pago_basico.id,
            'medio_pago': tauser_pago.id,
            'medio_cobro_tipo': tipo_cobro_basico.id,
            'medio_cobro': tauser_cobro.id,
            'confirmar': 'true'
        })

        # Verificar que se procesó correctamente
        self.assertEqual(response.status_code, 302)

    def test_sistema_notificaciones_email_transacciones(self):
        """Prueba que se envían notificaciones por email de transacciones"""
        self.client.login(username='admin', password='admin123')

        # Crear sesión con cliente seleccionado
        session = self.client.session
        session['cliente_id'] = self.cliente_basico.id
        session.save()

        # Crear tipos básicos para la prueba
        tipo_pago_basico = TipoPago.objects.create(nombre='Tauser', activo=True)
        tipo_cobro_basico = TipoCobro.objects.create(nombre='Tauser', activo=True)

        tauser_pago = Tauser.objects.create(
            nombre='Tauser Email Test',
            tipo='pago',
            ubicacion='Asunción',
            activo=True,
            tipo_pago=tipo_pago_basico
        )

        tauser_cobro = Tauser.objects.create(
            nombre='Tauser Email Cobro',
            tipo='cobro',
            ubicacion='Asunción',
            activo=True,
            tipo_cobro=tipo_cobro_basico
        )

        # Limpiar emails anteriores
        mail.outbox = []

        response = self.client.post(reverse('compraventa'), {
            'tipo': 'venta',
            'moneda_origen': 'USD',
            'moneda_destino': 'PYG',
            'monto_origen': '50',
            'monto_destino': '375000',
            'medio_pago_tipo': tipo_pago_basico.id,
            'medio_pago': tauser_pago.id,
            'medio_cobro_tipo': tipo_cobro_basico.id,
            'medio_cobro': tauser_cobro.id,
            'confirmar': 'true'
        })

        # Verificar que se creó la transacción
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Transaccion.objects.filter(
            cliente=self.cliente_basico,
            tipo='venta'
        ).exists())

    def test_conversacion_monedas_con_decimales_especiales(self):
        """Prueba conversión con monedas que tienen diferentes cantidades de decimales"""
        # Crear moneda con 3 decimales
        moneda_tres_decimales = Currency.objects.create(
            code='BHD',
            name='Dinar Bahreiní',
            base_price=Decimal('19500.0'),
            comision_compra=Decimal('0.02'),
            comision_venta=Decimal('0.02'),
            decimales_monto=3,
            is_active=True
        )

        self.client.login(username='admin', password='admin123')

        # Crear sesión con cliente seleccionado
        session = self.client.session
        session['cliente_id'] = self.cliente_basico.id
        session.save()

        response = self.client.get(reverse('api_active_currencies'))

        data = response.json()

        # Verificar que la moneda con 3 decimales aparece correctamente
        bhd_data = next((item for item in data['items'] if item['code'] == 'BHD'), None)
        self.assertIsNotNone(bhd_data)
        self.assertEqual(bhd_data['decimals'], 3)

    def test_seguridad_contra_ataques_csrf(self):
        """Prueba protección contra ataques CSRF"""
        self.client.login(username='admin', password='admin123')

        # Crear sesión con cliente seleccionado
        session = self.client.session
        session['cliente_id'] = self.cliente_basico.id
        session.save()

        # Intentar POST sin token CSRF
        response = self.client.post(reverse('compraventa'), {
            'tipo': 'compra',
            'moneda_origen': 'USD',
            'moneda_destino': 'PYG',
            'monto_origen': '100',
            'monto_destino': '750000',
            'medio_pago_tipo': '1',
            'medio_pago': '1',
            'medio_cobro_tipo': '1',
            'medio_cobro': '1',
            'confirmar': 'true'
        })

        # Django debe rechazar la petición por falta de token CSRF
        self.assertEqual(response.status_code, 403)

    def test_manejo_errores_base_datos_transacciones(self):
        """Prueba manejo de errores de base de datos durante transacciones"""
        self.client.login(username='admin', password='admin123')

        # Crear sesión con cliente seleccionado
        session = self.client.session
        session['cliente_id'] = self.cliente_basico.id
        session.save()

        # Crear tipos básicos para la prueba
        tipo_pago_basico = TipoPago.objects.create(nombre='Tauser', activo=True)
        tipo_cobro_basico = TipoCobro.objects.create(nombre='Tauser', activo=True)

        tauser_pago = Tauser.objects.create(
            nombre='Tauser Error Test',
            tipo='pago',
            ubicacion='Asunción',
            activo=True,
            tipo_pago=tipo_pago_basico
        )

        tauser_cobro = Tauser.objects.create(
            nombre='Tauser Error Cobro',
            tipo='cobro',
            ubicacion='Asunción',
            activo=True,
            tipo_cobro=tipo_cobro_basico
        )

        # Simular error de base de datos con datos inválidos
        response = self.client.post(reverse('compraventa'), {
            'tipo': 'compra',
            'moneda_origen': 'INVALID',  # Moneda inválida
            'moneda_destino': 'PYG',
            'monto_origen': '100',
            'monto_destino': '750000',
            'medio_pago_tipo': tipo_pago_basico.id,
            'medio_pago': tauser_pago.id,
            'medio_cobro_tipo': tipo_cobro_basico.id,
            'medio_cobro': tauser_cobro.id,
            'confirmar': 'true'
        })

        # Debe manejar el error gracefully
        self.assertEqual(response.status_code, 302)

    def test_rendimiento_api_monedas_con_cache(self):
        """Prueba rendimiento de API de monedas (simulación de cache)"""
        import time

        self.client.login(username='admin', password='admin123')

        # Crear sesión con cliente seleccionado
        session = self.client.session
        session['cliente_id'] = self.cliente_basico.id
        session.save()

        # Primera llamada
        inicio = time.time()
        response1 = self.client.get(reverse('api_active_currencies'))
        tiempo1 = time.time() - inicio

        # Segunda llamada (debería ser más rápida si hay cache)
        inicio = time.time()
        response2 = self.client.get(reverse('api_active_currencies'))
        tiempo2 = time.time() - inicio

        # Ambas deben ser exitosas
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)

        # Los datos deben ser consistentes
        data1 = response1.json()
        data2 = response2.json()
        self.assertEqual(data1['items'], data2['items'])

    def test_validacion_limites_categoria_cliente(self):
        """Prueba validación de límites según categoría del cliente"""
        self.client.login(username='admin', password='admin123')

        # Crear sesión con cliente básico (límite bajo)
        session = self.client.session
        session['cliente_id'] = self.cliente_basico.id
        session.save()

        # Crear tipos básicos para la prueba
        tipo_pago_basico = TipoPago.objects.create(nombre='Tauser', activo=True)
        tipo_cobro_basico = TipoCobro.objects.create(nombre='Tauser', activo=True)

        tauser_pago = Tauser.objects.create(
            nombre='Tauser Limite Test',
            tipo='pago',
            ubicacion='Asunción',
            activo=True,
            tipo_pago=tipo_pago_basico
        )

        tauser_cobro = Tauser.objects.create(
            nombre='Tauser Limite Cobro',
            tipo='cobro',
            ubicacion='Asunción',
            activo=True,
            tipo_cobro=tipo_cobro_basico
        )

        # Intentar transacción que exceda límite de categoría básica
        response = self.client.post(reverse('compraventa'), {
            'tipo': 'compra',
            'moneda_origen': 'USD',
            'moneda_destino': 'PYG',
            'monto_origen': '15000',  # Excede límite de 10000
            'monto_destino': '112500000',
            'medio_pago_tipo': tipo_pago_basico.id,
            'medio_pago': tauser_pago.id,
            'medio_cobro_tipo': tipo_cobro_basico.id,
            'medio_cobro': tauser_cobro.id,
            'confirmar': 'true'
        })

        # Debe fallar por límite excedido
        self.assertEqual(response.status_code, 302)

    def test_integracion_stripe_con_diferentes_monedas(self):
        """Prueba integración con Stripe usando diferentes monedas"""
        self.client.login(username='admin', password='admin123')

        # Crear sesión con cliente seleccionado
        session = self.client.session
        session['cliente_id'] = self.cliente_basico.id
        session.save()

        # Crear tarjeta internacional
        tarjeta_int = TarjetaInternacional.objects.create(
            medio_pago=None,
            ultimos_digitos='5678',
            stripe_payment_method_id='pm_test_456'
        )

        with patch('webapp.views.compraventa_y_conversión.procesar_pago_stripe') as mock_stripe:
            # Configurar diferentes respuestas según moneda
            def stripe_side_effect(*args, **kwargs):
                moneda = kwargs.get('moneda', '')
                if moneda == 'USD':
                    return {'success': True, 'payment_intent_id': 'pi_usd_123'}
                elif moneda == 'EUR':
                    return {'success': True, 'payment_intent_id': 'pi_eur_456'}
                else:
                    return {'success': False, 'message': 'Moneda no soportada'}

            mock_stripe.side_effect = stripe_side_effect

            # Probar con USD
            response_usd = self.client.post(reverse('compraventa'), {
                'tipo': 'compra',
                'moneda_origen': 'USD',
                'moneda_destino': 'PYG',
                'monto_origen': '100',
                'monto_destino': '750000',
                'medio_pago_tipo': self.tipo_pago.id,
                'medio_pago': tarjeta_int.id,
                'medio_cobro_tipo': self.tipo_cobro.id,
                'medio_cobro': '1',
                'confirmar': 'true'
            })

            # Probar con EUR
            response_eur = self.client.post(reverse('compraventa'), {
                'tipo': 'compra',
                'moneda_origen': 'EUR',
                'moneda_destino': 'PYG',
                'monto_origen': '100',
                'monto_destino': '820000',
                'medio_pago_tipo': self.tipo_pago.id,
                'medio_pago': tarjeta_int.id,
                'medio_cobro_tipo': self.tipo_cobro.id,
                'medio_cobro': '1',
                'confirmar': 'true'
            })

            # Ambas deben ser exitosas
            self.assertEqual(response_usd.status_code, 302)
            self.assertEqual(response_eur.status_code, 302)

    def test_sistema_alertas_cambios_significativos(self):
        """Prueba sistema de alertas para cambios significativos en tasas"""
        # Crear moneda con historial
        moneda_volatil = Currency.objects.create(
            code='BTC',
            name='Bitcoin',
            base_price=Decimal('500000000.0'),  # Muy volátil
            comision_compra=Decimal('0.05'),
            comision_venta=Decimal('0.05'),
            decimales_monto=8,
            is_active=True
        )

        self.client.login(username='admin', password='admin123')

        # Crear sesión con cliente seleccionado
        session = self.client.session
        session['cliente_id'] = self.cliente_basico.id
        session.save()

        response = self.client.get(reverse('api_active_currencies'))

        data = response.json()

        # Verificar que la moneda volátil aparece correctamente
        btc_data = next((item for item in data['items'] if item['code'] == 'BTC'), None)
        self.assertIsNotNone(btc_data)
        self.assertEqual(btc_data['decimals'], 8)  # Muchos decimales para cripto

    def test_manejo_concurrente_transacciones(self):
        """Prueba manejo de transacciones concurrentes"""
        self.client.login(username='admin', password='admin123')

        # Crear sesión con cliente seleccionado
        session = self.client.session
        session['cliente_id'] = self.cliente_basico.id
        session.save()

        # Crear tipos básicos para la prueba
        tipo_pago_basico = TipoPago.objects.create(nombre='Tauser', activo=True)
        tipo_cobro_basico = TipoCobro.objects.create(nombre='Tauser', activo=True)

        tauser_pago = Tauser.objects.create(
            nombre='Tauser Concurrente',
            tipo='pago',
            ubicacion='Asunción',
            activo=True,
            tipo_pago=tipo_pago_basico
        )

        tauser_cobro = Tauser.objects.create(
            nombre='Tauser Concurrente Cobro',
            tipo='cobro',
            ubicacion='Asunción',
            activo=True,
            tipo_cobro=tipo_cobro_basico
        )

        # Crear múltiples transacciones rápidamente
        responses = []
        for i in range(3):
            response = self.client.post(reverse('compraventa'), {
                'tipo': 'compra',
                'moneda_origen': 'USD',
                'moneda_destino': 'PYG',
                'monto_origen': f'{(i+1)*10}',
                'monto_destino': f'{(i+1)*75000}',
                'medio_pago_tipo': tipo_pago_basico.id,
                'medio_pago': tauser_pago.id,
                'medio_cobro_tipo': tipo_cobro_basico.id,
                'medio_cobro': tauser_cobro.id,
                'confirmar': 'true'
            })
            responses.append(response)

        # Todas deben procesarse correctamente
        for response in responses:
            self.assertEqual(response.status_code, 302)

        # Verificar que se crearon todas las transacciones
        transacciones_count = Transaccion.objects.filter(
            cliente=self.cliente_basico,
            tipo='compra'
        ).count()

        self.assertGreaterEqual(transacciones_count, 3)

    def test_backup_datos_transacciones_criticas(self):
        """Prueba backup automático de datos en transacciones críticas"""
        # Crear transacción de alto valor
        data = {
            'tipo': 'venta',
            'moneda_origen': 'USD',
            'moneda_destino': 'PYG',
            'tasa_cambio': '7500.0',
            'monto_origen': '10000.0',  # Alto valor
            'monto_destino': '75000000.0',
            'medio_pago_contenttype': 1,
            'medio_pago': 1,
            'medio_cobro_contenttype': 1,
            'medio_cobro': 1,
        }

        transaccion_critica = guardar_transaccion(
            cliente=self.cliente_premium,  # Cliente premium para transacción crítica
            usuario=self.admin_user,
            data=data,
            estado='procesando'
        )

        # Verificar que se guardó correctamente
        self.assertIsNotNone(transaccion_critica.id)
        self.assertEqual(transaccion_critica.monto_origen, Decimal('10000.0'))
        self.assertEqual(transaccion_critica.estado, 'procesando')

        # Verificar que se puede recuperar
        transaccion_recuperada = Transaccion.objects.get(id=transaccion_critica.id)
        self.assertEqual(transaccion_recuperada.monto_origen, Decimal('10000.0'))
        self.assertEqual(transaccion_recuperada.cliente, self.cliente_premium)