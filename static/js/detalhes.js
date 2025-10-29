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
    // Pega o esporte do primeiro botão de filtro que está ativo (definido no HTML)
    const primeiroEsporteAtivoEl = document.querySelector('.tab-esporte.active');
    let esporteAtivo = primeiroEsporteAtivoEl ? primeiroEsporteAtivoEl.dataset.esporte : null;
    // --- 2. LÓGICA ATUALIZADA (ENTRAR E SAIR) ---
    const container = document.querySelector('.container');
    const quadraTipo = container.dataset.quadraTipo;
    const grid = document.querySelector('.schedule-grid');

    grid.addEventListener('click', async (event) => {
        const botao = event.target.closest('.btn-entrar, .btn-sair');
        if (!botao) return;

        const cardPai = botao.closest('.card-horario');
        const idDoHorario = cardPai.dataset.horarioId;

        // Se por algum motivo nenhum esporte estiver ativo, impede a ação.
        if (!esporteAtivo) {
            alert('Por favor, selecione um esporte para continuar.');
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
            // --- LÓGICA DE SAIR (PÚBLICA E PRIVADA) ---
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
                // Um card é visível se:
                // 1. O esporte do card ainda não foi definido (está vazio).
                // 2. O esporte do card é o mesmo que o esporte ativo no filtro.

                if (esporteDoCard === esporteAtivo || esporteDoCard === '') {
                    card.style.display = 'block'; // Mostra o card
                } else {
                    card.style.display = 'none'; // Esconde o card
                }
            });
        });
    });

    // Dispara um clique no primeiro botão para aplicar o filtro inicial
    if (primeiroEsporteAtivoEl) primeiroEsporteAtivoEl.click();

});