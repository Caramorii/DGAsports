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

    // --- 2. LÓGICA ATUALIZADA (ENTRAR E SAIR) (Sem alteração) ---
    const container = document.querySelector('.container');
    const quadraTipo = container.dataset.quadraTipo;
    const grid = document.querySelector('.schedule-grid'); 

    grid.addEventListener('click', async (event) => {
        const botao = event.target.closest('.btn-entrar, .btn-sair');
        if (!botao) return;

        const cardPai = botao.closest('.card-horario');
        const idDoHorario = cardPai.dataset.horarioId;
        
        botao.disabled = true;
        botao.textContent = 'Processando...';

        const isEntrar = botao.classList.contains('btn-entrar');
        
        if (isEntrar) {
            // LÓGICA DE ENTRAR
            if (quadraTipo === 'privada') {
                window.location.href = `/reservar/${idDoHorario}`;
            } else {
                // Pública: chama a API de entrar
                try {
                    const resposta = await fetch('/quadra/entrar', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ horario_id: parseInt(idDoHorario) })
                    });
                    const dados = await resposta.json();
                    
                    if (dados.status === 'sucesso') {
                        // ATUALIZA O BOTÃO
                        botao.textContent = 'Sair da Partida';
                        botao.classList.remove('btn-entrar');
                        botao.classList.add('btn-sair');
                        botao.disabled = false;
                        
                        // Atualiza contagem
                        const contagem = cardPai.querySelector('.contagem');
                        const max = cardPai.querySelector('.barra-vagas').max;
                        contagem.textContent = `${dados.nova_contagem} / ${max}`;
                        cardPai.querySelector('.barra-vagas').value = dados.nova_contagem;
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
            // LÓGICA DE SAIR (SÓ PÚBLICA)
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

                    // Atualiza contagem
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

    // --- 3. NOVA LÓGICA DO FILTRO DE ESPORTES ---
    
    const botoesFiltroEsporte = document.querySelectorAll('.tab-esporte');
    const todosHorarioCards = document.querySelectorAll('.card-horario');

    botoesFiltroEsporte.forEach(botao => {
        botao.addEventListener('click', () => {
            // Pega o esporte selecionado (ex: "Futebol" ou "Todos")
            const esporteSelecionado = botao.dataset.esporte;

            // Atualiza a aparência do botão (ativo/inativo)
            botoesFiltroEsporte.forEach(b => b.classList.remove('active'));
            botao.classList.add('active');

            // Filtra os cards de horário
            todosHorarioCards.forEach(card => {
                const esporteDoCard = card.dataset.esporteDoHorario;
                
                // Se "Todos" foi clicado OU o esporte do card é o selecionado
                if (esporteSelecionado === 'Todos' || esporteDoCard === esporteSelecionado) {
                    card.style.display = 'block'; // Mostra o card
                } else {
                    card.style.display = 'none'; // Esconde o card
                }
            });
        });
    });

});