# DGAsports 🏀⚽

Projeto de um site para localizar e agendar horários em quadras próximas ao usuario.  
Feito em HTML, CSS e JavaScript. E back-end com Python Flask e sqlite.

## 🚀 Principais Funcionalidades
Autenticação de Usuários: Sistema completo de cadastro, login e logout com gerenciamento de sessão e mensagens de feedback.

- Busca e Filtro Inteligente:

- Seleção de Cidade e Esporte: Encontre quadras filtrando por localidade e pelo esporte desejado (Futebol, Basquete, Vôlei, etc.).
Geolocalização: Use sua localização atual para encontrar as quadras mais próximas.
Agendamento e Fila Dinâmica:

- Marcação de Horários: Visualize o calendário de cada quadra com datas e horários disponíveis.
Fila em Tempo Real: Entre em partidas em quadras públicas e veja a contagem de jogadores ser atualizada dinamicamente, sem precisar recarregar a página.
Sistema de Reserva Completo:

- Quadras Públicas: Entrada livre e gratuita nas partidas.
Quadras Privadas: Fluxo de reserva com simulação de pagamento via Cartão de Crédito e PIX (com geração de QR Code em tempo real).
Comunidade (DGA Social): Uma mini rede social para posts, interações e um sistema de mensagens diretas.

- Páginas Adicionais: Seção para visualização de Campeonatos e uma Central de Suporte com formulário de contato.

- Tema Dinâmico: Suporte para tema claro (light) e escuro (dark) em toda a aplicação, com persistência da escolha do usuário.

## 🔧 Tecnologias
- Backend: Python, Flask
- Banco de Dados: SQLite3
- Frontend: HTML5, CSS3, JavaScript
- Bibliotecas Python: qrcode (para geração de QR Code PIX)

## 📂 Estrutura
/DGAsports
|
|-- app.py                  # Arquivo principal da aplicação Flask (rotas e lógica de negócio)
|-- banco_de_dados.py       # Módulo para toda a interação com o banco de dados SQLite
|
|-- static/                 # Pasta para arquivos estáticos (CSS, JS, Imagens)
|   |-- css/                # Contém todas as folhas de estilo (main.css, auth.css, etc.)
|   |-- js/                 # Contém os scripts JavaScript (theme_switcher.js, detalhes.js, etc.)
|   |-- assets/             # Contém imagens, logos e outros recursos visuais
|
|-- templates/              # Pasta para os templates HTML (renderizados pelo Flask)
|   |-- DGAsports.html      # Página inicial (Home)
|   |-- explorar.html       # Página de busca e listagem de quadras
|   |-- detalhes_quadra.html # Página com detalhes de uma quadra específica
|   |-- login.html          # Formulário de login
|   |-- register.html       # Formulário de cadastro
|   |-- ... (e todas as outras páginas .html)
|
|-- meu_site.db             # Arquivo do banco de dados SQLite (gerado automaticamente)

## 👨‍💻 Como rodar
```bash
git clone https://github.com/Caramorii/DGAsports.git
cd DGAsports
git checkout master
Crie e ative um ambiente virtual (recomendado):
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
