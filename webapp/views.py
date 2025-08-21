from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.core.mail import send_mail
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User, Permission
from django.contrib.auth.views import LoginView
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .utils import get_user_primary_role

from .forms import RegistrationForm, LoginForm
from .forms import UserUpdateForm

from .decorators import role_required

PROTECTED_ROLES = ["Administrator", "Employee", "User"]

User = get_user_model()

def public_home(request):
    return render(request, "webapp/home.html")

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
    template_name = "webapp/login.html"
    form_class = LoginForm

    def get_success_url(self):
        # Redirect to the named URL 'landing'
        return reverse_lazy('landing')

def custom_logout(request):
    logout(request)
    return render(request, "webapp/logout.html")

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

def manage_roles(request):
    users = User.objects.all().prefetch_related("groups")
    roles = Group.objects.all()

    # Prepare data for template
    user_roles = []
    for u in users:
        user_group_names = set(g.name for g in u.groups.all())
        role_status = []
        for r in roles:
            role_status.append({
                "name": r.name,
                "has_role": r.name in user_group_names
            })
        user_roles.append({
            "user": u,
            "roles": role_status
        })

    return render(request, "webapp/manage_user_roles.html", {
        "user_roles": user_roles
    })


# --- Add Role ---
def add_role(request, user_id, role_name):
    user = get_object_or_404(User, id=user_id)
    group = get_object_or_404(Group, name=role_name)
    user.groups.add(group)
    return redirect("manage_user_roles")


# --- Remove Role ---
def remove_role(request, user_id, role_name):
    user = get_object_or_404(User, id=user_id)
    group = get_object_or_404(Group, name=role_name)
    user.groups.remove(group)
    return redirect("manage_user_roles")


@role_required("Administrator")
def admin_dash(request):
    return render(request, "webapp/admin_dashboard.html")

@role_required("Employee")
def employee_dash(request):
    return render(request, "webapp/employee_dashboard.html")

@login_required
def landing_page(request):
    role = get_user_primary_role(request.user)
    context = {"role": role}  # still available if needed
    return render(request, "webapp/landing.html", context)

@login_required
@role_required("Administrator")
def manage_user_roles(request):
    User = get_user_model()
    users = User.objects.all()
    all_roles = Group.objects.all()
    return render(request, "webapp/manage_user_roles.html", {"users": users, "all_roles": all_roles})

@login_required
@role_required("Administrator")
def remove_role(request, user_id, role):
    User = get_user_model()
    user = get_object_or_404(User, id=user_id)
    group = get_object_or_404(Group, name=role)
    user.groups.remove(group)
    user.save()
    return redirect("manage_user_roles")

@login_required
@role_required("Administrator")
def add_role(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        role_name = request.POST.get("role")
        if role_name:
            group = get_object_or_404(Group, name=role_name)
            user.groups.add(group)
            user.save()
        return redirect("manage_user_roles")


class UserListView(ListView):
    model = User
    template_name = 'webapp/user_list.html'
    context_object_name = 'users'

class UserCreateView(CreateView):
    model = User
    template_name = 'webapp/user_form.html'
    fields = ['username', 'password', 'email', 'first_name', 'last_name']
    success_url = reverse_lazy('user_list')

    def form_valid(self, form):
        # Hash password before saving
        form.instance.set_password(form.instance.password)
        return super().form_valid(form)

class UserUpdateView(UpdateView):
    model = User
    template_name = 'webapp/user_form.html'
    fields = ['username', 'email', 'first_name', 'last_name']
    success_url = reverse_lazy('user_list')

class UserDeleteView(DeleteView):
    model = User
    template_name = 'webapp/user_confirm_delete.html'
    success_url = reverse_lazy('user_list')



@login_required
def manage_roles(request):
    roles = Group.objects.all().order_by("name")
    permissions = Permission.objects.all()
    return render(request, "webapp/manage_roles.html", {
        "roles": roles,
        "permissions": permissions
    })


@login_required
def create_role(request):
    if request.method == "POST":
        name = request.POST.get("name")
        if name in PROTECTED_ROLES:
            messages.error(request, "This role name is reserved.")
        else:
            Group.objects.create(name=name)
            messages.success(request, f"Role '{name}' created successfully!")
    return redirect("manage_roles")


@login_required
def delete_role(request, role_id):
    role = get_object_or_404(Group, id=role_id)
    if role.name in PROTECTED_ROLES:
        messages.error(request, f"You cannot delete the '{role.name}' role.")
    else:
        role.delete()
        messages.success(request, f"Role '{role.name}' deleted successfully!")
    return redirect("manage_roles")


@login_required
def update_role_permissions(request, role_id):
    role = get_object_or_404(Group, id=role_id)
    if request.method == "POST":
        # Replace existing permissions with submitted ones
        selected = request.POST.getlist("permissions")
        role.permissions.set(selected)
        messages.success(request, f"Permissions updated for role '{role.name}'.")
    return redirect("manage_roles")

"""

@role_required("Regular User")
def regular_dashboard(request):
    ...


@role_required("Employee")
def employee_dashboard(request):
    ...

@role_required("Administrator")
def admin_dashboard(request):
    ...

#The role_required decorator works with any group,
# so you can add new roles anytime in /admin/ and protect views easily.
"""