// Dados simulados das quadras em Franca
const quadrasSimuladas = [
    { name: "Quadra Amazonas", lat: -20.5647897, lng: -47.3990868, distance: "1,2 km", rating: "4.6" },
    { name: "Poli Futevôlei", lat: -20.5617689, lng: -47.4071067, distance: "1,6 km", rating: "5.0" },
    { name: "Quadra de Esportes (Parque Francal)", lat: -20.5605204, lng: -47.4077272, distance: "1,7 km", rating: "N/A" },
    { name: "Arena São Gabriel", lat: -20.5637155, lng: -47.3899223, distance: "1,8 km", rating: "4.7" },
    { name: "Quadra de Esportes (Parque do Castelo)", lat: -20.5603889, lng: -47.3948654, distance: "1,8 km", rating: "4.3" }
];

let gmpMap; // O elemento <gmp-map>
let placePicker; // O elemento <gmpx-place-picker>
let mainMarker; // O marcador principal (central)
let infoWindow; // O balão de informação
let statusMessage; // A mensagem de status

// --- FUNÇÕES GERAIS ---

function updateStatus(message, isError = false) {
    statusMessage.textContent = message;
    statusMessage.style.color = isError ? 'red' : '#007bff';
}

function createMapMarker(position, title, iconUrl = null) {
    const marker = document.createElement('gmp-advanced-marker');
    marker.position = position;
    marker.title = title;
    if (iconUrl) {
        // Marcador azul para o usuário
        marker.content = document.createElement('img');
        marker.content.src = iconUrl;
        marker.content.style.width = '24px';
        marker.content.style.height = '24px';
    }
    gmpMap.appendChild(marker);
    return marker;
}

// --- LÓGICA DE GEOLOCALIZAÇÃO ---

function useMyLocation() {
    if (!navigator.geolocation) {
        updateStatus("Seu navegador não suporta geolocalização.", true);
        return;
    }

    updateStatus("Buscando sua localização...");

    navigator.geolocation.getCurrentPosition(
        (position) => {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;
            const newCenter = `${lat},${lng}`;

            // Centraliza o mapa
            gmpMap.center = newCenter;
            gmpMap.zoom = 15;

            // Atualiza o marcador principal para a localização do usuário (ícone diferente)
            mainMarker.remove(); // Remove o marcador anterior
            mainMarker = createMapMarker(newCenter, "Você está aqui", 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png');
            mainMarker.id = 'main-marker';

            updateStatus("Localização encontrada com sucesso!");

            // Aciona a busca de quadras
            findNearbyFields();
        },
        (error) => {
            updateStatus("Permissão de localização negada ou falhou. Usando centro padrão.", true);
            console.error("Geolocation Error:", error);
        }
    );
}

// --- LÓGICA DE BUSCA E EXIBIÇÃO ---

function findNearbyFields() {
    // Em uma aplicação real, aqui você usaria o serviço Places API
    // para buscar "quadras de futebol" dentro de um raio de gmpMap.center.

    // Para esta demo, usamos os dados simulados de Franca:
    displayFieldsOnMap(quadrasSimuladas);
}

function displayFieldsOnMap(fieldsArray) {
    const resultsList = document.getElementById('results-list');
    const resultsCount = document.getElementById('results-count');

    // Limpa a lista e remove marcadores antigos (exceto o principal)
    resultsList.innerHTML = '';
    const oldFieldMarkers = gmpMap.querySelectorAll('.field-marker');
    oldFieldMarkers.forEach(marker => marker.remove());

    resultsCount.textContent = fieldsArray.length;

    if (fieldsArray.length === 0) {
        resultsList.innerHTML = '<p class="placeholder">Nenhuma quadra encontrada nesta área.</p>';
        return;
    }

    fieldsArray.forEach((quadra) => {
        const localizacaoQuadra = `${quadra.lat},${quadra.lng}`;

        // 1. Cria o Marcador (sem ícone customizado)
        const marker = createMapMarker(localizacaoQuadra, quadra.name);
        marker.className = 'field-marker';

        // 2. Cria o InfoWindow Content
        const contentString = `
            <div style="font-family: Arial, sans-serif; padding: 5px;">
                <strong>${quadra.name}</strong><br>
                <span>Avaliação: ${quadra.rating} estrelas</span><br>
                <span>Distância: ${quadra.distance}</span>
                <p><a href="https://www.google.com/maps/dir/?api=1&destination=${quadra.lat},${quadra.lng}" target="_blank">Ver Rotas</a></p>
            </div>
        `;

        // 3. Adiciona interatividade no Mapa
        marker.addEventListener('gmp-click', () => {
            infoWindow.setContent(contentString);
            infoWindow.open({ anchor: marker, map: gmpMap.innerMap, shouldFocus: false });
        });

        // 4. Cria e Adiciona o Item na Lista Lateral
        const listItem = document.createElement('div');
        listItem.className = 'local-item';
        listItem.innerHTML = `
            <div class="titulo-local">${quadra.name}</div>
            <p>${quadra.distance} - Avaliação: ${quadra.rating}</p>
        `;

        // 5. Adiciona interatividade na Lista
        listItem.addEventListener('click', () => {
            gmpMap.center = localizacaoQuadra;
            gmpMap.zoom = 16;
            infoWindow.setContent(contentString);
            infoWindow.open({ anchor: marker, map: gmpMap.innerMap, shouldFocus: false });
        });

        resultsList.appendChild(listItem);
    });
}

// --- INICIALIZAÇÃO GERAL ---

document.addEventListener('DOMContentLoaded', async () => {
    // Espera o carregamento dos componentes do Google Maps
    await customElements.whenDefined('gmp-map');

    // Captura os elementos globais
    gmpMap = document.getElementById('main-map');
    placePicker = document.getElementById('place-picker');
    mainMarker = document.getElementById('main-marker');
    statusMessage = document.getElementById('status-message');
    document.getElementById('search-btn').disabled = false; // Habilita o botão de busca

    // Inicializa InfoWindow
    if (window.google && google.maps && google.maps.InfoWindow) {
        infoWindow = new google.maps.InfoWindow();
    }

    // Otimiza o mapa
    gmpMap.innerMap.setOptions({
        mapTypeControl: false,
        streetViewControl: false
    });

    // Tenta obter a localização do usuário automaticamente na abertura
    useMyLocation();

    // Ouve o Place Picker para centralizar o mapa
    placePicker.addEventListener('gmpx-placechange', () => {
        const place = placePicker.value;

        if (place && place.location) {
            const newCenter = `${place.location.lat},${place.location.lng}`;
            gmpMap.center = newCenter;
            gmpMap.zoom = 15;
            mainMarker.position = newCenter;
            updateStatus(`Mapa centralizado em: ${place.displayName}`);
        }
    });

    // A chamada inicial do findNearbyFields é feita dentro de useMyLocation()
    // para garantir que a busca ocorra a partir da localização inicial correta.
});
// A CHAVE EXTRA '}' QUE ESTAVA AQUI FOI REMOVIDA