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


def send_fallo_acreditacion_email(transaccion, error=None) -> None:
    """
    Envía correos de notificación cuando una acreditación falla.
    Usa plantillas ya existentes (.txt y .html) para el cuerpo.
    """

    project_name = getattr(settings, "PROJECT_NAME", "Global Exchange")
    soporte_email = getattr(settings, "SUPPORT_EMAIL", "soporte@globalexchange.com")
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)

    # Contexto común para las plantillas
    context = {
        "transaccion": transaccion,
        "project_name": project_name,
        "error": error,
    }

    # 1) Correo al usuario (si tiene email)
    usuario_email = getattr(transaccion.usuario, "email", None)
    if usuario_email:
        subject_usuario = "Error en la acreditación de la transacción"

        text_body_usuario = render_to_string(
            "emails/accreditation_failed_cliente.txt",
            context,
        )
        html_body_usuario = render_to_string(
            "emails/accreditation_failed_cliente.html",
            context,
        )

        send_mail(
            subject=subject_usuario,
            message=text_body_usuario,
            from_email=from_email,
            recipient_list=[usuario_email],
            html_message=html_body_usuario,
            fail_silently=True,
        )

    # 2) Correo al soporte (si tenés templates separados, mejor)
    subject_admin = f"⚠️ Error en la acreditación de la transacción #{transaccion.id}"

    text_body_admin = render_to_string(
        "emails/accreditation_failed_asistencia.txt",
        context,
    )
    html_body_admin = render_to_string(
        "emails/accreditation_failed_asistencia.html",
        context,
    )

    send_mail(
        subject=subject_admin,
        message=text_body_admin,
        from_email=from_email,
        recipient_list=[soporte_email],
        html_message=html_body_admin,
        fail_silently=True,
    )