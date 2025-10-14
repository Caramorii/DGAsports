// Botão "Entrar"
function entrar() {
    // Redireciona para a página de login
    window.open("login.html", "_blank");
}

// Botão "Cadastrar"
function cadastrar() {
    // Redireciona para a página de cadastro
    window.open('register.html', "_blank");
}

// Botão "Procurar partidas"
function futebol() {
    // Redireciona para a página de busca de partidas
    window.open('futebol.html', '_black');
}

// Botão "Assinar Premium"
document.querySelector('.hero div button:last-of-type').addEventListener('click', () => {
    // Redireciona para a página de assinatura premium
    window.location.href = 'premium.html';
});

// Cards de esportes - efeito de clique
document.querySelectorAll('.card').forEach(card => {
    card.addEventListener('click', () => {
        card.classList.toggle('ativo');
        // Você pode mostrar mais informações ou destacar o card
    });
});

// Navegação suave para âncoras
document.querySelectorAll('a[href^="#"]').forEach(link => {
    link.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth' });
        }
    });
});

// Animação no título "Junte-se à Comunidade" ao clicar
const titulo = document.querySelector('.hero h2');
if (titulo) {
    titulo.addEventListener('click', () => {
        titulo.style.animation = 'pulse 0.3s 3';
    });
}
