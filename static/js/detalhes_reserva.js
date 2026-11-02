function getCookie(name) {
    const prefix = `${name}=`;
    return document.cookie.split(';').map(item => item.trim()).find(item => item.startsWith(prefix))?.slice(prefix.length) || '';
}

document.addEventListener('DOMContentLoaded', () => {
    const container = document.querySelector('.content-container');
    const grid = document.querySelector('.schedule-grid');
    if (!container || !grid) return;

    const quadraId = container.dataset.quadraId;
    const tipoQuadra = container.dataset.quadraTipo;
    const esportes = (container.dataset.esportes || '').split('|').filter(Boolean);
    const csrfToken = getCookie('csrftoken');
    const botoesQuadra = [...document.querySelectorAll('.tab-quadra')];
    let quadraSelecionada = botoesQuadra[0]?.dataset.numeroQuadra || null;
    let horariosCarregados = [];
    let requisicaoHorarios = 0;

    botoesQuadra.forEach(botao => botao.addEventListener('click', () => {
        quadraSelecionada = botao.dataset.numeroQuadra;
        botoesQuadra.forEach(item => item.classList.toggle('active', item === botao));
        renderizarHorarios(horariosCarregados);
    }));

    document.querySelectorAll('.tab').forEach(tab => tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(item => item.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(item => item.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById(tab.dataset.tab)?.classList.add('active');
    }));

    const escapeHtml = value => String(value ?? '').replace(/[&<>'"]/g, char => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
    }[char]));

    function iconeEsporte(esporte) {
        const nome = esporte.toLocaleLowerCase('pt-BR');
        if (nome.includes('futebol')) return '⚽';
        if (nome.includes('basquete')) return '🏀';
        if (nome.includes('vôlei') || nome.includes('volei')) return '🏐';
        if (nome.includes('tênis') || nome.includes('tenis')) return '🎾';
        return '🎯';
    }

    function botoesEsporte(esporteReservado, indisponivel) {
        if (esporteReservado || indisponivel) return '';
        return `<p class="select-label">Escolha o esporte:</p><div class="seletor-esporte-reserva">${esportes.map(esporte =>
            `<button type="button" class="btn-esporte-opcao" data-esporte="${escapeHtml(esporte)}" aria-pressed="false"><span aria-hidden="true">${iconeEsporte(esporte)}</span>${escapeHtml(esporte)}</button>`
        ).join('')}</div>`;
    }

    function botaoHorario(horario) {
        if (horario.usuario_na_partida) return '<button type="button" class="btn btn-sair">Cancelar participação</button>';
        if (horario.passou) return '<button type="button" class="btn btn-entrar" disabled>Horário encerrado</button>';
        if (horario.indisponivel) return '<button type="button" class="btn btn-entrar" disabled>Indisponível</button>';
        if (horario.jogadores_atuais >= horario.max_jogadores) {
            return '<button type="button" class="btn btn-entrar" data-lotado="true" disabled>Horário lotado</button>';
        }
        const texto = tipoQuadra === 'privada'
            ? `Revisar reserva · R$ ${Number(horario.preco).toFixed(2)}`
            : 'Ver aviso e participar';
        return `<button type="button" class="btn btn-entrar" ${horario.esporte_reservado ? '' : 'disabled'}>${texto}</button>`;
    }

    function renderizarHorarios(horarios) {
        horariosCarregados = horarios;
        const horariosVisiveis = quadraSelecionada
            ? horarios.filter(horario => String(horario.numero_quadra) === String(quadraSelecionada))
            : horarios;
        if (!horariosVisiveis.length) {
            grid.innerHTML = '<p class="loading-message">Nenhum horário disponível para esta data.</p>';
            return;
        }
        grid.innerHTML = horariosVisiveis.map(horario => {
            const esporte = horario.esporte_reservado || '';
            return `<article class="card-horario" data-horario-id="${horario.id}" data-data="${horario.data || ''}" data-numero-quadra="${horario.numero_quadra}" data-esporte-reservado="${escapeHtml(esporte)}" data-preco="${horario.preco}" data-passou="${horario.passou}">
                <div class="time-slot-time">${tipoQuadra === 'privada' ? `Quadra ${horario.numero_quadra} · ` : ''}${escapeHtml(horario.hora_texto)}</div>
                ${horario.passou ? '<p class="status-encerrado">Horário encerrado</p>' : ''}
                ${horario.indisponivel ? '<p class="status-indisponivel">Indisponível pelo proprietário</p>' : ''}
                ${botoesEsporte(esporte, horario.passou || horario.indisponivel || horario.jogadores_atuais >= horario.max_jogadores)}
                <div class="vagas"><span class="esporte-travado">${escapeHtml(esporte)}</span><span class="contagem">${horario.jogadores_atuais} / ${horario.max_jogadores}</span></div>
                <progress class="barra-vagas" value="${horario.jogadores_atuais}" max="${horario.max_jogadores}"></progress>
                <ul class="participantes-horario" hidden>${(horario.jogadores || []).map(jogador => `<li>${escapeHtml(jogador.nome)}</li>`).join('')}</ul>
                ${botaoHorario(horario)}
            </article>`;
        }).join('');
    }

    async function enviar(url, dados) {
        const resposta = await fetch(url, {method: 'POST', headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrfToken}, body: JSON.stringify(dados)});
        const corpo = await resposta.json();
        if (!resposta.ok || corpo.status !== 'sucesso') throw new Error(corpo.mensagem || 'Não foi possível concluir a operação.');
        return corpo;
    }

    const dialogoConfirmacao = document.getElementById('confirmacao-partida');
    let cardPendente = null;
    let esportePendente = '';

    function abrirConfirmacaoPublica(card, esporte) {
        cardPendente = card;
        esportePendente = esporte;
        const participantes = [...card.querySelectorAll('.participantes-horario li')]
            .map(item => item.textContent.trim())
            .filter(Boolean);
        const data = card.dataset.data
            ? new Date(`${card.dataset.data}T00:00:00`).toLocaleDateString('pt-BR')
            : document.querySelector('.tab-data.active')?.textContent.trim() || '';
        const erro = document.getElementById('erro-confirmacao-partida');

        document.getElementById('resumo-quadra').textContent =
            document.querySelector('.page-title')?.textContent.trim() || '';
        document.getElementById('resumo-esporte').textContent = esporte;
        document.getElementById('resumo-data-horario').textContent =
            `${data} · ${card.querySelector('.time-slot-time')?.textContent.trim() || ''}`;
        document.getElementById('resumo-participantes').textContent = participantes.length
            ? `${participantes.join(', ')}${participantes.length ? ' e você' : ''} (${participantes.length + 1} pessoa(s) pelo site)`
            : `Você será a primeira pessoa inscrita pelo site`;
        erro.hidden = true;
        erro.textContent = '';
        dialogoConfirmacao.showModal();
    }

    document.getElementById('confirmar-participacao')?.addEventListener('click', async event => {
        if (!cardPendente) return;
        const botaoConfirmar = event.currentTarget;
        const erro = document.getElementById('erro-confirmacao-partida');
        botaoConfirmar.disabled = true;
        erro.hidden = true;
        try {
            await enviar('/quadra/entrar/', {
                horario_id: Number(cardPendente.dataset.horarioId),
                esporte_selecionado: esportePendente,
            });
            window.location.reload();
        } catch (falha) {
            erro.textContent = falha.message;
            erro.hidden = false;
        } finally {
            botaoConfirmar.disabled = false;
        }
    });

    grid.addEventListener('click', async event => {
        const opcao = event.target.closest('.btn-esporte-opcao');
        if (opcao) {
            const card = opcao.closest('.card-horario');
            card.querySelectorAll('.btn-esporte-opcao').forEach(item => {
                item.classList.remove('selected');
                item.setAttribute('aria-pressed', 'false');
            });
            opcao.classList.add('selected');
            opcao.setAttribute('aria-pressed', 'true');
            card.dataset.esporteSelecionado = opcao.dataset.esporte;
            const botao = card.querySelector('.btn-entrar');
            if (botao && botao.dataset.lotado !== 'true') botao.disabled = false;
            return;
        }
        const botao = event.target.closest('.btn-entrar, .btn-sair');
        if (!botao || botao.disabled) return;
        const card = botao.closest('.card-horario');
        const horarioId = card.dataset.horarioId;
        const esporte = card.dataset.esporteSelecionado || card.dataset.esporteReservado;
        if (botao.classList.contains('btn-entrar')) {
            if (!esporte) return alert('Escolha uma modalidade antes de continuar.');
            if (tipoQuadra === 'privada') return window.location.assign(`/reservar/${horarioId}?esporte=${encodeURIComponent(esporte)}`);
            abrirConfirmacaoPublica(card, esporte);
            return;
        }
        botao.disabled = true;
        try { await enviar('/quadra/sair/', {horario_id: Number(horarioId)}); window.location.reload(); }
        catch (erro) { botao.disabled = false; alert(erro.message); }
    });

    document.querySelectorAll('.tab-data').forEach(botao => botao.addEventListener('click', async () => {
        document.querySelectorAll('.tab-data').forEach(item => item.classList.remove('active'));
        botao.classList.add('active');
        const requisicaoAtual = ++requisicaoHorarios;
        grid.innerHTML = '<p class="loading-message">Carregando horários...</p>';
        try {
            const resposta = await fetch(`/api/quadra/${quadraId}/horarios/${botao.dataset.data}/`);
            const dados = await resposta.json();
            if (!resposta.ok || dados.status !== 'sucesso') {
                throw new Error(dados.mensagem || 'Não foi possível carregar os horários.');
            }
            if (requisicaoAtual !== requisicaoHorarios) return;
            renderizarHorarios(dados.horarios);
        } catch (erro) {
            if (requisicaoAtual !== requisicaoHorarios) return;
            grid.innerHTML = `<p class="error-message">${escapeHtml(erro.message || 'Não foi possível carregar os horários.')}</p>`;
        }
    }));

    const primeiraDataAtiva = document.querySelector('.tab-data.active') || document.querySelector('.tab-data');
    primeiraDataAtiva?.click();
});
