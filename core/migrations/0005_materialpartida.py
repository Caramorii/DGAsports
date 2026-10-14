from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0004_reservajogador_status_pagamento'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MaterialPartida',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item', models.CharField(max_length=100)),
                ('criada_em', models.DateTimeField(auto_now_add=True)),
                ('horario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='materiais', to='core.horario')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='materiais_partidas', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'materiais_partidas',
                'ordering': ['item'],
                'unique_together': {('horario', 'item')},
            },
        ),
    ]
