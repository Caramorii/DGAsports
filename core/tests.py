import json
from datetime import date, timedelta

from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import ComentarioQuadra, DivisaoQuadra, Horario, Quadra, ReservaJogador, Usuario


class SeedDataTests(TestCase):
    def test_seed_cria_exemplo_privado_para_fluxo_de_reserva(self):
        call_command('seed_data')

        quadra = Quadra.objects.get(nome='Quadra Amazonas')
        self.assertEqual(quadra.tipo, 'privada')
        self.assertEqual(Quadra.objects.filter(cidade='Franca').count(), 6)
        self.assertEqual(Quadra.objects.filter(cidade='Morro Agudo').count(), 3)


class ReservaPartidaTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            email='atleta@example.com', nome='Atleta', cidade='Franca', password='senha-segura-123'
        )
        self.quadra = Quadra.objects.create(nome='Arena', cidade='Franca', esporte='Futebol, Basquete')
        self.horario = Horario.objects.create(
            quadra=self.quadra,
            data=timezone.localdate() + timedelta(days=1),
            hora_texto='18:00 - 19:00',
            max_jogadores=1,
            preco=20,
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
        self.assertEqual(
            response.context['voltar_url'],
            f"/quadra/{self.quadra.id}/?data={self.horario.data.isoformat()}&quadra=1",
        )

    def test_erro_ao_confirmar_reserva_retorna_para_data_e_quadra_do_horario(self):
        self.quadra.tipo = 'privada'
        self.quadra.quantidade_quadras = 2
        self.quadra.save(update_fields=['tipo', 'quantidade_quadras'])
        self.horario.numero_quadra = 2
        self.horario.save(update_fields=['numero_quadra'])
        self.client.force_login(self.usuario)

        response = self.client.post(reverse('confirmar_reserva'), {
            'metodo': 'caixa',
            'horario_id': self.horario.id,
            'esporte_selecionado': 'Esporte inválido',
        })

        self.assertRedirects(
            response,
            f"/quadra/{self.quadra.id}/?data={self.horario.data.isoformat()}&quadra=2",
            fetch_redirect_response=False,
        )


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

    def _preparar_horario_privado(self):
        self.quadra.tipo = 'privada'
        self.quadra.localizacao = 'Rua das Palmeiras, 250'
        self.quadra.descricao = 'Quadra coberta'
        self.quadra.save(update_fields=['tipo', 'localizacao', 'descricao'])
        self.client.force_login(self.usuario)

    def test_confirmacao_privada_mostra_formas_de_pagamento_e_dados_da_quadra(self):
        self._preparar_horario_privado()

        response = self.client.get(reverse('reservar', args=[self.horario.id]), {'esporte': 'Futebol'})

        self.assertContains(response, 'value="credito"')
        self.assertContains(response, 'value="debito"')
        self.assertContains(response, 'Reserva provisória')
        self.assertContains(response, 'Rua das Palmeiras, 250')
        self.assertContains(response, 'Quadra coberta')

    def test_pagamento_com_cartao_registra_metodo_escolhido(self):
        self._preparar_horario_privado()

        for metodo, rotulo in (('credito', 'cartão de crédito'), ('debito', 'cartão de débito')):
            with self.subTest(metodo=metodo):
                dados = {
                    'metodo': metodo,
                    'modo_reserva': 'nova',
                    'horario_id': self.horario.id,
                    'esporte_selecionado': 'Futebol',
                }
                pagina = self.client.post(reverse('confirmar_reserva'), dados)
                self.assertContains(pagina, rotulo)
                self.assertContains(pagina, f'name="metodo" value="{metodo}"')

                confirmacao = self.client.post(reverse('finalizar_pix'), dados)

                self.assertRedirects(confirmacao, reverse('minhas_reservas'))
                reserva = ReservaJogador.objects.get(usuario=self.usuario, horario=self.horario)
                self.assertEqual(reserva.metodo_pagamento, metodo)
                self.assertEqual(reserva.status, 'pago')
                self.assertIsNotNone(reserva.pago_em)
                self.client.post(reverse('cancelar_reserva', args=[reserva.id]))

    def test_pagamento_pix_registra_metodo_pix(self):
        self._preparar_horario_privado()

        self.client.post(reverse('finalizar_pix'), {
            'modo_reserva': 'nova',
            'horario_id': self.horario.id,
            'esporte_selecionado': 'Futebol',
        })

        reserva = ReservaJogador.objects.get(usuario=self.usuario, horario=self.horario)
        self.assertEqual(reserva.metodo_pagamento, 'pix')

    def test_forma_de_pagamento_invalida_nao_cria_reserva(self):
        self._preparar_horario_privado()
        dados = {
            'metodo': 'boleto',
            'modo_reserva': 'nova',
            'horario_id': self.horario.id,
            'esporte_selecionado': 'Futebol',
        }

        for rota in ('confirmar_reserva', 'finalizar_pix'):
            with self.subTest(rota=rota):
                response = self.client.post(reverse(rota), dados)
                self.assertEqual(response.status_code, 302)
                self.assertFalse(ReservaJogador.objects.exists())

    def _estado_exibido(self):
        return self.client.get(
            reverse('api_horarios', args=[self.quadra.id, self.horario.data.isoformat()])
        ).json()['horarios'][0]

    def _reservar(self, status, metodo):
        ReservaJogador.objects.create(
            usuario=self.usuario, horario=self.horario, status=status, metodo_pagamento=metodo,
        )
        self.horario.esporte_reservado = 'Futebol'
        self.horario.responsavel_reserva = self.usuario
        self.horario.save(update_fields=['esporte_reservado', 'responsavel_reserva'])

    def test_horario_reservado_e_pago_fica_com_estado_pago(self):
        self._preparar_horario_privado()
        self._reservar('pago', 'pix')

        self.assertEqual(self._estado_exibido()['estado'], 'pago')

    def test_horario_para_pagar_no_local_fica_com_estado_pendente(self):
        self._preparar_horario_privado()
        self._reservar('pendente', 'caixa')

        self.assertEqual(self._estado_exibido()['estado'], 'pendente')

    def test_horario_bloqueado_pelo_dono_fica_com_estado_bloqueado(self):
        self._preparar_horario_privado()
        self.horario.indisponivel = True
        self.horario.save(update_fields=['indisponivel'])

        self.assertEqual(self._estado_exibido()['estado'], 'bloqueado')

    def test_horario_que_ja_passou_fica_encerrado_mesmo_bloqueado_ou_reservado(self):
        self._preparar_horario_privado()
        self._reservar('pago', 'pix')
        self.horario.indisponivel = True
        self.horario.data = timezone.localdate() - timedelta(days=1)
        self.horario.save(update_fields=['data', 'indisponivel'])

        horario = self._estado_exibido()

        self.assertEqual(horario['estado'], 'encerrado')
        self.assertEqual(len(horario['jogadores']), 1)

    def test_quadra_publica_com_participante_nao_mostra_pagamento(self):
        self.client.force_login(self.usuario)
        self._reservar('pendente', 'caixa')

        self.assertEqual(self._estado_exibido()['estado'], 'livre')

    def _outro_perfil(self):
        outro = Usuario.objects.create_user(
            email='outro@example.com', nome='Outro', cidade='Franca', password='senha-segura-123'
        )
        self.client.force_login(outro)
        return outro

    def test_reserva_paga_de_outro_perfil_nao_aparece_como_minha(self):
        self._preparar_horario_privado()
        self._reservar('pago', 'pix')
        self._outro_perfil()

        horario = self._estado_exibido()

        self.assertEqual(horario['estado'], 'ocupado')
        self.assertEqual(horario['usuario_na_partida'], 0)
        self.assertEqual(horario['meu_status'], '')
        self.assertEqual(horario['meu_metodo'], '')

    def test_visitante_nao_ve_reserva_de_outra_pessoa_como_paga(self):
        self._preparar_horario_privado()
        self._reservar('pago', 'pix')
        self.client.logout()

        self.assertEqual(self._estado_exibido()['estado'], 'ocupado')

    def test_dados_de_pagamento_de_outra_pessoa_nao_sao_enviados(self):
        self._preparar_horario_privado()
        self._reservar('pendente', 'caixa')
        self._outro_perfil()

        horario = self._estado_exibido()

        self.assertEqual(horario['estado'], 'assumivel')
        self.assertNotIn('status', horario['jogadores'][0])
        self.assertNotIn('metodo_pagamento', horario['jogadores'][0])

    def test_convidado_que_pagou_ve_o_proprio_pagamento(self):
        self._preparar_horario_privado()
        self._reservar('pendente', 'caixa')
        self.horario.aceita_convidados = True
        self.horario.max_jogadores = 4
        self.horario.save(update_fields=['aceita_convidados', 'max_jogadores'])
        outro = self._outro_perfil()
        ReservaJogador.objects.create(usuario=outro, horario=self.horario, status='pago', metodo_pagamento='pix')

        self.assertEqual(self._estado_exibido()['estado'], 'pago')

    def test_outra_pessoa_pode_assumir_reserva_para_pagar_no_local(self):
        self._preparar_horario_privado()
        self._reservar('pendente', 'caixa')
        outro = Usuario.objects.create_user(
            email='outro@example.com', nome='Outro', cidade='Franca', password='senha-segura-123'
        )
        self.assertFalse(self._estado_exibido()['pode_assumir'])
        self.assertEqual(self._estado_exibido()['estado'], 'pendente')

        self.client.force_login(outro)
        horario_cliente = self._estado_exibido()
        self.assertTrue(horario_cliente['pode_assumir'])
        self.assertEqual(horario_cliente['estado'], 'assumivel')

        response = self.client.get(reverse('reservar', args=[self.horario.id]), {'esporte': 'Futebol'})
        self.assertEqual(response.context['modo_reserva'], 'assumir')

    def test_reserva_paga_nao_pode_ser_assumida(self):
        self._preparar_horario_privado()
        self._reservar('pago', 'pix')
        outro = Usuario.objects.create_user(
            email='outro@example.com', nome='Outro', cidade='Franca', password='senha-segura-123'
        )
        self.client.force_login(outro)

        self.assertFalse(self._estado_exibido()['pode_assumir'])

    def _criar_divisoes(self):
        self._preparar_horario_privado()
        self.quadra.quantidade_quadras = 2
        self.quadra.esporte = 'Futevolei, Basquete'
        self.quadra.save(update_fields=['quantidade_quadras', 'esporte'])
        DivisaoQuadra.objects.create(
            quadra=self.quadra, numero=1, nome='Quadra de Areia', superficie='areia', esportes='Futevolei',
        )
        DivisaoQuadra.objects.create(
            quadra=self.quadra, numero=2, nome='Ginásio', superficie='madeira', esportes='Basquete',
        )

    def test_abas_mostram_nome_piso_e_esportes_de_cada_divisao(self):
        self._criar_divisoes()

        response = self.client.get(reverse('detalhes_quadra', args=[self.quadra.id]))

        self.assertContains(response, 'data-numero-quadra="1" data-esportes="Futevolei"')
        self.assertContains(response, 'data-numero-quadra="2" data-esportes="Basquete"')
        self.assertContains(response, 'Quadra de Areia')
        self.assertContains(response, 'Piso de madeira')

    def test_esporte_de_outra_divisao_e_recusado(self):
        self._criar_divisoes()

        response = self.client.get(reverse('reservar', args=[self.horario.id]), {'esporte': 'Basquete'})

        self.assertEqual(response.status_code, 302)
        self.assertFalse(ReservaJogador.objects.exists())

        recusa = self.client.post(reverse('finalizar_pix'), {
            'modo_reserva': 'nova',
            'horario_id': self.horario.id,
            'esporte_selecionado': 'Basquete',
        })

        self.assertEqual(recusa.status_code, 302)
        self.assertFalse(ReservaJogador.objects.exists())

    def test_esporte_da_divisao_e_aceito_e_confirmacao_mostra_o_nome_dela(self):
        self._criar_divisoes()

        response = self.client.get(reverse('reservar', args=[self.horario.id]), {'esporte': 'Futevolei'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Quadra de Areia')
        self.assertContains(response, 'Areia')

    def test_seed_cria_complexo_em_banco_existente_uma_vez_so(self):
        call_command('seed_data')
        call_command('seed_data')

        complexo = Quadra.objects.get(nome='Complexo Esportivo Franca')
        self.assertEqual(complexo.divisoes.count(), 3)
        self.assertEqual(complexo.divisao(3).lista_esportes, ['Futebol'])
        self.assertEqual(
            Horario.objects.filter(quadra=complexo, numero_quadra=2).count(), 7 * 15,
        )

    def test_pagina_nao_desenha_todos_os_horarios_no_html(self):
        response = self.client.get(reverse('detalhes_quadra', args=[self.quadra.id]))

        self.assertContains(response, 'Carregando horários...')
        self.assertNotContains(response, 'card-horario')

    def test_quadra_sem_horarios_mostra_mensagem_em_vez_de_carregar(self):
        quadra = Quadra.objects.create(nome='Sem agenda', cidade='Franca', esporte='Futebol')

        response = self.client.get(reverse('detalhes_quadra', args=[quadra.id]))

        self.assertContains(response, 'Nenhum horário disponível no momento.')
        self.assertNotContains(response, 'Carregando horários...')

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
        self.quadra.tipo = 'privada'
        self.quadra.save(update_fields=['tipo'])
        self.client.force_login(self.usuario)
        response = self.client.post(reverse('avaliar_quadra', args=[self.quadra.id]), {'nota': 5})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.quadra.avaliacoes.exists())

    def test_avaliacao_depois_de_reserva(self):
        self.quadra.tipo = 'privada'
        self.quadra.save(update_fields=['tipo'])
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
        self.horario.data = timezone.localdate() + timedelta(days=1)
        self.horario.save(update_fields=['data'])
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
    def test_resumo_de_quadras_mostra_se_sao_publicas_ou_privadas(self):
        Quadra.objects.create(nome='Praça Pública', cidade='Franca', esporte='Futebol')
        Quadra.objects.create(
            nome='Arena Privada', cidade='Franca', esporte='Basquete', tipo='privada'
        )

        response = self.client.get(reverse('explorar'))

        self.assertContains(response, 'Quadra pública')
        self.assertContains(response, 'Quadra privada')
        self.assertContains(response, 'court-type-badge--publica')
        self.assertContains(response, 'court-type-badge--privada')

    def test_detalhes_restauram_data_e_quadra_da_url(self):
        data_selecionada = timezone.localdate() + timedelta(days=2)
        quadra = Quadra.objects.create(
            nome='Arena', cidade='Franca', esporte='Futebol', tipo='privada', quantidade_quadras=2,
        )
        Horario.objects.create(
            quadra=quadra,
            numero_quadra=2,
            data=data_selecionada,
            hora_texto='18:00 - 19:00',
        )
        Horario.objects.create(
            quadra=quadra,
            numero_quadra=1,
            data=data_selecionada - timedelta(days=1),
            hora_texto='18:00 - 19:00',
        )

        response = self.client.get(
            reverse('detalhes_quadra', args=[quadra.id]),
            {'data': data_selecionada.isoformat(), 'quadra': '2'},
        )

        self.assertEqual(response.context['data_selecionada'], data_selecionada.isoformat())
        self.assertEqual(response.context['numero_quadra_selecionada'], '2')
        self.assertContains(
            response,
            f'class="tab-data active"\n            data-data="{data_selecionada.isoformat()}"',
        )
        self.assertContains(response, 'class="tab-quadra active" data-numero-quadra="2"')

    def test_quadras_publicas_exibem_formulario_de_relato_e_seus_comentarios(self):
        quadra = Quadra.objects.create(nome='Praça Esportiva', cidade='Franca', esporte='Futebol')
        self.client.force_login(Usuario.objects.create_user(
            email='atleta@example.com', nome='Atleta', cidade='Franca', password='senha-segura-123'
        ))

        page = self.client.get(reverse('detalhes_quadra', args=[quadra.id]))

        self.assertContains(page, 'Relatos da comunidade')
        self.assertContains(page, 'name="comentario"')
        self.assertNotContains(page, 'name="nota"')
        self.client.post(reverse('avaliar_quadra', args=[quadra.id]), {'comentario': 'A quadra está bem cuidada.'})

        page = self.client.get(reverse('detalhes_quadra', args=[quadra.id]))

        self.assertContains(page, 'A quadra está bem cuidada.')
        self.assertContains(page, 'Atleta')
        self.assertEqual(ComentarioQuadra.objects.filter(quadra=quadra).count(), 1)

    def test_envio_de_relato_publico_exige_login(self):
        quadra = Quadra.objects.create(nome='Praça Esportiva', cidade='Franca', esporte='Futebol')

        response = self.client.post(
            reverse('avaliar_quadra', args=[quadra.id]),
            {'comentario': 'Relato não autenticado'},
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)
        self.assertFalse(ComentarioQuadra.objects.filter(quadra=quadra).exists())

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
        self.client.force_login(outro)

        response = self.client.get(reverse('detalhes_quadra', args=[quadra.id]))

        self.assertContains(response, 'Confirmar participação na quadra pública')
        self.assertContains(response, 'somente quem confirmou participação pelo DGA Sports')
        self.assertContains(response, 'Quem vai jogar')
        self.assertNotContains(response, 'PIX pelo site')
        self.assertEqual(ReservaJogador.objects.count(), 1)

        horarios = self.client.get(
            reverse('api_horarios', args=[quadra.id, horario.data.isoformat()])
        ).json()['horarios']
        self.assertEqual(horarios[0]['jogadores'][0]['nome'], 'Outro Jogador')
        self.assertTrue(horarios[0]['jogadores'][0]['eh_usuario'])
        self.assertEqual(horarios[0]['usuario_na_partida'], 1)

    def test_participacao_publica_recusa_horario_encerrado(self):
        quadra = Quadra.objects.create(nome='Praça Esportiva', cidade='Franca', esporte='Futebol')
        horario = Horario.objects.create(
            quadra=quadra,
            data=timezone.localdate() - timedelta(days=1),
            hora_texto='18:00 - 19:00',
        )
        usuario = Usuario.objects.create_user(
            email='atleta@example.com', nome='Atleta', cidade='Franca', password='senha-segura-123'
        )
        self.client.force_login(usuario)

        response = self.client.post(
            reverse('entrar_na_partida'),
            data=json.dumps({'horario_id': horario.id, 'esporte_selecionado': 'Futebol'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['mensagem'], 'Este horário já passou.')
        self.assertFalse(ReservaJogador.objects.filter(horario=horario).exists())

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
