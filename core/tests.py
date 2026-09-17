import json
from datetime import date

from django.test import TestCase
from django.urls import reverse

from .models import Horario, Quadra, ReservaJogador, Usuario


class ReservaPartidaTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            email='atleta@example.com', nome='Atleta', cidade='Franca', password='senha-segura-123'
        )
        self.quadra = Quadra.objects.create(nome='Arena', cidade='Franca', esporte='Futebol, Basquete')
        self.horario = Horario.objects.create(
            quadra=self.quadra, data=date.today(), hora_texto='18:00 - 19:00', max_jogadores=1, preco=20
        )

    def test_entrada_reserva_vaga_e_modalidade(self):
        self.client.force_login(self.usuario)
        response = self.client.post(
            reverse('entrar_na_partida'),
            data=json.dumps({'horario_id': self.horario.id, 'esporte_selecionado': 'Futebol'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ReservaJogador.objects.count(), 1)
        self.horario.refresh_from_db()
        self.assertEqual(self.horario.esporte_reservado, 'Futebol')

    def test_entrada_recusa_quando_lotado(self):
        outro = Usuario.objects.create_user(
            email='outro@example.com', nome='Outro', cidade='Franca', password='senha-segura-123'
        )
        ReservaJogador.objects.create(usuario=outro, horario=self.horario)
        self.client.force_login(self.usuario)
        response = self.client.post(
            reverse('entrar_na_partida'),
            data=json.dumps({'horario_id': self.horario.id, 'esporte_selecionado': 'Futebol'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(ReservaJogador.objects.count(), 1)

    def test_avaliacao_exige_participacao_na_quadra(self):
        self.client.force_login(self.usuario)
        response = self.client.post(reverse('avaliar_quadra', args=[self.quadra.id]), {'nota': 5})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.quadra.avaliacoes.exists())

    def test_avaliacao_depois_de_reserva(self):
        ReservaJogador.objects.create(usuario=self.usuario, horario=self.horario)
        self.client.force_login(self.usuario)
        response = self.client.post(
            reverse('avaliar_quadra', args=[self.quadra.id]), {'nota': 5, 'comentario': 'Ótima quadra'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.quadra.avaliacoes.get().nota, 5)
