# 📁 Estructura de CSS Organizada

## 🎯 Organización por Funcionalidad

Esta estructura organiza los archivos CSS de manera modular, siguiendo la misma lógica que los templates.

### 📂 Estructura de Carpetas

```
css/
├── auth/                    # 🔐 Autenticación
│   └── auth.css
├── usuarios/               # 👥 Gestión de Usuarios
│   ├── manage_users.css
│   ├── modify_user.css
│   └── manage_user_roles.css
├── clientes/               # 🏢 Gestión de Clientes
│   ├── assign_clients.css
│   ├── change_client.css
│   ├── create_client.css
│   ├── manage_clients.css
│   ├── modify_client.css
│   └── view_client.css
├── compraventa/            # 💱 Operaciones de Compra/Venta
│   └── (archivos futuros)
├── cotizaciones/           # 📊 Gestión de Cotizaciones
│   ├── historical.css
│   ├── manage_quotes.css
│   └── modify_quote.css
├── metodos_pago/           # 💳 Métodos de Pago
│   ├── add_payment_method.css
│   ├── manage_payment_methods.css
│   ├── modify_payment_method.css
│   └── my_payment_methods.css
├── metodos_cobro/          # 💰 Métodos de Cobro
│   ├── manage_cobro_methods.css
│   ├── modify_cobro_method.css
│   └── my_cobro_methods.css
├── roles/                  # 🎭 Gestión de Roles
│   ├── create_role.css
│   ├── manage_roles.css
│   └── modify_role.css
├── categorias/             # 📋 Gestión de Categorías
│   ├── manage_categories.css
│   └── modify_category.css
├── monedas/                # 🪙 Gestión de Monedas
│   ├── create_currency.css
│   ├── manage_currencies.css
│   └── modify_currency.css
├── paginas_principales/    # 🏠 Páginas Principales
│   ├── home.css
│   ├── landing.css
│   └── profile.css
├── dashboards/             # 📊 Dashboards
│   ├── admin.css
│   ├── user_dashboard.css
│   └── user_menu.css
├── entidades/              # 🏛️ Entidades de Pago/Cobro
│   ├── entidad_edit.css
│   └── entidades.css
├── limites/                # ⚖️ Límites de Intercambio
│   ├── limite_edit.css
│   └── limites_intercambio.css
└── shared/                 # 🔧 Archivos Compartidos
    ├── forms.css
    ├── global.css
    └── tables.css
```

## 🎨 Convenciones de Nomenclatura

### 📝 Patrones de Nombres:
- `manage_*.css` - Para páginas de listado/gestión
- `modify_*.css` - Para páginas de edición
- `create_*.css` - Para páginas de creación
- `view_*.css` - Para páginas de visualización
- `my_*.css` - Para páginas del usuario (mis métodos, etc.)

### 🔧 Archivos Compartidos:
- `global.css` - Estilos globales del sistema
- `forms.css` - Estilos para formularios
- `tables.css` - Estilos para tablas

## 📱 Responsive Design

Cada archivo CSS debe incluir:
- **Mobile First** approach
- **Breakpoints** estándar:
  - Mobile: < 768px
  - Tablet: 768px - 1024px
  - Desktop: > 1024px

## 🎯 Beneficios de esta Estructura

### ✅ Ventajas:
1. **Modularidad** - Cada funcionalidad está aislada
2. **Mantenibilidad** - Fácil encontrar y modificar estilos
3. **Escalabilidad** - Fácil agregar nuevos módulos
4. **Consistencia** - Nomenclatura uniforme
5. **Colaboración** - Equipos pueden trabajar en paralelo

### 🔄 Flujo de Trabajo:
1. **Desarrollo** - Crear CSS en la carpeta correspondiente
2. **Testing** - Probar en diferentes dispositivos
3. **Optimización** - Minificar para producción
4. **Deployment** - Mantener estructura en producción

## 🚀 Próximos Pasos

1. **Actualizar referencias** en templates
2. **Crear archivos base** para nuevos módulos
3. **Implementar sistema de build** para CSS
4. **Documentar componentes** reutilizables

## 📚 Referencias

- [Django Static Files](https://docs.djangoproject.com/en/stable/howto/static-files/)
- [CSS Architecture Best Practices](https://css-tricks.com/css-architecture/)
- [BEM Methodology](https://getbem.com/)
