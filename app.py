# Importa as ferramentas do Flask e nossas funções do banco de dados
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort, jsonify

# Importa TODAS as funções que criamos no banco_de_dados.py
from banco_de_dados import (
    criar_tabelas_iniciais, popular_dados_iniciais, 
    cadastrar_usuario, verificar_login,
    get_quadras, get_detalhes_quadra, 
    adicionar_jogador_partida, get_detalhes_reserva
)

# (Opcional, para a simulação da API)
# No topo do arquivo, você importaria a biblioteca
# import mercadopago 

# Inicializa a aplicação Flask
app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_super_segura_12345'

# (Opcional, para a simulação da API)
# sdk = mercadopago.SDK("SUA_CHAVE_DE_TESTE")

# --- ROTAS DA APLICAÇÃO ---

@app.route('/')
def home():
    return render_template('DGASports.html')

@app.route('/explorar')
def explorar():
    # Atualizado para usar o filtro do banco de dados
    localidade_busca = request.args.get('localidade', '').strip().lower()
    esporte_busca = request.args.get('esporte', '').strip().lower()

    quadras_filtradas = get_quadras(localidade_busca, esporte_busca)

    return render_template(
        'explorar.html', 
        quadras=quadras_filtradas,
        localidade_busca=localidade_busca,
        esporte_busca=esporte_busca
    )

@app.route('/quadra/<int:id_da_quadra>')
def detalhes_quadra(id_da_quadra):
    # Atualizado para buscar do banco de dados
    quadra_encontrada = get_detalhes_quadra(id_da_quadra)
    
    if quadra_encontrada is None:
        abort(404) 
        
    return render_template('detalhes_quadra.html', quadra=quadra_encontrada)

# --- ROTAS DE AUTENTICAÇÃO ---

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
            # Salva o ID do usuário na sessão (MUITO IMPORTANTE)
            session['usuario_id'] = usuario['id'] 
            session['usuario_logado'] = usuario['email']
            session['nome_usuario'] = usuario['nome']
            flash(f"Login bem-sucedido! Bem-vindo(a), {usuario['nome']}!")
            # Pega a URL 'proximo' se ela existir
            proxima_pagina = request.args.get('proximo')
            if proxima_pagina:
                return redirect(proxima_pagina)
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

# --- ROTAS ESTÁTICAS (Exemplo) ---

@app.route('/social')
def social():
    return render_template('dga.social.html')

@app.route('/mensagem')
def mensagem():
    return render_template('DGAmensagem.html')

@app.route('/usuario')
def usuario():
    return render_template('DGAusuario.html')

# --- ROTAS DA API E RESERVA (O FLUXO PRINCIPAL) ---

@app.route('/quadra/entrar', methods=['POST'])
def entrar_na_partida():
    """API para quadras PÚBLICAS (chamada pelo JavaScript 'fetch')."""
    
    # 1. Verifica se o usuário está logado
    if 'usuario_id' not in session:
        return jsonify({'status': 'erro', 'mensagem': 'Você precisa estar logado para entrar.'}), 401

    # 2. Pega os dados enviados pelo JavaScript
    dados = request.get_json()
    horario_id = dados.get('horario_id') 
    usuario_id = session['usuario_id']

    if not horario_id:
         return jsonify({'status': 'erro', 'mensagem': 'ID do horário não fornecido.'}), 400

    # 3. Chama a função do banco de dados
    resultado = adicionar_jogador_partida(usuario_id, horario_id)
    
    # 4. Retorna o resultado (sucesso ou erro) para o JavaScript
    return jsonify(resultado)

@app.route('/reservar/<int:horario_id>')
def reservar(horario_id):
    """Página de checkout para quadras PRIVADAS."""
    
    # 1. Verifica se o usuário está logado
    if 'usuario_id' not in session:
        flash("Você precisa estar logado para fazer uma reserva.")
        return redirect(url_for('login', proximo=request.url)) # Salva a URL para redirecionar de volta

    # 2. Busca os dados da reserva
    reserva = get_detalhes_reserva(horario_id)
    
    if reserva is None:
        abort(404) # Horário não encontrado

    # 3. Pega os dados do usuário atual na sessão
    usuario_atual = {
        'id': session['usuario_id'],
        'nome': session['nome_usuario']
    }

    # 4. Renderiza a nova página de checkout
    return render_template(
        'reserva_privada.html', 
        reserva=reserva,
        usuario_atual=usuario_atual
    )

@app.route('/confirmar_reserva', methods=['POST'])
def confirmar_reserva():
    """Recebe o formulário de pagamento (SIMULAÇÃO DE API)."""

    # 1. Verifica login
    if 'usuario_id' not in session:
        flash("Sua sessão expirou. Por favor, faça login novamente.")
        return redirect(url_for('login'))

    # 2. Pega dados do formulário
    horario_id = request.form.get('horario_id')
    metodo_pagamento = request.form.get('metodo') 
    usuario_id = session['usuario_id']

    # --- INÍCIO DA LÓGICA DA API (PARA SUA APRESENTAÇÃO) ---
    
    # 1. BUSCAR O PREÇO NO BANCO DE DADOS
    # (No nosso caso, a função get_detalhes_reserva faria isso, 
    # mas para o exemplo, vamos apenas simular)
    # preco_da_vaga = buscar_preco(horario_id) ... R$ 15,00
    
    # 2. MONTAR O "PEDIDO" PARA A API
    # dados_do_pagamento = { "transaction_amount": 15.00, ... }
    
    # 3. CHAMAR A API (PUXAR A API)
    try:
        # ----> LINHA MÁGICA DE EXEMPLO <----
        # resultado_api = sdk.payment().create(dados_do_pagamento) 
        
        # SIMULAÇÃO: Vamos fingir que a API sempre aprova
        status_da_api = "approved" 
        
        # 4. VERIFICAR A RESPOSTA DA API
        if status_da_api == "approved":
            # SE A API APROVOU, SALVA NO NOSSO BANCO
            
            resultado = adicionar_jogador_partida(usuario_id, int(horario_id))

            if resultado['status'] == 'sucesso':
                flash(f"Pagamento Aprovado! Reserva confirmada.")
                return redirect(url_for('home'))
            else:
                # DEU CERTO PAGAR, MAS DEU ERRO AO RESERVAR (ex: lotou no último segundo)
                # (Aqui você teria que estornar o pagamento)
                # sdk.payment().refund(pagamento_id) 
                flash(f"Pagamento Aprovado, mas erro ao reservar: {resultado['mensagem']}. O valor será estornado.")
                return redirect(url_for('reservar', horario_id=horario_id))

        else:
            # SE A API REJEITOU (ex: cartão sem limite)
            flash("Pagamento foi recusado pela operadora.")
            return redirect(url_for('reservar', horario_id=horario_id))

    except Exception as e:
        # SE DEU ERRO AO CONECTAR NA API (ex: API offline)
        flash(f"Erro ao processar o pagamento: {e}")
        return redirect(url_for('reservar', horario_id=horario_id))
    
    # --- FIM DA LÓGICA DA API ---


# --- INICIALIZAÇÃO DO SERVIDOR ---

if __name__ == '__main__':
    # Garante que o banco de dados e as tabelas sejam criados
    criar_tabelas_iniciais()
    # Insere os dados iniciais (quadras, horários) se o DB estiver vazio
    popular_dados_iniciais()
    
    app.run(debug=True)