from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib.auth import logout, login
from django.contrib import messages
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import LoginView
from django.views import View
from web_project import settings
from web_project.settings import MFA_LOGIN
from webapp.emails import send_activation_email, send_exchange_rates_email_debug, send_mfa_login_email
from webapp.tasks import send_exchange_rates_email
from ..forms import RegistrationForm, LoginForm
from .constants import *

class CustomLoginView(LoginView):
    template_name = "webapp/auth/login.html"
    form_class = LoginForm

    def form_valid(self, form):
        """
        En vez de loguear directamente al usuario,
        enviamos el código MFA y redirigimos.
        """
        user = form.get_user()
        if user and user.is_active:
            if getattr(settings, "MFA_LOGIN", True):
                send_mfa_login_email(self.request, user)
                self.request.session["mfa_user_id"] = user.id
                return redirect("mfa_verify")
            else:
                #login directo
                if settings.DEBUG and settings.CORREO_TASAS_LOGIN and user.receive_exchange_emails:
                    send_exchange_rates_email_debug(user)  # envia un correo de prueba con las tasas actuales
                login(self.request, user, backend="django.contrib.auth.backends.ModelBackend")
                return redirect(self.get_success_url())
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy("public_home")
    
    def form_invalid(self, form):
        # Agregar mensaje específico para cuentas inactivas
        if form.errors.get('__all__'):
            for error in form.errors['__all__']:
                if 'inactive' in str(error):
                    messages.error(self.request, str(error))
                    break
        return super().form_invalid(form)
    
User = get_user_model()

class MFAVerifyView(View):
    template_name = "webapp/auth/mfa_verify.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        input_code = request.POST.get("code")
        session_code = request.session.get("mfa_code")
        user_id = request.session.get("mfa_user_id")

        if input_code and session_code and input_code == session_code:
            try:
                user = User.objects.get(pk=user_id)

                # ✅ aquí hacemos login "oficial"
                login(request, user, backend="django.contrib.auth.backends.ModelBackend")

                # limpiar la sesión
                request.session.pop("mfa_code", None)
                request.session.pop("mfa_user_id", None)

                return redirect("public_home")
            except User.DoesNotExist:
                messages.error(request, "Error: usuario no encontrado")
        else:
            messages.error(request, "Código incorrecto o expirado")

        return render(request, self.template_name)
    

def custom_logout(request):
    logout(request)
    return redirect("public_home")

def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            # enviar correo real a Mailtrap
            send_activation_email(request, user)

            messages.success(
                request, "Registro Exitoso! Por favor presione su link de verificacion."
            )
            return redirect("login")
        else:
            # Print form errors if invalid
            print("Form errors:", form.errors)
    else:
        form = RegistrationForm()

    return render(request, "webapp/auth/register.html", {"form": form})

def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Email verificado! Ahora puede hacer login.")
        return redirect("login")
    else:
        messages.error(request, "Link de verificacion expirado o invalido.")
        return redirect("register")

def resend_verification_email(request):
    if request.method == "POST":
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            if not user.is_active:
                send_activation_email(request, user)
                messages.success(request, "Email de verificación reenviado. Por favor revise su correo.")
            else:
                messages.info(request, "Su cuenta ya está activa. Puede hacer login.")
        except User.DoesNotExist:
            messages.error(request, "No se encontró una cuenta con este correo electrónico.")
        return redirect("login")
    
    return render(request, "webapp/auth/resend_verification.html")