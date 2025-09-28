from django.contrib.auth import get_user_model

User = get_user_model()
PROTECTED_ROLES = ["Administrador", "Empleado", "Usuario"]
ROLE_TIERS = {
    "Administrador": 3, #numero mayor: mas alto
    "Empleado": 2,
    "Usuario": 1,
}