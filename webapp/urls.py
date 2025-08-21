from django.urls import path
from . import views

urlpatterns = [
    # Public / auth
    path('', views.public_home, name='public_home'),
    path('register/', views.register, name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('verify-email/<uidb64>/<token>/', views.verify_email, name='verify-email'),

    # Landing & profile
    path('landing/', views.landing_page, name='landing'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),

    # Dashboards
    path('admin_dashboard/', views.admin_dash, name='admin_dash'),
    path('employee_dashboard/', views.employee_dash, name='employee_dash'),

    # User CRUD
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/add/', views.UserCreateView.as_view(), name='user_add'),
    path('users/<int:pk>/edit/', views.UserUpdateView.as_view(), name='user_edit'),
    path('users/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),

    # User roles management
    path('manage_user_roles/', views.manage_user_roles, name='manage_user_roles'),
    path('manage_user_roles/<int:user_id>/add/', views.add_role_to_user, name='add_role_to_user'),
    path('manage_user_roles/<int:user_id>/<str:role_name>/remove/', views.remove_role_from_user, name='remove_role_from_user'),


    # Role & permissions management
    path('manage_roles/', views.role_list, name='manage_roles'),
    path('manage_roles/create/', views.create_role, name='create_role'),
    path('manage_roles/<int:role_id>/delete/', views.delete_role, name='delete_role'),
    path('manage_roles/<int:role_id>/update_permissions/', views.update_role_permissions, name='update_role_permissions'),
]
