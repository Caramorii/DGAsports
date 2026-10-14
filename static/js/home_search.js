document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('home-search-form');
    const section = document.getElementById('home-search-results');
    const cardsContainer = document.getElementById('home-court-results');
    const summary = document.getElementById('home-results-summary');
    const clearButton = document.getElementById('home-results-clear');
    const locality = document.getElementById('input-localidade');
    if (!form || !section || !cardsContainer) return;

    const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, char => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[char]));
    const paramsForSearch = () => new URLSearchParams(new FormData(form));
    let currentRequest;
    let debounceTimer;

    function addressOf(court) {
        return [court.localizacao, court.cidade, court.estado].filter(Boolean).join(', ');
    }

    function mapsUrl(query) {
        return 'https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent(query);
    }

    function groupRow(court, group) {
        const date = group.data_encontro ? ' ' + String.fromCharCode(183) + ' ' + group.data_encontro.split('-').reverse().join('/') : '';
        const time = group.hora_inicio && group.hora_fim ? ' ' + String.fromCharCode(183) + ' ' + group.hora_inicio + String.fromCharCode(8211) + group.hora_fim : '';
        const materials = (group.materiais || []).length
            ? '<small>Materiais: ' + group.materiais.map(material => escapeHtml(material.item)).join(', ') + '</small>'
            : '';
        return '<li><div><span>' + escapeHtml(group.esporte + date + time) + ' ' + String.fromCharCode(183) + ' ' + Number(group.participantes) + ' participante' + (Number(group.participantes) === 1 ? '' : 's') + '</span>' + materials + '</div><a href="' + escapeHtml(court.url + '#grupo-' + group.id) + '">Participar</a></li>';
    }

    function groupPanel(court) {
        if (court.tipo !== 'publica') return '';
        const groups = court.grupos || [];
        const total = Number(court.total_grupos || 0);
        const rows = groups.map(group => groupRow(court, group)).join('');
        const empty = '<p>Ainda n&atilde;o h&aacute; grupos nesta quadra. Crie o primeiro.</p>';
        const seeAll = total > 2
            ? '<button type="button" class="home-groups-toggle" data-court-id="' + Number(court.id) + '" data-loaded="false">Ver todos os grupos</button>'
            : '';
        return '<div class="home-group-info"><strong>Grupos j&aacute; criados nesta quadra (' + total + ')</strong>' +
            (rows ? '<ul class="home-group-list">' + rows + '</ul>' : empty) + seeAll +
            '<div class="home-groups-expanded" hidden></div></div>';
    }

    function renderCourt(court) {
        const address = addressOf(court);
        const mapsQuery = [court.nome, address].filter(Boolean).join(', ');
        const imagePath = court.foto
            ? (/^(https?:|\/|data:)/i.test(court.foto) ? court.foto : '/static/' + court.foto.replace(/^\/+/, ''))
            : '';
        const image = imagePath
            ? '<img class="home-court-image" src="' + escapeHtml(imagePath) + '" alt="Quadra ' + escapeHtml(court.nome) + '" loading="lazy">'
            : '<div class="home-court-image home-court-placeholder" aria-hidden="true">DGA <span>SPORTS</span></div>';
        const sports = (court.esportes || []).map(sport => '<span class="home-sport-chip">' + escapeHtml(sport) + '</span>').join('');
        const groupsHtml = groupPanel(court);
        const rating = court.nota_media === null ? 'Ainda sem avaliacoes' : '&#9733; ' + Number(court.nota_media).toFixed(1) + ' avaliacoes';
        const actionLabel = court.tipo === 'publica' ? 'Criar grupo' : 'Agendar hor&#225;rio';
        const typeLabel = court.tipo === 'publica' ? 'P&#250;blica' : 'Particular';
        return '<article class="home-court-card">' + image +
            '<div class="home-court-body"><div class="home-court-heading"><h4>' + escapeHtml(court.nome) + '</h4><span class="home-type-chip">' + typeLabel + '</span></div>' +
            '<p class="home-court-location">' + escapeHtml(address || 'Endereco nao informado') + '</p>' +
            '<div class="home-sports-list">' + sports + '</div>' + groupsHtml +
            (court.tipo !== 'publica' ? '<div class="home-court-meta"><span>' + Number(court.total_horarios) + ' horarios</span><span>' + Number(court.total_jogadores) + ' participantes</span><span>' + rating + '</span></div>' : '') +
            '<div class="home-court-actions"><a class="home-details-link" href="' + escapeHtml(court.url) + '">' + actionLabel + '</a><a class="home-maps-link" href="' + escapeHtml(mapsUrl(mapsQuery)) + '" target="_blank" rel="noopener">Ver no Google Maps &#8599;</a></div></div></article>';
    }

    async function searchCourts(scrollToResults = false) {
        clearTimeout(debounceTimer);
        if (currentRequest) currentRequest.abort();
        currentRequest = new AbortController();
        const params = paramsForSearch();
        section.hidden = false;
        if (scrollToResults) section.scrollIntoView({behavior: 'smooth', block: 'start'});
        summary.textContent = 'Buscando quadras que correspondem aos filtros…';
        cardsContainer.innerHTML = '<p class="home-search-loading">Carregando resultados…</p>';

        try {
            const response = await fetch(form.dataset.apiUrl + '?' + params.toString(), {
                headers: {'Accept': 'application/json'},
                signal: currentRequest.signal
            });
            const data = await response.json();
            if (!response.ok || data.status !== 'sucesso') throw new Error('Não foi possível carregar as quadras.');

            const courts = data.quadras || [];
            if (!courts.length) {
                summary.textContent = 'Nenhuma quadra corresponde aos filtros selecionados.';
                cardsContainer.innerHTML = '<div class="home-search-empty"><strong>Nenhuma quadra encontrada</strong><p>Tente outra localidade ou escolha outro esporte.</p></div>';
                return;
            }

            const searchedLocality = params.get('localidade')?.trim();
            summary.textContent = courts.length + ' quadra' + (courts.length === 1 ? '' : 's') + ' encontrada' + (courts.length === 1 ? '' : 's') + (searchedLocality ? ' em ' + searchedLocality : '') + '.';
            cardsContainer.innerHTML = courts.map(renderCourt).join('');
        } catch (error) {
            if (error.name === 'AbortError') return;
            summary.textContent = 'Não foi possível atualizar os resultados.';
            cardsContainer.innerHTML = '<div class="home-search-empty"><strong>Falha na busca</strong><p>Verifique sua conexão e tente novamente.</p></div>';
        }
    }

    form.addEventListener('submit', event => {
        event.preventDefault();
        searchCourts(true);
    });
    form.querySelectorAll('select').forEach(select => select.addEventListener('change', searchCourts));
    locality?.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(searchCourts, 500);
    });
    cardsContainer.addEventListener('click', async event => {
        const button = event.target.closest('.home-groups-toggle');
        if (!button) return;
        const panel = button.closest('.home-group-info');
        const expanded = panel.querySelector('.home-groups-expanded');
        if (!expanded.hidden) {
            expanded.hidden = true;
            panel.querySelector('.home-group-list')?.removeAttribute('hidden');
            button.textContent = 'Ver todos os grupos';
            return;
        }
        if (button.dataset.loaded === 'true') {
            expanded.hidden = false;
            panel.querySelector('.home-group-list')?.setAttribute('hidden', '');
            button.textContent = 'Mostrar menos';
            return;
        }
        button.disabled = true;
        button.textContent = 'Carregando grupos...';
        try {
            const response = await fetch('/api/quadra/' + encodeURIComponent(button.dataset.courtId) + '/grupos/', {headers: {'Accept': 'application/json'}});
            const data = await response.json();
            if (!response.ok || data.status !== 'sucesso') throw new Error('Falha ao carregar os grupos.');
            const court = {url: '/quadra/' + button.dataset.courtId + '/'};
            expanded.innerHTML = '<ul class="home-group-list">' + data.grupos.map(group => groupRow(court, group)).join('') + '</ul>';
            expanded.hidden = false;
            button.dataset.loaded = 'true';
            panel.querySelector('.home-group-list')?.setAttribute('hidden', '');
            button.textContent = 'Mostrar menos';
        } catch (error) {
            expanded.textContent = error.message;
            expanded.hidden = false;
        } finally {
            button.disabled = false;
        }
    });
    clearButton?.addEventListener('click', () => {
        clearTimeout(debounceTimer);
        if (currentRequest) currentRequest.abort();
        form.reset();
        section.hidden = true;
        cardsContainer.innerHTML = '';
    });
});
