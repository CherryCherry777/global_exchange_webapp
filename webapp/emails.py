from decimal import Decimal
import secrets
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


def send_exchange_rates_email_debug(user):
    """
    Envía un correo con las tasas de cambio de todas las monedas activas.
    Incluye enlace de desuscripción persistente.
    """
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
    email.send(fail_silently=False)