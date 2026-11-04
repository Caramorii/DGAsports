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
    const parametrosPagina = new URLSearchParams(window.location.search);
    const dataDaUrl = parametrosPagina.get('data');
    const quadraDaUrl = parametrosPagina.get('quadra');
    let quadraSelecionada = botoesQuadra.some(botao => botao.dataset.numeroQuadra === quadraDaUrl)
        ? quadraDaUrl
        : botoesQuadra[0]?.dataset.numeroQuadra || null;
    const seletorEsporte = document.getElementById('escolha-esporte');
    const avisoEsporte = document.getElementById('escolha-esporte-aviso');
    let esportesAtuais = esportes;
    let esporteSelecionado = '';
    let horariosCarregados = [];
    let requisicaoHorarios = 0;

    botoesQuadra.forEach(botao => {
        botao.classList.toggle('active', botao.dataset.numeroQuadra === quadraSelecionada);
    });

    function atualizarUrlEstado(data = document.querySelector('.tab-data.active')?.dataset.data) {
        const url = new URL(window.location.href);
        if (data) url.searchParams.set('data', data);
        if (quadraSelecionada) url.searchParams.set('quadra', quadraSelecionada);
        window.history.replaceState(null, '', url);
    }

    botoesQuadra.forEach(botao => botao.addEventListener('click', () => {
        quadraSelecionada = botao.dataset.numeroQuadra;
        botoesQuadra.forEach(item => item.classList.toggle('active', item === botao));
        atualizarUrlEstado();
        atualizarEsportes();
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
        if (nome.includes('futebol') || nome.includes('futsal')) return '⚽';
        if (nome.includes('basquete')) return '🏀';
        if (nome.includes('vôlei') || nome.includes('volei')) return '🏐';
        if (nome.includes('tênis') || nome.includes('tenis') || nome.includes('tennis')) return '🎾';
        return '🎯';
    }

    const emReais = valor => `R$ ${Number(valor).toFixed(2).replace('.', ',')}`;

    function atualizarEsportes() {
        const abaAtiva = botoesQuadra.find(botao => botao.dataset.numeroQuadra === quadraSelecionada);
        esportesAtuais = abaAtiva ? (abaAtiva.dataset.esportes || '').split('|').filter(Boolean) : esportes;
        if (!esportesAtuais.includes(esporteSelecionado)) {
            esporteSelecionado = esportesAtuais.length === 1 ? esportesAtuais[0] : '';
        }
        seletorEsporte.querySelector('.seletor-esporte-reserva').innerHTML = esportesAtuais.map(esporte => {
            const selecionado = esporte === esporteSelecionado;
            return `<button type="button" class="btn-esporte-opcao${selecionado ? ' selected' : ''}" data-esporte="${escapeHtml(esporte)}" aria-pressed="${selecionado}"><span aria-hidden="true">${iconeEsporte(esporte)}</span>${escapeHtml(esporte)}</button>`;
        }).join('');
        seletorEsporte.hidden = esportesAtuais.length < 2;
    }

    function pedirEsporte() {
        avisoEsporte.hidden = false;
        seletorEsporte.classList.add('escolha-esporte--alerta');
        seletorEsporte.scrollIntoView({behavior: 'smooth', block: 'center'});
    }

    function botaoHorario(horario) {
        if (horario.passou || horario.indisponivel) return '';
        if (horario.usuario_na_partida) return '<button type="button" class="btn btn-sair" aria-label="Cancelar participação">Cancelar</button>';
        if (horario.pode_assumir) return `<button type="button" class="btn btn-entrar">Assumir · ${emReais(horario.preco)}</button>`;
        if (horario.jogadores_atuais >= horario.max_jogadores) {
            return horario.jogadores_atuais ? '' : '<button type="button" class="btn btn-entrar" disabled>Horário lotado</button>';
        }
        if (tipoQuadra !== 'privada') return '<button type="button" class="btn btn-entrar">Participar</button>';
        const verbo = horario.jogadores_atuais ? 'Entrar' : 'Reservar';
        return `<button type="button" class="btn btn-entrar">${verbo} · ${emReais(horario.preco)}</button>`;
    }

    function statusHorario(horario, reservado) {
        if (reservado) {
            const texto = {
                pago: 'Sua reserva · Pago',
                pendente: 'Sua reserva · Pagar no local',
                assumivel: 'Reservado sem pagamento',
                ocupado: horario.jogadores_atuais < horario.max_jogadores ? 'Partida com vagas' : 'Reservado por outra pessoa',
            }[horario.estado] || (horario.usuario_na_partida ? 'Você está nesta partida' : 'Partida reservada');
            return `<div class="status-partida${horario.usuario_na_partida ? ' status-partida--sua' : ''}"><span class="status-partida-ponto"></span>${texto}</div>`;
        }
        if (horario.estado === 'bloqueado') return '<p class="status-indisponivel">Indisponível</p>';
        if (horario.estado === 'encerrado') return '';
        return '<p class="status-livre">Disponível</p>';
    }

    function infoHorario(horario, esporte) {
        if (horario.estado === 'bloqueado') return '<p class="horario-aviso">O proprietário tirou este horário do ar.</p>';
        const esporteExibido = esporte || esporteSelecionado;
        const rotulo = esporteExibido
            ? `<span aria-hidden="true">${iconeEsporte(esporteExibido)}</span> ${escapeHtml(esporteExibido)}`
            : 'Escolha o esporte';
        const mostrarContagem = esporte || tipoQuadra !== 'privada';
        return `<div class="vagas"><span class="esporte-travado">${rotulo}</span>${mostrarContagem ? `<span class="contagem">${horario.jogadores_atuais} / ${horario.max_jogadores}</span>` : ''}</div>`;
    }

    function cartaoHorario(horario) {
        const esporte = horario.esporte_reservado || '';
        const reservado = Boolean(esporte && horario.jogadores_atuais);
        const compacto = horario.passou && !reservado;
        const classes = [
            'card-horario', `card-horario--${horario.estado}`,
            compacto && 'card-horario--compacto',
            reservado && 'card-horario--reservado',
            horario.usuario_na_partida && 'card-horario--minha-partida',
        ].filter(Boolean).join(' ');
        const botao = botaoHorario(horario);
        const resumo = reservado
            ? `<button type="button" class="btn btn-detalhes-partida">${botao ? 'Resumo' : 'Ver resumo da partida'}</button>`
            : '';
        const acoes = botao || resumo ? `<div class="acoes-horario">${botao}${resumo}</div>` : '';
        return `<article class="${classes}" data-horario-id="${horario.id}" data-data="${horario.data || ''}" data-hora="${escapeHtml(horario.hora_texto)}" data-numero-quadra="${horario.numero_quadra}" data-esporte-reservado="${escapeHtml(esporte)}" data-preco="${horario.preco}" data-passou="${horario.passou}" data-max-jogadores="${horario.max_jogadores}" data-jogadores-atuais="${horario.jogadores_atuais}" data-responsavel-nome="${escapeHtml(horario.responsavel_nome)}" data-meu-status="${horario.meu_status}" data-meu-metodo="${horario.meu_metodo}" data-responsavel-id="${horario.responsavel_reserva_id || ''}" data-aceita-convidados="${horario.aceita_convidados}">
                <div class="time-slot-time">${escapeHtml(horario.hora_texto)}</div>
                ${statusHorario(horario, reservado)}
                ${compacto ? '' : infoHorario(horario, esporte)}
                <ul class="participantes-horario" hidden>${(horario.jogadores || []).map(jogador => `<li data-id="${jogador.id}" data-e-voce="${jogador.eh_usuario}" data-status="${jogador.status}">${escapeHtml(jogador.nome)}</li>`).join('')}</ul>
                ${acoes}
            </article>`;
    }

    function dataFormatada(data) {
        if (!data) return 'Data não informada';
        const [ano, mes, dia] = data.split('-').map(Number);
        return new Date(ano, mes - 1, dia).toLocaleDateString('pt-BR', {
            weekday: 'long',
            day: '2-digit',
            month: 'long',
            year: 'numeric',
        });
    }

    function renderizarHorarios(horarios) {
        horariosCarregados = horarios;
        const horariosVisiveis = quadraSelecionada
            ? horarios.filter(horario => String(horario.numero_quadra) === String(quadraSelecionada))
            : horarios;
        if (!horariosVisiveis.length) {
            grid.innerHTML = '<p class="sem-horarios">Nenhum horário disponível para esta data.</p>';
            return;
        }
        const encerradosAbertos = Boolean(grid.querySelector('.horarios-encerrados')?.open);
        const ativos = horariosVisiveis.filter(horario => !horario.passou);
        const encerrados = horariosVisiveis.filter(horario => horario.passou);
        const principal = ativos.length
            ? `<div class="lista-horarios">${ativos.map(cartaoHorario).join('')}</div>`
            : '<p class="sem-horarios">Não há mais horários disponíveis nesta data. Escolha outro dia acima.</p>';
        const rotuloEncerrados = `${encerrados.length} ${encerrados.length === 1 ? 'horário encerrado' : 'horários encerrados'}`;
        const secaoEncerrados = encerrados.length
            ? `<details class="horarios-encerrados"${encerradosAbertos ? ' open' : ''}><summary>${rotuloEncerrados}</summary><div class="lista-encerrados">${encerrados.map(cartaoHorario).join('')}</div></details>`
            : '';
        grid.innerHTML = principal + secaoEncerrados;
    }

    const dialogoDetalhes = document.getElementById('detalhes-partida');

    function abrirDetalhesPartida(card) {
        const participantes = [...card.querySelectorAll('.participantes-horario li')];
        const maxJogadores = Number(card.dataset.maxJogadores) || 0;
        const jogadoresAtuais = Number(card.dataset.jogadoresAtuais) || participantes.length;
        const vagasRestantes = Math.max(0, maxJogadores - jogadoresAtuais);
        const esporte = card.dataset.esporteReservado || 'Esporte a definir';
        const dia = dataFormatada(card.dataset.data);
        const numeroQuadra = card.dataset.numeroQuadra;
        const responsavelId = card.dataset.responsavelId;
        const lista = document.getElementById('detalhes-partida-jogadores');

        document.getElementById('detalhes-partida-titulo').textContent =
            card.dataset.passou === 'true' ? 'Resumo da partida' : 'Partida reservada';
        document.getElementById('detalhes-partida-quadra').textContent =
            `${document.querySelector('.page-title')?.textContent.trim() || 'Quadra'}${tipoQuadra === 'privada' ? ` · ${document.querySelector('.tab-quadra.active .tab-quadra-nome')?.textContent.trim() || `Quadra ${numeroQuadra}`}` : ''}`;
        document.getElementById('detalhes-partida-data').textContent =
            `${dia} · ${card.dataset.hora || card.querySelector('.time-slot-time')?.textContent.trim() || ''}`;
        document.getElementById('detalhes-partida-esporte').textContent =
            `${iconeEsporte(esporte)} ${esporte}`;
        document.getElementById('detalhes-partida-vagas').textContent =
            `${jogadoresAtuais} de ${maxJogadores} pessoas${vagasRestantes ? ` · ${vagasRestantes} ${vagasRestantes === 1 ? 'vaga disponível' : 'vagas disponíveis'}` : ' · Lotado'}`;

        const linhaValor = document.getElementById('detalhes-partida-valor-linha');
        linhaValor.hidden = tipoQuadra !== 'privada';
        document.getElementById('detalhes-partida-valor').textContent =
            `R$ ${Number(card.dataset.preco || 0).toFixed(2).replace('.', ',')}`;

        const status = document.getElementById('detalhes-partida-status');
        if (tipoQuadra === 'privada' && card.dataset.meuStatus) {
            status.textContent = card.dataset.meuStatus === 'pago'
                ? 'Pagamento confirmado'
                : card.dataset.meuMetodo === 'caixa'
                    ? 'Pagamento combinado para ser feito na quadra'
                    : 'Pagamento pendente';
            status.hidden = false;
        } else {
            status.hidden = true;
        }

        document.getElementById('detalhes-partida-total').textContent =
            `${participantes.length} ${participantes.length === 1 ? 'participante' : 'participantes'}`;
        lista.replaceChildren();
        participantes.forEach(participante => {
            const item = document.createElement('li');
            const avatar = document.createElement('span');
            avatar.className = 'participante-avatar';
            avatar.setAttribute('aria-hidden', 'true');
            avatar.textContent = participante.textContent.trim().charAt(0).toLocaleUpperCase('pt-BR');

            const nome = document.createElement('span');
            nome.className = 'participante-nome';
            nome.textContent = participante.textContent.trim();

            item.append(avatar, nome);
            if (participante.dataset.eVoce === 'true') {
                const voce = document.createElement('span');
                voce.className = 'participante-etiqueta';
                voce.textContent = 'Você';
                item.append(voce);
            } else if (participante.dataset.id === responsavelId) {
                const responsavel = document.createElement('span');
                responsavel.className = 'participante-etiqueta participante-etiqueta--responsavel';
                responsavel.textContent = 'Responsável';
                item.append(responsavel);
            }
            lista.append(item);
        });
        dialogoDetalhes.showModal();
    }

    grid.addEventListener('click', event => {
        const botaoDetalhes = event.target.closest('.btn-detalhes-partida');
        if (!botaoDetalhes) return;
        const card = botaoDetalhes.closest('.card-horario');
        if (card) abrirDetalhesPartida(card);
    });

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

    seletorEsporte.addEventListener('click', event => {
        const opcao = event.target.closest('.btn-esporte-opcao');
        if (!opcao) return;
        esporteSelecionado = opcao.dataset.esporte;
        seletorEsporte.querySelectorAll('.btn-esporte-opcao').forEach(item => {
            const selecionado = item === opcao;
            item.classList.toggle('selected', selecionado);
            item.setAttribute('aria-pressed', String(selecionado));
        });
        avisoEsporte.hidden = true;
        seletorEsporte.classList.remove('escolha-esporte--alerta');
        renderizarHorarios(horariosCarregados);
    });

    atualizarEsportes();

    grid.addEventListener('click', async event => {
        const botao = event.target.closest('.btn-entrar, .btn-sair');
        if (!botao || botao.disabled) return;
        const card = botao.closest('.card-horario');
        const horarioId = card.dataset.horarioId;
        const esporte = card.dataset.esporteReservado || esporteSelecionado;
        if (botao.classList.contains('btn-entrar')) {
            if (!esporte) return pedirEsporte();
            if (tipoQuadra === 'privada') {
                const parametros = new URLSearchParams({
                    esporte,
                    data: card.dataset.data,
                    quadra: card.dataset.numeroQuadra,
                });
                return window.location.assign(`/reservar/${horarioId}/?${parametros}`);
            }
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
        atualizarUrlEstado(botao.dataset.data);
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

    const dataNaUrl = [...document.querySelectorAll('.tab-data')].find(botao => botao.dataset.data === dataDaUrl);
    const primeiraDataAtiva = dataNaUrl || document.querySelector('.tab-data.active') || document.querySelector('.tab-data');
    primeiraDataAtiva?.click();
});
