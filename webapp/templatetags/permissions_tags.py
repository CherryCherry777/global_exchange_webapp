from django import template
from webapp.models import ClienteUsuario

register = template.Library()

@register.simple_tag
def has_perms(user, *perms):
    """
    Devuelve True si el usuario tiene todos los permisos listados.
    Uso: {% has_perms user 'perm1' 'perm2' %}
    """
    return all(user.has_perm(perm) for perm in perms)

@register.simple_tag
def is_usuario_asociado(user):
    """
    Retorna True si el usuario está asociado al cliente dado.
    Uso: {% if request.user|is_usuario_asociado %}
    """
    if user.is_authenticated:
        return ClienteUsuario.objects.filter(usuario=user).exists()
    return False

