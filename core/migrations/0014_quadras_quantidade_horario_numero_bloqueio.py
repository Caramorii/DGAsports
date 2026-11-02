from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_usuario_eh_proprietario'),
    ]

    operations = [
        migrations.AddField(
            model_name='quadra',
            name='quantidade_quadras',
            field=models.PositiveSmallIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='horario',
            name='numero_quadra',
            field=models.PositiveSmallIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='horario',
            name='indisponivel',
            field=models.BooleanField(default=False),
        ),
    ]
