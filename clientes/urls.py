from django.urls import path
from . import views

urlpatterns = [
    path('', views.manage_clientes, name="manage_clientes"),
    path('clientes/', views.clientes, name='clientes'),  # tu lista de clientes
    path('clientes/nuevo/', views.crear_cliente, name='crear_cliente'),
]