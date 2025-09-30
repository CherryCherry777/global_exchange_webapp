from django.core.mail import send_mail, EmailMultiAlternatives
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

def send_exchange_rates_email_debug(to_email, user_id):
    """
    Envía un correo con las tasas de cambio de todas las monedas activas.
    Funciona tanto en modo debug (ejecutado al login) como en producción (ejecutado con Celery).
    """
    # Traemos las monedas activas
    currencies = Currency.objects.filter(is_active=True)

    """
    # Aplicar fórmulas según descuento del cliente
        venta = base + (com_venta * (1 - descuento))
        compra = base - (com_compra * (1 - descuento))

    # Obtener usuarios asignados a este cliente
    usuarios_asignados = ClienteUsuario.objects.filter(cliente=cliente).select_related('usuario')
   
    """
    try:
        cliente_usuario = ClienteUsuario.objects.select_related("cliente__categoria").get(usuario_id=user_id)
        descuento = cliente_usuario.cliente.categoria.descuento
    except ClienteUsuario.DoesNotExist:
        descuento = 0

    # Datos para la plantilla
    rows = []
    for currency in currencies:
        code = (currency.code or "").strip().upper()
        if code == "PYG":
            continue  # saltamos PYG
        precio_venta = currency.base_price + (currency.comision_venta * (1 - descuento))
        precio_compra = currency.base_price - (currency.comision_compra * (1 - descuento))
        rows.append({
            "name": currency.name,
            "code": code,
            "compra": f"{precio_compra:.2f}",
            "venta": f"{precio_venta:.2f}",
        })

    context = {
        "rows": rows,
        "user_email": to_email,
        "project_name": "Global Exchange",
    }

    subject = "Tasas de cambio - Global Exchange"
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@simulador.com")

    text_body = render_to_string("emails/exchange_rates.txt", context)
    html_body = render_to_string("emails/exchange_rates.html", context)

    msg = EmailMultiAlternatives(subject, text_body, from_email, [to_email])
    msg.attach_alternative(html_body, "text/html")
    msg.send()