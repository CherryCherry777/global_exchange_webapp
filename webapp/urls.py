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
    path("mfa-verify/", views.MFAVerifyView.as_view(), name="mfa_verify"),
    path("logout/", views.custom_logout, name="logout"),

    # Profile
    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),

    # Cliente Management (Admin only)
    path("manage-clientes/", views.manage_clientes, name="manage_clientes"),
    path("modify-client/<int:client_id>/", views.modify_client, name="modify_client"),
    path("view-client/<int:client_id>/", views.view_client, name="view_client"),
    path("create-client/", views.create_client, name="create_client"),
    path("assign-clients/", views.assign_clients, name="assign_clients"),
    path("manage-categories/", views.manage_categories, name="manage_categories"),
    path("modify-category/<int:category_id>/", views.modify_category, name="modify_category"),
    path("manage-currencies/", views.manage_currencies, name="manage_currencies"),
    path("create-currency/", views.create_currency, name="create_currency"),
    path("modify-currency/<int:currency_id>/", views.modify_currency, name="modify_currency"),
    path("manage-quotes/", views.manage_quotes, name="manage_quotes"),
    path("modify-quote/<int:currency_id>/", views.modify_quote, name="modify_quote"),
    path("delete-cliente/<int:cliente_id>/", views.delete_cliente, name="delete_cliente"),
    path('clientes/asignar-usuario/', views.asignar_cliente_usuario, name='asignar_cliente_usuario'),
    path('clientes/desasignar/<int:asignacion_id>/', views.desasignar_cliente_usuario, name='desasignar_cliente_usuario'),
    path('inactivar-cliente/<int:pk>/', views.inactivar_cliente, name='inactivar_cliente'),
    path('activar-cliente/<int:pk>/', views.activar_cliente, name='activar_cliente'),

    # Landing pages
    path("landing/", views.landing_page, name="landing"),
    path("admin-dashboard/", views.admin_dash, name="admin_dashboard"),
    path("employee-dashboard/", views.employee_dash, name="employee_dashboard"),
    path("analyst-dashboard/", views.analyst_dash, name="analyst_dashboard"),

    # User roles management
    path('manage-user-roles/', views.manage_user_roles, name='manage_user_roles'),
    path('manage-user-roles/add/<int:user_id>/', views.add_role_to_user, name='add_role_user'),
    path('manage-user-roles/remove/<int:user_id>/<str:role_name>/', views.remove_role_from_user, name='remove_role_user'),

    # Roles management
    path("manage-roles/", views.manage_roles, name="manage_roles"),
    path("manage-roles/create/", views.create_role, name="create_role"),
    path("roles/delete/<int:role_id>/", views.delete_role, name="delete_role"),
    path("roles/update-permissions/<int:role_id>/", views.update_role_permissions, name="update_role_permissions"),
    path('manage-roles/delete/<int:role_id>/confirm/', views.confirm_delete_role, name='confirm_delete_role'),

    # User CRUD
    path("users/", views.UserListView.as_view(), name="user_list"),
    path("users/create/", views.UserCreateView.as_view(), name="user_create"),
    path("users/update/<int:pk>/", views.UserUpdateView.as_view(), name="user_update"),
    path("users/delete/<int:pk>/", views.UserDeleteView.as_view(), name="user_delete"),

    # managing users
    path('manage-users/', views.manage_users, name='manage_users'),
    path('manage-users/<int:user_id>/modify/', views.modify_users, name='modify_users'),
    path('manage-users/<int:user_id>/activate/', views.activate_user, name='activate_user'),
    path('manage-users/<int:user_id>/deactivate/', views.deactivate_user, name='deactivate_user'),
    path('manage-users/delete/<int:user_id>/confirm/', views.confirm_delete_user, name='confirm_delete_user'),
    path('manage-roles/', views.manage_roles, name='manage_roles'),
    path('manage-roles/<int:role_id>/modify/', views.modify_role, name='modify_role'),
    path('manage-user-roles/', views.manage_user_roles, name='manage_user_roles'),

    # Currency Manager
    path('currency/crear/', views.create_currency, name='create_currency'),
    path('currency/editar/<int:currency_id>/', views.edit_currency, name='edit_currency'),
    path('currency/toggle/', views.toggle_currency, name='toggle_currency'),

    # Categories management
    path('manage-categories/', views.manage_categories, name='manage_categories'),
    path('create-sample-categories/', views.create_sample_categories_view, name='create_sample_categories'),

    # Mis métodos de pago (cliente)
    path('mis-medios/', views.my_payment_methods, name='my_payment_methods'),
    path('mis-medios/add/<str:tipo>/', views.manage_payment_method, name='add_payment_method'),
    path('mis-medios/manage/<str:tipo>/<int:medio_pago_id>/', views.manage_payment_method, name='manage_payment_method'),
    path('mis-medios/delete/<int:medio_pago_id>/confirm/', views.confirm_delete_payment_method, name='confirm_delete_payment_method'),

    # Administración global de métodos de pago
    path("payment-types/", views.payment_types_list, name="payment_types_list"),
    path("payment-types/edit/<int:tipo_id>/", views.edit_payment_type, name="edit_payment_type"),

    # Administración de límites de intercambio
    path('limites/', views.limites_intercambio_list, name='limites_list'),
    path('limites/config/<int:config_id>/editar/', views.limite_config_edit, name='limite_config_edit'),
    path('limites/cargar-tabla/', views.limites_intercambio_tabla_htmx, name='limites_tabla_htmx'),

    # Administración de cotizaciones
    path('prices/', views.prices_list, name='prices_list'),
    path('prices/editar/<int:currency_id>/', views.edit_prices, name='edit_prices'),

    # Mis métodos de cobro (cliente)
    path('mis-cobros/', views.my_cobro_methods, name='my_cobro_methods'),
    path('mis-cobros/add/<str:tipo>/', views.manage_cobro_method, name='add_cobro_method'),
    path('mis-cobros/manage/<str:tipo>/<int:medio_cobro_id>/', views.manage_cobro_method, name='manage_cobro_method'),
    path('mis-cobros/delete/<int:medio_cobro_id>/confirm/', views.confirm_delete_cobro_method, name='confirm_delete_cobro_method'),

    # Administracion global de metodos de cobro
    path('cobros/', views.cobro_types_list, name='cobro_types_list'),
    path('cobros/editar/<int:tipo_id>/', views.edit_cobro_type, name='edit_cobro_type'),
    
    # Administrar métodos de pago globales
    path('manage-payment-methods/', views.manage_payment_methods, name='manage_payment_methods'),
    path('modify-payment-method/<int:payment_method_id>/', views.modify_payment_method, name='modify_payment_method'),
    
    # Administrar métodos de cobro globales
    path('manage-cobro-methods/', views.manage_cobro_methods, name='manage_cobro_methods'),
    path('modify-cobro-method/<int:cobro_method_id>/', views.modify_cobro_method, name='modify_cobro_method'),

    # Compraventa de divisas
    path("compraventa/", views.compraventa_view, name="compraventa"),

    # Administrar entidades de medios de pago y cobro de cliente
    path("entidades/", views.entidad_list, name="entidad_list"),
    path("entidades/add/", views.entidad_create, name="entidad_add"),
    path("entidades/<int:pk>/edit/", views.entidad_update, name="entidad_edit"),
    path("entidades/<int:pk>/toggle/", views.entidad_toggle, name="entidad_toggle"),

    # Conversión
    path("api/currencies/", views.api_active_currencies, name="api_currencies"),
    path("api/currencies/active/", views.api_active_currencies, name="api_active_currencies"),
    path("api/currencies/history/", views.api_currency_history, name="api_currency_history"),
    path("historical/", views.historical_view, name="historical"),   
    path("cliente-seleccionado/", views.set_cliente_seleccionado, name="set_cliente_seleccionado"),
    path("metodos-pago-cobro/", views.get_metodos_pago_cobro, name="get_metodos_pago_cobro"),
    path("change-client/", views.change_client, name="change_client"),

    # Transacciones
    path("historial-transacciones/", views.transaccion_list, name="transaccion_list"),
    path("transaccion/<int:transaccion_id>/ingresar-id/", views.ingresar_idTransferencia, name="ingresar_idTransferencia"),

    #Configuracion de notificaciones de correo
    path("schedule/", views.manage_schedule, name="manage_schedule"),
    path("unsubscribe/<uidb64>/<token>/", views.unsubscribe, name="unsubscribe"),
    path('unsubscribe/confirm/', views.unsubscribe_confirm, name='unsubscribe_confirm'),
    path('unsubscribe/error/', views.unsubscribe_error, name='unsubscribe_error'),
    #path("verificar_mfa/", views.verificar_mfa, name="verificar_mfa"),

    # Tauser
    path("tauser/", views.tauser_home, name="tauser_home"),
    path("tauser/login/", views.tauser_login, name="tauser_login"),
    path("tauser/pagar/<int:pk>/", views.tauser_pagar, name="tauser_pagar"),
    path("tauser/cobrar/<int:pk>/", views.tauser_cobrar, name="tauser_cobrar"),

]
