from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
import random

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