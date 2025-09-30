from celery import shared_task
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string

from .models import Currency, ClienteUsuario, EmailScheduleConfig

from django.utils import timezone
from .tasks import send_exchange_rates_email

@shared_task
def check_and_send_exchange_rates():
    """
    Se ejecuta cada minuto. Verifica la configuración guardada y decide si mandar correo.
    """
    try:
        config = EmailScheduleConfig.objects.first()
    except EmailScheduleConfig.DoesNotExist:
        return  # si no hay config, no hace nada

    now = timezone.localtime()

    # Caso diario
    if config.frequency == "daily" and now.hour == config.hour and now.minute == config.minute:
        _send_to_all_users()

    # Caso semanal (ej: domingo a las 8:00)
    elif config.frequency == "weekly" and now.weekday() == 0 and now.hour == config.hour and now.minute == config.minute:
        _send_to_all_users()

    # Caso personalizado
    elif config.frequency == "custom" and config.interval_minutes:
        if now.minute % config.interval_minutes == 0:
            _send_to_all_users()


def _send_to_all_users():
    from django.contrib.auth import get_user_model
    User = get_user_model()
    for user in User.objects.filter(is_active=True).exclude(email=""):
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
