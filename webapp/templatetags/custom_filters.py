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
    Formatea un número con una cantidad de decimales específica y separador de miles.
    Acepta tanto un número de decimales como una instancia de Currency (para leer decimales_monto).
    
    Ejemplos:
        {{ 1234.5678|format_decimals:4 }}        -> 1.234,5678
        {{ 1234.5678|format_decimals:moneda }}   -> 1.234,57   (usa moneda.decimales_monto)
    """
    if value is None:
        return ""

    # Si se pasa un objeto Currency, usa sus decimales
    if hasattr(num_decimals, "decimales_monto"):
        num_decimals = getattr(num_decimals, "decimales_monto", 2)
    else:
        try:
            num_decimals = int(num_decimals)
        except (ValueError, TypeError):
            num_decimals = 2

    try:
        num = float(value)
    except (ValueError, TypeError):
        return value

    formatted = f"{num:,.{num_decimals}f}"
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return formatted

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

@register.filter
def replace_underscore(value):
    """Reemplaza guiones bajos con espacios.
    
    Ejemplo:
        {{ "tarjeta_nacional"|replace_underscore|capfirst }}  -> Tarjeta Nacional
    """
    return str(value).replace('_', ' ')

