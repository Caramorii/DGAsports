from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    Avaliacao,
    DivisaoQuadra,
    Horario,
    PerfilSocial,
    Post,
    Quadra,
    ReservaJogador,
    Usuario,
)


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    list_display = ("email", "nome", "cidade", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active", "is_superuser", "groups")
    search_fields = ("email", "nome", "cidade")
    ordering = ("email",)
    list_per_page = 25

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Dados pessoais", {"fields": ("nome", "cidade")}),
        (
            "Permissoes",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Datas", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "nome", "cidade", "password1", "password2"),
            },
        ),
    )


class DivisaoQuadraInline(admin.TabularInline):
    model = DivisaoQuadra
    extra = 0


@admin.register(Quadra)
class QuadraAdmin(admin.ModelAdmin):
    inlines = [DivisaoQuadraInline]
    list_display = (
        "nome",
        "cidade",
        "estado",
        "esporte",
        "tipo",
        "proprietario",
        "destaque",
    )
    list_filter = ("estado", "esporte", "tipo", "destaque")
    search_fields = ("nome", "cidade", "estado", "proprietario__email")
    list_per_page = 25


@admin.register(Horario)
class HorarioAdmin(admin.ModelAdmin):
    list_display = ("quadra", "data", "hora_texto", "preco", "max_jogadores")
    list_filter = ("data", "quadra")
    date_hierarchy = "data"
    search_fields = ("quadra__nome",)
    list_per_page = 25


@admin.register(ReservaJogador)
class ReservaJogadorAdmin(admin.ModelAdmin):
    list_display = ("usuario", "horario", "status", "metodo_pagamento", "criada_em")
    list_filter = ("status", "metodo_pagamento", "horario__data")
    search_fields = ("usuario__email", "usuario__nome", "horario__quadra__nome")
    date_hierarchy = "criada_em"
    list_select_related = ("usuario", "horario", "horario__quadra")
    list_per_page = 25


@admin.register(PerfilSocial)
class PerfilSocialAdmin(admin.ModelAdmin):
    list_display = ("usuario", "usuario_social")
    search_fields = ("usuario__email", "usuario__nome", "usuario_social")
    list_select_related = ("usuario",)
    list_per_page = 25


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("usuario", "tipo", "data_postagem")
    list_filter = ("tipo",)
    search_fields = ("usuario__email", "usuario__nome", "texto")
    date_hierarchy = "data_postagem"
    list_select_related = ("usuario",)
    list_per_page = 25


@admin.register(Avaliacao)
class AvaliacaoAdmin(admin.ModelAdmin):
    list_display = ("quadra", "usuario", "nota", "criada_em")
    list_filter = ("nota",)
    search_fields = ("quadra__nome", "usuario__email", "usuario__nome")
    date_hierarchy = "criada_em"
    list_select_related = ("quadra", "usuario")
    list_per_page = 25
