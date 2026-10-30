from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


class UsuarioManager(BaseUserManager):
    def create_user(self, email, nome, cidade, password=None, **extra_fields):
        if not email:
            raise ValueError('O e-mail é obrigatório')
        email = self.normalize_email(email)
        user = self.model(email=email, nome=nome, cidade=cidade, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nome, cidade, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, nome, cidade, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    nome = models.CharField(max_length=150)
    cidade = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UsuarioManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nome', 'cidade']

    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

    def __str__(self):
        return self.nome


class Quadra(models.Model):
    TIPO_CHOICES = [
        ('publica', 'Pública'),
        ('privada', 'Privada'),
    ]

    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True, null=True)
    localizacao = models.CharField(max_length=255, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=50, blank=True, null=True)
    esporte = models.CharField(max_length=200, blank=True, null=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='publica')
    proprietario = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='quadras'
    )
    destaque = models.BooleanField(default=False)
    foto = models.CharField(max_length=500, blank=True, null=True)
    situacao = models.CharField(max_length=200, blank=True, default='Em boas condições')
    comentario_admin = models.TextField(blank=True)

    class Meta:
        db_table = 'quadras'
        verbose_name = 'Quadra'
        verbose_name_plural = 'Quadras'

    def __str__(self):
        return self.nome

    @property
    def lista_esportes(self):
        if self.esporte:
            return [e.strip() for e in self.esporte.split(',')]
        return []


class Horario(models.Model):
    quadra = models.ForeignKey(Quadra, on_delete=models.CASCADE, related_name='horarios')
    data = models.DateField()
    hora_texto = models.CharField(max_length=50)
    max_jogadores = models.IntegerField(default=12)
    preco = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    esporte_reservado = models.CharField(max_length=100, blank=True, null=True)
    responsavel_reserva = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='horarios_reservados'
    )
    aceita_convidados = models.BooleanField(default=False)

    class Meta:
        db_table = 'horarios'
        verbose_name = 'Horário'
        verbose_name_plural = 'Horários'
        ordering = ['data', 'hora_texto']

    def __str__(self):
        return f"{self.quadra.nome} - {self.data} {self.hora_texto}"

    @property
    def jogadores_atuais(self):
        return self.reservas.count()


class ReservaJogador(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente de pagamento'),
        ('pago', 'Pago'),
    ]
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='reservas')
    horario = models.ForeignKey(Horario, on_delete=models.CASCADE, related_name='reservas')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pendente')
    METODO_PAGAMENTO_CHOICES = [
        ('sistema', 'Pago pelo sistema'),
        ('caixa', 'Pagar no caixa'),
    ]
    metodo_pagamento = models.CharField(max_length=10, choices=METODO_PAGAMENTO_CHOICES, default='caixa')
    criada_em = models.DateTimeField(auto_now_add=True)
    pago_em = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'reservas_jogadores'
        unique_together = ('usuario', 'horario')
        verbose_name = 'Reserva de Jogador'
        verbose_name_plural = 'Reservas de Jogadores'

    def __str__(self):
        return f"{self.usuario.nome} em {self.horario}"


class GrupoQuadraPublica(models.Model):
    quadra = models.ForeignKey(Quadra, on_delete=models.CASCADE, related_name='grupos_publicos')
    esporte = models.CharField(max_length=100)
    data_encontro = models.DateField(blank=True, null=True)
    hora_inicio = models.TimeField(blank=True, null=True)
    hora_fim = models.TimeField(blank=True, null=True)
    criador = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='grupos_criados')
    participantes = models.ManyToManyField(Usuario, through='ParticipanteGrupoPublico', related_name='grupos_publicos')
    criado_em = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'grupos_quadras_publicas'
        ordering = ['-criado_em']

    def __str__(self):
        return f"{self.quadra.nome} - {self.esporte}"


class ParticipanteGrupoPublico(models.Model):
    grupo = models.ForeignKey(GrupoQuadraPublica, on_delete=models.CASCADE, related_name='inscricoes')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='participacoes_grupo')
    presencas = models.PositiveIntegerField(default=1)
    ultima_confirmacao = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'participantes_grupo_publico'
        constraints = [models.UniqueConstraint(fields=['grupo', 'usuario'], name='unico_usuario_por_grupo_publico')]


class MaterialGrupoPublico(models.Model):
    grupo = models.ForeignKey(GrupoQuadraPublica, on_delete=models.CASCADE, related_name='materiais')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='materiais_grupos_publicos')
    item = models.CharField(max_length=100)
    criado_em = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'materiais_grupos_publicos'
        ordering = ['criado_em', 'id']

    def __str__(self):
        return f"{self.item} - {self.grupo}"


class PerfilSocial(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='perfil_social')
    usuario_social = models.CharField(max_length=100, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    foto_perfil = models.CharField(max_length=500, default='images/default_avatar.png')

    class Meta:
        db_table = 'perfis_sociais'
        verbose_name = 'Perfil Social'
        verbose_name_plural = 'Perfis Sociais'

    def __str__(self):
        return self.usuario_social or self.usuario.nome


class Post(models.Model):
    TIPO_CHOICES = [
        ('atleta', 'Atleta'),
        ('admin', 'Admin'),
    ]
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='posts')
    texto = models.TextField(blank=True, null=True)
    imagem = models.CharField(max_length=500, blank=True, null=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='atleta')
    data_postagem = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'posts'
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'
        ordering = ['-data_postagem']

    def __str__(self):
        return f"Post de {self.usuario.nome} - {self.data_postagem}"


class CurtidaPost(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='curtidas')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='curtidas_posts')
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'curtidas_posts'
        constraints = [models.UniqueConstraint(fields=['post', 'usuario'], name='curtida_unica_por_usuario_post')]
        ordering = ['criada_em']


class ComentarioPost(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comentarios')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='comentarios_posts')
    texto = models.CharField(max_length=1000)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'comentarios_posts'
        ordering = ['criada_em']

    def __str__(self):
        return f"Comentário de {self.usuario.nome} na publicação {self.post_id}"


class Avaliacao(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='avaliacoes')
    quadra = models.ForeignKey(Quadra, on_delete=models.CASCADE, related_name='avaliacoes')
    nota = models.PositiveSmallIntegerField()
    comentario = models.TextField(blank=True)
    criada_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'avaliacoes'
        unique_together = ('usuario', 'quadra')
        ordering = ['-criada_em']

    def __str__(self):
        return f"{self.quadra.nome}: {self.nota}/5"


class MaterialPartida(models.Model):
    """Indica quem vai levar cada item para uma partida comunitária."""
    horario = models.ForeignKey(Horario, on_delete=models.CASCADE, related_name='materiais')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='materiais_partidas')
    item = models.CharField(max_length=100)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'materiais_partidas'
        ordering = ['item']
        unique_together = ('horario', 'item')

    def __str__(self):
        return f"{self.item} — {self.usuario.nome}"


class ComentarioQuadra(models.Model):
    quadra = models.ForeignKey(Quadra, on_delete=models.CASCADE, related_name='comentarios')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='comentarios_quadra')
    texto = models.TextField(max_length=1000)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'comentarios_quadras'
        ordering = ['-criada_em']

    def __str__(self):
        return f"Comentário de {self.usuario.nome} em {self.quadra.nome}"
