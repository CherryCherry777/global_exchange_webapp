from django.contrib.auth import authenticate
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from webapp.models import Transaccion, Tauser
from django.db.models import Q


User = get_user_model()

def tauser_login(request):
    """
    Login independiente para el entorno Tauser.
    Permite autenticarse con las credenciales del CustomUser principal,
    seleccionar la sucursal (ubicación) y guardar esa información en sesión.
    No inicia sesión estándar de Django.
    """
    # 🔹 Obtenemos todas las sucursales registradas (sin duplicados)
    ubicaciones = Tauser.objects.values_list("ubicacion", flat=True).distinct()

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        ubicacion = request.POST.get("ubicacion")

        # Autenticación simple sin iniciar sesión Django
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Guardamos solo variables de sesión personalizadas
            request.session["tauser_authenticated"] = True
            request.session["tauser_user_id"] = user.id
            request.session["tauser_username"] = user.username
            request.session["tauser_ubicacion"] = ubicacion

            messages.success(
                request,
                f"Sesión Tauser iniciada correctamente en la sucursal: {ubicacion}."
            )
            return redirect("tauser_home")
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")

    # 🔹 Renderiza el template con las ubicaciones disponibles
    return render(
        request,
        "webapp/tauser/tauser_login.html",
        {"ubicaciones": ubicaciones},
    )


def tauser_home(request):
    """
    Lista las transacciones vinculadas a Tausers de la ubicación seleccionada.
    Solo incluye las que no están completas, anuladas, canceladas ni con AC fallida.
    """
    ubicacion = request.session.get("tauser_ubicacion")

    if not ubicacion:
        messages.warning(request, "Debe seleccionar una ubicación para continuar.")
        return redirect("tauser_login")

    # Tipo de contenido para Tauser
    ct_tauser = ContentType.objects.get_for_model(Tauser)

    # IDs de Tausers que pertenecen a esa ubicación
    tausers_ids = list(Tauser.objects.filter(ubicacion=ubicacion).values_list("id", flat=True))

    # Si no hay Tausers registrados en esa sucursal
    if not tausers_ids:
        messages.info(request, f"No hay Tausers registrados en la ubicación {ubicacion}.")
        return render(request, "webapp/tauser/tauser_home.html", {
            "transacciones": [],
            "ubicacion": ubicacion,
        })

    # Filtrar las transacciones con Tauser en medio_pago o medio_cobro
    transacciones = (
        Transaccion.objects.select_related(
            "cliente", "usuario", "moneda_origen", "moneda_destino"
        )
        .filter(
            (
                Q(medio_pago_type=ct_tauser, medio_pago_id__in=tausers_ids)
                | Q(medio_cobro_type=ct_tauser, medio_cobro_id__in=tausers_ids)
            ),
            ~Q(
                estado__in=[
                    Transaccion.Estado.COMPLETA,
                    Transaccion.Estado.ANULADA,
                    Transaccion.Estado.CANCELADA,
                    Transaccion.Estado.AC_FALLIDA,
                ]
            ),
        )
        .order_by("-fecha_creacion")
    )

    # Añadir banderas para el template
    for t in transacciones:
        t.es_pago_tauser = t.medio_pago_type == ct_tauser and t.medio_pago_id in tausers_ids
        t.es_cobro_tauser = t.medio_cobro_type == ct_tauser and t.medio_cobro_id in tausers_ids

    return render(request, "webapp/tauser/tauser_home.html", {
        "transacciones": transacciones,
        "ubicacion": ubicacion,
    })


def tauser_pagar(request, pk):
    """
    Simula un pago desde el cliente hacia el sistema (Tauser como medio de pago).
    Redirige amablemente si la transacción no existe o no es válida.
    """
    try:
        transaccion = Transaccion.objects.get(pk=pk)
    except Transaccion.DoesNotExist:
        messages.error(request, "La transacción no existe o ya fue eliminada.")
        return redirect(request.META.get("HTTP_REFERER", reverse("tauser_home")))

    # Validar que pueda pagarse (estado pendiente)
    if transaccion.estado != Transaccion.Estado.PENDIENTE:
        messages.warning(request, "Esta transacción ya fue procesada o no puede pagarse.")
        return redirect("tauser_home")

    if request.method == "POST":
        accion = request.POST.get("accion")
        if accion == "confirmar":
            # Actualiza estado y fecha de actualización
            transaccion.estado = Transaccion.Estado.PAGADA
            transaccion.save(update_fields=["estado", "fecha_actualizacion"])
            messages.success(request, f"Transacción #{pk} marcada como PAGADA con éxito.")
            return redirect("tauser_home")
        elif accion == "cancelar":
            messages.info(request, "Operación cancelada.")
            return redirect("tauser_home")

    return render(request, "webapp/tauser/tauser_simulador.html", {
        "transaccion": transaccion,
        "modo": "pagar"
    })


def tauser_cobrar(request, pk):
    """
    Simula un cobro desde el sistema hacia el cliente (Tauser como medio de cobro).
    Redirige amablemente si no se encuentra la transacción.
    """
    try:
        transaccion = Transaccion.objects.get(pk=pk)
    except Transaccion.DoesNotExist:
        messages.error(request, "La transacción no existe o ya fue eliminada.")
        return redirect(request.META.get("HTTP_REFERER", reverse("tauser_home")))

    # Validar que pueda cobrarse (estado pagada)
    if transaccion.estado != Transaccion.Estado.PAGADA:
        messages.warning(request, "Esta transacción aún no puede cobrarse.")
        return redirect("tauser_home")

    if request.method == "POST":
        accion = request.POST.get("accion")
        if accion == "confirmar":
            transaccion.estado = Transaccion.Estado.COMPLETA
            transaccion.save(update_fields=["estado", "fecha_actualizacion"])
            messages.success(request, f"Transacción #{pk} completada con éxito.")
            return redirect("tauser_home")
        elif accion == "cancelar":
            messages.info(request, "Operación cancelada.")
            return redirect("tauser_home")

    return render(request, "webapp/tauser/tauser_simulador.html", {
        "transaccion": transaccion,
        "modo": "cobrar"
    })
