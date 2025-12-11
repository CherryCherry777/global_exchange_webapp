Documentación de Módulos
=========================

Esta sección centraliza la documentación por módulos de la aplicación. Aquí podrás encontrar, por módulo, explicaciones de su propósito, las principales funciones/clases, ejemplos de uso y enlaces a las vistas o formularios relacionados.

Estructura
---------

.. toctree::
   :maxdepth: 1

   modulos_documentacion
   modulo_usuarios
   modulo_roles
   modulo_administrar_roles
   modulo_clientes
   modulo_asignacion_cliente
   modulo_categorias
   modulo_monedas
   modulo_cotizaciones
   modulo_limites_intercambio
   modulo_reportes_transacciones
   modulo_metodos_pago
   modulo_metodos_cobro
   modulo_entidades_pago

Páginas futuras (plantilla)
---------------------------

Cuando quieras añadir la documentación de un módulo específico, crea un archivo en `docs/source/` con el nombre `modulo_<nombre>.rst` y agrégalo a este `toctree`.

Ejemplo mínimo de archivo de módulo (guardar como `modulo_ejemplo.rst`):

.. code-block:: rst

   Módulo Ejemplo
   --------------

   Descripción breve del módulo.

   .. automodule:: webapp.ejemplo
      :members:

Notas para colaboradores
-----------------------

- Mantén los archivos en `docs/source/` y agrega la referencia aquí para que se incluyan en la navegación.
- Si prefieres una carpeta dedicada (`docs/source/modulos/`), puedo mover los archivos y actualizar la configuración.
