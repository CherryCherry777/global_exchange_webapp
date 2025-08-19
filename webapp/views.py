from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth import login, logout
from django.contrib import messages
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from .forms import UserUpdateForm

from .forms import RegistrationForm, LoginForm

User = get_user_model()

# Registration
def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Require email verification
            user.save()

            # Send verification email (simulated)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            domain = get_current_site(request).domain
            link = request.build_absolute_uri(
                reverse("verify-email", kwargs={"uidb64": uid, "token": token})
            )
            send_mail(
                "Verify your account",
                f"Click this link to verify your account: {link}",
                "noreply@example.com",
                [user.email],
            )
            messages.success(request, "Registration successful! Check console email for verification link.")
            return redirect("login")
    else:
        form = RegistrationForm()
    return render(request, "webapp/register.html", {"form": form})


# Email verification
def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Email verified! You can now log in.")
        return redirect("login")
    else:
        messages.error(request, "Invalid or expired link.")
        return redirect("register")


# Login
from django.contrib.auth.views import LoginView, LogoutView

class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = "webapp/login.html"

class CustomLogoutView(LogoutView):
    template_name = "webapp/logout.html"

@login_required
def profile(request):
    return render(request, "webapp/profile.html", {"user": request.user})

@login_required
def edit_profile(request):
    if request.method == "POST":
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("profile")
    else:
        form = UserUpdateForm(instance=request.user)
    return render(request, "webapp/edit_profile.html", {"form": form})