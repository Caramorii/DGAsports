// Função para aplicar o tema salvo
function applySavedTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    if (savedTheme === 'light') {
        document.body.classList.add('light-theme');
    } else {
        document.body.classList.remove('light-theme');
    }
}

// Aplica o tema imediatamente ao carregar o script
applySavedTheme();

document.addEventListener('DOMContentLoaded', () => {
    const themeToggleButton = document.getElementById('theme-toggle');
    if (!themeToggleButton) return;

    const sunIcon = themeToggleButton.querySelector('.sun-icon');
    const moonIcon = themeToggleButton.querySelector('.moon-icon');

    function updateIcons() {
        if (document.body.classList.contains('light-theme')) {
            sunIcon.style.display = 'none';
            moonIcon.style.display = 'block';
        } else {
            sunIcon.style.display = 'block';
            moonIcon.style.display = 'none';
        }
    }

    themeToggleButton.addEventListener('click', () => {
        document.body.classList.toggle('light-theme');
        const newTheme = document.body.classList.contains('light-theme') ? 'light' : 'dark';
        localStorage.setItem('theme', newTheme);
        updateIcons();
    });

    // Garante que os ícones estejam corretos no carregamento da página
    updateIcons();
});
document.addEventListener('DOMContentLoaded', function() {
    // Lógica para selecionar o emoji
    const cards = document.querySelectorAll('.card-horario');

    cards.forEach(card => {
        const botoesEsporte = card.querySelectorAll('.btn-esporte-opcao');
        const btnEntrar = card.querySelector('.btn-entrar');

        botoesEsporte.forEach(btn => {
            btn.addEventListener('click', function() {
                // Remove seleção dos outros emojis do mesmo card
                botoesEsporte.forEach(b => b.classList.remove('selected'));
                // Seleciona o atual
                this.classList.add('selected');
                
                // Ativa o botão de reserva e guarda o esporte escolhido
                if (btnEntrar) {
                    btnEntrar.disabled = false;
                    card.setAttribute('data-esporte-selecionado', this.getAttribute('data-esporte'));
                }
            });
        });
    });
});

// Ao clicar no botão Entrar/Reservar, certifique-se de enviar o esporte:
// No seu arquivo detalhes.js, na função que faz o fetch para '/quadra/entrar':
/*
    const esporte = card.getAttribute('data-esporte-selecionado') || card.getAttribute('data-esporte-reservado');
    body: JSON.stringify({
        horario_id: id,
        esporte_selecionado: esporte
    })
*/