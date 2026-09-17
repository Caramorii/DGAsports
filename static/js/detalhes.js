
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
const csrftoken = getCookie('csrftoken');
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
    // Seleciona o elemento select do HTML (Adicionado para busca)
    const selectEsporte = document.getElementById('filtro-esporte-js');
    const primeiroEsporteAtivoEl = document.querySelector('.tab-esporte.active');
    
    // Inicializa a variável priorizando o select se ele existir
    let esporteAtivo = selectEsporte ? selectEsporte.value : (primeiroEsporteAtivoEl ? primeiroEsporteAtivoEl.dataset.esporte : null);

    // --- 2. LÓGICA ATUALIZADA (ENTRAR E SAIR) ---
    const container = document.querySelector('.content-container');
    const quadraId = container ? container.dataset.quadraId : null;
    const quadraTipo = container ? container.dataset.quadraTipo : null;
    const grid = document.querySelector('.schedule-grid') || document.querySelector('.results-grid');

    // --- FUNÇÃO AUXILIAR PARA ATUALIZAR O BOTÃO ---
    function atualizarBotao(cardPai, isEntrando, dados) {
        const botaoAntigo = cardPai.querySelector('.btn-entrar, .btn-sair, .details-btn');
        if (!botaoAntigo) return;
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
                // Usa o preço que está no HTML ou nos dados
                const preco = cardPai.dataset.preco || (dados.preco ? dados.preco : "0");
                novoBotao.textContent = `Reservar (R$ ${parseFloat(preco).toFixed(2)})`;
            }
        }

        botaoAntigo.replaceWith(novoBotao);
    }

    // Monitora mudanças no select (Para a página de busca)
    if (selectEsporte) {
        selectEsporte.addEventListener('change', (e) => {
            esporteAtivo = e.target.value;
            // Sincroniza visualmente com as abas de esporte se existirem
            document.querySelectorAll('.tab-esporte').forEach(tab => {
                if (tab.dataset.esporte === esporteAtivo) {
                    tab.classList.add('active');
                } else {
                    tab.classList.remove('active');
                }
            });
            // Dispara o filtro visual nos cards
            aplicarFiltroEsporte();
        });
    }

    if (grid) {
        grid.addEventListener('click', async (event) => {
            const opcaoEsporte = event.target.closest('.btn-esporte-opcao');
            if (opcaoEsporte) {
                const card = opcaoEsporte.closest('.card-horario');
                card.querySelectorAll('.btn-esporte-opcao').forEach((opcao) => opcao.classList.remove('selected'));
                opcaoEsporte.classList.add('selected');
                card.dataset.esporteSelecionado = opcaoEsporte.dataset.esporte;
                const botaoReserva = card.querySelector('.btn-entrar');
                if (botaoReserva) botaoReserva.disabled = false;
                return;
            }

            const botao = event.target.closest('.btn-entrar, .btn-sair');
            if (!botao) return;

            const cardPai = botao.closest('.card-horario') || botao.closest('.court-card');
            const idDoHorario = cardPai.dataset.horarioId;
            const esporteSelecionado = cardPai.dataset.esporteSelecionado || esporteAtivo || cardPai.dataset.esporteReservado;

            // Se por algum motivo nenhum esporte estiver ativo ou for "Todos", impede a entrada.
            if (!esporteSelecionado || esporteSelecionado === 'Todos') {
                alert('Por favor, selecione um esporte específico para continuar.');
                return;
            }

            botao.disabled = true;
            botao.textContent = 'Processando...';

            const isEntrar = botao.classList.contains('btn-entrar');

            if (isEntrar) {
                // --- LÓGICA DE ENTRAR ---
                if (quadraTipo === 'privada') {
                    // Envia o esporte selecionado na URL
                    window.location.href = `/reservar/${idDoHorario}?esporte=${encodeURIComponent(esporteSelecionado)}`;
                } else {
                    // Pública: chama a API de entrar
                    try {
                        const resposta = await fetch('/quadra/entrar/', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
                            body: JSON.stringify({
                                horario_id: parseInt(idDoHorario),
                                esporte_selecionado: esporteSelecionado
                            })
                        });
                        const dados = await resposta.json();

                        if (dados.status === 'sucesso') {
                            atualizarBotao(cardPai, true, dados);
                            // Atualiza contagem e ícone (Suporte aos novos esportes)
                            const icones = { 
                                'Futebol': '⚽', 'Basquete': '🏀', 'Volei': '🏐', 
                                'Futevolei': '⚽🏐', 'Beach-Tennis': '🎾' 
                            };
                            const esporteTravadoEl = cardPai.querySelector('.esporte-travado');
                            if (esporteTravadoEl) {
                                esporteTravadoEl.textContent = icones[esporteAtivo] || '🎮';
                            }

                            const contagem = cardPai.querySelector('.contagem');
                            const barra = cardPai.querySelector('.barra-vagas');
                            if (contagem && barra) {
                                contagem.textContent = `${dados.nova_contagem} / ${barra.max}`;
                                barra.value = dados.nova_contagem;
                            }
                            // Atualiza o data-attribute para o filtro funcionar
                            cardPai.dataset.esporteReservado = esporteSelecionado;
                            cardPai.dataset.usuarioNaPartida = 'true';
                        } else {
                            alert(dados.mensagem);
                            atualizarBotao(cardPai, false, dados); 
                        }
                    } catch (e) {
                        alert('Erro de conexão.');
                        atualizarBotao(cardPai, false, {}); 
                    }
                }
            } else {
                // --- LÓGICA DE SAIR (PÚBLICA E PRIVADA) ---
                try {
                    const resposta = await fetch('/quadra/sair/', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
                        body: JSON.stringify({ horario_id: parseInt(idDoHorario) })
                    });
                    const dados = await resposta.json();

                    if (dados.status === 'sucesso') {
                        atualizarBotao(cardPai, false, dados);
                        // Atualiza contagem e ícone
                        if (dados.esporte_destravado) {
                            const esporteTravadoEl = cardPai.querySelector('.esporte-travado');
                            if (esporteTravadoEl) esporteTravadoEl.textContent = '';
                            cardPai.dataset.esporteReservado = ''; 
                        }
                        const contagem = cardPai.querySelector('.contagem');
                        const barra = cardPai.querySelector('.barra-vagas');
                        if (contagem && barra) {
                            contagem.textContent = `${dados.nova_contagem} / ${barra.max}`;
                            barra.value = dados.nova_contagem;
                        }
                        cardPai.dataset.usuarioNaPartida = 'false';
                    } else {
                        alert(dados.mensagem);
                        atualizarBotao(cardPai, true, dados); 
                    }
                } catch (e) {
                    alert('Erro de conexão.');
                    atualizarBotao(cardPai, true, {}); 
                }
            }
        });
    }

    // --- 3. LÓGICA ATUALIZADA DO FILTRO DE ESPORTES ---
    const botoesFiltroEsporte = document.querySelectorAll('.tab-esporte');

    function aplicarFiltroEsporte() {
        document.querySelectorAll('.card-horario, .court-card').forEach(card => {
            const esporteDoCard = card.dataset.esporteReservado || card.dataset.esportes || "";
            if (esporteAtivo === 'Todos' || esporteDoCard === '' || esporteDoCard.includes(esporteAtivo)) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    }

    botoesFiltroEsporte.forEach(botao => {
        botao.addEventListener('click', () => {
            esporteAtivo = botao.dataset.esporte;
            botoesFiltroEsporte.forEach(b => b.classList.remove('active'));
            botao.classList.add('active');
            if (selectEsporte) selectEsporte.value = esporteAtivo;
            aplicarFiltroEsporte();
        });
    });

    // --- 4. NOVA LÓGICA DO FILTRO DE DATAS ---
    const botoesFiltroData = document.querySelectorAll('.tab-data');

    botoesFiltroData.forEach(botao => {
        botao.addEventListener('click', async () => {
            botoesFiltroData.forEach(b => b.classList.remove('active'));
            botao.classList.add('active');
            const dataSelecionada = botao.dataset.data;

            if (grid) grid.innerHTML = '<p class="loading-message">Buscando horários...</p>';

            try {
                const response = await fetch(`/api/quadra/${quadraId}/horarios/${dataSelecionada}/`);
                const dados = await response.json();

                if (dados.status === 'sucesso') {
                    renderizarHorarios(dados.horarios);
                } else {
                    grid.innerHTML = `<p class="error-message">${dados.mensagem}</p>`;
                }
            } catch (error) {
                if (grid) grid.innerHTML = '<p class="error-message">Não foi possível carregar os horários.</p>';
            }
        });
    });

    function renderizarHorarios(horarios) {
        if (!grid) return;
        grid.innerHTML = ''; 

        if (horarios.length === 0) {
            grid.innerHTML = '<p class="loading-message">Nenhum horário disponível para este dia.</p>';
            return;
        }

        horarios.forEach(horario => {
            const esporteReservado = horario.esporte_reservado || '';
            const icones = { 'Futebol': '⚽', 'Basquete': '🏀', 'Volei': '🏐', 'Futevolei': '⚽🏐', 'Beach-Tennis': '🎾' };
            const iconeEsporte = icones[esporteReservado] || '';

            let botaoHtml;
            if (horario.usuario_na_partida) {
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
                     data-esporte-reservado="${esporteReservado}"
                     data-preco="${horario.preco}">
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

        aplicarFiltroEsporte();
    }

    // Inicialização final
    if (primeiroEsporteAtivoEl) primeiroEsporteAtivoEl.click();
    aplicarFiltroEsporte();
});
