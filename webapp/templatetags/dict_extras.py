from django import template

register = template.Library()

@register.filter
def dict_get(d, key):
    return d.get(key, {})

@register.filter
def get_item(dictionary, key):
    """
    Permite acceder a dictionary[key] en un template.
    Uso en template: {{ mydict|get_item:mykey }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)