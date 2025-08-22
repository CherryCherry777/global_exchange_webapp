from django.contrib.auth.models import Group

def admin_status(request):
    is_admin = False
    if request.user.is_authenticated:
        is_admin = request.user.groups.filter(name='Administrador').exists()
    return {'is_admin': is_admin}
