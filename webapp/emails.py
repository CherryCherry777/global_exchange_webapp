from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
import random

from web_project import settings
from webapp.models import Currency

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

def send_exchange_rates_email(to_email):
    """
    Envía un correo con las tasas de cambio de todas las monedas activas.
    Funciona tanto en modo debug (ejecutado al login) como en producción (ejecutado con Celery).
    """
    # Traemos las monedas activas
    currencies = Currency.objects.filter(is_active=True)

    # Construimos el mensaje
    lines = ["Tasas de cambio actuales:\n"]
    for currency in currencies:
        lines.append(f"- {currency.name}: {currency.exchange_rate}")

    message = "\n".join(lines)

    # Asunto configurable
    subject = "Simulador - Tasas de cambio"

    # Dirección de envío (usa settings.DEFAULT_FROM_EMAIL)
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@simulador.com")

    # Enviamos correo
    send_mail(
        subject,
        message,
        from_email,
        [to_email],
        fail_silently=False,
    )