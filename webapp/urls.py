from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Public pages
    path("", views.public_home, name="public_home"),
    path("register/", views.register, name="register"),
    path("verify-email/<uidb64>/<token>/", views.verify_email, name="verify-email"),
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.custom_logout, name="logout"),

    # Profile
    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),

    # Landing pages
    path("landing/", views.landing_page, name="landing"),
    path("admin-dashboard/", views.admin_dash, name="admin_dashboard"),
    path("employee-dashboard/", views.employee_dash, name="employee_dashboard"),

    # User roles management
    path('manage-user-roles/', views.manage_user_roles, name='manage_user_roles'),
    path('manage-user-roles/add/<int:user_id>/', views.add_role_to_user, name='add_role_user'),
    path('manage-user-roles/remove/<int:user_id>/<str:role_name>/', views.remove_role_from_user, name='remove_role_user'),

    # Roles management
    path("manage-roles/", views.manage_roles, name="manage_roles"),
    path("roles/create/", views.create_role, name="create_role"),
    path("roles/delete/<int:role_id>/", views.delete_role, name="delete_role"),
    path("roles/update-permissions/<int:role_id>/", views.update_role_permissions, name="update_role_permissions"),

    # User CRUD
    path("users/", views.UserListView.as_view(), name="user_list"),
    path("users/create/", views.UserCreateView.as_view(), name="user_create"),
    path("users/update/<int:pk>/", views.UserUpdateView.as_view(), name="user_update"),
    path("users/delete/<int:pk>/", views.UserDeleteView.as_view(), name="user_delete"),

    # managing users
    path('manage-users/', views.manage_users, name='manage_users'),
    path('manage-users/add-role/<int:user_id>/', views.add_role_to_user, name='add_role_to_user'),
    path('manage-users/remove-role/<int:user_id>/<str:role_name>/', views.remove_role_from_user, name='remove_role_from_user'),
    path('manage-users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
]
