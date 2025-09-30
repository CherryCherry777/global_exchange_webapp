from decimal import Decimal
from celery import shared_task
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string

from .models import Currency, ClienteUsuario, CustomUser, EmailScheduleConfig

from django.utils import timezone

from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

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
    for user in User.objects.filter(is_active=True,receive_exchange_emails=True).exclude(email=""):
        send_exchange_rates_email(user.email, user.id)

def send_exchange_rates_email():
    currencies_db = Currency.objects.filter(is_active=True)
    users = CustomUser.objects.filter(receive_exchange_emails=True)

    for user in users:
        # Descuento del cliente relacionado
        try:
            cliente_usuario = ClienteUsuario.objects.select_related("cliente__categoria").get(usuario=user)
            descuento = cliente_usuario.cliente.categoria.descuento
        except ClienteUsuario.DoesNotExist:
            descuento = Decimal("0")

        # Preparar lista de monedas con precios
        currencies = []
        for c in currencies_db:
            if c.code != "PYG":
                currencies.append({
                    "name": c.name,
                    "code": c.code,
                    "precio_compra": f"{(c.base_price - c.comision_compra*(1-descuento)):.2f}",
                    "precio_venta": f"{(c.base_price + c.comision_venta*(1-descuento)):.2f}"
                })

        # URL de desuscripción
        uidb64 = urlsafe_base64_encode(force_bytes(user.id))
        unsubscribe_url = f"{settings.SITE_URL}/unsubscribe/{uidb64}/token/"

        # Renderizar templates
        text_content = render_to_string("emails/exchange_rates.txt", {"currencies": currencies, "unsubscribe_url": unsubscribe_url})
        html_content = render_to_string("emails/exchange_rates.html", {"currencies": currencies, "unsubscribe_url": unsubscribe_url})

        # Enviar email
        subject = "Simulador - Tasas de cambio"
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@simulador.com")
        email_message = EmailMultiAlternatives(subject, text_content, from_email, [user.email])
        email_message.attach_alternative(html_content, "text/html")
        email_message.send(fail_silently=False)
