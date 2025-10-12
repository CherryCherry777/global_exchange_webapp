from .constants import *
from django.shortcuts import render, redirect
from django.contrib import messages
from ..forms import TarjetaForm, BilleteraForm, CuentaBancariaForm, MedioPagoForm
from ..decorators import role_required
from ..models import Cliente, MedioPago, TarjetaNacional, Billetera

# -----------------------
# Dashboards
# -----------------------
@role_required("Administrador")
def admin_dash(request):
    return render(request, "webapp/vistas_varias/admin_dashboard.html")

@role_required("Empleado")
def employee_dash(request):
    return render(request, "webapp/vistas_varias/employee_dashboard.html")
