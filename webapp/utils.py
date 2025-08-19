def get_user_primary_role(user):
    """Return the highest-priority role of the user as a string."""
    if user.groups.filter(name="Administrator").exists():
        return "Administrator"
    elif user.groups.filter(name="Employee").exists():
        return "Employee"
    else:
        return "Regular User"