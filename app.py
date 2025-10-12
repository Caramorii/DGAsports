# Importa as ferramentas do Flask e nossas funções do banco de dados
from flask import Flask, render_template, request, redirect, url_for, flash, session
from banco_de_dados import criar_tabela_usuarios, cadastrar_usuario, verificar_login

# Inicializa a aplicação Flask
app = Flask(__name__)

# Chave secreta para gerenciar sessões de usuário (MUITO IMPORTANTE!)
app.secret_key = 'sua_chave_secreta_super_segura_12345'

# --- ROTAS DA APLICAÇÃO ---

@app.route('/')
def home():
    """ Rota da página inicial (DGASports.html) """
    return render_template('DGASports.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """ Rota para a página de cadastro """
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
    """ Rota para a página de login """
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
    """ Rota para fazer logout do usuário """
    session.pop('usuario_logado', None)
    session.pop('nome_usuario', None)
    flash("Você saiu da sua conta.")
    return redirect(url_for('home'))

# Note que a função explorar aparece APENAS UMA VEZ
@app.route('/explorar')
def explorar():
    """ Rota para a página de explorar quadras """
    return render_template('explorar.html')

@app.route('/social')
def social():
    """ Rota para a página da comunidade DGA Social """
    return render_template('dga.social.html')


# --- INICIALIZAÇÃO ---

if __name__ == '__main__':
    # Garante que a tabela de usuários exista antes de rodar a aplicação
    criar_tabela_usuarios()
    # Roda a aplicação em modo de desenvolvimento (debug=True)
    app.run(debug=True)