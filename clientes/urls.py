from django.urls import path
from . import views

urlpatterns = [
    path('', views.manage_clientes, name="manage_clientes"),
    path('clientes/', views.clientes, name='clientes'),  # lista de clientes
    path('crear/', views.crear_cliente, name='crear_cliente'),
    #path('asociar-usuario/', views.asociar_usuario_cliente, name='asociar_usuario_cliente'),
    path('inactivar/<int:pk>/', views.inactivar_cliente, name='inactivar_cliente'),
    path('activar/<int:pk>/', views.activar_cliente, name='activar_cliente'),
]