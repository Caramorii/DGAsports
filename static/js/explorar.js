document.addEventListener('DOMContentLoaded', () => {
    // --- ELEMENTOS DO DOM (ORIGINAIS) ---
    const filtroEstado = document.getElementById('filtro-estado');
    const filtroCidade = document.getElementById('filtro-cidade');
    const filtroEsporte = document.getElementById('filtro-esporte');
    const searchForm = document.querySelector('.filter-panel');
    const statusBusca = document.getElementById('status-busca');
    const quadras = document.querySelectorAll('.court-card');
    const semResultados = document.getElementById('sem-resultados');

    // --- ELEMENTOS DO DOM (NOVOS FILTROS) ---
    const filtrosTipoQuadra = document.querySelectorAll('input[name="tipo_quadra"]');
    const filtrosOcupacao = document.querySelectorAll('input[name="ocupacao"]');
    const filtroSeguindo = document.getElementById('filtro-seguindo');

    // --- DADOS PARA OS FILTROS DINÂMICOS ---
    const cidadesPorEstado = {
        "SP": ["Franca", "Ribeirão Preto", "São Paulo", "Campinas"],
        "RJ": ["Rio de Janeiro", "Niterói", "Duque de Caxias"],
        "MG": ["Belo Horizonte", "Uberlândia", "Contagem"]
    };

    // --- FUNÇÕES ---

    function atualizarCidades() {
        const estadoSelecionado = filtroEstado.value;
        filtroCidade.innerHTML = '';
        if (estadoSelecionado && cidadesPorEstado[estadoSelecionado]) {
            filtroCidade.disabled = false;
            let optionsHtml = '<option value="">Todas</option>';
            cidadesPorEstado[estadoSelecionado].forEach(cidade => {
                optionsHtml += `<option value="${cidade}">${cidade}</option>`;
            });
            filtroCidade.innerHTML = optionsHtml;
        } else {
            filtroCidade.innerHTML = '<option value="">Escolha um estado</option>';
            filtroCidade.disabled = true;
        }
    }

    function filtrarQuadras(event) {
        if (event) {
            event.preventDefault();
        }

        const estadoSelecionado = filtroEstado.value;
        const cidadeSelecionada = filtroCidade.value;
        const esporteSelecionado = filtroEsporte.value;
        const tipoSelecionado = document.querySelector('input[name="tipo_quadra"]:checked').value;
        const ocupacaoSelecionada = document.querySelector('input[name="ocupacao"]:checked').value;
        const seguindoSelecionado = filtroSeguindo.checked;

        let quadrasVisiveis = 0;
        statusBusca.textContent = "Filtrando resultados...";
        statusBusca.style.color = "#1CB5E0";

        quadras.forEach(quadra => {
            const estadoDaQuadra = quadra.dataset.estado;
            const cidadeDaQuadra = quadra.dataset.cidade;
            const esportesDaQuadra = quadra.dataset.esportes || "";
            const tipoDaQuadra = quadra.dataset.tipo;
            const ocupacaoDaQuadra = parseInt(quadra.dataset.ocupacao, 10);
            const seguindoNaQuadra = quadra.dataset.seguindo === 'true';

            const correspondeEstado = !estadoSelecionado || estadoDaQuadra === estadoSelecionado;
            const correspondeCidade = !cidadeSelecionada || cidadeDaQuadra === cidadeSelecionada;
            const correspondeEsporte = esporteSelecionado === 'Qualquer' || esportesDaQuadra.includes(esporteSelecionado);
            const correspondeTipo = tipoSelecionado === 'qualquer' || tipoDaQuadra === tipoSelecionado;
            let correspondeOcupacao = false;
            if (ocupacaoSelecionada === 'qualquer') { correspondeOcupacao = true; }
            else if (ocupacaoSelecionada === 'vazia' && ocupacaoDaQuadra === 0) { correspondeOcupacao = true; }
            else if (ocupacaoSelecionada === 'poucos' && ocupacaoDaQuadra >= 1 && ocupacaoDaQuadra <= 5) { correspondeOcupacao = true; }
            else if (ocupacaoSelecionada === 'cheia' && ocupacaoDaQuadra > 5) { correspondeOcupacao = true; }
            const correspondeSeguindo = !seguindoSelecionado || seguindoNaQuadra;

            if (correspondeEstado && correspondeCidade && correspondeEsporte && correspondeTipo && correspondeOcupacao && correspondeSeguindo) {
                quadra.style.display = 'block';
                quadrasVisiveis++;
            } else {
                quadra.style.display = 'none';
            }
        });

        setTimeout(() => {
            if (quadrasVisiveis > 0) {
                statusBusca.textContent = `Exibindo ${quadrasVisiveis} resultado(s).`;
                statusBusca.style.color = "#1ab480";
                semResultados.style.display = 'none';
            } else {
                statusBusca.textContent = "";
                semResultados.style.display = 'block';
            }
        }, 300);
    }

    // --- INICIALIZAÇÃO E EVENT LISTENERS ---

    searchForm.addEventListener('submit', filtrarQuadras);
    filtrosTipoQuadra.forEach(radio => radio.addEventListener('change', filtrarQuadras));
    filtrosOcupacao.forEach(radio => radio.addEventListener('change', filtrarQuadras));
    filtroSeguindo.addEventListener('change', filtrarQuadras);
    filtroEstado.addEventListener('change', () => { atualizarCidades(); filtrarQuadras(); });
    filtroCidade.addEventListener('change', filtrarQuadras);
    filtroEsporte.addEventListener('change', filtrarQuadras);

    // Inicializa os componentes da página na ordem correta
    atualizarCidades(); // CORREÇÃO: Adiciona esta chamada para configurar o campo de cidade
    filtrarQuadras();   // Mantém esta chamada para aplicar o filtro inicial
});