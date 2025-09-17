from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Public pages
    path("", views.public_home, name="public_home"),
    path("register/", views.register, name="register"),
    path("verify-email/<uidb64>/<token>/", views.verify_email, name="verify-email"),
    path("resend-verification/", views.resend_verification_email, name="resend_verification"),
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.custom_logout, name="logout"),

    # Profile
    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),

    # Cliente Management (Admin only)
    path("manage-clientes/", views.manage_clientes, name="manage_clientes"),
    path("create-cliente/", views.create_cliente, name="create_cliente"),
    path("update-cliente/<int:cliente_id>/", views.update_cliente, name="update_cliente"),
    path("delete-cliente/<int:cliente_id>/", views.delete_cliente, name="delete_cliente"),
    path("view-cliente/<int:cliente_id>/", views.view_cliente, name="view_cliente"),
    path('clientes/asignar-usuario/', views.asignar_cliente_usuario, name='asignar_cliente_usuario'),
    path('clientes/desasignar/<int:asignacion_id>/', views.desasignar_cliente_usuario, name='desasignar_cliente_usuario'),
    path('inactivar-cliente/<int:pk>/', views.inactivar_cliente, name='inactivar_cliente'),
    path('activar-cliente/<int:pk>/', views.activar_cliente, name='activar_cliente'),

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
    path('manage-roles/delete/<int:role_id>/confirm/', views.confirm_delete_role, name='confirm_delete_role'),

    # User CRUD
    path("users/", views.UserListView.as_view(), name="user_list"),
    path("users/create/", views.UserCreateView.as_view(), name="user_create"),
    path("users/update/<int:pk>/", views.UserUpdateView.as_view(), name="user_update"),
    path("users/delete/<int:pk>/", views.UserDeleteView.as_view(), name="user_delete"),

    # managing users
    #path('manage-users/', views.manage_users, name='manage_users'),
    #path('manage-users/add-role/<int:user_id>/', views.add_role_to_user, name='add_role_to_user'),
    #path('manage-users/remove-role/<int:user_id>/<str:role_name>/', views.remove_role_from_user, name='remove_role_from_user'),
    #path('manage-users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    #path('manage-users/delete/<int:user_id>/confirm/', views.confirm_delete_user, name='confirm_delete_user'),
    #path('manage-users/<int:user_id>/modify/', views.modify_user, name='modify_user'),
    #path('manage-users/delete/<int:user_id>/confirm/', views.confirm_delete_user, name='confirm_delete_user'),
    # Users
    path('manage-users/', views.manage_users, name='manage_users'),
    path('manage-users/<int:user_id>/modify/', views.modify_users, name='modify_users'),
    path('manage-users/delete/<int:user_id>/confirm/', views.confirm_delete_user, name='confirm_delete_user'),

    # Currency Manager
    path('currency/', views.currency_list, name='currency_list'),
    path('currency/crear/', views.create_currency, name='create_currency'),
    path('currency/editar/<int:currency_id>/', views.edit_currency, name='edit_currency'),
    path('currency/toggle/', views.toggle_currency, name='toggle_currency'),
    path("api/currencies/", views.api_active_currencies, name="api_currencies"),

    # Categories management
    path('manage-categories/', views.manage_categories, name='manage_categories'),
    
    # Payment methods management
    #path('manage-client-payment-methods/', views.manage_client_payment_methods, name='manage_client_payment_methods'),
    #path('manage-client-payment-methods/<int:cliente_id>/', views.manage_client_payment_methods_detail, name='manage_client_payment_methods_detail'),
    #path('manage-client-payment-methods/<int:cliente_id>/add/<str:tipo>/', views.add_payment_method, name='add_payment_method'),
    #path('manage-client-payment-methods/<int:cliente_id>/edit/<int:medio_pago_id>/', views.edit_payment_method, name='edit_payment_method'),
    #path('view-client-payment-methods/<int:cliente_id>/', views.view_client_payment_methods, name='view_client_payment_methods'),

    # Metodos para que el cliente administre sus propios metodos de pago
    path('mis-medios/add-billetera/', views.add_payment_method_billetera, name='add_payment_method_billetera'),
    path('mis-medios/add-cheque/', views.add_payment_method_cheque, name='add_payment_method_cheque'),
    path('mis-medios/add-cuenta-bancaria/', views.add_payment_method_cuenta_bancaria, name='add_payment_method_cuenta_bancaria'),
    path('mis-medios/add-tarjeta/', views.add_payment_method_tarjeta, name='add_payment_method_tarjeta'),
    path('mis-medios/', views.my_payment_methods, name='my_payment_methods'),
    path('mis-medios/edit/<int:medio_pago_id>/', views.edit_payment_method, name='edit_payment_method'),
    path('mis-medios/delete/<int:medio_pago_id>/', views.delete_payment_method, name='delete_payment_method'),
    path('mis-medios/billetera/edit/<int:medio_pago_id>/', views.edit_payment_method_billetera, name='edit_payment_method_billetera'),
    path('mis-medios/cheque/edit/<int:medio_pago_id>/', views.edit_payment_method_cheque, name='edit_payment_method_cheque'),
    path('mis-medios/cuenta-bancaria/edit/<int:medio_pago_id>/', views.edit_payment_method_cuenta_bancaria, name='edit_payment_method_cuenta_bancaria'),
    path('mis-medios/tarjeta/edit/<int:medio_pago_id>/', views.edit_payment_method_tarjeta, name='edit_payment_method_tarjeta'),
    path('mis-medios/billetera/delete/<int:medio_pago_id>/', views.delete_payment_method_billetera, name='delete_payment_method_billetera'),
    path('mis-medios/cheque/delete/<int:medio_pago_id>/', views.delete_payment_method_cheque, name='delete_payment_method_cheque'),
    path('mis-medios/cuenta-bancaria/delete/<int:medio_pago_id>/', views.delete_payment_method_cuenta_bancaria, name='delete_payment_method_cuenta_bancaria'),
    path('mis-medios/tarjeta/delete/<int:medio_pago_id>/', views.delete_payment_method_tarjeta, name='delete_payment_method_tarjeta'),

    #administracion global de metodos de pago
    path("payment-types/", views.payment_types_list, name="payment_types_list"),
    path("payment-types/edit/<int:tipo_id>/", views.edit_payment_type, name="edit_payment_type"),

    #Administracion de limites de intercambio de monedas por tipo de cliente
    path('limites/', views.limites_intercambio_list, name='limites_list'),
    path('limites/<int:moneda_id>/editar/', views.limite_edit, name='limite_edit'),

    #Administracion  de cotizaciones
    # Currency Manager
    path('prices/', views.prices_list, name='prices_list'),
    path('prices/editar/<int:currency_id>/', views.edit_prices, name='edit_prices'),
]

