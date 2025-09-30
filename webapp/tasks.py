from celery import shared_task
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string

from .models import Currency, ClienteUsuario


@shared_task
def send_daily_exchange_rates():
    """
    Envía las tasas de cambio a todos los usuarios activos.
    Se ejecuta automáticamente cada día a las 8:00 AM (configurado en Celery Beat).
    """
    User = get_user_model()
    users = User.objects.filter(is_active=True).exclude(email="")

    for user in users:
        send_exchange_rates_email(user.email, user.id)


def send_exchange_rates_email(to_email, user_id):
    """
    Construye y envía un correo HTML con las tasas de cambio.
    """
    currencies = Currency.objects.filter(is_active=True)

    # Obtener descuento del cliente (si corresponde)
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
