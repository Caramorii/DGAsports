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