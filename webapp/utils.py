def get_user_primary_role(user):
    """Return the highest-priority role of the user as a string."""
    if user.groups.filter(name="Administrador").exists():
        return "Administrador"
    elif user.groups.filter(name="Empleado").exists():
        return "Empleado"
    else:
        return "Usuario"