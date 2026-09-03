// Em: static/js/interaction_dga.js

document.addEventListener('DOMContentLoaded', () => {
    const geoButton = document.getElementById('btn-geolocate');
    const localidadeInput = document.getElementById('input-localidade');

    if (geoButton) {
        geoButton.addEventListener('click', () => {
            // 1. Verifica se o navegador suporta geolocalização
            if (!navigator.geolocation) {
                alert('Geolocalização não é suportada pelo seu navegador.');
                return;
            }

            // 2. Mostra um feedback para o usuário
            localidadeInput.value = "Buscando sua localização...";

            // 3. Função de sucesso (quando o usuário permite)
            function success(position) {
                const latitude = position.coords.latitude;
                const longitude = position.coords.longitude;

                // 4. Converte Coordenadas em Nome de Cidade
                // Usamos uma API gratuita chamada Nominatim (do OpenStreetMap)
                // Isso é chamado de "Reverse Geocoding"
                const apiUrl = `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${latitude}&lon=${longitude}`;

                fetch(apiUrl)
                    .then(response => response.json())
                    .then(data => {
                        if (data.address) {
                            // Tenta pegar o nome da cidade ou vila
                            const city = data.address.city || data.address.town || data.address.village || "";
                            const state = data.address.state || "";

                            // 5. Preenche o input
                            localidadeInput.value = `${city}, ${state}`;
                        } else {
                            localidadeInput.value = "";
                            alert('Não foi possível encontrar o nome da sua cidade.');
                        }
                    })
                    .catch(error => {
                        console.error('Erro no Reverse Geocoding:', error);
                        localidadeInput.value = "";
                        alert('Erro ao buscar nome da localização.');
                    });
            }

            // 6. Função de erro (quando o usuário nega ou dá erro)
            function error() {
                localidadeInput.value = "";
                alert('Não foi possível obter sua localização. Verifique as permissões do navegador.');
            }

            // 7. Pede a localização ao usuário
            navigator.geolocation.getCurrentPosition(success, error);
        });
    }

    // O resto do seu código antigo (entrar(), cadastrar(), futebol())
    // foi removido, pois o Flask agora cuida dessa navegação
    // através dos links e formulários.
});