from flask import render_template, request, redirect, url_for, flash, session, abort, jsonify
from datetime import date
import qrcode
import uuid
import io
import base64
import os
from werkzeug.utils import secure_filename
from banco_de_dados import (
    get_quadras, get_detalhes_quadra, get_horarios_por_data,
    adicionar_jogador_partida, get_detalhes_reserva,
    remover_jogador_partida, conectar, cadastrar_usuario, 
    verificar_login, cadastrar_nova_quadra
)

def init_routes(app):
    
    # --- HOME E EXPLORAÇÃO ---
    @app.route('/')
    def home():
        return render_template('DGASports.html')

    @app.route('/explorar')
    def explorar():
        localidade_busca_raw = request.args.get('localidade', '').strip()
        esporte_busca_raw = request.args.get('esporte', '').strip()
        quadras_filtradas = get_quadras(localidade_busca_raw or None, esporte_busca_raw or None)
        return render_template(
            'explorar.html', 
            quadras=quadras_filtradas, 
            localidade_busca=localidade_busca_raw, 
            esporte_busca=esporte_busca_raw
        )

    @app.route('/quadra/<int:id_da_quadra>')
    def detalhes_quadra(id_da_quadra):
        usuario_id_atual = session.get('usuario_id')
        quadra_encontrada = get_detalhes_quadra(id_da_quadra, usuario_id_atual)
        if quadra_encontrada is None:
            abort(404) 
        return render_template('detalhes_quadra.html', quadra=quadra_encontrada, hoje=date.today().isoformat())

    @app.route('/campeonatos')
    def campeonatos():
        return render_template('campeonatos.html')

    # --- AUTENTICAÇÃO ---
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            nome = request.form['nome']
            email = request.form['email']
            senha = request.form['senha']
            cidade = request.form['cidade']
            resultado = cadastrar_usuario(nome, cidade, email, senha)
            flash(resultado, 'success' if "sucesso" in resultado else 'error')
            return redirect(url_for('login' if "sucesso" in resultado else 'register'))
        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            usuario = verificar_login(request.form['email'], request.form['senha'])
            if usuario:
                session.update({
                    'usuario_id': usuario['id'], 
                    'usuario_logado': usuario['email'], 
                    'nome_usuario': usuario['nome']
                })
                flash(f"Bem-vindo, {usuario['nome']}!", 'success')
                return redirect(request.args.get('proximo') or url_for('home'))
            flash("E-mail ou senha inválidos.", 'error')
        return render_template('login.html')

    @app.route('/logout')
    def logout():
        session.clear()
        flash("Você saiu da sua conta.")
        return redirect(url_for('home'))

    # --- ÁREA ADMINISTRATIVA (CORRIGIDA) ---
    @app.route('/admin/cadastrar_quadra', methods=['GET', 'POST'])
    def admin_cadastrar_quadra():
        # 1. Verificação de segurança
        if session.get('usuario_logado') != 'admin@gmail.com':
            flash("Acesso restrito!", "error")
            return redirect(url_for('login'))
        
        # 2. Processamento do formulário (POST)
        if request.method == 'POST':
            nome = request.form.get('nome')
            descricao = request.form.get('descricao')
            localizacao = request.form.get('localizacao')
            cidade = request.form.get('cidade')
            estado = request.form.get('estado')
            esporte = request.form.get('esporte')
        
            # Processamento da Imagem
            file = request.files.get('foto')
            if file and file.filename != '':
                filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
                upload_folder = os.path.join(app.root_path, 'static', 'uploads')
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                file.save(os.path.join(upload_folder, filename))
                foto_path = f"uploads/{filename}"
            else:
                foto_path = "uploads/default_quadra.jpg"

            # CHAMADA COM 7 ARGUMENTOS (DENTRO DO IF POST)
            cadastrar_nova_quadra(nome, descricao, localizacao, cidade, estado, esporte, foto_path)
            
            flash("Quadra cadastrada com sucesso!", "success")
            return redirect(url_for('explorar'))

        # 3. Retorno do Template (FORA DO IF POST, PARA O MÉTODO GET)
        return render_template('cadastrar_novas_quadras.html')

    # --- APIs (PARTIDAS) ---
    @app.route('/quadra/entrar', methods=['POST'])
    def entrar_na_partida():
        if 'usuario_id' not in session:
            return jsonify({'status': 'erro', 'mensagem': 'Faça login primeiro.'}), 401
        dados = request.get_json()
        resultado = adicionar_jogador_partida(session['usuario_id'], dados.get('horario_id'), dados.get('esporte_selecionado'))
        return jsonify(resultado)

    @app.route('/quadra/sair', methods=['POST'])
    def sair_da_partida():
        if 'usuario_id' not in session:
            return jsonify({'status': 'erro', 'mensagem': 'Faça login primeiro.'}), 401
        dados = request.get_json()
        resultado = remover_jogador_partida(session['usuario_id'], dados.get('horario_id'))
        return jsonify(resultado)

    @app.route('/api/quadra/<int:quadra_id>/horarios/<string:data_selecionada>')
    def api_get_horarios_por_data(quadra_id, data_selecionada):
        horarios = get_horarios_por_data(quadra_id, data_selecionada, session.get('usuario_id'))
        return jsonify({'status': 'sucesso', 'horarios': horarios})

    # --- RESERVAS E PAGAMENTO ---
    @app.route('/reservar/<int:horario_id>')
    def reservar(horario_id):
        if 'usuario_id' not in session:
            flash("Você precisa estar logado para reservar.")
            return redirect(url_for('login', proximo=request.url))
        reserva = get_detalhes_reserva(horario_id)
        if not reserva:
            abort(404)
        return render_template('reserva_privada.html', reserva=reserva, esporte_selecionado=request.args.get('esporte'))

    @app.route('/confirmar_reserva', methods=['POST'])
    def confirmar_reserva():
        metodo = request.form.get('metodo')
        horario_id = request.form.get('horario_id')
        esporte = request.form.get('esporte_selecionado')

        if metodo == 'pix':
            chave_pix = str(uuid.uuid4())
            qr = qrcode.make(chave_pix)
            buf = io.BytesIO()
            qr.save(buf, format="PNG")
            img_str = base64.b64encode(buf.getvalue()).decode("utf-8")
            return render_template('pagamento_pix.html', chave_pix=chave_pix, qr_code_data_uri=f"data:image/png;base64,{img_str}", horario_id=horario_id, esporte_selecionado=esporte)
        
        adicionar_jogador_partida(session['usuario_id'], int(horario_id), esporte)
        flash("Pagamento aprovado! Sua reserva está garantida.", "success")
        return redirect(url_for('home'))

    @app.route('/finalizar_pix', methods=['POST'])
    def finalizar_pix():
        adicionar_jogador_partida(session['usuario_id'], int(request.form.get('horario_id')), request.form.get('esporte_selecionado'))
        flash("PIX Confirmado! Reserva efetuada com sucesso.", "success")
        return redirect(url_for('home'))

    # --- PÁGINAS ESTÁTICAS ---


    @app.route('/social')
    def social():
        usuario_id = session.get('usuario_id')
        if not usuario_id:
            return redirect(url_for('login'))
        
        from banco_de_dados import get_perfil_social, usuario_tem_perfil_social
        
        if usuario_tem_perfil_social(usuario_id):
            perfil = get_perfil_social(usuario_id)
            return render_template('dga.social.html', dados=perfil)
        else:
        # IMPORTANTE: Envia um dicionário vazio para não dar erro no template
            return render_template('cadastro_social.html', dados={})
    @app.route('/social/editar', methods=['GET', 'POST'])
    def editar_perfil():
        usuario_id = session.get('usuario_id')
        if not usuario_id:
            return redirect(url_for('login'))

        from banco_de_dados import get_perfil_social, salvar_perfil_social

        if request.method == 'POST':
            usuario_social = request.form.get('usuario_social')
            bio = request.form.get('bio')
            salvar_perfil_social(usuario_id, usuario_social, bio, foto_path)
            flash("Perfil salvo!", "success")
            return redirect(url_for('social'))
        perfil = get_perfil_social(usuario_id) or {}
        return render_template('cadastro_social.html', dados=perfil)

    @app.route('/mensagem')
    def mensagem(): return render_template('DGAmensagem.html')

    @app.route('/perfil')
    def perfil(): return render_template('perfil.html')

    @app.route('/suporte', methods=['GET', 'POST'])
    def suporte():
        if request.method == 'POST':
            flash('Sua mensagem foi enviada com sucesso!')
            return redirect(url_for('home'))
        return render_template('suporte.html')