from django.db import migrations

def create_default_tausers(apps, schema_editor):
    Tauser = apps.get_model("webapp", "Tauser")
    TipoPago = apps.get_model("webapp", "TipoPago")
    TipoCobro = apps.get_model("webapp", "TipoCobro")

    default_names = [
        "Tauser 1", "Tauser 2", "Tauser 3", "Tauser 4", "Tauser 5",
        "Tauser 6", "Tauser 7", "Tauser 8", "Tauser 9", "Tauser 10"
    ]

    # Filtrar tipo_pago y tipo_cobro con "tauser" en el nombre
    default_tipo_pago = TipoPago.objects.filter(nombre__icontains="tauser", activo=True).first()
    default_tipo_cobro = TipoCobro.objects.filter(nombre__icontains="tauser", activo=True).first()

    i = 1
    for name in default_names:
        Tauser.objects.create(
            nombre=name,
            activo=True,
            ubicacion=f"Sucursal {i}",
            tipo_pago=default_tipo_pago,
            tipo_cobro=default_tipo_cobro
        )
        i += 1

class Migration(migrations.Migration):

    dependencies = [
        ('webapp', '0038_tauser'),  # Cambiar por la migración previa de tu app
    ]

    operations = [
        migrations.RunPython(create_default_tausers),
    ]
