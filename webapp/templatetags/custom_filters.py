from django import template
register = template.Library()

"""@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)
"""

register = template.Library()

@register.filter
def dict_get(d, key):
    """Get value from dictionary by key safely."""
    if not d:
        return None
    return d.get(key)



@register.filter
def get_item(dictionary, key):
    """Allow dictionary access in templates: {{ mydict|get_item:key }}"""
    if dictionary and key in dictionary:
        return dictionary.get(key)
    return None

@register.filter
def porcentaje(value):
    """
    Converts a decimal to a percentage for templates.
    
    Example:
        0.3 -> 30
        Usage: {{ categoria.descuento|porcentaje }}%
    
    Purpose:
    - Store as decimal in DB, display as readable percentage in templates.
    """
    return round(value * 100, 1)

@register.filter
def format_decimals(value, num_decimals=2):
    """
    Formatea un número con la cantidad de decimales especificada.
    Ejemplo: {{ 123.4567|format_decimals:4 }} -> 123.4567
    """
    try:
        num_decimals = int(num_decimals)
    except (ValueError, TypeError):
        num_decimals = 2

    if value is None:
        return ""

    format_str = f"{{:.{num_decimals}f}}"
    return format_str.format(value)

@register.filter
def decimal_step(value):
    """Devuelve el step para un input tipo number según decimales."""
    try:
        dec = int(value)
        if dec <= 0:
            return '1'
        return '0.' + '0'*(dec-1) + '1'
    except:
        return '1'

