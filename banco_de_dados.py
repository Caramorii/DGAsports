import sqlite3
import hashlib

# --- CONFIGURAÇÃO ---

def conectar():
    """Conecta ao banco de dados e retorna conexão e cursor."""
    conn = sqlite3.connect('meu_site.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row 
    return conn, conn.cursor()

# --- CRIAÇÃO DAS TABELAS ---

def criar_tabelas_iniciais():
    """Cria todas as tabelas necessárias para o site."""
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

        # Tabela de Esportes (N:N)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS esportes_quadras (
                quadra_id INTEGER,
                esporte TEXT,
                FOREIGN KEY(quadra_id) REFERENCES quadras(id)
            );
        """)

        # Tabela de Horários (com esporte e preco)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS horarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quadra_id INTEGER NOT NULL,
                data TEXT NOT NULL, -- NOVA COLUNA
                hora_texto TEXT NOT NULL,
                max_jogadores INTEGER NOT NULL,
                preco REAL DEFAULT 0,
                esporte_reservado TEXT,
                FOREIGN KEY(quadra_id) REFERENCES quadras(id)
            );
        """)
        
        # Tabela de Reservas (N:N)
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
        # --- CADASTRA USUÁRIOS DE TESTE ---
        print("Cadastrando usuários de teste...")
        cadastrar_usuario('Ana Silva', 'ana@email.com', 'senha123')
        cadastrar_usuario('Beto Costa', 'beto@email.com', 'abc456')

        # Verifica se já tem quadras
        cursor.execute("SELECT COUNT(*) FROM quadras")
        if cursor.fetchone()[0] > 0:
            conn.close() 
            print("Dados de quadras/horários já haviam sido populados.")
            return 

        print("Populando quadras e horários...")
        # Dados das quadras (sem mudança)
        quadras_data = [
            (1, 'Quadra Amazonas', 'Franca', 'SP', 'privada', 'assets/quadraamazonas.jpeg'),
            (2, 'Gol De Placa', 'Franca', 'SP', 'privada', 'assets/goldeplaca.jpg'),
            (3, 'Arena Residencial Palermo', 'Franca', 'SP', 'publica', 'assets/residencialpalermo.jpeg'),
            (4, 'Quadra Parque Castelo', 'Franca', 'SP', 'publica', 'assets/parquecastelo.jpeg')
        ]
        cursor.executemany("INSERT INTO quadras (id, nome, cidade, estado, tipo, imagem) VALUES (?, ?, ?, ?, ?, ?)", quadras_data)

        # Esportes (sem mudança)
        esportes_data = [
            (1, 'Futebol'), (1, 'Basquete'), (2, 'Futebol'),
            (3, 'Futebol'), (3, 'Basquete'), (4, 'Basquete'), (4, 'Futebol')
        ]
        cursor.executemany("INSERT INTO esportes_quadras (quadra_id, esporte) VALUES (?, ?)", esportes_data)

        # --- HORÁRIOS ATUALIZADOS COM DATAS ---
        from datetime import date, timedelta
        hoje = date.today()
        amanha = hoje + timedelta(days=1)

        horarios_data = [
            # (quadra_id, data, hora, max_jogadores, preco)
            # Quadra 1 (Poli, Privada)
            (1, hoje.isoformat(), '18:00 - 19:00', 10, 15.00), # ID 1
            (1, hoje.isoformat(), '19:00 - 20:00', 10, 15.00), # ID 2
            (1, hoje.isoformat(), '20:00 - 21:00', 10, 15.00), # ID 3
            (1, amanha.isoformat(), '18:00 - 19:00', 10, 15.00), # Horário para amanhã

            # Quadra 2 (Só Futebol, Privada)
            (2, hoje.isoformat(), '19:30 - 20:30', 12, 12.50), # ID 4
            (2, hoje.isoformat(), '20:30 - 21:30', 12, 12.50), # ID 5

            # Quadra 3 (Poli, Pública)
            (3, hoje.isoformat(), '19:00 - 20:00', 15, 0), # ID 6
            (3, amanha.isoformat(), '20:00 - 21:00', 15, 0), # ID 7

            # Quadra 4 (Poli, Pública)
            (4, hoje.isoformat(), '17:00 - 18:00', 10, 0), # ID 8
            (4, hoje.isoformat(), '18:00 - 19:00', 10, 0)  # ID 9
        ]
        # ATUALIZE A QUERY PARA 5 VALORES
        cursor.executemany("INSERT INTO horarios (quadra_id, data, hora_texto, max_jogadores, preco) VALUES (?, ?, ?, ?, ?)", horarios_data)
        
        # --- ADICIONA RESERVAS INICIAIS E TRAVA O ESPORTE ---
        print("Adicionando reservas de teste...")
        ana_id = 1
        beto_id = 2
        
        reservas_data = [
            (ana_id, 1),  # Ana no (ID 1: Q1, 18:00)
            (beto_id, 1), # Beto no (ID 1: Q1, 18:00)
            (ana_id, 3)   # Ana no (ID 3: Q1, 20:00)
        ]
        cursor.executemany("INSERT INTO reservas_jogadores (usuario_id, horario_id) VALUES (?, ?)", reservas_data)
        
        # --- Trava o esporte para os horários pré-populados ---
        cursor.execute("UPDATE horarios SET esporte_reservado = 'Futebol' WHERE id = 1")
        cursor.execute("UPDATE horarios SET esporte_reservado = 'Futebol' WHERE id = 3")
        
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
            return dict(usuario) 
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

    # A query base agora busca todas as quadras.
    query = """
        SELECT q.*,
            (SELECT COUNT(*) FROM horarios h WHERE h.quadra_id = q.id) as total_horarios,
            (SELECT COUNT(rj.usuario_id) FROM reservas_jogadores rj
             JOIN horarios h ON rj.horario_id = h.id
             WHERE h.quadra_id = q.id) as total_jogadores_agora
        FROM quadras q
    """
    params = []
    conditions = []
    
    if localidade_busca:
        # LÓGICA CORRIGIDA: Trata "Cidade, Estado" de forma mais flexível.
        partes_busca = [p.strip() for p in localidade_busca.split(',')]
        partes_busca = [p for p in partes_busca if p] # Remove strings vazias
        
        # Cria uma única condição OR para todas as partes da busca
        if partes_busca:
            # Ex: (LOWER(cidade) LIKE ? OR LOWER(estado) LIKE ?) OR (LOWER(cidade) LIKE ? OR LOWER(estado) LIKE ?)
            or_conditions = ["(LOWER(q.cidade) LIKE ? OR LOWER(q.estado) LIKE ?)"] * len(partes_busca)
            conditions.append(f"({' OR '.join(or_conditions)})")
            for parte in partes_busca:
                params.extend([f"%{parte}%", f"%{parte}%"])
        
    if esporte_busca:
        # Adiciona condição de esporte, buscando em uma subquery
        conditions.append("q.id IN (SELECT quadra_id FROM esportes_quadras WHERE LOWER(esporte) = ?)")
        params.append(esporte_busca.lower()) # Converte para minúsculo aqui

    # Se houver condições, adiciona a cláusula WHERE
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
        
    cursor.execute(query, params)
    quadras = [dict(row) for row in cursor.fetchall()]
    
    # Busca os esportes de cada quadra separadamente para exibição
    for quadra in quadras:
        cursor.execute("SELECT esporte FROM esportes_quadras WHERE quadra_id = ?", (quadra['id'],))
        quadra['esportes'] = [row['esporte'] for row in cursor.fetchall()]

    conn.close()
    return quadras

def get_detalhes_quadra(id_quadra, usuario_id_atual=None):
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

    # 3. Pega horários e todos os jogadores
    cursor.execute("""
        SELECT DISTINCT data FROM horarios WHERE quadra_id = ? ORDER BY data ASC
    """, (id_quadra,))
    quadra_dict['datas_disponiveis'] = [row['data'] for row in cursor.fetchall()]

    # 4. Pega horários e jogadores APENAS DO PRIMEIRO DIA DISPONÍVEL
    primeira_data = quadra_dict['datas_disponiveis'][0] if quadra_dict['datas_disponiveis'] else None
    
    cursor.execute(f"""
        SELECT
            h.id, h.data, h.hora_texto, h.max_jogadores, h.preco, h.esporte_reservado,
            (SELECT COUNT(*) FROM reservas_jogadores rj WHERE rj.horario_id = h.id) as jogadores_atuais,
            (SELECT 1 FROM reservas_jogadores rj WHERE rj.horario_id = h.id AND rj.usuario_id = ?) as usuario_esta_na_partida
        FROM horarios h
        WHERE h.quadra_id = ? AND h.data = ?
    """, (usuario_id_atual, id_quadra, primeira_data))
    
    horarios_raw = cursor.fetchall()
    conn.close()

    # 4. Processa os dados dos horários
    horarios_processados = {}
    for row in horarios_raw:
        horario_id = row['id']
        if horario_id not in horarios_processados:
            horarios_processados[horario_id] = {
                'id': row['id'],
                'hora_texto': row['hora_texto'],
                'max_jogadores': row['max_jogadores'],
                'preco': row['preco'],
                'esporte_reservado': row['esporte_reservado'], # MUDANÇA AQUI
                'jogadores_atuais': row['jogadores_atuais'],
                'usuario_esta_na_partida': bool(row['usuario_esta_na_partida'])
            }
            
    quadra_dict['horarios'] = list(horarios_processados.values())
    quadra_dict['seguindo'] = (id_quadra % 2 == 1) 
    
    return quadra_dict

def get_horarios_por_data(quadra_id, data_selecionada, usuario_id):
    """Busca os horários de uma quadra para uma data específica."""
    try:
        conn, cursor = conectar()
        cursor.execute(f"""
            SELECT
                h.id, h.data, h.hora_texto, h.max_jogadores, h.preco, h.esporte_reservado,
                (SELECT COUNT(*) FROM reservas_jogadores rj WHERE rj.horario_id = h.id) as jogadores_atuais,
                (SELECT 1 FROM reservas_jogadores rj WHERE rj.horario_id = h.id AND rj.usuario_id = ?) as usuario_esta_na_partida
            FROM horarios h
            WHERE h.quadra_id = ? AND h.data = ?
            ORDER BY h.hora_texto
        """, (usuario_id, quadra_id, data_selecionada))
        
        horarios = [dict(row) for row in cursor.fetchall()]

        # Converte o valor booleano para o JS
        for horario in horarios:
            horario['usuario_esta_na_partida'] = bool(horario['usuario_esta_na_partida'])

        return horarios
    except Exception as e:
        print(f"Erro ao buscar horários por data: {e}")
        return []
    finally:
        if conn: conn.close()

# --- ESTA É A FUNÇÃO QUE ESTÁ CAUSANDO O ERRO ---
# --- GARANTA QUE A SUA SEJA SUBSTITUÍDA POR ESTA ---
def get_detalhes_reserva(horario_id):
    """Busca todos os detalhes de um horário para a página de checkout."""
    conn, cursor = conectar()
    
    cursor.execute("""
        SELECT 
            h.id as horario_id, h.hora_texto, h.max_jogadores, h.preco, h.esporte_reservado,
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
            'preco': rows[0]['preco'],
            'esporte_reservado': rows[0]['esporte_reservado']
        },
        'jogadores': []
    }
    
    contagem_atual = 0
    for row in rows:
        if row['jogador_id']:
            if not any(j['id'] == row['jogador_id'] for j in reserva_detalhes['jogadores']):
                reserva_detalhes['jogadores'].append({
                    'id': row['jogador_id'],
                    'nome': row['jogador_nome'],
                    'avatar': f'https://placehold.co/50x50/9F7AEA/FFFFFF?text={row["jogador_nome"][0].upper()}'
                })
                contagem_atual += 1
            
    reserva_detalhes['horario']['jogadores_atuais'] = contagem_atual
    
    return reserva_detalhes

# --- FUNÇÕES DE AÇÃO (ENTRAR/SAIR) ---

def adicionar_jogador_partida(usuario_id, horario_id, esporte_selecionado):
    """Tenta adicionar um jogador a um horário, travando o esporte se for o primeiro."""
    conn, cursor = conectar()
    
    try:
        # 1. Pega dados do horário (max_jogadores E esporte_reservado)
        cursor.execute("SELECT max_jogadores, esporte_reservado FROM horarios WHERE id = ?", (horario_id,))
        horario = cursor.fetchone()
        if not horario:
            return {'status': 'erro', 'mensagem': 'Horário não encontrado.'}
        
        # 2. Verifica se o esporte é compatível
        esporte_atual = horario['esporte_reservado']
        if esporte_atual is not None and esporte_atual != esporte_selecionado:
            return {'status': 'erro', 'mensagem': f'Este horário já está reservado para {esporte_atual}.'}

        # 3. Conta jogadores atuais
        cursor.execute("SELECT COUNT(*) FROM reservas_jogadores WHERE horario_id = ?", (horario_id,))
        contagem_atual = cursor.fetchone()[0]

        # 4. Verifica se está lotado
        if contagem_atual >= horario['max_jogadores']:
            return {'status': 'erro', 'mensagem': 'Esta partida já está lotada!'}

        # 5. Tenta inserir (vai dar erro se o usuário já estiver)
        cursor.execute(
            "INSERT INTO reservas_jogadores (usuario_id, horario_id) VALUES (?, ?)",
            (usuario_id, horario_id)
        )
        
        # 6. SE FOI O PRIMEIRO JOGADOR (contagem == 0), TRAVA O ESPORTE
        if contagem_atual == 0:
            cursor.execute("UPDATE horarios SET esporte_reservado = ? WHERE id = ?", (esporte_selecionado, horario_id))
            print(f"Horário {horario_id} travado para {esporte_selecionado}.")

        conn.commit()
        
        # 7. Pega os dados do usuário
        cursor.execute("SELECT nome, email FROM usuarios WHERE id = ?", (usuario_id,))
        usuario = cursor.fetchone()
        
        novo_jogador = {
            'id': usuario['email'], 'nome': usuario['nome'],
            'avatar': f'https://placehold.co/50x50/9F7AEA/FFFFFF?text={usuario["nome"][0].upper()}'
        }

        return {
            'status': 'sucesso',
            'nova_contagem': contagem_atual + 1,
            'novo_jogador': novo_jogador,
            'esporte_travado': esporte_selecionado
        }

    except sqlite3.IntegrityError:
        return {'status': 'erro', 'mensagem': 'Você já está nessa partida.'}
    except sqlite3.Error as e:
        return {'status': 'erro', 'mensagem': f'Erro de banco de dados: {e}'}
    finally:
        if conn:
            conn.close()

def remover_jogador_partida(usuario_id, horario_id):
    """Tenta remover um jogador de um horário. Se for o último, destrava o esporte."""
    conn, cursor = conectar()
    
    try:
        # Tenta deletar a reserva
        cursor.execute(
            "DELETE FROM reservas_jogadores WHERE usuario_id = ? AND horario_id = ?",
            (usuario_id, horario_id)
        )
        conn.commit()
        
        if cursor.rowcount == 0:
            return {'status': 'erro', 'mensagem': 'Você não estava nesta partida.'}

        # Pega a nova contagem de jogadores
        cursor.execute("SELECT COUNT(*) FROM reservas_jogadores WHERE horario_id = ?", (horario_id,))
        contagem_atual = cursor.fetchone()[0]
        
        esporte_destravado = None
        # SE FOI O ÚLTIMO A SAIR, DESTRAVA O ESPORTE
        if contagem_atual == 0:
            cursor.execute("UPDATE horarios SET esporte_reservado = NULL WHERE id = ?", (horario_id,))
            conn.commit()
            esporte_destravado = True # Sinaliza para o JS
            print(f"Horário {horario_id} destravado.")

        return {
            'status': 'sucesso',
            'nova_contagem': contagem_atual,
            'esporte_destravado': esporte_destravado
        }

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