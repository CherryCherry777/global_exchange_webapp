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
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import RegistrationForm, LoginForm, UserUpdateForm
from .decorators import role_required
from .utils import get_user_primary_role

User = get_user_model()
PROTECTED_ROLES = ["Administrator", "Employee", "User"]

# -----------------------
# Public / Auth views
# -----------------------
def public_home(request):
    return render(request, "webapp/home.html")

def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            # Generate verification link
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            link = request.build_absolute_uri(
                reverse("verify-email", kwargs={"uidb64": uid, "token": token})
            )

            # PRINT TO TERMINAL
            print("=== VERIFICATION LINK ===")
            print(link)
            print("=========================")

            messages.success(request, "Registration successful! Check console for verification link.")
            return redirect("login")
        else:
            # Print form errors if invalid
            print("Form errors:", form.errors)
    else:
        form = RegistrationForm()

    return render(request, "webapp/register.html", {"form": form})




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
        messages.error(request, "Invalid or expired verification link.")
        return redirect("register")

class CustomLoginView(LoginView):
    template_name = "webapp/login.html"
    form_class = LoginForm

    def get_success_url(self):
        return reverse_lazy("landing")

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

@login_required
def landing_page(request):
    role = get_user_primary_role(request.user)
    return render(request, "webapp/landing.html", {"role": role})

# -----------------------
# User Role Management
# -----------------------
# Assign roles to users

@login_required
@role_required("Administrator")
def manage_user_roles(request):
    User = get_user_model()
    users = User.objects.all().prefetch_related("groups")
    roles = Group.objects.all()

    user_data = []
    for u in users:
        user_roles = list(u.groups.all())
        user_role_names = [r.name for r in user_roles]

        # Determine roles available to add
        addable_roles = [r for r in roles if r.name not in user_role_names]

        # Determine the "highest-tier role" of this user
        highest_role = None
        for r in PROTECTED_ROLES:
            if r in user_role_names:
                highest_role = r
                break

        user_data.append({
            "user": u,
            "roles": user_roles,
            "addable_roles": addable_roles,
            "highest_role": highest_role
        })

    return render(request, "webapp/manage_user_roles.html", {
        "user_data": user_data
    })

@login_required
@role_required("Administrator")
def user_role_list(request):
    users = User.objects.all().prefetch_related("groups")
    all_roles = Group.objects.all()
    return render(request, "webapp/manage_user_roles.html", {
        "users": users,
        "all_roles": all_roles,
    })

@login_required
@role_required("Administrator")
def add_role_to_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        role_name = request.POST.get("role")
        if role_name:
            group = get_object_or_404(Group, name=role_name)
            user.groups.add(group)
            user.save()
    return redirect("manage_user_roles")


@login_required
@role_required("Administrator")
def remove_role_from_user(request, user_id, role_name):
    user = get_object_or_404(User, id=user_id)
    if user == request.user:
        # Prevent removing own highest-tier role
        user_roles = [g.name for g in user.groups.all()]
        for r in PROTECTED_ROLES:
            if r in user_roles:
                if r == role_name:
                    return redirect("manage_user_roles")
    group = get_object_or_404(Group, name=role_name)
    user.groups.remove(group)
    user.save()
    return redirect("manage_user_roles")


# -----------------------
# Role / Permission Management
# -----------------------
@login_required
@role_required("Administrator")
def role_list(request):
    roles = Group.objects.all()
    permissions = Permission.objects.all()
    return render(request, "webapp/manage_roles.html", {
        "roles": roles,
        "permissions": permissions,
        "protected_roles": PROTECTED_ROLES,
    })

@login_required
@role_required("Administrator")
def create_role(request):
    if request.method == "POST":
        name = request.POST.get("name")
        if name in PROTECTED_ROLES:
            messages.error(request, "This role name is reserved.")
        else:
            Group.objects.create(name=name)
            messages.success(request, f"Role '{name}' created successfully!")
    return redirect("role_list")

@login_required
@role_required("Administrator")
def delete_role(request, role_id):
    role = get_object_or_404(Group, id=role_id)
    if role.name in PROTECTED_ROLES:
        messages.error(request, f"You cannot delete the '{role.name}' role.")
    else:
        role.delete()
        messages.success(request, f"Role '{role.name}' deleted successfully!")
    return redirect("role_list")

@login_required
@role_required("Administrator")
def update_role_permissions(request, role_id):
    role = get_object_or_404(Group, id=role_id)
    if request.method == "POST":
        selected_perms = request.POST.getlist("permissions")
        role.permissions.set(selected_perms)
        messages.success(request, f"Permissions updated for role '{role.name}'.")
    return redirect("role_list")

# -----------------------
# User CRUD (class-based views)
# -----------------------
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


# -----------------------
# Dashboards
# -----------------------
@role_required("Administrator")
def admin_dash(request):
    return render(request, "webapp/admin_dashboard.html")

@role_required("Employee")
def employee_dash(request):
    return render(request, "webapp/employee_dashboard.html")
