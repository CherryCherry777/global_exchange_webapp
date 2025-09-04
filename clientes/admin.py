from django.contrib import admin
from .models import Cliente, ClienteUsuario

# Register your models here.

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipoCliente', 'categoria', 'estado', 'fechaRegistro']
    list_filter = ['tipoCliente', 'categoria', 'estado']
    search_fields = ['nombre', 'documento', 'correo']
    readonly_fields = ['fechaRegistro']

@admin.register(ClienteUsuario)
class ClienteUsuarioAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'usuario', 'fecha_asignacion']
    list_filter = ['fecha_asignacion']
    search_fields = ['cliente__nombre', 'usuario__username']
    readonly_fields = ['fecha_asignacion']
