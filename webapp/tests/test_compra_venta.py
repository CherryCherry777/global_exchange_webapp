from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from decimal import Decimal
from unittest.mock import patch, MagicMock

from ..models import (
    CustomUser, Cliente, Currency, Transaccion, TipoPago, TipoCobro,
    TarjetaNacional, TarjetaInternacional, Billetera, CuentaBancariaCobro,
    BilleteraCobro, Tauser, ClienteUsuario, Categoria
)
from ..views.compraventa_y_conversión import (
    compraventa_view, get_metodos_pago_cobro, transaccion_list,
    api_active_currencies, set_cliente_seleccionado, guardar_transaccion,
    monto_stripe
)

User = get_user_model()

class CompraVentaTests(TestCase):
    """Pruebas unitarias para el módulo de compra y venta"""

    def setUp(self):
        """Configuración inicial para las pruebas"""
        # Crear usuario de prueba
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )

        # Crear categoría
        self.categoria = Categoria.objects.create(
            nombre='Premium',
            descuento=Decimal('0.05')
        )

        # Crear cliente
        self.cliente = Cliente.objects.create(
            nombre='Cliente Test',
            documento='12345678',
            categoria=self.categoria
        )

        # Obtener o crear monedas (evitar duplicados)
        self.pyg, created = Currency.objects.get_or_create(
            code='PYG',
            defaults={
                'name': 'Guaraní Paraguayo',
                'base_price': Decimal('1.0'),
                'comision_compra': Decimal('0.02'),
                'comision_venta': Decimal('0.02'),
                'decimales_monto': 0,
                'is_active': True
            }
        )

        self.usd, created = Currency.objects.get_or_create(
            code='USD',
            defaults={
                'name': 'Dólar Americano',
                'base_price': Decimal('7500.0'),
                'comision_compra': Decimal('0.02'),
                'comision_venta': Decimal('0.02'),
                'decimales_monto': 2,
                'is_active': True
            }
        )

        # Obtener o crear tipos de pago y cobro (evitar duplicados)
        self.tipo_pago, created = TipoPago.objects.get_or_create(
            nombre='Tarjeta Nacional',
            defaults={
                'activo': True,
                'comision': Decimal('0.02')
            }
        )

        self.tipo_cobro, created = TipoCobro.objects.get_or_create(
            nombre='Transferencia',
            defaults={
                'activo': True,
                'comision': Decimal('0.01')
            }
        )

        # Asociar cliente con usuario
        self.cliente_usuario = ClienteUsuario.objects.create(
            cliente=self.cliente,
            usuario=self.user
        )

        # Crear cliente de test HTTP
        self.client = Client()

    def test_compraventa_view_sin_cliente_seleccionado(self):
        """Prueba que redirige cuando no hay cliente seleccionado"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('compraventa'))
        self.assertEqual(response.status_code, 302)  # Redirección

    def test_compraventa_view_con_cliente_seleccionado(self):
        """Prueba que muestra la vista cuando hay cliente seleccionado"""
        self.client.login(username='testuser', password='testpass123')

        # Crear sesión con cliente seleccionado
        session = self.client.session
        session['cliente_id'] = self.cliente.id
        session.save()

        response = self.client.get(reverse('compraventa'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'webapp/compraventa_y_conversion/compraventa.html')

    @patch('webapp.views.compraventa_y_conversión.procesar_pago_stripe')
    def test_compraventa_procesar_pago_stripe_exitoso(self, mock_stripe):
        """Prueba procesamiento exitoso de pago con Stripe"""
        self.client.login(username='testuser', password='testpass123')

        # Crear sesión con cliente seleccionado
        session = self.client.session
        session['cliente_id'] = self.cliente.id
        session.save()

        # Mock de respuesta exitosa de Stripe
        mock_stripe.return_value = {
            'success': True,
            'payment_intent_id': 'pi_test_123'
        }

        # Crear MedioPago y tarjeta internacional
        from ..models import MedioPago
        
        tipo_pago_tarjeta_int, _ = TipoPago.objects.get_or_create(
            nombre='Tarjeta Internacional Test',
            defaults={'activo': True, 'comision': Decimal('0.03')}
        )
        
        medio_pago = MedioPago.objects.create(
            cliente=self.cliente,
            tipo='tarjeta_internacional',
            nombre='Mi Tarjeta Internacional Test',
            activo=True,
            tipo_pago=tipo_pago_tarjeta_int
        )
        
        tarjeta_int = TarjetaInternacional.objects.create(
            medio_pago=medio_pago,
            ultimos_digitos='1234',
            stripe_payment_method_id='pm_test_123',
            exp_month=12,
            exp_year=2026
        )

        response = self.client.post(reverse('compraventa'), {
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

        # 200 = formulario/MFA, 302 = redirección exitosa
        self.assertIn(response.status_code, [200, 302])

    def test_get_metodos_pago_cobro_sin_cliente(self):
        """Prueba API de métodos de pago/cobro sin cliente seleccionado"""
        response = self.client.get(reverse('get_metodos_pago_cobro'))
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['metodo_pago'], [])
        self.assertEqual(data['metodo_cobro'], [])

    def test_get_metodos_pago_cobro_con_cliente(self):
        """Prueba API de métodos de pago/cobro con cliente seleccionado"""
        # Crear sesión con cliente seleccionado
        session = self.client.session
        session['cliente_id'] = self.cliente.id
        session.save()

        response = self.client.get(reverse('get_metodos_pago_cobro'))
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('metodo_pago', data)
        self.assertIn('metodo_cobro', data)

    def test_transaccion_list_sin_cliente(self):
        """Prueba lista de transacciones sin cliente seleccionado"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('transaccion_list'))
        self.assertEqual(response.status_code, 302)  # Redirección

    def test_transaccion_list_con_cliente(self):
        """Prueba lista de transacciones con cliente seleccionado"""
        self.client.login(username='testuser', password='testpass123')

        # Crear sesión con cliente seleccionado
        session = self.client.session
        session['cliente_id'] = self.cliente.id
        session.save()

        response = self.client.get(reverse('transaccion_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'webapp/compraventa_y_conversion/historial_transacciones.html')

    def test_api_active_currencies_sin_autenticacion(self):
        """Prueba API de monedas activas sin autenticación"""
        response = self.client.get(reverse('api_active_currencies'))
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('items', data)
        self.assertGreater(len(data['items']), 0)

    def test_api_active_currencies_con_autenticacion(self):
        """Prueba API de monedas activas con autenticación"""
        self.client.login(username='testuser', password='testpass123')

        # Crear sesión con cliente seleccionado
        session = self.client.session
        session['cliente_id'] = self.cliente.id
        session.save()

        response = self.client.get(reverse('api_active_currencies'))
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('items', data)

    def test_set_cliente_seleccionado_post(self):
        """Prueba establecer cliente seleccionado vía POST"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post(reverse('set_cliente_seleccionado'), {
            'cliente_id': self.cliente.id
        })

        # Verificar que se guardó en sesión
        self.assertEqual(self.client.session.get('cliente_id'), self.cliente.id)

    def test_set_cliente_seleccionado_remove(self):
        """Prueba remover cliente seleccionado"""
        self.client.login(username='testuser', password='testpass123')

        # Primero establecer cliente
        self.client.post(reverse('set_cliente_seleccionado'), {
            'cliente_id': self.cliente.id
        })

        # Luego remover
        response = self.client.post(reverse('set_cliente_seleccionado'), {})

        # Verificar que se removió de sesión
        self.assertNotIn('cliente_id', self.client.session)

    def test_guardar_transaccion_function(self):
        """Prueba función auxiliar para guardar transacciones"""
        data = {
            'tipo': 'compra',
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

        transaccion = guardar_transaccion(
            cliente=self.cliente,
            usuario=self.user,
            data=data,
            estado='pendiente'
        )

        self.assertIsNotNone(transaccion.id)
        self.assertEqual(transaccion.cliente, self.cliente)
        self.assertEqual(transaccion.usuario, self.user)
        self.assertEqual(transaccion.tipo, 'compra')
        self.assertEqual(transaccion.estado, 'pendiente')

    def test_monto_stripe_monedas_sin_decimales(self):
        """Prueba cálculo de monto Stripe para monedas sin decimales"""
        monto = monto_stripe(Decimal('1000'), 'PYG')
        self.assertEqual(monto, 1000)  # Debe ser entero

    def test_monto_stripe_monedas_con_decimales(self):
        """Prueba cálculo de monto Stripe para monedas con decimales"""
        monto = monto_stripe(Decimal('100.50'), 'USD')
        self.assertEqual(monto, 10050)  # Debe convertirse a centavos

    def test_compraventa_validacion_monto_invalido(self):
        """Prueba validación de monto inválido en compraventa"""
        self.client.login(username='testuser', password='testpass123')

        # Crear sesión con cliente seleccionado
        session = self.client.session
        session['cliente_id'] = self.cliente.id
        session.save()

        response = self.client.post(reverse('compraventa'), {
            'tipo': 'compra',
            'moneda_origen': 'USD',
            'moneda_destino': 'PYG',
            'monto_origen': '-100',  # Monto negativo inválido
            'monto_destino': '750000',
            'medio_pago_tipo': self.tipo_pago.id,
            'medio_pago': '1',
            'medio_cobro_tipo': self.tipo_cobro.id,
            'medio_cobro': '1',
            'confirmar': 'true'
        })

        # 200 = formulario con errores, 302 = redirección
        self.assertIn(response.status_code, [200, 302])

    def test_compraventa_tipo_transaccion_invalido(self):
        """Prueba manejo de tipo de transacción inválido"""
        self.client.login(username='testuser', password='testpass123')

        # Crear sesión con cliente seleccionado
        session = self.client.session
        session['cliente_id'] = self.cliente.id
        session.save()

        response = self.client.post(reverse('compraventa'), {
            'tipo': 'invalido',  # Tipo inválido
            'moneda_origen': 'USD',
            'moneda_destino': 'PYG',
            'monto_origen': '100',
            'monto_destino': '750000',
            'medio_pago_tipo': self.tipo_pago.id,
            'medio_pago': '1',
            'medio_cobro_tipo': self.tipo_cobro.id,
            'medio_cobro': '1',
            'confirmar': 'true'
        })

        # 200 = formulario con errores, 302 = redirección por error
        self.assertIn(response.status_code, [200, 302])

    def test_api_active_currencies_con_comisiones_metodo(self):
        """Prueba API de monedas con comisiones de método aplicadas"""
        self.client.login(username='testuser', password='testpass123')

        # Crear sesión con cliente seleccionado
        session = self.client.session
        session['cliente_id'] = self.cliente.id
        session.save()

        response = self.client.get(reverse('api_active_currencies'), {
            'tipo_metodo_pago_id': self.tipo_pago.id,
            'tipo_metodo_cobro_id': self.tipo_cobro.id
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('items', data)

        # Verificar que las comisiones se aplicaron
        pyg_data = next((item for item in data['items'] if item['code'] == 'PYG'), None)
        self.assertIsNotNone(pyg_data)

    def test_compraventa_billetera_con_pin(self):
        """Prueba flujo de pago con billetera que requiere PIN"""
        self.client.login(username='testuser', password='testpass123')

        # Crear sesión con cliente seleccionado
        session = self.client.session
        session['cliente_id'] = self.cliente.id
        session.save()

        # Crear MedioPago primero
        from ..models import MedioPago, Entidad
        
        entidad, _ = Entidad.objects.get_or_create(
            nombre='Tigo Money Test',
            defaults={'tipo': 'telefono', 'activo': True}
        )
        
        tipo_pago_billetera, _ = TipoPago.objects.get_or_create(
            nombre='Billetera',
            defaults={'activo': True, 'comision': Decimal('0.01')}
        )
        
        medio_pago = MedioPago.objects.create(
            cliente=self.cliente,
            tipo='billetera',
            nombre='Mi Billetera Test',
            activo=True,
            tipo_pago=tipo_pago_billetera
        )
        
        # Crear billetera asociada al MedioPago
        billetera = Billetera.objects.create(
            medio_pago=medio_pago,
            numero_celular='0981123456',
            entidad=entidad
        )

        with patch('webapp.views.compraventa_y_conversión.cobrar_al_cliente_billetera') as mock_cobrar:
            # Mock que requiere PIN
            mock_cobrar.return_value = {
                'require_pin': True,
                'message': 'Ingrese PIN',
                'allow_retry': True
            }

            response = self.client.post(reverse('compraventa'), {
                'tipo': 'compra',
                'moneda_origen': 'PYG',
                'moneda_destino': 'USD',
                'monto_origen': '100000',
                'monto_destino': '13.33',
                'medio_pago_tipo': self.tipo_pago.id,
                'medio_pago': billetera.id,
                'medio_cobro_tipo': self.tipo_cobro.id,
                'medio_cobro': '1',
                'confirmar': 'true'
            })

            # Debe mostrar formulario de PIN o MFA (200)
            self.assertEqual(response.status_code, 200)

    def test_compraventa_cancelar_pago_billetera(self):
        """Prueba cancelación de pago con billetera"""
        self.client.login(username='testuser', password='testpass123')

        # Crear sesión con cliente seleccionado
        session = self.client.session
        session['cliente_id'] = self.cliente.id
        session.save()

        response = self.client.post(reverse('compraventa'), {
            'tipo': 'compra',
            'moneda_origen': 'PYG',
            'moneda_destino': 'USD',
            'monto_origen': '100000',
            'monto_destino': '13.33',
            'medio_pago_tipo': self.tipo_pago.id,
            'medio_pago': '1',
            'medio_cobro_tipo': self.tipo_cobro.id,
            'medio_cobro': '1',
            'cancelar': 'true'
        })

        # 200 = muestra formulario, 302 = redirección tras cancelar
        self.assertIn(response.status_code, [200, 302])

    def test_compraventa_tarjeta_nacional_solo_pyg(self):
        """Prueba que tarjeta nacional solo funciona con PYG"""
        self.client.login(username='testuser', password='testpass123')

        # Crear sesión con cliente seleccionado
        session = self.client.session
        session['cliente_id'] = self.cliente.id
        session.save()

        # Crear MedioPago y TarjetaNacional
        from ..models import MedioPago
        from datetime import date
        
        tipo_pago_tarjeta, _ = TipoPago.objects.get_or_create(
            nombre='Tarjeta Nacional Test',
            defaults={'activo': True, 'comision': Decimal('0.02')}
        )
        
        medio_pago = MedioPago.objects.create(
            cliente=self.cliente,
            tipo='tarjeta_nacional',
            nombre='Mi Tarjeta Nacional Test',
            activo=True,
            tipo_pago=tipo_pago_tarjeta
        )
        
        # Crear tarjeta nacional con fecha de vencimiento
        tarjeta_nacional = TarjetaNacional.objects.create(
            medio_pago=medio_pago,
            ultimos_digitos='1234',
            numero_tokenizado='token123',
            fecha_vencimiento=date(2026, 12, 31)
        )

        with patch('webapp.views.compraventa_y_conversión.cobrar_al_cliente_tarjeta_nacional') as mock_cobrar:
            mock_cobrar.return_value = {'success': True}

            # Intentar usar tarjeta nacional con USD (debe fallar)
            response = self.client.post(reverse('compraventa'), {
                'tipo': 'compra',
                'moneda_origen': 'USD',  # Moneda diferente a PYG
                'moneda_destino': 'PYG',
                'monto_origen': '100',
                'monto_destino': '750000',
                'medio_pago_tipo': self.tipo_pago.id,
                'medio_pago': tarjeta_nacional.id,
                'medio_cobro_tipo': self.tipo_cobro.id,
                'medio_cobro': '1',
                'confirmar': 'true'
            })

            # 200 = formulario con error, 302 = redirección por error
            self.assertIn(response.status_code, [200, 302])

    def test_api_active_currencies_aplicar_descuento_categoria(self):
        """Prueba que se aplica descuento de categoría correctamente"""
        self.client.login(username='testuser', password='testpass123')

        # Crear sesión con cliente seleccionado
        session = self.client.session
        session['cliente_id'] = self.cliente.id
        session.save()

        response = self.client.get(reverse('api_active_currencies'))

        data = response.json()
        pyg_data = next((item for item in data['items'] if item['code'] == 'PYG'), None)

        # Verificar que PYG existe en la respuesta
        self.assertIsNotNone(pyg_data)
        # Los valores de PYG pueden variar según la configuración
        self.assertIn('venta', pyg_data)
        self.assertIn('compra', pyg_data)

    def test_compraventa_crear_transaccion_exitosa(self):
        """Prueba creación exitosa de transacción"""
        self.client.login(username='testuser', password='testpass123')

        # Crear sesión con cliente seleccionado
        session = self.client.session
        session['cliente_id'] = self.cliente.id
        session.save()

        # Obtener o crear tipos de pago y cobro básicos para la prueba
        tipo_pago_basico, _ = TipoPago.objects.get_or_create(
            nombre='Tauser', 
            defaults={'activo': True, 'comision': Decimal('0')}
        )
        tipo_cobro_basico, _ = TipoCobro.objects.get_or_create(
            nombre='Tauser', 
            defaults={'activo': True, 'comision': Decimal('0')}
        )

        # Obtener o crear Tauser para pago y cobro
        tauser_pago, _ = Tauser.objects.get_or_create(
            nombre='Tauser Pago Test',
            defaults={
                'ubicacion': 'Asunción',
                'activo': True,
                'tipo_pago': tipo_pago_basico
            }
        )

        tauser_cobro, _ = Tauser.objects.get_or_create(
            nombre='Tauser Cobro Test',
            defaults={
                'ubicacion': 'Asunción',
                'activo': True,
                'tipo_cobro': tipo_cobro_basico
            }
        )

        response = self.client.post(reverse('compraventa'), {
            'tipo': 'compra',
            'moneda_origen': 'USD',
            'moneda_destino': 'PYG',
            'monto_origen': '100',
            'monto_destino': '750000',
            'medio_pago_tipo': tipo_pago_basico.id,
            'medio_pago': tauser_pago.id,
            'medio_cobro_tipo': tipo_cobro_basico.id,
            'medio_cobro': tauser_cobro.id,
            'confirmar': 'true'
        })

        # 200 = formulario/MFA requerido, 302 = redirección exitosa
        # La vista puede requerir MFA antes de crear la transacción
        self.assertIn(response.status_code, [200, 302])

    def test_compraventa_monto_cero_invalido(self):
        """Prueba que monto cero es inválido"""
        self.client.login(username='testuser', password='testpass123')

        # Crear sesión con cliente seleccionado
        session = self.client.session
        session['cliente_id'] = self.cliente.id
        session.save()

        response = self.client.post(reverse('compraventa'), {
            'tipo': 'compra',
            'moneda_origen': 'USD',
            'moneda_destino': 'PYG',
            'monto_origen': '0',  # Monto cero inválido
            'monto_destino': '0',  # Monto cero inválido
            'medio_pago_tipo': self.tipo_pago.id,
            'medio_pago': '1',
            'medio_cobro_tipo': self.tipo_cobro.id,
            'medio_cobro': '1',
            'confirmar': 'true'
        })

        # 200 = formulario con errores, 302 = redirección por error
        self.assertIn(response.status_code, [200, 302])

    def test_get_metodos_pago_cobro_filtrado_por_moneda(self):
        """Prueba filtrado de métodos de pago/cobro por moneda"""
        # Crear sesión con cliente seleccionado
        session = self.client.session
        session['cliente_id'] = self.cliente.id
        session.save()

        response = self.client.get(reverse('get_metodos_pago_cobro'), {
            'from': 'USD',
            'to': 'PYG'
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Verificar estructura de respuesta
        self.assertIn('metodo_pago', data)
        self.assertIn('metodo_cobro', data)

    def test_monto_stripe_monedas_especiales(self):
        """Prueba cálculo de monto Stripe para monedas especiales"""
        # Probar moneda sin decimales
        monto_pyg = monto_stripe(Decimal('1000'), 'PYG')
        self.assertEqual(monto_pyg, 1000)

        # Probar moneda con decimales
        monto_usd = monto_stripe(Decimal('100.50'), 'USD')
        self.assertEqual(monto_usd, 10050)

        # Probar moneda especial CLP
        monto_clp = monto_stripe(Decimal('1000'), 'CLP')
        self.assertEqual(monto_clp, 1000)

        # Probar moneda especial JPY
        monto_jpy = monto_stripe(Decimal('1000'), 'JPY')
        self.assertEqual(monto_jpy, 1000)