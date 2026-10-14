function getCookie(name) {
    const prefix = name + '=';
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
    const escapeHtml = value => String(value ?? '').replace(/[&<>'"]/g, char => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
    }[char]));

    document.querySelectorAll('.tab').forEach(tab => tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(item => item.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(item => item.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById(tab.dataset.tab)?.classList.add('active');
    }));

    function botoesEsporte(esporteReservado) {
        if (esporteReservado) return '';
        return '<p class="select-label">Escolha o esporte:</p><div class="seletor-esporte-reserva">' + esportes.map(esporte =>
            '<button type="button" class="btn-esporte-opcao" data-esporte="' + escapeHtml(esporte) + '">' + escapeHtml(esporte) + '</button>'
        ).join('') + '</div>';
    }

    function botaoHorario(h) {
        if (h.disponivel === false) return '<button type="button" class="btn" disabled>Indisponível (horário passado)</button>';
        if (tipoQuadra !== 'privada') {
            if (h.usuario_na_partida) return '<button type="button" class="btn btn-sair">Sair da partida</button>';
            if (h.jogadores_atuais >= h.max_jogadores) return '<button type="button" class="btn" disabled>Horário lotado</button>';
            return '<button type="button" class="btn btn-entrar" ' + (h.esporte_reservado ? '' : 'disabled') + '>Entrar na partida</button>';
        }
        if (h.usuario_na_partida) {
            if (h.responsavel_reserva_id && String(h.responsavel_reserva_id) === String(container.dataset.usuarioId)
                && h.responsavel_status === 'pendente' && h.responsavel_metodo === 'caixa') {
                return '<button type="button" class="btn btn-entrar">Pagar pelo sistema e garantir</button>';
            }
            return '<button type="button" class="btn btn-sair">Cancelar reserva</button>';
        }
        if (!h.jogadores_atuais) return '<button type="button" class="btn btn-entrar" ' + (h.esporte_reservado ? '' : 'disabled') + '>Reservar (R$ ' + Number(h.preco).toFixed(2) + ')</button>';
        const pendenteCaixa = h.responsavel_status === 'pendente' && h.responsavel_metodo === 'caixa';
        if (h.jogadores_atuais < h.max_jogadores && h.aceita_convidados) return '<button type="button" class="btn btn-entrar">Entrar pagando pelo sistema</button>';
        if (pendenteCaixa && h.jogadores_atuais === 1) return '<button type="button" class="btn btn-entrar">Assumir pagando pelo sistema</button>';
        return '<button type="button" class="btn" disabled>Reservado por ' + escapeHtml(h.responsavel_nome || 'outro jogador') + '</button>';
    }

    function renderizarHorarios(horarios) {
        if (!horarios.length) { grid.innerHTML = '<p class="loading-message">Nenhum horário disponível para esta data.</p>'; return; }
        grid.innerHTML = horarios.map(h => {
            const esporte = h.esporte_reservado || '';
            const pendenteCaixa = h.responsavel_status === 'pendente' && h.responsavel_metodo === 'caixa';
            const classe = (h.disponivel === false ? ' horario-passado' : '') + (!h.jogadores_atuais ? '' : (pendenteCaixa ? ' reserva-caixa-pendente' : ' reserva-paga'));
            const nomes = (h.jogadores || []).map(j => escapeHtml(j.nome) + (j.status === 'pendente' ? ' (caixa pendente)' : '')).join(', ');
            const reservado = h.responsavel_nome ? '<p class="reserva-responsavel">Responsável: <strong>' + escapeHtml(h.responsavel_nome) + '</strong></p>' : '';
            return '<article class="card-horario' + classe + '" data-horario-id="' + h.id + '" data-esporte-reservado="' + escapeHtml(esporte) + '" data-preco="' + h.preco + '">' +
                '<div class="time-slot-time">' + escapeHtml(h.hora_texto) + '</div>' + (h.disponivel === false ? '<p class="aviso-horario-passado">Horário passado</p>' : botoesEsporte(esporte)) +
                '<div class="vagas"><span class="esporte-travado">' + escapeHtml(esporte) + '</span><span class="contagem">' + h.jogadores_atuais + ' / ' + h.max_jogadores + '</span></div>' +
                (nomes ? '<p class="nomes-jogadores">Participantes: ' + nomes + '</p>' : '') + reservado +
                (pendenteCaixa ? '<p class="aviso-caixa">Reserva provisória. Outra pessoa pode garantir este horário pagando pelo sistema.</p>' : '') +
                '<progress class="barra-vagas" value="' + h.jogadores_atuais + '" max="' + h.max_jogadores + '"></progress>' + botaoHorario(h) + '</article>';
        }).join('');
    }

    async function enviar(url, dados) {
        const resposta = await fetch(url, {method: 'POST', headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrfToken}, body: JSON.stringify(dados)});
        const corpo = await resposta.json();
        if (!resposta.ok || corpo.status !== 'sucesso') throw new Error(corpo.mensagem || 'Não foi possível concluir a operação.');
        return corpo;
    }

    grid.addEventListener('click', async event => {
        const opcao = event.target.closest('.btn-esporte-opcao');
        if (opcao) {
            const card = opcao.closest('.card-horario');
            card.querySelectorAll('.btn-esporte-opcao').forEach(item => item.classList.remove('selected'));
            opcao.classList.add('selected');
            card.dataset.esporteSelecionado = opcao.dataset.esporte;
            const botao = card.querySelector('.btn-entrar');
            if (botao) botao.disabled = false;
            return;
        }
        const botao = event.target.closest('.btn-entrar, .btn-sair');
        if (!botao || botao.disabled) return;
        const card = botao.closest('.card-horario');
        const horarioId = card.dataset.horarioId;
        const esporte = card.dataset.esporteSelecionado || card.dataset.esporteReservado;
        if (botao.classList.contains('btn-entrar')) {
            if (!esporte) return alert('Escolha uma modalidade antes de continuar.');
            if (tipoQuadra === 'privada') return window.location.assign('/reservar/' + horarioId + '?esporte=' + encodeURIComponent(esporte));
            botao.disabled = true;
            try { await enviar('/quadra/entrar/', {horario_id: Number(horarioId), esporte_selecionado: esporte}); window.location.reload(); }
            catch (erro) { botao.disabled = false; alert(erro.message); }
            return;
        }
        botao.disabled = true;
        try { await enviar('/quadra/sair/', {horario_id: Number(horarioId)}); window.location.reload(); }
        catch (erro) { botao.disabled = false; alert(erro.message); }
    });

    document.querySelectorAll('.tab-data').forEach(button => button.addEventListener('click', async () => {
        document.querySelectorAll('.tab-data').forEach(item => item.classList.remove('active'));
        button.classList.add('active');
        grid.innerHTML = '<p class="loading-message">Carregando horários...</p>';
        try {
            const response = await fetch('/api/quadra/' + quadraId + '/horarios/' + button.dataset.data + '/');
            const data = await response.json();
            if (!response.ok || data.status !== 'sucesso') throw new Error();
            renderizarHorarios(data.horarios);
        } catch (_) { grid.innerHTML = '<p class="error-message">Não foi possível carregar os horários.</p>'; }
    }));

    const dataInicial = document.querySelector('.tab-data.active');
    if (dataInicial) dataInicial.click();
});
