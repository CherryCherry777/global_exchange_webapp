# Comandos de Testing para Global Exchange

## Tests Individuales (Nuevos)

```powershell
# Test de configuración de schedules/temporizadores
python manage.py test webapp.tests.test_schedule_config -v 2

# Test de vistas del landing y administración
python manage.py test webapp.tests.test_landing_views -v 2

# Test de límites de intercambio
python manage.py test webapp.tests.test_limits -v 2

# Test de métodos de pago
python manage.py test webapp.tests.test_payment_methods -v 2

# Test de entidades del sistema
python manage.py test webapp.tests.test_entities -v 2

# Test de categorías y roles
python manage.py test webapp.tests.test_categories -v 2

# Test de configuración de monedas
python manage.py test webapp.tests.test_currency_config -v 2

# Test de utilidades del sistema
python manage.py test webapp.tests.test_system_utils -v 2

# Test de modelos de transacciones
python manage.py test webapp.tests.test_transaction_models -v 2

# Test de vistas de historial
python manage.py test webapp.tests.test_history_views -v 2
```

## Tests por Grupos

```powershell
# Ejecutar TODOS los nuevos tests
python manage.py test webapp.tests -v 2

# Ejecutar solo tests de la app webapp
python manage.py test webapp -v 2

# Ejecutar tests con coverage
python manage.py test webapp.tests --verbosity=2
```

## Tests con Coverage (Cobertura)

```powershell
# Generar reporte de cobertura
coverage run --source='.' manage.py test webapp.tests
coverage report
coverage html
```

## Debugging Tests

```powershell
# Ejecutar un test específico con máximo detalle
python manage.py test webapp.tests.test_schedule_config.ScheduleConfigTest.test_email_schedule_config_model -v 3

# Ejecutar tests pero parar en el primer fallo
python manage.py test webapp.tests --failfast -v 2

# Ejecutar tests manteniendo la base de datos de test
python manage.py test webapp.tests --keepdb -v 2
```

## Verificación Rápida

```powershell
# Solo verificar que los tests se pueden cargar (sin ejecutar)
python manage.py test --help

# Verificar sintaxis de todos los archivos de test
python -m py_compile webapp/tests/*.py
```