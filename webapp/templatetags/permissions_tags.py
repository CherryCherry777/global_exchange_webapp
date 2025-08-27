from django import template

register = template.Library()

@register.simple_tag
def has_perms(user, *perms):
    """
    Devuelve True si el usuario tiene todos los permisos listados.
    Uso: {% has_perms user 'perm1' 'perm2' %}
    """
    return all(user.has_perm(perm) for perm in perms)
