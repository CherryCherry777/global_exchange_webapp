from django.db import migrations

def create_generic_entities(apps, schema_editor):
    Entidad = apps.get_model('webapp', 'Entidad')
    Billetera = apps.get_model('webapp', 'Billetera')
    CuentaBancaria = apps.get_model('webapp', 'CuentaBancaria')
    Cheque = apps.get_model('webapp', 'Cheque')

    # Crear entidades genéricas si no existen
    banco, _ = Entidad.objects.get_or_create(nombre='Banco Generico')
    billetera_ent, _ = Entidad.objects.get_or_create(nombre='Billetera Generica')

    # Asignar entidad a los registros existentes si están vacíos
    Billetera.objects.filter(entidad__isnull=True).update(entidad=billetera_ent)
    CuentaBancaria.objects.filter(entidad__isnull=True).update(entidad=banco)
    Cheque.objects.filter(entidad__isnull=True).update(entidad=banco)

class Migration(migrations.Migration):

    dependencies = [
        ('webapp', '0029_billetera_entidad_billeteracobro_entidad_and_more'),
    ]

    operations = [
        migrations.RunPython(create_generic_entities),
    ]
