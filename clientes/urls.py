from django.urls import path
from . import views

urlpatterns = [
    path('', views.manage_clientes, name="manage_clientes"),  # lista de clientes
    path('crear/', views.crear_cliente, name='crear_cliente'),
    path('asignar-usuario/', views.asignar_cliente_usuario, name='asignar_cliente_usuario'),
    path('desasignar/<int:asignacion_id>/', views.desasignar_cliente_usuario, name='desasignar_cliente_usuario'),
    path("clientes/modificar/<int:cliente_id>/", views.modificar_cliente, name="modificar_cliente"),
    path('inactivar/<int:pk>/', views.inactivar_cliente, name='inactivar_cliente'),
    path('activar/<int:pk>/', views.activar_cliente, name='activar_cliente'),
]