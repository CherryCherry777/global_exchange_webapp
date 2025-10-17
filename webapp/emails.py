from decimal import Decimal
import secrets
import time
from django.core.mail import send_mail, EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
import random

from web_project import settings
from webapp.models import Currency, ClienteUsuario

def send_activation_email(request, user):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    activation_url = request.build_absolute_uri(
        reverse("verify-email", kwargs={"uidb64": uid, "token": token})
    )

    context = {
        "user": user,
        "activation_link": activation_url,
        "project_name": "Global Exchange",
    }

    subject = "Confirma tu correo para activar tu cuenta"
    text_body = render_to_string("emails/activation.txt", context)
    html_body = render_to_string("emails/activation.html", context)

    # Usa DEFAULT_FROM_EMAIL ya definido en settings
    send_mail(
        subject=subject,
        message=text_body,
        from_email=None,
        recipient_list=[user.email],
        html_message=html_body,
    )

def send_mfa_login_email(request, user):
    code = f"{random.randint(100000,999999)}"
    request.session["mfa_code"] = code
    request.session["mfa_user_id"] = user.id

    context = {
        "user": user,
        "project_name": "Global Exchange",
        "code" : code
    }

    subject = "Código de verificación MFA - Global Exchange"
    text_body = render_to_string("emails/mfa_login.txt", context)
    html_body = render_to_string("emails/mfa_login.html", context)

    # Usa DEFAULT_FROM_EMAIL ya definido en settings
    send_mail(
        subject=subject,
        message=text_body,
        from_email=None,
        recipient_list=[user.email],
        html_message=html_body,
    )

"""
def send_exchange_rates_email_debug(user):

    #Envía un correo con las tasas de cambio de todas las monedas activas.
    #Incluye enlace de desuscripción persistente.



    # Obtener descuento del cliente relacionado
    try:
        cliente_usuario = ClienteUsuario.objects.select_related("cliente__categoria").get(usuario=user)
        descuento = cliente_usuario.cliente.categoria.descuento
    except ClienteUsuario.DoesNotExist:
        descuento = Decimal("0")

    # Preparar lista de monedas (excluyendo PYG)
    currencies = []
    for c in Currency.objects.filter(is_active=True).exclude(code="PYG"):
        precio_compra = c.base_price - c.comision_compra * (1 - descuento)
        precio_venta = c.base_price + c.comision_venta * (1 - descuento)
        currencies.append({
            "name": c.name,
            "code": c.code,
            "precio_compra": f"{precio_compra:.2f}",
            "precio_venta": f"{precio_venta:.2f}"
        })

    # Generar token persistente para desuscripción
    if not user.unsubscribe_token:
        user.unsubscribe_token = secrets.token_urlsafe(32)
        user.save()

    uidb64 = urlsafe_base64_encode(force_bytes(user.id))
    unsubscribe_url = f"{settings.SITE_URL}/unsubscribe/{uidb64}/{user.unsubscribe_token}/"

    # Renderizar plantillas
    context = {"currencies": currencies, "unsubscribe_url": unsubscribe_url}
    text_content = render_to_string("emails/exchange_rates.txt", context)
    html_content = render_to_string("emails/exchange_rates.html", context)

    # Enviar email
    subject = "Simulador - Tasas de cambio"
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@simulador.com")
    email = EmailMultiAlternatives(subject, text_content, from_email, [user.email])
    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=False)"""

"""def send_exchange_rates_email_debug(user):
    
    #Envía un correo con las tasas de cambio para cada ClienteUsuario asociado al `user`.
    #Si el usuario no tiene clientes, envía un único correo con descuento 0.
    
    connection = get_connection()
    connection.open()

    # Generar token persistente si no existe (solo una vez)
    if not getattr(user, "unsubscribe_token", None):
        user.unsubscribe_token = secrets.token_urlsafe(32)
        user.save(update_fields=["unsubscribe_token"])

    uidb64 = urlsafe_base64_encode(force_bytes(user.id))
    unsubscribe_url = f"{settings.SITE_URL}/unsubscribe/{uidb64}/{user.unsubscribe_token}/"

    # Traer todos los ClienteUsuario asociados (cada uno tiene su cliente y categoría)
    cliente_usuarios = ClienteUsuario.objects.select_related("cliente__categoria").filter(usuario=user)

    # Query de monedas (una sola vez, luego lo usamos por cliente)
    currency_qs = Currency.objects.filter(is_active=True).exclude(code="PYG")

    # Si no hay clientes asociados, enviamos una vez con descuento 0
    if not cliente_usuarios.exists():
        cliente_iterable = [None]  # un único envío con cliente=None y descuento 0
    else:
        cliente_iterable = list(cliente_usuarios)

    for cu in cliente_iterable:
        # obtener descuento (si no hay cliente -> 0)
        if cu is None:
            descuento = Decimal("0")
            cliente = None
        else:
            # Manejo defensivo por si la categoría o su descuento son None
            cliente = cu.cliente
            descuento = getattr(getattr(cliente, "categoria", None), "descuento", None) or Decimal("0")

        # Preparar lista de monedas con el descuento correspondiente
        currencies = []
        for c in currency_qs:
            precio_compra = c.base_price - (c.comision_compra * (Decimal("1") - descuento))
            precio_venta  = c.base_price + (c.comision_venta * (Decimal("1") - descuento))
            currencies.append({
                "name": c.name,
                "code": c.code,
                "precio_compra": f"{precio_compra:.2f}",
                "precio_venta":  f"{precio_venta:.2f}"
            })

        # Renderizar y enviar
        context = {
            "currencies": currencies,
            "unsubscribe_url": unsubscribe_url,
            "cliente": cliente,
        }
        text_content = render_to_string("emails/exchange_rates.txt", context)
        html_content = render_to_string("emails/exchange_rates.html", context)

        subject = "Simulador - Tasas de cambio" + (f" - {cliente}" if cliente else "")
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@simulador.com")
        email = EmailMultiAlternatives(subject, text_content, from_email, [user.email])
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        time.sleep(1)

    connection.close()"""

def send_exchange_rates_email_debug(user):
    """
    Envía un solo correo al usuario con las tasas de cambio
    de todas las monedas activas, agrupadas por cada cliente
    asociado al usuario.
    """

    # Generar token persistente si no existe
    if not getattr(user, "unsubscribe_token", None):
        user.unsubscribe_token = secrets.token_urlsafe(32)
        user.save(update_fields=["unsubscribe_token"])

    uidb64 = urlsafe_base64_encode(force_bytes(user.id))
    unsubscribe_url = f"{settings.SITE_URL}/unsubscribe/{uidb64}/{user.unsubscribe_token}/"

    # Obtener todos los ClienteUsuario relacionados con el usuario
    cliente_usuarios = (
        ClienteUsuario.objects.select_related("cliente__categoria")
        .filter(usuario=user)
    )

    # Si no hay clientes, se usa un descuento 0
    if not cliente_usuarios.exists():
        cliente_usuarios = [None]

    # Monedas activas
    currencies = Currency.objects.filter(is_active=True).exclude(code="PYG")

    # Preparar datos consolidados
    clientes_data = []

    for cu in cliente_usuarios:
        if cu:
            cliente = cu.cliente
            descuento = getattr(getattr(cliente, "categoria", None), "descuento", None) or Decimal("0")
        else:
            cliente = None
            descuento = Decimal("0")

        # Calcular precios con descuento por moneda
        monedas_info = []
        for c in currencies:
            precio_compra = c.base_price - (c.comision_compra * (Decimal("1") - descuento))
            precio_venta  = c.base_price + (c.comision_venta * (Decimal("1") - descuento))
            monedas_info.append({
                "name": c.name,
                "code": c.code,
                "precio_compra": f"{precio_compra:.2f}",
                "precio_venta":  f"{precio_venta:.2f}",
            })

        clientes_data.append({
            "cliente": cliente,
            "descuento": f"{(descuento * 100):.0f}%" if descuento else "0%",
            "monedas": monedas_info,
        })

    # Contexto del email
    context = {
        "user": user,
        "clientes_data": clientes_data,
        "unsubscribe_url": unsubscribe_url,
    }

    # Renderizar contenido
    text_content = render_to_string("emails/exchange_rates.txt", context)
    html_content = render_to_string("emails/exchange_rates.html", context)

    # Enviar email único
    subject = "Simulador - Tasas de cambio"
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@simulador.com")
    email = EmailMultiAlternatives(subject, text_content, from_email, [user.email])
    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=False)