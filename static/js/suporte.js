// Aguarda o conteúdo da página carregar completamente
document.addEventListener("DOMContentLoaded", function() {

    // --- LÓGICA DO FORMULÁRIO DE SUPORTE ---
    const supportForm = document.getElementById("support-form");
    const submitButton = supportForm ? supportForm.querySelector('button[type="submit"]') : null;

    // Verifica se o formulário existe na página
    if (supportForm && submitButton) {
        // Adiciona um ouvinte de evento para o 'submit' (envio) do formulário
        supportForm.addEventListener("submit", function(event) {
            // Este código agora não previne o envio (event.preventDefault()),
            // permitindo que o formulário seja enviado para o action definido no HTML.
            // Apenas damos um feedback visual ao usuário.

            // 1. Desabilita o botão para evitar envios múltiplos
            submitButton.disabled = true;

            // 2. Altera o texto do botão para feedback
            submitButton.textContent = 'Enviando...';

            // O formulário será enviado normalmente para o backend (Flask).
            // O backend deve ser responsável por redirecionar o usuário após o processamento.
        });
    }

    // --- LÓGICA DO LINK "VOLTAR" ---
    const backLink = document.querySelector(".back-link a");
    if (backLink) { // Verifica se o link existe
        backLink.addEventListener("click", function(event) {
            event.preventDefault(); // Previne a navegação padrão do link.
            window.history.back();  // Usa a API do navegador para voltar para a página anterior.
        });
    }
});
