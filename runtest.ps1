# Ejecuta tests y genera reporte de cobertura
coverage run manage.py test
coverage report -m
coverage html
Write-Host "Reporte HTML generado en htmlcov\index.html"
