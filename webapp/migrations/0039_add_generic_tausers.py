from django.db import migrations

def create_default_tausers(apps, schema_editor):
    Tauser = apps.get_model("webapp", "Tauser")

    default_names = [
        "Tauser 1", "Tauser 2", "Tauser 3", "Tauser 4", "Tauser 5",
        "Tauser 6", "Tauser 7", "Tauser 8", "Tauser 9", "Tauser 10"
    ]

    i = 1
    for name in default_names:
        Tauser.objects.create(
            nombre=name,
            activo=True,
            ubicacion=f"Sucursal {i}",
            # No asignamos tipo_pago ni tipo_cobro
        )
        i += 1

class Migration(migrations.Migration):

    dependencies = [
        ('webapp', '0038_tauser'),  # Cambiar por la migración previa de tu app
    ]

    operations = [
        migrations.RunPython(create_default_tausers),
    ]
