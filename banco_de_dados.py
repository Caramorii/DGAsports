import sqlite3
import hashlib

# --- CONFIGURAÇÃO ---

def conectar():
    """Conecta ao banco de dados e retorna conexão e cursor."""
    # check_same_thread=False é necessário para o Flask em modo de desenvolvimento
    conn = sqlite3.connect('meu_site.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row # Permite acessar colunas pelo nome
    return conn, conn.cursor()

# --- CRIAÇÃO DAS TABELAS ---

def criar_tabelas_iniciais():
    """Cria todas as tabelas necessárias para o site (usuários, quadras, horários)."""
    try:
        conn, cursor = conectar()
        
        # Tabela de Usuários
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                senha_hash TEXT NOT NULL
            );
        """)
        
        # Tabela de Quadras
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quadras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                cidade TEXT,
                estado TEXT,
                tipo TEXT,
                imagem TEXT
            );
        """)

        # Tabela de Esportes (para ligar esportes a quadras - N:N)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS esportes_quadras (
                quadra_id INTEGER,
                esporte TEXT,
                FOREIGN KEY(quadra_id) REFERENCES quadras(id)
            );
        """)

        # Tabela de Horários (com a coluna 'preco')
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS horarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quadra_id INTEGER NOT NULL,
                hora_texto TEXT NOT NULL,
                max_jogadores INTEGER NOT NULL,
                preco REAL DEFAULT 0,
                FOREIGN KEY(quadra_id) REFERENCES quadras(id)
            );
        """)
        
        # Tabela de Reservas (quem entrou em qual partida - N:N)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reservas_jogadores (
                usuario_id INTEGER NOT NULL,
                horario_id INTEGER NOT NULL,
                PRIMARY KEY (usuario_id, horario_id),
                FOREIGN KEY(usuario_id) REFERENCES usuarios(id),
                FOREIGN KEY(horario_id) REFERENCES horarios(id)
            );
        """)
        
        conn.commit()
    except sqlite3.Error as e:
        print(f"Erro ao criar tabelas: {e}")
    finally:
        if conn:
            conn.close()

# --- POPULAR DADOS INICIAIS ---

def popular_dados_iniciais():
    """Insere os dados simulados no banco de dados (só roda uma vez)."""
    conn, cursor = conectar()
    
    try:
        # --- CADASTRA USUÁRIOS DE TESTE PRIMEIRO ---
        print("Cadastrando usuários de teste...")
        # (Não vai cadastrar de novo se já existirem, por causa do UNIQUE email)
        cadastrar_usuario('Ana Silva', 'ana@email.com', 'senha123')
        cadastrar_usuario('Beto Costa', 'beto@email.com', 'abc456')

        # Verifica se já tem quadras
        cursor.execute("SELECT COUNT(*) FROM quadras")
        if cursor.fetchone()[0] > 0:
            conn.close() # Fecha a conexão
            print("Dados de quadras/horários já haviam sido populados.")
            return # Já foi populado

        print("Populando quadras e horários...")
        # Dados das quadras
        quadras_data = [
            (1, 'Quadra Amazonas', 'Franca', 'SP', 'privada', 'assets/quadraamazonas.jpeg'),
            (2, 'Gol De Placa', 'Franca', 'SP', 'privada', 'assets/goldeplaca.jpg'),
            (3, 'Arena Residencial Palermo', 'Franca', 'SP', 'publica', 'assets/residencialpalermo.jpeg'),
            (4, 'Quadra Parque Castelo', 'Franca', 'SP', 'publica', 'assets/parquecastelo.jpeg')
        ]
        cursor.executemany("INSERT INTO quadras (id, nome, cidade, estado, tipo, imagem) VALUES (?, ?, ?, ?, ?, ?)", quadras_data)

        # Esportes
        esportes_data = [
            (1, 'Futebol'), (1, 'Basquete'), (2, 'Futebol'),
            (3, 'Futebol'), (3, 'Basquete'), (4, 'Basquete'), (4, 'Futebol')
        ]
        cursor.executemany("INSERT INTO esportes_quadras (quadra_id, esporte) VALUES (?, ?)", esportes_data)

        # Horários (com preços por vaga)
        horarios_data = [
            # (quadra_id, hora, max_jogadores, preco_POR_PESSOA)
            (1, '18:00 - 19:00', 10, 15.00), # R$ 15 por pessoa (ID 1)
            (1, '19:00 - 20:00', 10, 15.00), # (ID 2)
            (1, '20:00 - 21:00', 10, 15.00), # (ID 3)
            (2, '19:30 - 20:30', 12, 12.50), # R$ 12.50 por pessoa (ID 4)
            (2, '20:30 - 21:30', 12, 12.50), # (ID 5)
            (3, '19:00 - 20:00', 15, 0),     # Quadra pública (grátis) (ID 6)
            (3, '20:00 - 21:00', 15, 0),     # (ID 7)
            (4, '17:00 - 18:00', 10, 0),     # (ID 8)
            (4, '18:00 - 19:00', 10, 0)      # (ID 9)
        ]
        cursor.executemany("INSERT INTO horarios (quadra_id, hora_texto, max_jogadores, preco) VALUES (?, ?, ?, ?)", horarios_data)
        
        # --- ADICIONA RESERVAS INICIAIS ---
        print("Adicionando reservas de teste...")
        # IDs dos usuários (Ana=1, Beto=2)
        ana_id = 1
        beto_id = 2
        
        # IDs dos horários (baseado na lista acima)
        reservas_data = [
            (ana_id, 1),  # Ana no horário 1 (Quadra 1, 18:00)
            (beto_id, 1), # Beto no horário 1 (Quadra 1, 18:00)
            (ana_id, 2)   # Ana no horário 2 (Quadra 1, 19:00)
        ]
        
        cursor.executemany("INSERT INTO reservas_jogadores (usuario_id, horario_id) VALUES (?, ?)", reservas_data)
        
        conn.commit()
        print("Banco de dados populado com dados iniciais (incluindo reservas de teste).")
    except Exception as e:
        print(f"Erro ao popular dados: {e}")
    finally:
        if conn:
            conn.close()


# --- FUNÇÕES DE USUÁRIO ---

def _hash_senha(senha):
    return hashlib.sha256(senha.encode('utf-8')).hexdigest()

def cadastrar_usuario(nome, email, senha):
    if not nome or not email or not senha:
        return "Todos os campos são obrigatórios."
    senha_hash = _hash_senha(senha)
    try:
        conn, cursor = conectar()
        cursor.execute(
            "INSERT INTO usuarios (nome, email, senha_hash) VALUES (?, ?, ?)",
            (nome, email, senha_hash)
        )
        conn.commit()
        return "Usuário cadastrado com sucesso!"
    except sqlite3.IntegrityError:
        return "Este e-mail já está cadastrado."
    except sqlite3.Error as e:
        return f"Ocorreu um erro no banco de dados: {e}"
    finally:
        if conn:
            conn.close()

def verificar_login(email, senha):
    senha_hash = _hash_senha(senha)
    try:
        conn, cursor = conectar()
        cursor.execute(
            "SELECT * FROM usuarios WHERE email = ? AND senha_hash = ?",
            (email, senha_hash)
        )
        usuario = cursor.fetchone()
        if usuario:
            return dict(usuario) # Retorna o dict completo (incluindo ID)
        else:
            return None
    except sqlite3.Error as e:
        print(f"Ocorreu um erro ao verificar o login: {e}")
        return None
    finally:
        if conn:
            conn.close()

# --- FUNÇÕES DE QUADRAS E HORÁRIOS ---

def get_quadras(localidade_busca, esporte_busca):
    """Busca quadras no DB, filtrando e contando jogadores/horários."""
    conn, cursor = conectar()
    
    # Query para buscar quadras e contar jogadores/horários
    query = """
        SELECT DISTINCT q.*,
            (SELECT COUNT(*) FROM horarios h WHERE h.quadra_id = q.id) as total_horarios,
            (SELECT COUNT(rj.usuario_id) FROM reservas_jogadores rj
             JOIN horarios h ON rj.horario_id = h.id
             WHERE h.quadra_id = q.id) as total_jogadores_agora
        FROM quadras q
        LEFT JOIN esportes_quadras eq ON q.id = eq.quadra_id
        WHERE 1=1
    """
    params = []
    
    if localidade_busca:
        query += " AND (LOWER(q.cidade) LIKE ? OR LOWER(q.estado) LIKE ?)"
        term = f"%{localidade_busca}%"
        params.extend([term, term])
        
    if esporte_busca:
        query += " AND LOWER(eq.esporte) = ?"
        params.append(esporte_busca)
        
    cursor.execute(query, params)
    quadras = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return quadras

def get_detalhes_quadra(id_quadra):
    """Busca uma quadra específica e seus horários detalhados."""
    conn, cursor = conectar()
    
    # 1. Pega dados da quadra
    cursor.execute("SELECT * FROM quadras WHERE id = ?", (id_quadra,))
    quadra = cursor.fetchone()
    if not quadra:
        conn.close()
        return None
    
    quadra_dict = dict(quadra)
    
    # 2. Pega esportes da quadra
    cursor.execute("SELECT esporte FROM esportes_quadras WHERE quadra_id = ?", (id_quadra,))
    quadra_dict['esportes'] = [row['esporte'] for row in cursor.fetchall()]

    # 3. Pega horários e contagem de jogadores
    cursor.execute("""
        SELECT 
            h.id, h.hora_texto, h.max_jogadores, h.preco,
            (SELECT COUNT(*) FROM reservas_jogadores rj WHERE rj.horario_id = h.id) as jogadores_atuais,
            u.nome as jogador_nome
        FROM horarios h
        LEFT JOIN reservas_jogadores rj ON h.id = rj.horario_id
        LEFT JOIN usuarios u ON rj.usuario_id = u.id
        WHERE h.quadra_id = ?
    """, (id_quadra,))
    
    horarios_raw = cursor.fetchall()
    conn.close()

    # 4. Processa os dados dos horários (agrupando jogadores)
    horarios_processados = {}
    for row in horarios_raw:
        horario_id = row['id']
        if horario_id not in horarios_processados:
            horarios_processados[horario_id] = {
                'id': row['id'],
                'hora': row['hora_texto'],
                'max_jogadores': row['max_jogadores'],
                'preco': row['preco'],
                'jogadores_atuais': row['jogadores_atuais'],
                'jogadores': []
            }
        
        if row['jogador_nome']:
            horarios_processados[horario_id]['jogadores'].append({
                'nome': row['jogador_nome'],
                'avatar': f'https://placehold.co/50x50/9F7AEA/FFFFFF?text={row["jogador_nome"][0].upper()}'
            })
            
    quadra_dict['horarios'] = list(horarios_processados.values())
    
    # Simula o "seguindo"
    quadra_dict['seguindo'] = (id_quadra % 2 == 1) 
    
    return quadra_dict

def get_detalhes_reserva(horario_id):
    """Busca todos os detalhes de um horário para a página de checkout."""
    conn, cursor = conectar()
    
    cursor.execute("""
        SELECT 
            h.id as horario_id, h.hora_texto, h.max_jogadores, h.preco,
            q.id as quadra_id, q.nome as quadra_nome, q.cidade, q.estado, q.imagem,
            u.id as jogador_id, u.nome as jogador_nome
        FROM horarios h
        JOIN quadras q ON h.quadra_id = q.id
        LEFT JOIN reservas_jogadores rj ON h.id = rj.horario_id
        LEFT JOIN usuarios u ON rj.usuario_id = u.id
        WHERE h.id = ?
    """, (horario_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return None

    # Processa os dados
    reserva_detalhes = {
        'quadra': {
            'id': rows[0]['quadra_id'],
            'nome': rows[0]['quadra_nome'],
            'cidade': rows[0]['cidade'],
            'estado': rows[0]['estado'],
            'imagem': rows[0]['imagem']
        },
        'horario': {
            'id': rows[0]['horario_id'],
            'hora': rows[0]['hora_texto'],
            'max_jogadores': rows[0]['max_jogadores'],
            'preco': rows[0]['preco']
        },
        'jogadores': []
    }
    
    contagem_atual = 0
    for row in rows:
        if row['jogador_id']:
            # Evita adicionar o mesmo jogador várias vezes se a query duplicar
            if not any(j['id'] == row['jogador_id'] for j in reserva_detalhes['jogadores']):
                reserva_detalhes['jogadores'].append({
                    'id': row['jogador_id'],
                    'nome': row['jogador_nome'],
                    'avatar': f'https://placehold.co/50x50/9F7AEA/FFFFFF?text={row["jogador_nome"][0].upper()}'
                })
                contagem_atual += 1
            
    reserva_detalhes['horario']['jogadores_atuais'] = contagem_atual
    
    return reserva_detalhes

def adicionar_jogador_partida(usuario_id, horario_id):
    """Tenta adicionar um jogador a um horário."""
    conn, cursor = conectar()
    
    try:
        # 1. Pega dados do horário (max_jogadores)
        cursor.execute("SELECT max_jogadores FROM horarios WHERE id = ?", (horario_id,))
        horario = cursor.fetchone()
        if not horario:
            return {'status': 'erro', 'mensagem': 'Horário não encontrado.'}
        
        # 2. Conta jogadores atuais
        cursor.execute("SELECT COUNT(*) FROM reservas_jogadores WHERE horario_id = ?", (horario_id,))
        contagem_atual = cursor.fetchone()[0]

        # 3. Verifica se está lotado
        if contagem_atual >= horario['max_jogadores']:
            return {'status': 'erro', 'mensagem': 'Esta partida já está lotada!'}

        # 4. Tenta inserir (vai dar erro se o usuário já estiver)
        cursor.execute(
            "INSERT INTO reservas_jogadores (usuario_id, horario_id) VALUES (?, ?)",
            (usuario_id, horario_id)
        )
        conn.commit()
        
        # 5. Pega os dados do usuário que acabou de entrar
        cursor.execute("SELECT nome, email FROM usuarios WHERE id = ?", (usuario_id,))
        usuario = cursor.fetchone()
        
        novo_jogador = {
            'id': usuario['email'], # JS usa o email
            'nome': usuario['nome'],
            'avatar': f'https://placehold.co/50x50/9F7AEA/FFFFFF?text={usuario["nome"][0].upper()}'
        }

        return {
            'status': 'sucesso',
            'nova_contagem': contagem_atual + 1,
            'novo_jogador': novo_jogador
        }

    except sqlite3.IntegrityError:
        # Erro (PRIMARY KEY (usuario_id, horario_id)): Usuário já está na partida
        return {'status': 'erro', 'mensagem': 'Você já está nessa partida.'}
    except sqlite3.Error as e:
        return {'status': 'erro', 'mensagem': f'Erro de banco de dados: {e}'}
    finally:
        if conn:
            conn.close()


# --- INICIALIZAÇÃO ---
if __name__ == "__main__":
    print("Inicializando o banco de dados...")
    criar_tabelas_iniciais()
    popular_dados_iniciais()
    print("Banco de dados pronto.")