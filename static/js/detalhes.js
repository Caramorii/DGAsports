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
    const container = document.querySelector('.content-container');
    const quadraId = container.dataset.quadraId;
    const quadraTipo = container ? container.dataset.quadraTipo : null;
    const grid = document.querySelector('.schedule-grid');

    // --- FUNÇÃO AUXILIAR PARA ATUALIZAR O BOTÃO ---
    function atualizarBotao(cardPai, isEntrando, dados) {
        const botaoAntigo = cardPai.querySelector('.btn-entrar, .btn-sair');
        let novoBotao;

        if (isEntrando) {
            // O usuário entrou, então criamos um botão de "Sair"
            novoBotao = document.createElement('button');
            novoBotao.className = 'btn btn-sair';
            novoBotao.textContent = 'Sair da Partida';
        } else {
            // O usuário saiu, então criamos um botão de "Entrar"
            novoBotao = document.createElement('button');
            novoBotao.className = 'btn btn-entrar';
            if (quadraTipo === 'publica') {
                novoBotao.textContent = 'Entrar na Partida';
            } else {
                // Usa o preço que está no HTML
                const preco = cardPai.dataset.preco;
                novoBotao.textContent = `Reservar (R$ ${parseFloat(preco).toFixed(2)})`;
            }
        }

        botaoAntigo.replaceWith(novoBotao);
    }

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
                        atualizarBotao(cardPai, true, dados);
                        // Atualiza contagem e ícone
                        cardPai.querySelector('.esporte-travado').textContent = (esporteAtivo === 'Futebol' ? '⚽' : '🏀');
                        const contagem = cardPai.querySelector('.contagem');
                        const max = cardPai.querySelector('.barra-vagas').max;
                        contagem.textContent = `${dados.nova_contagem} / ${max}`;
                        cardPai.querySelector('.barra-vagas').value = dados.nova_contagem;
                        // Atualiza o data-attribute para o filtro funcionar
                        cardPai.dataset.esporteReservado = dados.esporte_travado;

                        // MARCA QUE O USUÁRIO ESTÁ NA PARTIDA (CORREÇÃO)
                        cardPai.dataset.usuarioNaPartida = 'true';
                    } else {
                        alert(dados.mensagem);
                        atualizarBotao(cardPai, false, dados); // Restaura o botão de "Entrar"
                    }
                } catch (e) {
                    alert('Erro de conexão.');
                    atualizarBotao(cardPai, false, {}); // Restaura o botão de "Entrar"
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
                    atualizarBotao(cardPai, false, dados);
                    // Atualiza contagem e ícone
                    if (dados.esporte_destravado) {
                        cardPai.querySelector('.esporte-travado').textContent = '';
                        cardPai.dataset.esporteReservado = ''; // Limpa o data-attribute
                    }
                    const contagem = cardPai.querySelector('.contagem');
                    const max = cardPai.querySelector('.barra-vagas').max;
                    contagem.textContent = `${dados.nova_contagem} / ${max}`;
                    cardPai.querySelector('.barra-vagas').value = dados.nova_contagem;

                    // MARCA QUE O USUÁRIO NÃO ESTÁ MAIS NA PARTIDA (CORREÇÃO)
                    cardPai.dataset.usuarioNaPartida = 'false';
                } else {
                    alert(dados.mensagem);
                    atualizarBotao(cardPai, true, dados); // Restaura o botão de "Sair"
                }
            } catch (e) {
                alert('Erro de conexão.');
                atualizarBotao(cardPai, true, {}); // Restaura o botão de "Sair"
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

                // LÓGICA DE EXIBIÇÃO CORRIGIDA:
                // Um card é visível se:
                // 1. O filtro selecionado é "Todos".
                // 2. O esporte do card ainda não foi definido (está vazio).
                // 3. O esporte do card é o mesmo que o esporte ativo no filtro.
                if (esporteAtivo === 'Todos' || esporteDoCard === '' || esporteDoCard === esporteAtivo) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none'; // Esconde o card
                }
            });
        });
    });

    // --- 4. NOVA LÓGICA DO FILTRO DE DATAS ---
    const botoesFiltroData = document.querySelectorAll('.tab-data');

    botoesFiltroData.forEach(botao => {
        botao.addEventListener('click', async () => {
            // 1. Atualiza a aparência dos botões
            botoesFiltroData.forEach(b => b.classList.remove('active'));
            botao.classList.add('active');

            const dataSelecionada = botao.dataset.data;

            // 2. Mostra um estado de carregamento
            grid.innerHTML = '<p class="loading-message">Buscando horários...</p>';

            // 3. Busca os novos horários na API
            try {
                const response = await fetch(`/api/quadra/${quadraId}/horarios/${dataSelecionada}`);
                const dados = await response.json();

                if (dados.status === 'sucesso') {
                    renderizarHorarios(dados.horarios);
                } else {
                    grid.innerHTML = `<p class="error-message">${dados.mensagem}</p>`;
                }
            } catch (error) {
                grid.innerHTML = '<p class="error-message">Não foi possível carregar os horários. Verifique sua conexão.</p>';
            }
        });
    });

    function renderizarHorarios(horarios) {
        grid.innerHTML = ''; // Limpa a grade

        if (horarios.length === 0) {
            grid.innerHTML = '<p class="loading-message">Nenhum horário disponível para este dia.</p>';
            return;
        }

        horarios.forEach(horario => {
            const esporteReservado = horario.esporte_reservado || '';
            const iconeEsporte = esporteReservado === 'Futebol' ? '⚽' : (esporteReservado === 'Basquete' ? '🏀' : '');

            let botaoHtml;
            if (horario.usuario_esta_na_partida) {
                botaoHtml = '<button class="btn btn-sair">Sair da Partida</button>';
            } else {
                let textoBotao = 'Entrar na Partida';
                if (quadraTipo === 'privada') {
                    textoBotao = esporteReservado ? `Entrar (R$ ${horario.preco.toFixed(2)})` : `Reservar (R$ ${horario.preco.toFixed(2)})`;
                }
                botaoHtml = `<button class="btn btn-entrar">${textoBotao}</button>`;
            }

            const cardHtml = `
                <div class="card-horario" 
                     data-horario-id="${horario.id}"
                     data-esporte-reservado="${esporteReservado}">
                    
                    <div class="time-slot-time">${horario.hora_texto}</div>
                    
                    <div class="vagas">
                        <span class="esporte-travado">${iconeEsporte}</span>
                        <span class="contagem">${horario.jogadores_atuais} / ${horario.max_jogadores}</span>
                    </div>
                    
                    <progress class="barra-vagas" value="${horario.jogadores_atuais}" max="${horario.max_jogadores}"></progress>
                    
                    ${botaoHtml}
                </div>
            `;
            grid.insertAdjacentHTML('beforeend', cardHtml);
        });

        // Re-aplica o filtro de esporte atual
        document.querySelector('.tab-esporte.active')?.click();
    }

    // Dispara um clique no primeiro botão para aplicar o filtro inicial
    if (primeiroEsporteAtivoEl) primeiroEsporteAtivoEl.click();

});