document.addEventListener('DOMContentLoaded', () => {

    // --- ELEMENTOS DO DOM ---
    const filtroEstado = document.getElementById('filtro-estado');
    const filtroCidade = document.getElementById('filtro-cidade');
    const searchForm = document.querySelector('.filter-panel');
    const statusBusca = document.getElementById('status-busca');
    const detailsButtons = document.querySelectorAll('.details-btn');

    // --- DADOS PARA OS FILTROS DINÂMICOS ---
    const cidadesPorEstado = {
        "SP": ["Franca", "Ribeirão Preto", "São Paulo", "Campinas"],
        "RJ": ["Rio de Janeiro", "Niterói", "Duque de Caxias"],
        "MG": ["Belo Horizonte", "Uberlândia", "Contagem"]
    };

    // --- FUNÇÕES ---

    /**
     * Atualiza o dropdown de cidades com base no estado selecionado.
     */
    function atualizarCidades() {
        const estadoSelecionado = filtroEstado.value;

        // Limpa as opções atuais
        filtroCidade.innerHTML = '';

        if (estadoSelecionado && cidadesPorEstado[estadoSelecionado]) {
            filtroCidade.disabled = false;

            // Adiciona uma opção padrão
            const defaultOption = document.createElement('option');
            defaultOption.textContent = 'Selecione a Cidade';
            defaultOption.value = '';
            filtroCidade.appendChild(defaultOption);

            // Adiciona as cidades do estado selecionado
            cidadesPorEstado[estadoSelecionado].forEach(cidade => {
                const option = document.createElement('option');
                option.textContent = cidade;
                option.value = cidade;
                filtroCidade.appendChild(option);
            });
        } else {
            // Se nenhum estado for selecionado, desabilita o campo de cidade
            const defaultOption = document.createElement('option');
            defaultOption.textContent = 'Escolha um estado';
            filtroCidade.appendChild(defaultOption);
            filtroCidade.disabled = true;
        }
    }

    /**
     * Simula a ação de busca ao clicar no botão.
     */
    function simularBusca(event) {
        event.preventDefault(); // Impede o recarregamento da página

        const cidade = filtroCidade.value;
        const esporte = document.getElementById('filtro-esporte').value;

        if (!cidade) {
            statusBusca.textContent = "Por favor, selecione uma cidade para buscar.";
            statusBusca.style.color = "#ffc107"; // Amarelo para alerta
            return;
        }

        statusBusca.textContent = `Buscando quadras de ${esporte} em ${cidade}...`;
        statusBusca.style.color = "#1CB5E0"; // Azul claro para informação

        // Simula um tempo de espera (como uma busca em um servidor)
        setTimeout(() => {
            statusBusca.textContent = `Exibindo resultados para ${cidade}.`;
            statusBusca.style.color = "#1ab480"; // Verde para sucesso
        }, 1500); // 1.5 segundos
    }

    /**
     * Adiciona funcionalidade aos botões "Ver Detalhes".
     */
    function adicionarInteracaoCards() {
        detailsButtons.forEach(button => {
            button.addEventListener('click', (event) => {
                // Pega o nome da quadra do elemento H3 mais próximo
                const card = event.target.closest('.court-card');
                const courtName = card.querySelector('h3').textContent;

                alert(`Função "Ver Detalhes" para a quadra: ${courtName}\n\nEm uma aplicação real, isso abriria uma nova página com mais informações.`);
            });
        });
    }


    // --- INICIALIZAÇÃO E EVENT LISTENERS ---

    filtroEstado.addEventListener('change', atualizarCidades);
    searchForm.addEventListener('submit', simularBusca);
    adicionarInteracaoCards();
});