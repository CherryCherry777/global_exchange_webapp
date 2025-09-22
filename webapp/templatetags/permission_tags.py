from django import template

register = template.Library()

@register.filter
def translate_permission(permission_name):
    """Traduce los nombres de permisos del inglés al español"""
    translations = {
        # Permisos de monedas
        'Can view currency': 'Ver moneda',
        'Can add currency': 'Crear moneda',
        'Can change currency': 'Modificar moneda',
        'Can delete currency': 'Eliminar moneda',
        'Can deactivate currency': 'Desactivar moneda',
        
        # Permisos de tasas de cambio
        'Can view exchange rate': 'Ver tasa de cambio',
        'Can add exchange rate': 'Crear tasa de cambio',
        'Can change exchange rate': 'Modificar tasa de cambio',
        'Can delete exchange rate': 'Eliminar tasa de cambio',
        
        # Permisos de usuarios
        'Can view user': 'Ver usuario',
        'Can add user': 'Crear usuario',
        'Can change user': 'Modificar usuario',
        'Can delete user': 'Eliminar usuario',
        'Can activate user': 'Activar usuario',
        'Can deactivate user': 'Desactivar usuario',
        
        # Permisos de roles
        'Can view group': 'Ver rol',
        'Can add group': 'Crear rol',
        'Can change group': 'Modificar rol',
        'Can delete group': 'Eliminar rol',
        'Can deactivate role': 'Desactivar rol',
        
        # Permisos de permisos
        'Can view permission': 'Ver permisos',
        'Can add permission': 'Crear permisos',
        'Can change permission': 'Modificar permisos',
        'Can delete permission': 'Eliminar permisos',
        
        # Permisos de clientes
        'Can view cliente': 'Ver cliente',
        'Can add cliente': 'Crear cliente',
        'Can change cliente': 'Modificar cliente',
        'Can delete cliente': 'Eliminar cliente',
        
        # Permisos de transacciones
        'Can view transaction': 'Ver transacción',
        'Can add transaction': 'Crear transacción',
        'Can change transaction': 'Modificar transacción',
        'Can delete transaction': 'Eliminar transacción',
        
        # Permisos de categorías
        'Can view category': 'Ver categoría',
        'Can add category': 'Crear categoría',
        'Can change category': 'Modificar categoría',
        'Can delete category': 'Eliminar categoría',
        
        # Permisos de tipos de pago
        'Can view payment type': 'Ver tipo de pago',
        'Can add payment type': 'Crear tipo de pago',
        'Can change payment type': 'Modificar tipo de pago',
        'Can delete payment type': 'Eliminar tipo de pago',
    }
    
    return translations.get(permission_name, permission_name)
