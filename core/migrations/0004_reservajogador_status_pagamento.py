from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('core', '0003_quadra_proprietario_destaque_avaliacao')]

    operations = [
        migrations.AddField(
            model_name='reservajogador', name='status',
            field=models.CharField(choices=[('pendente', 'Pendente de pagamento'), ('pago', 'Pago')], default='pendente', max_length=10),
        ),
        migrations.AddField(
            model_name='reservajogador', name='criada_em', field=models.DateTimeField(auto_now_add=True), preserve_default=False,
        ),
        migrations.AddField(
            model_name='reservajogador', name='pago_em', field=models.DateTimeField(blank=True, null=True),
        ),
    ]
