// Botão "Entrar"
document.querySelectorAll('.btn-entrar').forEach(btn => {
    btn.addEventListener('click', () => {
        // Redireciona para a página de login
        window.location.href = 'login.html';
    });
});

// Botão "Cadastrar"
document.querySelectorAll('.btn-cadastrar').forEach(btn => {
    btn.addEventListener('click', () => {
        // Redireciona para a página de cadastro
        window.location.href = 'register.html';
    });
});

// Botão "Procurar partidas"
document.querySelectorAll('.btn-procurar').forEach(btn => {
    btn.addEventListener('click', () => {
        // Redireciona para a página de busca de partidas
        window.location.href = 'partidas.html';
    });
});

// Botão "Assinar Premium"
document.querySelectorAll('.btn-premium').forEach(btn => {
    btn.addEventListener('click', () => {
        // Redireciona para a página de assinatura premium
        window.location.href = 'premium.html';
    });
});

// Cards de esportes - efeito de clique
document.querySelectorAll('.card-bg, .card-shadow').forEach(card => {
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

// Exemplo: animação no título "Junte-se à Comunidade" ao clicar
const titulo = document.querySelector('.hero-gradient h2');
if (titulo) {
    titulo.addEventListener('click', () => {
        titulo.style.animation = 'pulse 0.3s 3';
    });
}