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

    @app.route('/quadra/<int:quadra_id>') # Alterado de id para quadra_id
    def detalhes_quadra(quadra_id):
        # Use quadra_id aqui para garantir que é um número, não a função id()
        quadra_encontrada = get_detalhes_quadra(quadra_id) 
        
        if not quadra_encontrada:
            return "Quadra não encontrada", 404

        # Lógica para transformar a string de esportes em lista para os emojis
        if quadra_encontrada.get('esporte'):
            quadra_encontrada['lista_esportes'] = [e.strip() for e in quadra_encontrada['esporte'].split(',')]
        else:
            quadra_encontrada['lista_esportes'] = []

        return render_template('detalhes_quadra.html', 
                            quadra=quadra_encontrada, 
                            hoje=date.today().isoformat())

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
        if session.get('usuario_logado') != 'admin@gmail.com':
            flash("Acesso restrito!", "error")
            return redirect(url_for('login'))
        
        if request.method == 'POST':
            # Dados básicos
            nome = request.form.get('nome')
            descricao = request.form.get('descricao')
            localizacao = request.form.get('localizacao')
            cidade = request.form.get('cidade')
            estado = request.form.get('estado')
            esporte = request.form.get('esporte')
            
            # Dados de horário e preço
            abertura = request.form.get('hora_abertura')
            fechamento = request.form.get('hora_fechamento')
            preco = request.form.get('preco')

            # Upload de Imagem
            file = request.files.get('foto')
            if file and file.filename != '':
                # Salvando com UUID para evitar nomes duplicados
                extensao = os.path.splitext(file.filename)[1]
                novo_nome = f"{uuid.uuid4()}{extensao}"
                upload_folder = os.path.join(app.root_path, 'static/uploads')
                
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                    
                file.save(os.path.join(upload_folder, novo_nome))
                # IMPORTANTE: Salve o caminho relativo para o Jinja2 encontrar
                foto_path = f"uploads/{novo_nome}"
            else:
                foto_path = "uploads/default_quadra.jpg"

            # Chamada da função atualizada
            cadastrar_nova_quadra(nome, descricao, localizacao, cidade, estado, esporte, foto_path, abertura, fechamento, preco)
            
            flash("Quadra e agenda de 7 dias criadas com sucesso!", "success")
            return redirect(url_for('explorar'))

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
        
        from banco_de_dados import get_perfil_social, usuario_tem_perfil_social, get_posts_com_usuarios
        
        perfil = get_perfil_social(usuario_id) or {}
        posts = get_posts_com_usuarios()
        
        return render_template('dga.social.html', dados=perfil, posts=posts)

    @app.route('/postar', methods=['POST'])
    def postar():
        if 'usuario_id' not in session:
            flash("Faça login para postar", "error")
            return redirect(url_for('login'))

        texto = request.form.get('texto')
        file = request.files.get('imagem')
        
        # Define se é um post comum ou de divulgação (admin)
        tipo = 'admin' if session.get('usuario_logado') == 'admin@gmail.com' else 'atleta'
        
        foto_path = None
        if file and file.filename != '':
            extensao = os.path.splitext(file.filename)[1]
            novo_nome = f"post_{uuid.uuid4().hex}{extensao}"
            upload_folder = os.path.join(app.root_path, 'static/uploads/posts')
            
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
                
            file.save(os.path.join(upload_folder, novo_nome))
            foto_path = f"uploads/posts/{novo_nome}"

        from banco_de_dados import salvar_novo_post
        salvar_novo_post(session['usuario_id'], texto, foto_path, tipo)
        
        flash("Postagem realizada!", "success")
        return redirect(url_for('social'))
    @app.route('/social/editar', methods=['GET', 'POST'])
    def editar_perfil():
        usuario_id = session.get('usuario_id')
        if not usuario_id:
            return redirect(url_for('login'))

        from banco_de_dados import get_perfil_social, salvar_perfil_social

        if request.method == 'POST':
            usuario_social = request.form.get('usuario_social')
            bio = request.form.get('bio')
            
            # Pegar o arquivo enviado
            file = request.files.get('foto_perfil')
            foto_path = None  # Começa como None

            if file and file.filename != '':
                # Se o usuário enviou uma foto nova, processamos ela
                extensao = os.path.splitext(file.filename)[1]
                novo_nome = f"perfil_{usuario_id}{extensao}"
                upload_folder = os.path.join(app.root_path, 'static/uploads/perfis')
                
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                    
                file.save(os.path.join(upload_folder, novo_nome))
                foto_path = f"uploads/perfis/{novo_nome}"

            # Enviamos para o banco. 
            # Se foto_path for None, a função salvar_perfil_social que você já tem 
            # vai ignorar o update da foto e manter a antiga (ou a padrão).
            salvar_perfil_social(usuario_id, usuario_social, bio, foto_path)
            
            flash("Perfil atualizado com sucesso!", "success")
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