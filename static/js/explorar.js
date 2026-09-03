document.addEventListener('DOMContentLoaded', () => {
    // --- LÓGICA DO BOTÃO DE GEOLOCALIZAÇÃO ---
    const geoButton = document.getElementById('btn-geolocate');
    const localidadeInput = document.getElementById('filtro-localidade');
 
    if (geoButton && localidadeInput) {
        geoButton.addEventListener('click', () => {
            if (!navigator.geolocation) {
                alert('Geolocalização não é suportada pelo seu navegador.');
                return;
            }
 
            localidadeInput.placeholder = "Buscando...";
 
            function success(position) {
                const latitude = position.coords.latitude;
                const longitude = position.coords.longitude;
                const apiUrl = `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${latitude}&lon=${longitude}`;
 
                fetch(apiUrl)
                    .then(response => response.json())
                    .then(data => {
                        if (data.address) {
                            const city = data.address.city || data.address.town || data.address.village || "";
                            const state = data.address.state || "";
                            localidadeInput.value = `${city}, ${state}`;
                        } else {
                            localidadeInput.placeholder = "Digite a cidade ou estado";
                            alert('Não foi possível encontrar o nome da sua cidade.');
                        }
                    })
                    .catch(error => {
                        console.error('Erro no Reverse Geocoding:', error);
                        localidadeInput.placeholder = "Digite a cidade ou estado";
                        alert('Erro ao buscar nome da localização.');
                    });
            }
 
            function error() {
                localidadeInput.placeholder = "Digite a cidade ou estado";
                alert('Não foi possível obter sua localização. Verifique as permissões do navegador.');
            }
 
            navigator.geolocation.getCurrentPosition(success, error);
        });
    }
 
    // --- LÓGICA DOS FILTROS DA SIDEBAR ---
    const filtrosTipoQuadra = document.querySelectorAll('input[name="tipo_quadra"]');
    const filtrosOcupacao = document.querySelectorAll('input[name="ocupacao"]');
    const filtroSeguindo = document.getElementById('filtro-seguindo');
    const statusBusca = document.getElementById('status-busca');
    const quadras = document.querySelectorAll('.court-card');
 
    function filtrarQuadras() {
        const tipoSelecionado = document.querySelector('input[name="tipo_quadra"]:checked').value;
        const ocupacaoSelecionada = document.querySelector('input[name="ocupacao"]:checked').value;
        const seguindoSelecionado = filtroSeguindo.checked;
 
        let quadrasVisiveis = 0;
        statusBusca.textContent = "Filtrando resultados...";
        statusBusca.style.color = "#1CB5E0";
 
        quadras.forEach(quadra => {
            const tipoDaQuadra = quadra.dataset.tipo;
            const ocupacaoDaQuadra = parseInt(quadra.dataset.ocupacao, 10);
            const seguindoNaQuadra = quadra.dataset.seguindo === 'true';
 
            const correspondeTipo = tipoSelecionado === 'qualquer' || tipoDaQuadra === tipoSelecionado;
 
            let correspondeOcupacao = false;
            if (ocupacaoSelecionada === 'qualquer') { correspondeOcupacao = true; }
            else if (ocupacaoSelecionada === 'vazia' && ocupacaoDaQuadra === 0) { correspondeOcupacao = true; }
            else if (ocupacaoSelecionada === 'poucos' && ocupacaoDaQuadra >= 1 && ocupacaoDaQuadra <= 5) { correspondeOcupacao = true; }
            else if (ocupacaoSelecionada === 'cheia' && ocupacaoDaQuadra > 5) { correspondeOcupacao = true; }
 
            const correspondeSeguindo = !seguindoSelecionado || seguindoNaQuadra;
 
            if (correspondeTipo && correspondeOcupacao && correspondeSeguindo) {
                quadra.style.display = 'block';
                quadrasVisiveis++;
            } else {
                quadra.style.display = 'none';
            }
        });
 
        setTimeout(() => {
            if (quadras.length === 0) {
                statusBusca.textContent = "";
                return;
            }
 
            if (quadrasVisiveis > 0) {
                statusBusca.textContent = `Exibindo ${quadrasVisiveis} de ${quadras.length} resultado(s) encontrados.`;
                statusBusca.style.color = "#1ab480";
            } else {
                statusBusca.textContent = "Nenhum resultado corresponde aos filtros da sidebar.";
                statusBusca.style.color = "#a0a0a0";
            }
        }, 300);
    }
 
    filtrosTipoQuadra.forEach(radio => radio.addEventListener('change', filtrarQuadras));
    filtrosOcupacao.forEach(radio => radio.addEventListener('change', filtrarQuadras));
    filtroSeguindo.addEventListener('change', filtrarQuadras);
 
    filtrarQuadras();
});
