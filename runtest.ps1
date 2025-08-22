# Ejecuta tests y genera reporte de cobertura
coverage run manage.py test

# Muestra reporte en consola
coverage report -m

# Genera reporte HTML
coverage html

# Abrir el reporte HTML (opcional)
xdg-open htmlcov/index.html

