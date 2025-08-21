from django import template
register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


register = template.Library()

@register.filter
def dict_get(d, key):
    """Get value from dictionary by key safely."""
    if not d:
        return None
    return d.get(key)
