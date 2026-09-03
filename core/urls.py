from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('explorar/', views.explorar, name='explorar'),
    path('quadra/<int:quadra_id>/', views.detalhes_quadra, name='detalhes_quadra'),
    path('campeonatos/', views.campeonatos, name='campeonatos'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('admin/cadastrar_quadra/', views.admin_cadastrar_quadra, name='admin_cadastrar_quadra'),
    path('quadra/entrar/', views.entrar_na_partida, name='entrar_na_partida'),
    path('quadra/sair/', views.sair_da_partida, name='sair_da_partida'),
    path('api/quadra/<int:quadra_id>/horarios/<str:data_selecionada>/', views.api_get_horarios_por_data, name='api_horarios'),
    path('reservar/<int:horario_id>/', views.reservar, name='reservar'),
    path('confirmar_reserva/', views.confirmar_reserva, name='confirmar_reserva'),
    path('finalizar_pix/', views.finalizar_pix, name='finalizar_pix'),
    path('social/', views.social, name='social'),
    path('postar/', views.postar, name='postar'),
    path('social/editar/', views.editar_perfil, name='editar_perfil'),
    path('mensagem/', views.mensagem, name='mensagem'),
    path('perfil/', views.perfil, name='perfil'),
    path('suporte/', views.suporte, name='suporte'),
]
