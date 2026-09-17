from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Usuario, Quadra, Horario, ReservaJogador, PerfilSocial, Post, Avaliacao


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    list_display = ('email', 'nome', 'cidade', 'is_staff', 'is_active')
    search_fields = ('email', 'nome')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Dados pessoais', {'fields': ('nome', 'cidade')}),
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nome', 'cidade', 'password1', 'password2'),
        }),
    )


@admin.register(Quadra)
class QuadraAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cidade', 'estado', 'esporte', 'tipo', 'proprietario', 'destaque')
    search_fields = ('nome', 'cidade')


@admin.register(Horario)
class HorarioAdmin(admin.ModelAdmin):
    list_display = ('quadra', 'data', 'hora_texto', 'preco', 'max_jogadores')
    list_filter = ('data', 'quadra')


@admin.register(ReservaJogador)
class ReservaJogadorAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'horario')


@admin.register(PerfilSocial)
class PerfilSocialAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'usuario_social')


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'tipo', 'data_postagem')
    list_filter = ('tipo',)


@admin.register(Avaliacao)
class AvaliacaoAdmin(admin.ModelAdmin):
    list_display = ('quadra', 'usuario', 'nota', 'criada_em')
    list_filter = ('nota',)
