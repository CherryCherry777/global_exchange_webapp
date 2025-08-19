"""
decorators pueden ser aplicados a diferentes vistas para soportar elementos HTTP
"""
from django.contrib.auth.decorators import user_passes_test

def role_required(role_name):
    def decorator(view_func):
        def check_role(user):
            return user.groups.filter(name=role_name).exists()
        return user_passes_test(check_role)(view_func)
    return decorator

