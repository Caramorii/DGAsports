document.addEventListener('DOMContentLoaded', () => {
    // --- ELEMENTOS DO DOM (APENAS SIDEBAR) ---
    // Removemos os filtros do topo (filtroEstado, etc.), pois o Flask cuida deles.
    const filtrosTipoQuadra = document.querySelectorAll('input[name="tipo_quadra"]');
    const filtrosOcupacao = document.querySelectorAll('input[name="ocupacao"]');
    const filtroSeguindo = document.getElementById('filtro-seguindo');

    // --- ELEMENTOS DOS RESULTADOS ---
    const statusBusca = document.getElementById('status-busca');
    const quadras = document.querySelectorAll('.court-card');
    // A mensagem 'semResultados' agora é controlada pelo Jinja2 (Flask)
    // const semResultados = document.getElementById('sem-resultados'); 

    // --- FUNÇÃO DE FILTRO (Simplificada) ---
    function filtrarQuadras() {
        // Pega os valores APENAS da sidebar
        const tipoSelecionado = document.querySelector('input[name="tipo_quadra"]:checked').value;
        const ocupacaoSelecionada = document.querySelector('input[name="ocupacao"]:checked').value;
        const seguindoSelecionado = filtroSeguindo.checked;

        let quadrasVisiveis = 0;
        statusBusca.textContent = "Filtrando resultados...";
        statusBusca.style.color = "#1CB5E0"; // Cor do seu CSS

        quadras.forEach(quadra => {
            // Pega os dados de cada quadra que o Flask renderizou
            const tipoDaQuadra = quadra.dataset.tipo;
            const ocupacaoDaQuadra = parseInt(quadra.dataset.ocupacao, 10);
            const seguindoNaQuadra = quadra.dataset.seguindo === 'true';

            // Verifica APENAS os filtros da sidebar
            const correspondeTipo = tipoSelecionado === 'qualquer' || tipoDaQuadra === tipoSelecionado;

            let correspondeOcupacao = false;
            if (ocupacaoSelecionada === 'qualquer') { correspondeOcupacao = true; }
            else if (ocupacaoSelecionada === 'vazia' && ocupacaoDaQuadra === 0) { correspondeOcupacao = true; }
            else if (ocupacaoSelecionada === 'poucos' && ocupacaoDaQuadra >= 1 && ocupacaoDaQuadra <= 5) { correspondeOcupacao = true; }
            else if (ocupacaoSelecionada === 'cheia' && ocupacaoDaQuadra > 5) { correspondeOcupacao = true; }

            const correspondeSeguindo = !seguindoSelecionado || seguindoNaQuadra;

            // O Flask já cuidou da Localidade e Esporte.
            if (correspondeTipo && correspondeOcupacao && correspondeSeguindo) {
                quadra.style.display = 'block';
                quadrasVisiveis++;
            } else {
                quadra.style.display = 'none';
            }
        });

        // Atualiza a mensagem de status
        setTimeout(() => {
            // 'quadras.length' é o total que o Flask enviou (que já foram filtrados no backend)
            // Se 'quadras.length' for 0, o 'else' do Jinja2 (em explorar.html) já mostrou a mensagem.
            if (quadras.length === 0) {
                statusBusca.textContent = "";
                return;
            }

            if (quadrasVisiveis > 0) {
                statusBusca.textContent = `Exibindo ${quadrasVisiveis} de ${quadras.length} resultado(s) encontrados.`;
                statusBusca.style.color = "#1ab480"; // Verde do seu CSS
            } else {
                statusBusca.textContent = "Nenhum resultado corresponde aos filtros da sidebar.";
                statusBusca.style.color = "#a0a0a0"; // Cinza do seu CSS
            }
        }, 300);
    }

    // --- INICIALIZAÇÃO E EVENT LISTENERS (APENAS SIDEBAR) ---

    // Removemos os listeners do formulário do topo, pois o Flask cuida disso
    filtrosTipoQuadra.forEach(radio => radio.addEventListener('change', filtrarQuadras));
    filtrosOcupacao.forEach(radio => radio.addEventListener('change', filtrarQuadras));
    filtroSeguindo.addEventListener('change', filtrarQuadras);

    // Aplica o filtro inicial da sidebar assim que a página carrega
    filtrarQuadras();
});