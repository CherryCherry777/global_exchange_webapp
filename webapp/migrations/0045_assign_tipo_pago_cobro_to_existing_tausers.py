from django.db import migrations

def assign_tipo_pago_cobro_to_existing_tausers(apps, schema_editor):
    Tauser = apps.get_model("webapp", "Tauser")
    TipoPago = apps.get_model("webapp", "TipoPago")
    TipoCobro = apps.get_model("webapp", "TipoCobro")

    # Buscar los tipos existentes
    default_tipo_pago = TipoPago.objects.filter(nombre__icontains="tauser", activo=True).first()
    default_tipo_cobro = TipoCobro.objects.filter(nombre__icontains="tauser", activo=True).first()

    if not default_tipo_pago or not default_tipo_cobro:
        print("No se encontró TipoPago o TipoCobro con 'tauser'. No se actualizarán Tauser.")
        return

    # Actualizar todos los Tauser existentes de una sola vez
    Tauser.objects.all().update(
        tipo_pago=default_tipo_pago,
        tipo_cobro=default_tipo_cobro
    )

class Migration(migrations.Migration):

    dependencies = [
        ('webapp', '0044_customuser_unsubscribe_token'),
    ]

    operations = [
        migrations.RunPython(assign_tipo_pago_cobro_to_existing_tausers),
    ]

