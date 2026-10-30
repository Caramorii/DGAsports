from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0005_materialpartida'),
    ]

    operations = [
        migrations.AddField(
            model_name='quadra',
            name='situacao',
            field=models.CharField(blank=True, default='Em boas condições', max_length=200),
        ),
        migrations.AddField(
            model_name='quadra',
            name='comentario_admin',
            field=models.TextField(blank=True),
        ),
        migrations.CreateModel(
            name='ComentarioQuadra',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('texto', models.TextField(max_length=1000)),
                ('criada_em', models.DateTimeField(auto_now_add=True)),
                ('quadra', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comentarios', to='core.quadra')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comentarios_quadra', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'comentarios_quadras',
                'ordering': ['-criada_em'],
            },
        ),
    ]
