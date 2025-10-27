document.addEventListener('DOMContentLoaded', () => {

    // --- 1. LÓGICA DAS ABAS (Corrigida para o HTML verde/escuro) ---
    const todasAsAbas = document.querySelectorAll('.tab');
    const todosOsConteudos = document.querySelectorAll('.tab-content');

    todasAsAbas.forEach(aba => {
        aba.addEventListener('click', () => {
            // Remove 'active' de todas as abas e conteúdos
            todasAsAbas.forEach(t => t.classList.remove('active'));
            todosOsConteudos.forEach(c => c.classList.remove('active'));

            // Adiciona 'active' na aba clicada
            aba.classList.add('active');

            // Pega o 'data-tab' da aba (ex: 'reserva' ou 'mapa')
            const targetTabName = aba.dataset.tab;
            const elementoParaMostrar = document.getElementById(targetTabName);
            if (elementoParaMostrar) {
                elementoParaMostrar.classList.add('active');
            }
        });
    });

    // --- 2. LÓGICA ATUALIZADA DO "ENTRAR NA PARTIDA" ---

    // Pega o tipo da quadra (privada ou publica) do atributo data
    const container = document.querySelector('.container');
    const quadraTipo = container.dataset.quadraTipo;

    const todosBotoesEntrar = document.querySelectorAll('.btn-entrar');

    todosBotoesEntrar.forEach(botao => {

        const cardPai = botao.closest('.card-horario');
        const idDoHorario = cardPai.dataset.horarioId;

        botao.addEventListener('click', async () => {

            botao.disabled = true;
            botao.textContent = 'Processando...';

            // --- AQUI ESTÁ A NOVA LÓGICA ---
            if (quadraTipo === 'privada') {
                // Se for privada, redireciona para a página de checkout
                // ex: /reservar/1
                window.location.href = `/reservar/${idDoHorario}`;

            } else {
                // Se for pública, usa a lógica fetch() antiga (grátis)
                try {
                    const resposta = await fetch('/quadra/entrar', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            horario_id: parseInt(idDoHorario)
                        })
                    });

                    const dados = await resposta.json();

                    if (dados.status === 'sucesso') {
                        // --- SUCESSO! (pública) ---
                        const elementoContagem = cardPai.querySelector('.contagem');
                        const maxJogadores = cardPai.querySelector('.barra-vagas').max;
                        elementoContagem.textContent = `${dados.nova_contagem} / ${maxJogadores}`;

                        const elementoProgress = cardPai.querySelector('.barra-vagas');
                        elementoProgress.value = dados.nova_contagem;

                        botao.textContent = 'Você está na partida';
                    } else {
                        // --- ERRO! (pública) ---
                        alert(dados.mensagem);
                        botao.disabled = false;
                        botao.textContent = 'Entrar na Partida';
                    }
                } catch (error) {
                    console.error("Erro ao tentar entrar na partida (pública):", error);
                    alert("Erro de conexão. Tente novamente.");
                    botao.disabled = false;
                    botao.textContent = 'Entrar na Partida';
                }
            }
            // --- FIM DA NOVA LÓGICA ---
        });
    });
});