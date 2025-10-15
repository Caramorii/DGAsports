# Importa as ferramentas do Flask e nossas funções do banco de dados
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from banco_de_dados import criar_tabela_usuarios, cadastrar_usuario, verificar_login

# Inicializa a aplicação Flask
app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_super_segura_12345'

# --- BANCO DE DADOS SIMULADO PARA AS QUADRAS ---
# Em um projeto real, isso viria do SQLite.

# Perfis de jogadores para simulação
JOGADORES = [
    {'id': 1, 'nome': 'Carlos', 'avatar': 'https://placehold.co/50x50/70d155/1A202C?text=C'},
    {'id': 2, 'nome': 'Beatriz', 'avatar': 'https://placehold.co/50x50/4A90E2/FFFFFF?text=B'},
    {'id': 3, 'nome': 'Daniel', 'avatar': 'https://placehold.co/50x50/f6ad55/1A202C?text=D'},
    {'id': 4, 'nome': 'Fernanda', 'avatar': 'https://placehold.co/50x50/f56565/FFFFFF?text=F'},
    {'id': 5, 'nome': 'Lucas', 'avatar': 'https://placehold.co/50x50/a0aec0/1A202C?text=L'},
]

DADOS_DAS_QUADRAS = [
    {
        'id': 1, 'nome': 'Quadra Amazonas', 'cidade': 'Franca', 'estado': 'SP', 'tipo': 'privada', 'seguindo': True,
        'esportes': ['Futebol', 'Basquete'], 'imagem': 'assets/quadraamazonas.jpeg',
        'horarios': [
            {'hora': '18:00 - 19:00', 'jogadores_atuais': 2, 'max_jogadores': 10, 'jogadores': [JOGADORES[0], JOGADORES[2]]},
            {'hora': '19:00 - 20:00', 'jogadores_atuais': 3, 'max_jogadores': 10, 'jogadores': [JOGADORES[1], JOGADORES[3], JOGADORES[4]]},
            {'hora': '20:00 - 21:00', 'jogadores_atuais': 1, 'max_jogadores': 10, 'jogadores': [JOGADORES[0]]},
        ]
    },
    {
        'id': 2, 'nome': 'Gol De Placa', 'cidade': 'Franca', 'estado': 'SP', 'tipo': 'privada', 'seguindo': False,
        'esportes': ['Futebol'], 'imagem': 'assets/goldeplaca.jpg',
        'horarios': [
            {'hora': '19:30 - 20:30', 'jogadores_atuais': 2, 'max_jogadores': 12, 'jogadores': [JOGADORES[1], JOGADORES[2]]},
            {'hora': '20:30 - 21:30', 'jogadores_atuais': 1, 'max_jogadores': 12, 'jogadores': [JOGADORES[4]]},
        ]
    },
    {
        'id': 3, 'nome': 'Arena Residencial Palermo', 'cidade': 'Franca', 'estado': 'SP', 'tipo': 'publica', 'seguindo': True,
        'esportes': ['Futebol', 'Basquete'], 'imagem': 'assets/residencialpalermo.jpeg',
        'horarios': [
            {'hora': '19:00 - 20:00', 'jogadores_atuais': 0, 'max_jogadores': 15, 'jogadores': []},
            {'hora': '20:00 - 21:00', 'jogadores_atuais': 1, 'max_jogadores': 15, 'jogadores': [JOGADORES[3]]},
        ]
    },
    {
        'id': 4, 'nome': 'Quadra Parque Castelo', 'cidade': 'Franca', 'estado': 'SP', 'tipo': 'publica', 'seguindo': False,
        'esportes': ['Basquete', 'Futebol'], 'imagem': 'assets/parquecastelo.jpeg',
        'horarios': [
            {'hora': '17:00 - 18:00', 'jogadores_atuais': 3, 'max_jogadores': 10, 'jogadores': [JOGADORES[0], JOGADORES[1], JOGADORES[4]]},
            {'hora': '18:00 - 19:00', 'jogadores_atuais': 1, 'max_jogadores': 10, 'jogadores': [JOGADORES[2]]},
        ]
    }
]

# --- ROTAS DA APLICAÇÃO ---

@app.route('/')
def home():
    return render_template('DGASports.html')

@app.route('/explorar')
def explorar():
    # Agora a rota explorar envia os dados das quadras para o template
    return render_template('explorar.html', quadras=DADOS_DAS_QUADRAS)

# ROTA NOVA PARA A PÁGINA DE DETALHES
@app.route('/quadra/<int:id_da_quadra>')
def detalhes_quadra(id_da_quadra):
    # Procura a quadra na nossa lista pelo ID
    quadra_encontrada = next((quadra for quadra in DADOS_DAS_QUADRAS if quadra['id'] == id_da_quadra), None)
    
    if quadra_encontrada is None:
        abort(404) # Retorna erro "Não Encontrado" se o ID não existir
        
    return render_template('detalhes_quadra.html', quadra=quadra_encontrada)

# Suas rotas existentes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        resultado = cadastrar_usuario(nome, email, senha)
        flash(resultado)
        if "sucesso" in resultado:
            return redirect(url_for('login'))
        else:
            return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        usuario = verificar_login(email, senha)
        if usuario:
            session['usuario_logado'] = usuario['email']
            session['nome_usuario'] = usuario['nome']
            flash(f"Login bem-sucedido! Bem-vindo(a), {usuario['nome']}!")
            return redirect(url_for('home'))
        else:
            flash("E-mail ou senha inválidos. Tente novamente.")
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Você saiu da sua conta.")
    return redirect(url_for('home'))

@app.route('/social')
def social():
    return render_template('dga.social.html')

@app.route('/mensagem')
def mensagem():
    return render_template('DGAmensagem.html')

@app.route('/perfil')
def perfil():
    return render_template('DGAusuario.html')

if __name__ == '__main__':
    criar_tabela_usuarios()
    app.run(debug=True)