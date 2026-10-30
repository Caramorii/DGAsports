from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0006_quadrasituacao_comentario'),
    ]

    operations = [
        migrations.CreateModel(
            name='CurtidaPost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('criada_em', models.DateTimeField(auto_now_add=True)),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='curtidas', to='core.post')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='curtidas_posts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'curtidas_posts',
                'ordering': ['criada_em'],
            },
        ),
        migrations.AddConstraint(
            model_name='curtidapost',
            constraint=models.UniqueConstraint(fields=('post', 'usuario'), name='curtida_unica_por_usuario_post'),
        ),
        migrations.CreateModel(
            name='ComentarioPost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('texto', models.CharField(max_length=1000)),
                ('criada_em', models.DateTimeField(auto_now_add=True)),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comentarios', to='core.post')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comentarios_posts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'comentarios_posts',
                'ordering': ['criada_em'],
            },
        ),
    ]
