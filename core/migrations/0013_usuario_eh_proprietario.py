from django.db import migrations, models


def marcar_proprietarios_existentes(apps, schema_editor):
    Usuario = apps.get_model('core', 'Usuario')
    Quadra = apps.get_model('core', 'Quadra')
    ids = Quadra.objects.exclude(proprietario_id=None).values_list('proprietario_id', flat=True).distinct()
    Usuario.objects.filter(pk__in=ids).update(eh_proprietario=True)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_materialgrupopublico'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='eh_proprietario',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(marcar_proprietarios_existentes, migrations.RunPython.noop),
    ]
