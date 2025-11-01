# Importa as ferramentas do Flask e nossas funções do banco de dados
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort, jsonify
from datetime import date
import qrcode
import uuid
import io

# Importa TODAS as funções que criamos no banco_de_dados.py
# Certifique-se de adicionar 'conectar' se não estiver
from banco_de_dados import (
    criar_tabelas_iniciais, popular_dados_iniciais, 
    cadastrar_usuario, verificar_login,
    get_quadras, get_detalhes_quadra, get_horarios_por_data,
    adicionar_jogador_partida, get_detalhes_reserva,
    remover_jogador_partida, conectar # Adicionado 'conectar' aqui
)

# (Opcional, para a simulação da API)
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
    # Pega os valores do formulário
    localidade_busca_raw = request.args.get('localidade', '').strip()
    esporte_busca_raw = request.args.get('esporte', '').strip()

    # Passa para a função de busca. Se a string estiver vazia, vira None.
    quadras_filtradas = get_quadras(localidade_busca_raw or None, esporte_busca_raw or None)

    return render_template(
        'explorar.html', 
        quadras=quadras_filtradas, # Os resultados da busca
        localidade_busca=localidade_busca_raw, # Para preencher o campo de busca
        esporte_busca=esporte_busca_raw # Para selecionar a opção correta no <select>
    )

@app.route('/quadra/<int:id_da_quadra>')
def detalhes_quadra(id_da_quadra):
    usuario_id_atual = session.get('usuario_id')
    
    # Passa o ID do usuário para a função
    quadra_encontrada = get_detalhes_quadra(id_da_quadra, usuario_id_atual)
    
    if quadra_encontrada is None:
        abort(404) 
        
    return render_template(
        'detalhes_quadra.html', 
        quadra=quadra_encontrada,
        hoje=date.today().isoformat() # Passa a data de hoje para o template
    )

# --- ROTAS DE AUTENTICAÇÃO ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        resultado = cadastrar_usuario(nome, email, senha)
        if "sucesso" in resultado:
            flash(resultado, 'success') # Categoria 'success'
            return redirect(url_for('login'))
        else:
            flash(resultado, 'error') # Categoria 'error'
            return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        usuario = verificar_login(email, senha)
        if usuario:
            session['usuario_id'] = usuario['id'] 
            session['usuario_logado'] = usuario['email']
            session['nome_usuario'] = usuario['nome']
            flash(f"Login bem-sucedido! Bem-vindo(a), {usuario['nome']}!", 'success')
            proxima_pagina = request.args.get('proximo')
            if proxima_pagina:
                return redirect(proxima_pagina)
            return redirect(url_for('home'))
        else:
            flash("E-mail ou senha inválidos. Tente novamente.", 'error')
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

@app.route('/campeonatos')
def campeonatos():
    # No futuro, você pode adicionar lógica para buscar campeonatos do banco de dados
    return render_template('campeonatos.html')

@app.route('/perfil')
def perfil():
    return render_template('DGAusuario.html')

# --- ROTA DE SUPORTE (COM LÓGICA DE FORMULÁRIO) ---
@app.route('/suporte', methods=['GET', 'POST'])
def suporte():
    # Se o formulário for enviado (método POST)
    if request.method == 'POST':
        # 1. Coleta os dados do formulário
        nome = request.form.get('name')
        email = request.form.get('email')
        assunto = request.form.get('subject')
        mensagem = request.form.get('message')

        # 2. Processa os dados (aqui, apenas imprimimos no console)
        # Em um projeto real, você enviaria um e-mail ou salvaria no banco de dados.
        print(f"--- NOVA MENSAGEM DE SUPORTE ---")
        print(f"Nome: {nome} ({email})")
        print(f"Assunto: {assunto}")
        print(f"Mensagem: {mensagem}")
        print(f"---------------------------------")

        # 3. Envia uma mensagem de sucesso e redireciona
        flash('Sua mensagem foi enviada com sucesso! Entraremos em contato em breve.')
        return redirect(url_for('home'))

    # Se for um acesso normal (método GET), apenas mostra a página
    return render_template('suporte.html')

# --- ROTAS DA API E RESERVA (O FLUXO PRINCIPAL) ---

@app.route('/quadra/entrar', methods=['POST'])
def entrar_na_partida():
    """API para quadras PÚBLICAS (chamada pelo JavaScript 'fetch')."""
    
    if 'usuario_id' not in session:
        return jsonify({'status': 'erro', 'mensagem': 'Você precisa estar logado para entrar.'}), 401

    dados = request.get_json()
    horario_id = dados.get('horario_id') 
    esporte_selecionado = dados.get('esporte_selecionado')
    usuario_id = session['usuario_id']

    if not horario_id or not esporte_selecionado:
         return jsonify({'status': 'erro', 'mensagem': 'Dados incompletos (horário ou esporte).'}), 400

    resultado = adicionar_jogador_partida(usuario_id, horario_id, esporte_selecionado)
    
    return jsonify(resultado)

@app.route('/quadra/sair', methods=['POST'])
def sair_da_partida():
    """API para sair de partidas PÚBLICAS."""
    
    if 'usuario_id' not in session:
        return jsonify({'status': 'erro', 'mensagem': 'Você precisa estar logado.'}), 401

    dados = request.get_json()
    horario_id = dados.get('horario_id')
    usuario_id = session['usuario_id']

    if not horario_id:
         return jsonify({'status': 'erro', 'mensagem': 'ID do horário não fornecido.'}), 400

    resultado = remover_jogador_partida(usuario_id, horario_id)
    
    return jsonify(resultado)

@app.route('/api/quadra/<int:quadra_id>/horarios/<string:data_selecionada>')
def api_get_horarios_por_data(quadra_id, data_selecionada):
    """API para buscar horários de uma quadra em uma data específica."""
    if 'usuario_id' not in session:
        return jsonify({'status': 'erro', 'mensagem': 'Acesso não autorizado.'}), 401

    usuario_id = session['usuario_id']
    
    try:
        # Valida o formato da data
        date.fromisoformat(data_selecionada)
    except ValueError:
        return jsonify({'status': 'erro', 'mensagem': 'Formato de data inválido.'}), 400

    # Chama a função do banco de dados para buscar os horários
    horarios = get_horarios_por_data(quadra_id, data_selecionada, usuario_id)
    return jsonify({'status': 'sucesso', 'horarios': horarios})


@app.route('/reservar/<int:horario_id>')
def reservar(horario_id):
    """Página de checkout para quadras PRIVADAS."""
    
    if 'usuario_id' not in session:
        flash("Você precisa estar logado para fazer uma reserva.")
        return redirect(url_for('login', proximo=request.url))

    esporte_selecionado = request.args.get('esporte')
    if not esporte_selecionado:
        abort(400, "Esporte não selecionado.")

    reserva = get_detalhes_reserva(horario_id)
    if reserva is None:
        abort(404) 

    usuario_atual = {
        'id': session['usuario_id'],
        'nome': session['nome_usuario']
    }

    return render_template(
        'reserva_privada.html', 
        reserva=reserva,
        usuario_atual=usuario_atual,
        esporte_selecionado=esporte_selecionado
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
    esporte_selecionado = request.form.get('esporte_selecionado')
    usuario_id = session['usuario_id']

    # --- NOVA LÓGICA DE PAGAMENTO ---
    if metodo_pagamento == 'pix':
        # 1. Gera uma chave PIX aleatória (simulação)
        chave_pix = str(uuid.uuid4())
        
        # 2. Gera o QR Code em memória
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(chave_pix)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        
        # 3. Salva a imagem em um buffer e converte para base64
        import base64
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        qr_code_data_uri = f"data:image/png;base64,{img_str}"

        # 4. Renderiza a nova página de pagamento PIX
        return render_template(
            'pagamento_pix.html',
            chave_pix=chave_pix,
            qr_code_data_uri=qr_code_data_uri,
            horario_id=horario_id,
            esporte_selecionado=esporte_selecionado
        )
    else: # Lógica antiga para Cartão de Crédito
        id_da_quadra = None
        try:
            conn, cursor = conectar()
            cursor.execute("SELECT quadra_id FROM horarios WHERE id = ?", (horario_id,))
            quadra_info = cursor.fetchone()
            if quadra_info: id_da_quadra = quadra_info['quadra_id']
            conn.close()

            status_da_api = "approved"
            if status_da_api == "approved":
                resultado = adicionar_jogador_partida(usuario_id, int(horario_id), esporte_selecionado)
                if resultado['status'] == 'sucesso':
                    flash(f"Pagamento Aprovado! Reserva confirmada para {esporte_selecionado}.")
                    return redirect(url_for('home'))
                else:
                    flash(f"Erro ao reservar: {resultado['mensagem']}")
            else:
                flash("Pagamento foi recusado pela operadora.")
        except Exception as e:
            flash(f"Erro ao processar o pagamento: {e}")
        finally:
            if id_da_quadra:
                return redirect(url_for('detalhes_quadra', id_da_quadra=id_da_quadra))
            return redirect(url_for('home'))

@app.route('/finalizar_pix', methods=['POST'])
def finalizar_pix():
    """Rota chamada após a 'confirmação' do pagamento PIX."""
    horario_id = request.form.get('horario_id')
    esporte_selecionado = request.form.get('esporte_selecionado')
    usuario_id = session['usuario_id']
    
    resultado = adicionar_jogador_partida(usuario_id, int(horario_id), esporte_selecionado)
    flash(f"Pagamento PIX confirmado! Reserva para {esporte_selecionado} efetuada com sucesso.")
    return redirect(url_for('home'))


# --- INICIALIZAÇÃO DO SERVIDOR ---

if __name__ == '__main__':
    # Garante que o banco de dados e as tabelas sejam criados
    criar_tabelas_iniciais()
    # Insere os dados iniciais (quadras, horários) se o DB estiver vazio
    popular_dados_iniciais()
    
    app.run(debug=True)
