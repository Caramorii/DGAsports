from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('core', '0002_quadra_tipo')]

    operations = [
        migrations.AddField(
            model_name='quadra', name='destaque', field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='quadra', name='proprietario',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='quadras', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='Avaliacao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nota', models.PositiveSmallIntegerField()),
                ('comentario', models.TextField(blank=True)),
                ('criada_em', models.DateTimeField(auto_now=True)),
                ('quadra', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='avaliacoes', to='core.quadra')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='avaliacoes', to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'avaliacoes', 'ordering': ['-criada_em'], 'unique_together': {('usuario', 'quadra')}},
        ),
    ]
