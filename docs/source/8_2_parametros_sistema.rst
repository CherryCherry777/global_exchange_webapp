8.2 Parámetros del sistema
==========================

Los parámetros del sistema son configuraciones globales que afectan el comportamiento de la aplicación en todos sus módulos.

Categorías de parámetros
------------------------

**Parámetros de seguridad:**

- ``SECRET_KEY``: Clave secreta de Django para firmas criptográficas.
- ``ALLOWED_HOSTS``: Lista de dominios/IPs permitidos.
- ``DEBUG``: Modo de depuración (nunca ``True`` en producción).
- ``CSRF_COOKIE_SECURE``: Cookies CSRF solo por HTTPS.

**Parámetros de roles:**

- ``ROLE_TIERS``: Jerarquía de roles y sus niveles de privilegio.
- ``PROTECTED_ROLES``: Roles que no pueden ser eliminados (ej: Administrador).
- ``DEFAULT_USER_ROLE``: Rol asignado a nuevos usuarios por defecto.

**Parámetros de sesión:**

- ``SESSION_COOKIE_AGE``: Duración de sesión en segundos.
- ``SESSION_EXPIRE_AT_BROWSER_CLOSE``: Expira al cerrar navegador.
- ``LOGIN_URL``: URL de redirección para usuarios no autenticados.

**Parámetros de integraciones:**

- ``STRIPE_SECRET_KEY``: Clave secreta de Stripe.
- ``STRIPE_PUBLISHABLE_KEY``: Clave pública de Stripe.
- ``STRIPE_WEBHOOK_SECRET``: Secreto para validar webhooks.

**Parámetros operativos:**

- ``DEFAULT_CURRENCY``: Moneda local por defecto (ej: "PYG").
- ``TRANSACTION_TIMEOUT``: Tiempo límite para completar transacción.
- ``MAX_OFFLINE_TRANSACTIONS``: Máximo de transacciones en modo offline.

Ejemplos de parámetros comunes
------------------------------

**Parámetros en settings.py:**

.. code-block:: python

   # Jerarquía de roles
   ROLE_TIERS = {
       'Administrador': 100,
       'Supervisor': 75,
       'Operador': 50,
       'Consulta': 25,
   }

   # Roles protegidos
   PROTECTED_ROLES = ['Administrador']

   # Configuración de sesión
   SESSION_COOKIE_AGE = 3600
   SESSION_COOKIE_SECURE = True

   # Integración Stripe
   STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY')
   STRIPE_WEBHOOK_SECRET = env('STRIPE_WEBHOOK_SECRET')

   # Parámetros operativos
   DEFAULT_CURRENCY = 'PYG'
   TRANSACTION_TIMEOUT = 300  # 5 minutos

Ubicación de parámetros
-----------------------

**Nivel 1: Variables de entorno**

Para valores sensibles y específicos por ambiente:

.. code-block:: text

   # Archivo .env
   SECRET_KEY=tu-clave-secreta-muy-larga
   DATABASE_URL=postgres://user:pass@host:5432/db
   STRIPE_SECRET_KEY=sk_live_xxx
   DEBUG=False

**Nivel 2: settings.py**

Para configuraciones estructuradas y valores por defecto:

.. code-block:: python

   import os
   from dotenv import load_dotenv

   load_dotenv()

   SECRET_KEY = os.getenv('SECRET_KEY')
   DEBUG = os.getenv('DEBUG', 'False') == 'True'

**Nivel 3: Modelo SystemParameter (opcional)**

Para parámetros editables desde la UI:

.. code-block:: python

   class SystemParameter(models.Model):
       key = models.CharField(max_length=100, unique=True)
       value = models.TextField()
       description = models.TextField(blank=True)
       is_sensitive = models.BooleanField(default=False)
       updated_at = models.DateTimeField(auto_now=True)
       updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

Auditoría de cambios
--------------------

**Registro de modificaciones:**

Cada cambio en parámetros críticos debe registrarse:

- Fecha y hora del cambio.
- Usuario que realizó la modificación.
- Valor anterior y nuevo valor.
- Motivo del cambio (campo obligatorio para parámetros críticos).

**Ejemplo de log:**

.. code-block:: text

   2025-12-12 10:30:00 | admin_juan | SESSION_COOKIE_AGE
   Valor anterior: 7200 | Nuevo valor: 3600
   Motivo: Política de seguridad actualizada

Proceso de despliegue
---------------------

**Validación en staging:**

1. Aplicar cambios de parámetros en entorno staging.
2. Ejecutar suite de pruebas completa.
3. Verificar funcionamiento manual de áreas afectadas.
4. Documentar resultados de la validación.

**Despliegue en producción:**

1. Programar ventana de mantenimiento si es necesario.
2. Realizar backup de configuración actual.
3. Aplicar cambios.
4. Verificar logs y métricas post-despliegue.
5. Tener plan de rollback preparado.

**Changelog:**

Mantener historial de cambios en archivo centralizado:

.. code-block:: text

   # CHANGELOG_CONFIG.md
   
   ## 2025-12-12
   - SESSION_COOKIE_AGE: 7200 -> 3600
     Motivo: Mejora de seguridad
     Aprobado por: Director de TI

Buenas prácticas
----------------

- Nunca almacenar secretos en el código fuente.
- Usar variables de entorno para valores sensibles.
- Documentar cada parámetro con su propósito y valores válidos.
- Validar parámetros al iniciar la aplicación.
- Mantener valores diferentes por ambiente claramente identificados.
- Requerir aprobación para cambios en parámetros críticos.
