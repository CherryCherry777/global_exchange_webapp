from .constants import *
from django.shortcuts import render, redirect
from django.contrib import messages
from ..forms import TarjetaForm, BilleteraForm, CuentaBancariaForm, MedioPagoForm
from ..decorators import role_required
from ..models import Cliente, MedioPago, Tarjeta, Billetera, CuentaBancaria

# ===========================================
# VISTAS PARA MEDIOS DE PAGO (DEPRECADO)
# ===========================================

@role_required("Administrador")
def manage_client_payment_methods_deprecado(request):
    #Vista para gestionar los medios de pago de los clientes
    # GET - Listar clientes con opción de gestionar medios de pago
    clientes = Cliente.objects.filter(estado=True).order_by('nombre')
    
    return render(request, "webapp/manage_client_payment_methods.html", {
        "clientes": clientes
    })


@role_required("Administrador")
def manage_client_payment_methods_detail_deprecado(request, cliente_id):
    #Vista para gestionar los medios de pago de un cliente específico
    try:
        cliente = Cliente.objects.get(id=cliente_id)
        
        if request.method == "POST":
            action = request.POST.get("action")
            
            if action == "toggle":
                medio_pago_id = request.POST.get("medio_pago_id")
                try:
                    medio_pago = MedioPago.objects.get(id=medio_pago_id, cliente=cliente)
                    medio_pago.activo = not medio_pago.activo
                    medio_pago.save()
                    status = "activado" if medio_pago.activo else "desactivado"
                    messages.success(request, f"Medio de pago '{medio_pago.nombre}' {status}")
                except MedioPago.DoesNotExist:
                    messages.error(request, "Medio de pago no encontrado")
            
            elif action == "delete":
                medio_pago_id = request.POST.get("medio_pago_id")
                try:
                    medio_pago = MedioPago.objects.get(id=medio_pago_id, cliente=cliente)
                    nombre_medio = medio_pago.nombre
                    medio_pago.delete()
                    messages.success(request, f"Medio de pago '{nombre_medio}' eliminado")
                except MedioPago.DoesNotExist:
                    messages.error(request, "Medio de pago no encontrado")
            
            return redirect("manage_client_payment_methods_detail", cliente_id=cliente_id)
        
        # GET - Mostrar tipos de medios de pago disponibles y su estado para el cliente
        tipos_disponibles = MedioPago.TIPO_CHOICES
        medios_pago_existentes = MedioPago.objects.filter(cliente=cliente)
        
        # Crear lista de tipos con su estado
        tipos_con_estado = []
        for tipo_codigo, tipo_nombre in tipos_disponibles:
            # Buscar si el cliente tiene medios de pago de este tipo
            medios_del_tipo = medios_pago_existentes.filter(tipo=tipo_codigo)
            
            tipo_info = {
                'codigo': tipo_codigo,
                'nombre': tipo_nombre,
                'tiene_medios': medios_del_tipo.exists(),
                'medios': list(medios_del_tipo),
                'cantidad': medios_del_tipo.count()
            }
            tipos_con_estado.append(tipo_info)
        
        return render(request, "webapp/manage_client_payment_methods_detail.html", {
            "cliente": cliente,
            "tipos_con_estado": tipos_con_estado
        })
        
    except Cliente.DoesNotExist:
        messages.error(request, "Cliente no encontrado")
        return redirect("manage_client_payment_methods")


@role_required("Administrador")
def view_client_payment_methods_deprecado(request, cliente_id):
    """Vista para ver los medios de pago de un cliente específico"""
    try:
        cliente = Cliente.objects.get(id=cliente_id)
        medios_pago = MedioPago.objects.filter(cliente=cliente).order_by('tipo', 'nombre')
        
        return render(request, "webapp/view_client_payment_methods.html", {
            "cliente": cliente,
            "medios_pago": medios_pago
        })
    except Cliente.DoesNotExist:
        messages.error(request, "Cliente no encontrado")
        return redirect("manage_client_payment_methods")
 
@role_required("Administrador")
def add_payment_method_deprecado(request, cliente_id, tipo):
    """Vista para agregar un nuevo medio de pago"""
    try:
        cliente = Cliente.objects.get(id=cliente_id)
        
        if request.method == "POST":
            # Crear el medio de pago base
            medio_pago_form = MedioPagoForm(request.POST)
            
            if medio_pago_form.is_valid():
                medio_pago = medio_pago_form.save(commit=False)
                medio_pago.cliente = cliente
                medio_pago.tipo = tipo
                medio_pago.save()
                
                # Crear el medio de pago específico según el tipo
                if tipo == 'tarjeta':
                    form = TarjetaForm(request.POST)
                elif tipo == 'billetera':
                    form = BilleteraForm(request.POST)
                elif tipo == 'cuenta_bancaria':
                    form = CuentaBancariaForm(request.POST)
                else:
                    messages.error(request, "Tipo de medio de pago no válido")
                    return redirect("manage_client_payment_methods_detail", cliente_id=cliente_id)
                
                if form.is_valid():
                    medio_especifico = form.save(commit=False)
                    medio_especifico.medio_pago = medio_pago
                    medio_especifico.save()
                    
                    messages.success(request, f"Medio de pago '{medio_pago.nombre}' agregado exitosamente")
                    return redirect("manage_client_payment_methods_detail", cliente_id=cliente_id)
                else:
                    # Si el formulario específico no es válido, eliminar el medio de pago base
                    medio_pago.delete()
            else:
                form = None
        else:
            # GET - Mostrar formularios vacíos
            medio_pago_form = MedioPagoForm()
            if tipo == 'tarjeta':
                form = TarjetaForm()
            elif tipo == 'billetera':
                form = BilleteraForm()
            elif tipo == 'cuenta_bancaria':
                form = CuentaBancariaForm()
            else:
                messages.error(request, "Tipo de medio de pago no válido")
                return redirect("manage_client_payment_methods_detail", cliente_id=cliente_id)
        
        return render(request, f"webapp/add_payment_method_{tipo}.html", {
            "cliente": cliente,
            "tipo": tipo,
            "medio_pago_form": medio_pago_form,
            "form": form
        })
        
    except Cliente.DoesNotExist:
        messages.error(request, "Cliente no encontrado")
        return redirect("manage_client_payment_methods")


@role_required("Administrador")
def edit_payment_method_deprecado(request, cliente_id, medio_pago_id):
    """Vista para editar un medio de pago existente"""
    try:
        cliente = Cliente.objects.get(id=cliente_id)
        medio_pago = MedioPago.objects.get(id=medio_pago_id, cliente=cliente)
        
        if request.method == "POST":
            # Actualizar el medio de pago base
            medio_pago_form = MedioPagoForm(request.POST, instance=medio_pago)
            
            if medio_pago_form.is_valid():
                medio_pago_form.save()
                
                # Actualizar el medio de pago específico
                if medio_pago.tipo == 'tarjeta':
                    try:
                        medio_especifico = medio_pago.tarjeta
                        form = TarjetaForm(request.POST, instance=medio_especifico)
                    except Tarjeta.DoesNotExist:
                        form = TarjetaForm(request.POST)
                        medio_especifico = None
                elif medio_pago.tipo == 'billetera':
                    try:
                        medio_especifico = medio_pago.billetera
                        form = BilleteraForm(request.POST, instance=medio_especifico)
                    except Billetera.DoesNotExist:
                        form = BilleteraForm(request.POST)
                        medio_especifico = None
                elif medio_pago.tipo == 'cuenta_bancaria':
                    try:
                        medio_especifico = medio_pago.cuenta_bancaria
                        form = CuentaBancariaForm(request.POST, instance=medio_especifico)
                    except CuentaBancaria.DoesNotExist:
                        form = CuentaBancariaForm(request.POST)
                        medio_especifico = None
                else:
                    messages.error(request, "Tipo de medio de pago no válido")
                    return redirect("manage_client_payment_methods_detail", cliente_id=cliente_id)
                
                if form.is_valid():
                    if medio_especifico:
                        form.save()
                    else:
                        medio_especifico = form.save(commit=False)
                        medio_especifico.medio_pago = medio_pago
                        medio_especifico.save()
                    
                    messages.success(request, f"Medio de pago '{medio_pago.nombre}' actualizado exitosamente")
                    return redirect("manage_client_payment_methods_detail", cliente_id=cliente_id)
            else:
                form = None
        else:
            # GET - Mostrar formularios con datos existentes
            medio_pago_form = MedioPagoForm(instance=medio_pago)
            
            if medio_pago.tipo == 'tarjeta':
                try:
                    medio_especifico = medio_pago.tarjeta
                    form = TarjetaForm(instance=medio_especifico)
                except Tarjeta.DoesNotExist:
                    form = TarjetaForm()
            elif medio_pago.tipo == 'billetera':
                try:
                    medio_especifico = medio_pago.billetera
                    form = BilleteraForm(instance=medio_especifico)
                except Billetera.DoesNotExist:
                    form = BilleteraForm()
            elif medio_pago.tipo == 'cuenta_bancaria':
                try:
                    medio_especifico = medio_pago.cuenta_bancaria
                    form = CuentaBancariaForm(instance=medio_especifico)
                except CuentaBancaria.DoesNotExist:
                    form = CuentaBancariaForm()
            else:
                messages.error(request, "Tipo de medio de pago no válido")
                return redirect("manage_client_payment_methods_detail", cliente_id=cliente_id)
        
        return render(request, f"webapp/edit_payment_method_{medio_pago.tipo}.html", {
            "cliente": cliente,
            "medio_pago": medio_pago,
            "medio_pago_form": medio_pago_form,
            "form": form
        })
        
    except (Cliente.DoesNotExist, MedioPago.DoesNotExist):
        messages.error(request, "Cliente o medio de pago no encontrado")
        return redirect("manage_client_payment_methods")


# -----------------------
# Dashboards
# -----------------------
@role_required("Administrador")
def admin_dash(request):
    return render(request, "webapp/admin_dashboard.html")

@role_required("Empleado")
def employee_dash(request):
    return render(request, "webapp/employee_dashboard.html")
