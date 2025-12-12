9.3 Asignación de nuevo cliente
================================

Este procedimiento describe el proceso completo para incorporar un nuevo cliente al sistema y asignarlo a un operador responsable.

Requisitos previos
------------------

**Documentación del cliente:**

- Documento de identidad válido (cédula, pasaporte, RUC).
- Comprobante de domicilio (para montos altos o clientes corporativos).
- Formulario de registro completado (si aplica).

**Permisos necesarios:**

- ``add_cliente``: Para crear el registro del cliente.
- ``add_clienteusuario``: Para asignar el cliente a un operador.

Proceso de alta de cliente
--------------------------

**Paso 1: Verificación inicial**

1. Solicitar documento de identidad al cliente.

2. Verificar en el sistema si ya existe:
   - Buscar por número de documento.
   - Buscar por nombre (posibles duplicados).

3. Si existe: actualizar datos si es necesario y continuar con la operación.

4. Si no existe: proceder con el alta.

**Paso 2: Crear registro de cliente**

1. Acceder a: Menú → Clientes → Nuevo cliente.

2. Completar datos obligatorios:
   - ``nombre``: Nombre completo según documento.
   - ``documento``: Número de documento (validar formato).
   - ``tipo_documento``: Cédula, RUC, Pasaporte, etc.

3. Completar datos adicionales:
   - ``correo``: Email válido para comunicaciones.
   - ``telefono``: Con código de país.
   - ``direccion``: Dirección de contacto.
   - ``fecha_nacimiento``: Para personas físicas.

4. Asignar categoría inicial:
   - Nuevos clientes: generalmente "Estándar" o "Nuevo".
   - Clientes con referencia: según evaluación comercial.

5. Guardar el registro.

**Paso 3: Validación de información (KYC)**

Según el nivel de riesgo y montos esperados:

**Nivel básico (montos bajos):**

- Verificar documento de identidad (original o copia).
- Confirmar datos ingresados.
- Marcar como "Verificado - Básico".

**Nivel intermedio (montos medios):**

- Todo lo anterior, más:
- Comprobante de domicilio.
- Verificación de teléfono/email.
- Marcar como "Verificado - Intermedio".

**Nivel completo (montos altos / corporativos):**

- Todo lo anterior, más:
- Declaración de origen de fondos.
- Documentación de empresa (si aplica).
- Aprobación de área de cumplimiento.
- Marcar como "Verificado - Completo".

**Paso 4: Asignación a operador**

1. Determinar el operador responsable:
   - Por zona geográfica del cliente.
   - Por carga de trabajo actual.
   - Por especialidad (clientes corporativos, VIP).

2. Acceder a: Clientes → Asignaciones (vista ``assign_clients``).

3. Seleccionar el cliente recién creado.

4. Seleccionar el operador asignado.

5. Confirmar la asignación.

**Paso 5: Configurar límites y restricciones**

1. Verificar límites aplicables según categoría:
   - Límite por transacción.
   - Límite diario.
   - Límite mensual.

2. Si el cliente requiere límites especiales:
   - Documentar justificación.
   - Obtener aprobación del supervisor.
   - Configurar límites personalizados.

**Paso 6: Comunicación**

1. Notificar al operador asignado:
   - Datos del nuevo cliente.
   - Categoría y límites.
   - Cualquier observación especial.

2. Si aplica, enviar bienvenida al cliente:
   - Email de confirmación de registro.
   - Información sobre servicios disponibles.

Puntos de control
-----------------

**Validaciones del sistema:**

- Documento no duplicado.
- Email con formato válido.
- Teléfono con formato correcto.
- Categoría seleccionada.

**Validaciones manuales:**

- Documento coincide con persona presente.
- Datos ingresados correctamente.
- Nivel de KYC apropiado.

**Auditoría:**

- Registrar quién creó el cliente.
- Registrar quién realizó la asignación.
- Fecha y hora de cada acción.
- Documentos verificados.

Casos especiales
----------------

**Cliente corporativo/empresa:**

- Solicitar RUC y documentos de constitución.
- Identificar representante legal.
- Verificar poderes y facultades.
- Categoría: "Corporativo".

**Cliente extranjero:**

- Pasaporte válido.
- Verificar vigencia de visa si aplica.
- Puede requerir documentación adicional.

**Cliente referido por otro cliente:**

- Registrar la referencia en observaciones.
- Considerar para programas de fidelidad.

Buenas prácticas
----------------

- Verificar siempre el documento original, no solo copias.
- No omitir pasos de validación por presión de tiempo.
- Mantener comunicación clara sobre límites y requisitos.
- Documentar cualquier situación inusual.
- Actualizar datos del cliente cuando haya cambios.
