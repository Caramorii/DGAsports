document.addEventListener('DOMContentLoaded', () => {

    // --- 1. LÓGICA DAS ABAS (continua igual) ---
    const todasAsAbas = document.querySelectorAll('.tab-esporte');
    todasAsAbas.forEach(aba => {
        aba.addEventListener('click', () => {
            todasAsAbas.forEach(a => a.classList.remove('ativo'));
            aba.classList.add('ativo');
        });
    });

    // --- 2. LÓGICA ATUALIZADA DO "ENTRAR NA PARTIDA" ---

    const todosBotoesEntrar = document.querySelectorAll('.btn-entrar');

    // Pega o ID da quadra que guardamos no container principal
    const idDaQuadra = document.querySelector('.container-detalhes').dataset.quadraId;

    todosBotoesEntrar.forEach(botao => {
        botao.addEventListener('click', async () => { // Usamos 'async' para poder usar 'await'

            // Pega o card-pai do botão
            const cardPai = botao.closest('.card-horario');

            // Pega a hora que guardamos no card
            const horaDaPartida = cardPai.dataset.hora;

            // Mostra ao usuário que algo está acontecendo
            botao.disabled = true;
            botao.textContent = 'Processando...';

            try {
                // Chama o "garçom" (fetch) para a "cozinha" (Flask)
                const resposta = await fetch('/quadra/entrar', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json', // Avisa que estamos enviando JSON
                    },
                    body: JSON.stringify({ // Converte nossos dados em texto JSON
                        id_quadra: parseInt(idDaQuadra), // Converte o ID para número
                        hora_partida: horaDaPartida
                    })
                });

                // Pega a resposta da cozinha (Flask) e converte de JSON
                const dados = await resposta.json();

                if (dados.status === 'sucesso') {
                    // --- SUCESSO! Atualiza o HTML ---

                    // 1. Atualiza a contagem (ex: "3 / 10")
                    const elementoContagem = cardPai.querySelector('.contagem');
                    const maxJogadores = cardPai.querySelector('.barra-vagas').max;
                    elementoContagem.textContent = `${dados.nova_contagem} / ${maxJogadores}`;

                    // 2. Atualiza a barra de progresso
                    const elementoProgress = cardPai.querySelector('.barra-vagas');
                    elementoProgress.value = dados.nova_contagem;

                    // 3. Adiciona o avatar do novo jogador
                    const listaAvatares = cardPai.querySelector('.lista-avatares');
                    const novoAvatarHTML = `
                        <img src="${dados.novo_jogador.avatar}" 
                             alt="${dados.novo_jogador.nome}" 
                             title="${dados.novo_jogador.nome}">
                    `;
                    // Remove a mensagem "Ninguém agendado" se ela existir
                    const semJogadoresMsg = listaAvatares.querySelector('.sem-jogadores');
                    if (semJogadoresMsg) {
                        semJogadoresMsg.remove();
                    }
                    listaAvatares.insertAdjacentHTML('beforeend', novoAvatarHTML);

                    // 4. Atualiza o botão
                    botao.textContent = 'Você está na partida';
                    // (O botão já está desabilitado)

                } else {
                    // --- ERRO! Avisa o usuário ---
                    alert(dados.mensagem); // Ex: "Partida lotada!" ou "Você precisa estar logado"
                    botao.disabled = false; // Habilita o botão de novo
                    botao.textContent = 'Entrar na Partida';
                }

            } catch (error) {
                // Erro de rede ou algo quebrou
                console.error("Erro ao tentar entrar na partida:", error);
                alert("Erro de conexão. Tente novamente.");
                botao.disabled = false;
                botao.textContent = 'Entrar na Partida';
            }
        });
    });

    // --- 3. LÓGICA DO BOTÃO "SEGUIR" (continua igual) ---
    // ...
});