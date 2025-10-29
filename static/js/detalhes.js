document.addEventListener('DOMContentLoaded', () => {

    // --- 1. LÓGICA DAS ABAS (Sem alteração) ---
    const todasAsAbas = document.querySelectorAll('.tab');
    const todosOsConteudos = document.querySelectorAll('.tab-content');
    todasAsAbas.forEach(aba => {
        aba.addEventListener('click', () => {
            todasAsAbas.forEach(t => t.classList.remove('active'));
            todosOsConteudos.forEach(c => c.classList.remove('active'));
            aba.classList.add('active');
            const targetTabName = aba.dataset.tab;
            const elementoParaMostrar = document.getElementById(targetTabName);
            if (elementoParaMostrar) {
                elementoParaMostrar.classList.add('active');
            }
        });
    });

    // --- VARIÁVEL GLOBAL PARA O ESPORTE ATIVO ---
    let esporteAtivo = 'Todos'; // Começa com "Todos"

    // --- 2. LÓGICA ATUALIZADA (ENTRAR E SAIR) ---
    const container = document.querySelector('.container');
    const quadraTipo = container.dataset.quadraTipo;
    const grid = document.querySelector('.schedule-grid');

    grid.addEventListener('click', async (event) => {
        const botao = event.target.closest('.btn-entrar, .btn-sair');
        if (!botao) return;

        const cardPai = botao.closest('.card-horario');
        const idDoHorario = cardPai.dataset.horarioId;

        // Verifica se o esporteAtivo é "Todos", o que não é permitido para reservar
        if (esporteAtivo === 'Todos' && quadraTipo === 'publica') {
            alert('Por favor, selecione um esporte (Futebol ou Basquete) antes de entrar na partida.');
            return;
        }
        // Para quadras privadas, o 'esporteAtivo' será pego do filtro
        if (esporteAtivo === 'Todos' && quadraTipo === 'privada') {
            alert('Por favor, selecione um esporte (Futebol ou Basquete) antes de reservar.');
            return;
        }

        botao.disabled = true;
        botao.textContent = 'Processando...';

        const isEntrar = botao.classList.contains('btn-entrar');

        if (isEntrar) {
            // --- LÓGICA DE ENTRAR ---
            if (quadraTipo === 'privada') {
                // Envia o esporte selecionado na URL
                window.location.href = `/reservar/${idDoHorario}?esporte=${esporteAtivo}`;
            } else {
                // Pública: chama a API de entrar
                try {
                    const resposta = await fetch('/quadra/entrar', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        // Envia o esporte selecionado
                        body: JSON.stringify({
                            horario_id: parseInt(idDoHorario),
                            esporte_selecionado: esporteAtivo
                        })
                    });
                    const dados = await resposta.json();

                    if (dados.status === 'sucesso') {
                        // ATUALIZA O BOTÃO
                        botao.textContent = 'Sair da Partida';
                        botao.classList.remove('btn-entrar');
                        botao.classList.add('btn-sair');
                        botao.disabled = false;

                        // Atualiza contagem e ícone
                        cardPai.querySelector('.esporte-travado').textContent = (esporteAtivo === 'Futebol' ? '⚽' : '🏀');
                        const contagem = cardPai.querySelector('.contagem');
                        const max = cardPai.querySelector('.barra-vagas').max;
                        contagem.textContent = `${dados.nova_contagem} / ${max}`;
                        cardPai.querySelector('.barra-vagas').value = dados.nova_contagem;
                        // Atualiza o data-attribute para o filtro funcionar
                        cardPai.dataset.esporteReservado = dados.esporte_travado;
                    } else {
                        alert(dados.mensagem);
                        botao.disabled = false;
                        botao.textContent = 'Entrar na Partida';
                    }
                } catch (e) {
                    alert('Erro de conexão.');
                    botao.disabled = false;
                    botao.textContent = 'Entrar na Partida';
                }
            }
        } else {
            // --- LÓGICA DE SAIR (SÓ PÚBLICA) ---
            try {
                const resposta = await fetch('/quadra/sair', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ horario_id: parseInt(idDoHorario) })
                });
                const dados = await resposta.json();

                if (dados.status === 'sucesso') {
                    // ATUALIZA O BOTÃO
                    botao.textContent = 'Entrar na Partida';
                    botao.classList.remove('btn-sair');
                    botao.classList.add('btn-entrar');
                    botao.disabled = false;

                    // Atualiza contagem e ícone
                    if (dados.esporte_destravado) {
                        cardPai.querySelector('.esporte-travado').textContent = '';
                        cardPai.dataset.esporteReservado = ''; // Limpa o data-attribute
                    }
                    const contagem = cardPai.querySelector('.contagem');
                    const max = cardPai.querySelector('.barra-vagas').max;
                    contagem.textContent = `${dados.nova_contagem} / ${max}`;
                    cardPai.querySelector('.barra-vagas').value = dados.nova_contagem;
                } else {
                    alert(dados.mensagem);
                    botao.disabled = false;
                    botao.textContent = 'Sair da Partida';
                }
            } catch (e) {
                alert('Erro de conexão.');
                botao.disabled = false;
                botao.textContent = 'Sair da Partida';
            }
        }
    });

    // --- 3. LÓGICA ATUALIZADA DO FILTRO DE ESPORTES ---

    const botoesFiltroEsporte = document.querySelectorAll('.tab-esporte');
    const todosHorarioCards = document.querySelectorAll('.card-horario');

    // Inicializa os ícones
    todosHorarioCards.forEach(card => {
        const esporte = card.dataset.esporteReservado;
        const iconeEl = card.querySelector('.esporte-travado');
        if (esporte === 'Futebol') iconeEl.textContent = '⚽';
        if (esporte === 'Basquete') iconeEl.textContent = '🏀';
    });

    botoesFiltroEsporte.forEach(botao => {
        botao.addEventListener('click', () => {
            // Pega o esporte selecionado (ex: "Futebol" ou "Todos")
            esporteAtivo = botao.dataset.esporte; // ATUALIZA A VARIÁVEL GLOBAL

            // Atualiza a aparência do botão (ativo/inativo)
            botoesFiltroEsporte.forEach(b => b.classList.remove('active'));
            botao.classList.add('active');

            // Filtra os cards de horário
            todosHorarioCards.forEach(card => {
                const esporteDoCard = card.dataset.esporteReservado; // (Ex: "Futebol" ou "")

                // Lógica de exibição:
                // 1. Se o filtro for "Todos", mostra tudo.
                // 2. Se o filtro for "Futebol", mostra cards onde esporte_reservado="Futebol" OU esporte_reservado="" (vazio)
                // 3. Se o filtro for "Basquete", mostra cards onde esporte_reservado="Basquete" OU esporte_reservado="" (vazio)

                if (esporteAtivo === 'Todos' || esporteDoCard === esporteAtivo || esporteDoCard === '') {
                    card.style.display = 'block'; // Mostra o card
                } else {
                    card.style.display = 'none'; // Esconde o card
                }
            });
        });
    });

});