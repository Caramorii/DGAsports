import json
from datetime import date, timedelta

from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Horario, Quadra, ReservaJogador, Usuario


class SeedDataTests(TestCase):
    def test_seed_cria_exemplo_privado_para_fluxo_de_reserva(self):
        call_command('seed_data')

        quadra = Quadra.objects.get(nome='Quadra Amazonas')
        self.assertEqual(quadra.tipo, 'privada')
        self.assertEqual(Quadra.objects.filter(cidade='Franca').count(), 2)
        self.assertEqual(Quadra.objects.filter(cidade='Morro Agudo').count(), 1)


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

    def test_resumo_privado_mostra_participantes_preco_e_formas_de_pagamento(self):
        self.quadra.tipo = 'privada'
        self.quadra.save(update_fields=['tipo'])
        self.horario.data = timezone.localdate() + timedelta(days=1)
        self.horario.save(update_fields=['data'])
        self.client.force_login(self.usuario)

        response = self.client.get(
            reverse('reservar', args=[self.horario.id]),
            {'esporte': 'Futebol'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Resumo da reserva')
        self.assertContains(response, 'Atleta (Você)')
        self.assertContains(response, 'R$ 20,00')
        self.assertContains(response, 'PIX pelo site')
        self.assertContains(response, 'Pagar na quadra')

    def test_resumo_de_partida_privada_lista_quem_ja_vai_jogar(self):
        outro = Usuario.objects.create_user(
            email='convidado@example.com', nome='Convidado', cidade='Franca', password='senha-segura-123'
        )
        self.quadra.tipo = 'privada'
        self.quadra.save(update_fields=['tipo'])
        self.horario.data = timezone.localdate() + timedelta(days=1)
        self.horario.esporte_reservado = 'Futebol'
        self.horario.max_jogadores = 5
        self.horario.aceita_convidados = True
        self.horario.save(update_fields=['data', 'esporte_reservado', 'max_jogadores', 'aceita_convidados'])
        self.horario.responsavel_reserva = outro
        self.horario.save(update_fields=['responsavel_reserva'])
        ReservaJogador.objects.create(usuario=outro, horario=self.horario)
        self.client.force_login(self.usuario)

        response = self.client.get(
            reverse('reservar', args=[self.horario.id]),
            {'esporte': 'Futebol'},
        )

        self.assertContains(response, 'Convidado')
        self.assertContains(response, 'Atleta (Você)')
        self.assertContains(response, '2 / 5')
        self.assertNotContains(response, 'value="caixa"')

    def test_fluxo_pix_preserva_modo_ate_confirmar_reserva(self):
        self.quadra.tipo = 'privada'
        self.quadra.save(update_fields=['tipo'])
        self.horario.data = timezone.localdate() + timedelta(days=1)
        self.horario.save(update_fields=['data'])
        self.client.force_login(self.usuario)

        pagamento = self.client.post(reverse('confirmar_reserva'), {
            'metodo': 'pix',
            'modo_reserva': 'nova',
            'horario_id': self.horario.id,
            'esporte_selecionado': 'Futebol',
        })

        self.assertEqual(pagamento.status_code, 200)
        self.assertContains(pagamento, 'name="modo_reserva" value="nova"')
        confirmacao = self.client.post(reverse('finalizar_pix'), {
            'modo_reserva': 'nova',
            'horario_id': self.horario.id,
            'esporte_selecionado': 'Futebol',
        })

        self.assertRedirects(confirmacao, reverse('minhas_reservas'))
        self.assertTrue(ReservaJogador.objects.filter(usuario=self.usuario, horario=self.horario).exists())

    def test_reserva_publica_funciona_com_csrf_apos_abrir_detalhes(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.usuario)

        page = client.get(reverse('detalhes_quadra', args=[self.quadra.id]))
        csrf_token = client.cookies['csrftoken'].value
        response = client.post(
            reverse('entrar_na_partida'),
            data=json.dumps({
                'horario_id': self.horario.id,
                'esporte_selecionado': 'Futebol',
            }),
            content_type='application/json',
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(page.status_code, 200)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'sucesso')
        self.assertTrue(ReservaJogador.objects.filter(usuario=self.usuario, horario=self.horario).exists())

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

    def test_confirmacao_de_reserva_privada(self):
        self.quadra.tipo = 'privada'
        self.quadra.save(update_fields=['tipo'])
        self.client.force_login(self.usuario)
        response = self.client.post(reverse('confirmar_reserva'), {
            'metodo': 'caixa',
            'horario_id': self.horario.id,
            'esporte_selecionado': 'Futebol',
        })
        self.assertRedirects(response, reverse('minhas_reservas'))
        self.assertTrue(ReservaJogador.objects.filter(usuario=self.usuario, horario=self.horario).exists())

    def test_cancelamento_libera_modalidade(self):
        reserva = ReservaJogador.objects.create(usuario=self.usuario, horario=self.horario)
        self.horario.esporte_reservado = 'Futebol'
        self.horario.save(update_fields=['esporte_reservado'])
        self.client.force_login(self.usuario)
        response = self.client.post(reverse('cancelar_reserva', args=[reserva.id]))
        self.assertRedirects(response, reverse('minhas_reservas'))
        self.horario.refresh_from_db()
        self.assertIsNone(self.horario.esporte_reservado)


class DetalhesQuadraTests(TestCase):
    def test_quadras_publicas_exibem_confirmacao_com_participantes_sem_pagamento(self):
        quadra = Quadra.objects.create(nome='Praça Esportiva', cidade='Franca', esporte='Futebol')
        horario = Horario.objects.create(
            quadra=quadra,
            data=timezone.localdate() + timedelta(days=1),
            hora_texto='18:00 - 19:00',
            esporte_reservado='Futebol',
        )
        outro = Usuario.objects.create_user(
            email='jogador@example.com', nome='Outro Jogador', cidade='Franca', password='senha-segura-123'
        )
        ReservaJogador.objects.create(usuario=outro, horario=horario)

        response = self.client.get(reverse('detalhes_quadra', args=[quadra.id]))

        self.assertContains(response, 'Confirmar participação na quadra pública')
        self.assertContains(response, 'somente quem confirmou participação pelo DGA Sports')
        self.assertContains(response, 'Outro Jogador')
        self.assertNotContains(response, 'PIX pelo site')
        self.assertEqual(ReservaJogador.objects.count(), 1)

    def test_datas_usam_valor_iso_no_botao_e_api_carrega_horarios_do_dia(self):
        data_selecionada = date(2026, 11, 6)
        quadra = Quadra.objects.create(nome='Arena', cidade='Franca', esporte='Futebol')
        horario = Horario.objects.create(
            quadra=quadra,
            data=data_selecionada,
            hora_texto='18:00 - 19:00',
        )

        response = self.client.get(reverse('detalhes_quadra', args=[quadra.id]))

        self.assertContains(response, f'data-data="{data_selecionada.isoformat()}"')
        self.assertContains(response, 'sexta-feira · 06/11')
        self.assertNotContains(response, "'valor':")

        response = self.client.get(
            reverse('api_horarios', args=[quadra.id, data_selecionada.isoformat()])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['horarios'][0]['id'], horario.id)
