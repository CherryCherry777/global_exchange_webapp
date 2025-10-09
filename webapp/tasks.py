from decimal import Decimal
import secrets
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
        """
        Envía un correo con las tasas de cambio de todas las monedas activas.
        Incluye enlace de desuscripción persistente.
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