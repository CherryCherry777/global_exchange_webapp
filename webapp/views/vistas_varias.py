from .constants import *
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from ..decorators import role_required

# -----------------------
# Dashboards
# -----------------------
@role_required("Administrador")
def admin_dash(request):
    return render(request, "webapp/vistas_varias/admin_dashboard.html")

@role_required("Empleado")
def employee_dash(request):
    return render(request, "webapp/vistas_varias/employee_dashboard.html")

@login_required
@permission_required('webapp.access_analyst_panel', raise_exception=True)
def analyst_dash(request):
    # Usamos la misma landing; el template decide qué panel mostrar por permisos
    return redirect('landing')
