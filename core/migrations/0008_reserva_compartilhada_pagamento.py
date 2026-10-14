from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def marcar_pagamentos_anteriores(apps, schema_editor):
    ReservaJogador = apps.get_model('core', 'ReservaJogador')
    ReservaJogador.objects.filter(status='pago').update(metodo_pagamento='sistema')


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0007_interacoes_posts'),
    ]

    operations = [
        migrations.AddField(
            model_name='horario',
            name='responsavel_reserva',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='horarios_reservados', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='horario',
            name='aceita_convidados',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='reservajogador',
            name='metodo_pagamento',
            field=models.CharField(choices=[('sistema', 'Pago pelo sistema'), ('caixa', 'Pagar no caixa')], default='caixa', max_length=10),
        ),
        migrations.RunPython(marcar_pagamentos_anteriores, migrations.RunPython.noop),
    ]
