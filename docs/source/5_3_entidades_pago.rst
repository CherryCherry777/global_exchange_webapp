5.3 Entidades de pago/cobro
==========================

Registrar entidades (bancos, billeteras, etc.)
---------------------------------------------

- `Entidad` (modelo): representa proveedores externos (bancos, PSPs) o contrapartes.
- Pasos para registrar: crear una `Entidad` en el panel, añadir `CuentaBancariaNegocio` o `Billetera` asociada, configurar datos de conciliación.

Vincular con métodos
---------------------

- Asociar `Entidad` con `MedioPago` / `MedioCobro` para definir qué proveedor maneja cada método.
- Registrar metadatos como `provider_id`, `api_key`, `webhook_url` y mantener acceso restringido.

Consideraciones de compliance
-----------------------------

- Cifrar datos sensibles (IBAN, claves) y limitar acceso mediante permisos.
- Mantener registros de auditoría para cambios en entidades y cuentas.
