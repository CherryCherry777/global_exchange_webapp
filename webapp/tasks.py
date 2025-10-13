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
    Runs every minute. Checks config and decides if emails should be sent.
    """
    config = EmailScheduleConfig.objects.first()
    if not config:
        return

    now = timezone.localtime()

    should_send = False
    if config.frequency == "daily":
        should_send = now.hour == config.hour and now.minute == config.minute
    elif config.frequency == "weekly":
        # e.g., Monday at configured time
        should_send = now.weekday() == 0 and now.hour == config.hour and now.minute == config.minute
    elif config.frequency == "custom" and config.interval_minutes:
        should_send = now.minute % config.interval_minutes == 0

    if should_send:
        _send_to_all_users.delay()  # ✅ Run as background task


@shared_task
def _send_to_all_users():
    """
    Dispatches one subtask per user, staggered to avoid rate limits.
    """
    users = CustomUser.objects.filter(is_active=True, receive_exchange_emails=True).exclude(email="")
    for i, user in enumerate(users):
        # space out each email by 2 seconds
        send_exchange_rates_email.apply_async(args=[user.id], countdown=i * 2)


@shared_task
def send_exchange_rates_email(user_id):
    """
    Sends one email with exchange rates to a single user.
    """
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return

    # generate persistent unsubscribe token
    if not getattr(user, "unsubscribe_token", None):
        user.unsubscribe_token = secrets.token_urlsafe(32)
        user.save(update_fields=["unsubscribe_token"])

    uidb64 = urlsafe_base64_encode(force_bytes(user.id))
    unsubscribe_url = f"{settings.SITE_URL}/unsubscribe/{uidb64}/{user.unsubscribe_token}/"

    cliente_usuarios = (
        ClienteUsuario.objects.select_related("cliente__categoria").filter(usuario=user)
    )
    if not cliente_usuarios.exists():
        cliente_usuarios = [None]

    currencies = Currency.objects.filter(is_active=True).exclude(code="PYG")
    clientes_data = []

    for cu in cliente_usuarios:
        if cu:
            cliente = cu.cliente
            descuento = getattr(getattr(cliente, "categoria", None), "descuento", None) or Decimal("0")
        else:
            cliente = None
            descuento = Decimal("0")

        monedas_info = []
        for c in currencies:
            precio_compra = c.base_price - (c.comision_compra * (Decimal("1") - descuento))
            precio_venta = c.base_price + (c.comision_venta * (Decimal("1") - descuento))
            monedas_info.append({
                "name": c.name,
                "code": c.code,
                "precio_compra": f"{precio_compra:.2f}",
                "precio_venta": f"{precio_venta:.2f}",
            })

        clientes_data.append({
            "cliente": cliente,
            "descuento": f"{(descuento * 100):.0f}%" if descuento else "0%",
            "monedas": monedas_info,
        })

    context = {
        "user": user,
        "clientes_data": clientes_data,
        "unsubscribe_url": unsubscribe_url,
    }

    text_content = render_to_string("emails/exchange_rates.txt", context)
    html_content = render_to_string("emails/exchange_rates.html", context)

    subject = "Simulador - Tasas de cambio"
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@simulador.com")
    email = EmailMultiAlternatives(subject, text_content, from_email, [user.email])
    email.attach_alternative(html_content, "text/html")

    try:
        email.send(fail_silently=False)
    except Exception as e:
        print(f"Error sending email to {user.email}: {e}")

@shared_task
def send_welcome_email(user_email):
    send_mail(
        'Welcome!',
        'Thanks for signing up!',
        'from@example.com',
        [user_email],
        fail_silently=False,
    )