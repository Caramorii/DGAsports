from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('core', '0001_initial')]

    operations = [
        migrations.AddField(
            model_name='quadra',
            name='tipo',
            field=models.CharField(
                choices=[('publica', 'Pública'), ('privada', 'Privada')],
                default='publica',
                max_length=10,
            ),
        ),
    ]
