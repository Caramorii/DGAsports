import sqlite3
import hashlib
from datetime import date, timedelta

# --- CONFIGURAÇÃO ---

def conectar():
    """Conecta ao banco de dados e retorna conexão e cursor."""
    conn = sqlite3.connect('meu_site.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row 
    return conn, conn.cursor()

# --- CRIAÇÃO DAS TABELAS ---

def criar_tabelas_iniciais():
    """Cria todas as tabelas com todas as colunas necessárias de uma só vez."""
    try:
        conn, cursor = conectar()
        
        # Tabela de Usuários
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                cidade TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                senha_hash TEXT NOT NULL
            );
        """)
        
        # Tabela de Quadras (Incluindo coluna ESTADO)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quadras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                descricao TEXT,
                localizacao TEXT,
                cidade TEXT,
                estado TEXT, 
                esporte TEXT,
                foto TEXT
            );
        """)

        # Tabela de Horários
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS horarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quadra_id INTEGER NOT NULL,
                data TEXT NOT NULL, 
                hora_texto TEXT NOT NULL,
                max_jogadores INTEGER NOT NULL,
                preco REAL DEFAULT 0,
                esporte_reservado TEXT,
                FOREIGN KEY(quadra_id) REFERENCES quadras(id)
            );
        """)
        
        # Tabela de Reservas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reservas_jogadores (
                usuario_id INTEGER NOT NULL,
                horario_id INTEGER NOT NULL,
                PRIMARY KEY (usuario_id, horario_id),
                FOREIGN KEY(usuario_id) REFERENCES usuarios(id),
                FOREIGN KEY(horario_id) REFERENCES horarios(id)
            );
        """)

        # Tabela de Perfis Sociais (Incluindo USUARIO_SOCIAL e BIO)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS perfis_sociais (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                usuario_social TEXT,
                bio TEXT,
                foto_perfil TEXT,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            );
        """)
        
        conn.commit()
        print("✅ Tabelas sincronizadas com sucesso!")
    except sqlite3.Error as e:
        print(f"❌ Erro ao criar tabelas: {e}")
    finally:
        if conn:
            conn.close()

# --- FUNÇÕES DE PERFIL SOCIAL ---

def usuario_tem_perfil_social(usuario_id):
    conn, cursor = conectar()
    cursor.execute("SELECT 1 FROM perfis_sociais WHERE usuario_id = ?", (usuario_id,))
    perfil = cursor.fetchone()
    conn.close()
    return perfil is not None

def get_perfil_social(usuario_id):
    """Retorna o perfil como dicionário para o Jinja2 ou None."""
    conn, cursor = conectar()
    cursor.execute("SELECT * FROM perfis_sociais WHERE usuario_id = ?", (usuario_id,))
    linha = cursor.fetchone()
    conn.close()
    return dict(linha) if linha else None

def salvar_perfil_social(usuario_id, usuario_social, bio, foto_path):
    conn, cursor = conectar()
    cursor.execute("SELECT id FROM perfis_sociais WHERE usuario_id = ?", (usuario_id,))
    existe = cursor.fetchone()

    if existe:
        if foto_path:
            cursor.execute("UPDATE perfis_sociais SET usuario_social=?, bio=?, foto_perfil=? WHERE usuario_id=?", 
                           (usuario_social, bio, foto_path, usuario_id))
        else:
            cursor.execute("UPDATE perfis_sociais SET usuario_social=?, bio=? WHERE usuario_id=?", 
                           (usuario_social, bio, usuario_id))
    else:
        cursor.execute("INSERT INTO perfis_sociais (usuario_id, usuario_social, bio, foto_perfil) VALUES (?, ?, ?, ?)",
                       (usuario_id, usuario_social, bio, foto_path or 'images/default_avatar.png'))
    
    conn.commit()
    conn.close()

# --- POPULAR DADOS INICIAIS ---

def popular_dados_iniciais():
    conn, cursor = conectar()
    try:
        cursor.execute("SELECT COUNT(*) FROM quadras")
        if cursor.fetchone()[0] > 0:
            return 

        quadras_data = [
            (1, 'Quadra Amazonas', 'Melhor quadra da região', 'Rua Amazonas, 100', 'Franca', 'SP', 'Futebol', 'assets/quadraamazonas.jpeg'),
            (2, 'Gol De Placa', 'Gramado sintético novo', 'Av. Brasil, 500', 'Franca', 'SP', 'Futebol', 'assets/goldeplaca.jpg'),
            (3, 'Arena Palermo', 'Quadra pública reformada', 'Praça Palermo', 'Franca', 'SP', 'Basquete', 'assets/residencialpalermo.jpeg')
        ]
        cursor.executemany("""
            INSERT INTO quadras (id, nome, descricao, localizacao, cidade, estado, esporte, foto) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, quadras_data)

        hoje = date.today()
        horarios_data = [
            (1, hoje.isoformat(), '18:00 - 19:00', 10, 15.00),
            (1, hoje.isoformat(), '19:00 - 20:00', 10, 15.00),
            (2, hoje.isoformat(), '18:30 - 19:30', 12, 12.50)
        ]
        cursor.executemany("INSERT INTO horarios (quadra_id, data, hora_texto, max_jogadores, preco) VALUES (?, ?, ?, ?, ?)", horarios_data)
        
        conn.commit()
        print("✅ Dados iniciais inseridos!")
    except Exception as e:
        print(f"❌ Erro ao popular dados: {e}")
    finally:
        conn.close()

# --- USUÁRIOS E SEGURANÇA ---

def _hash_senha(senha):
    return hashlib.sha256(senha.encode('utf-8')).hexdigest()

def cadastrar_usuario(nome, cidade, email, senha):
    senha_hash = _hash_senha(senha)
    try:
        conn, cursor = conectar()
        cursor.execute("INSERT INTO usuarios (nome, cidade, email, senha_hash) VALUES (?, ?, ?, ?)", (nome, cidade, email, senha_hash))
        conn.commit()
        return "Usuário cadastrado com sucesso!"
    except sqlite3.IntegrityError:
        return "Este e-mail já existe."
    finally:
        conn.close()

def verificar_login(email, senha):
    senha_hash = _hash_senha(senha)
    conn, cursor = conectar()
    cursor.execute("SELECT * FROM usuarios WHERE email = ? AND senha_hash = ?", (email, senha_hash))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def criar_usuario_admin():
    conn, cursor = conectar()
    cursor.execute("SELECT id FROM usuarios WHERE email = ?", ("admin@gmail.com",))
    if not cursor.fetchone():
        senha_hash = _hash_senha("senha_admin_123")
        cursor.execute("INSERT INTO usuarios (nome, cidade, email, senha_hash) VALUES (?, ?, ?, ?)", ("Admin", "Franca", "admin@gmail.com", senha_hash))
        conn.commit()
    conn.close()

# --- GERENCIAMENTO ---

def cadastrar_nova_quadra(nome, descricao, localizacao, cidade, estado, esporte, foto_path):
    """Recebe exatamente 7 argumentos das rotas."""
    conn, cursor = conectar()
    cursor.execute("""
        INSERT INTO quadras (nome, descricao, localizacao, cidade, estado, esporte, foto)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (nome, descricao, localizacao, cidade, estado, esporte, foto_path))
    conn.commit()
    conn.close()

# --- CONSULTAS (GETTERS) ---

def get_quadras(localidade_busca=None, esporte_busca=None):
    conn, cursor = conectar()
    query = "SELECT * FROM quadras WHERE 1=1"
    params = []
    
    if localidade_busca:
        query += " AND (cidade LIKE ? OR estado LIKE ?)"
        params.extend([f"%{localidade_busca}%", f"%{localidade_busca}%"])
    
    if esporte_busca:
        query += " AND esporte LIKE ?"
        params.append(f"%{esporte_busca}%")
        
    cursor.execute(query, params)
    quadras = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return quadras

def get_detalhes_quadra(id_quadra, usuario_id=None):
    conn, cursor = conectar()
    cursor.execute("SELECT * FROM quadras WHERE id = ?", (id_quadra,))
    quadra = cursor.fetchone()
    if not quadra: return None
    
    q_dict = dict(quadra)
    cursor.execute("SELECT * FROM horarios WHERE quadra_id = ? ORDER BY data, hora_texto", (id_quadra,))
    q_dict['horarios'] = [dict(row) for row in cursor.fetchall()]
    q_dict['datas_disponiveis'] = sorted(list(set(h['data'] for h in q_dict['horarios'])))
    
    conn.close()
    return q_dict

def get_horarios_por_data(quadra_id, data_sel, usuario_id):
    conn, cursor = conectar()
    cursor.execute("""
        SELECT h.*, 
        (SELECT COUNT(*) FROM reservas_jogadores WHERE horario_id = h.id) as jogadores_atuais,
        (SELECT 1 FROM reservas_jogadores WHERE horario_id = h.id AND usuario_id = ?) as usuario_na_partida
        FROM horarios h WHERE quadra_id = ? AND data = ?
    """, (usuario_id, quadra_id, data_sel))
    res = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return res

def get_detalhes_reserva(horario_id):
    conn, cursor = conectar()
    cursor.execute("""
        SELECT h.*, q.nome as quadra_nome, q.cidade, q.foto as imagem 
        FROM horarios h JOIN quadras q ON h.quadra_id = q.id WHERE h.id = ?
    """, (horario_id,))
    row = cursor.fetchone()
    conn.close()
    if not row: return None
    
    data = dict(row)
    return {
        'quadra': {'nome': data['quadra_nome'], 'cidade': data['cidade'], 'imagem': data['imagem']},
        'horario': {'id': data['id'], 'hora': data['hora_texto'], 'preco': data['preco'], 'max_jogadores': data['max_jogadores']}
    }

# --- AÇÕES DE PARTIDA ---

def adicionar_jogador_partida(u_id, h_id, esporte=None):
    conn, cursor = conectar()
    try:
        cursor.execute("INSERT INTO reservas_jogadores (usuario_id, horario_id) VALUES (?, ?)", (u_id, h_id))
        conn.commit()
        return {'status': 'sucesso'}
    except:
        return {'status': 'erro', 'mensagem': 'Você já está nesta partida ou ocorreu um erro.'}
    finally:
        conn.close()

def remover_jogador_partida(u_id, h_id):
    conn, cursor = conectar()
    cursor.execute("DELETE FROM reservas_jogadores WHERE usuario_id = ? AND horario_id = ?", (u_id, h_id))
    conn.commit()
    conn.close()
    return {'status': 'sucesso'}