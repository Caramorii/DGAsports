import sqlite3
import hashlib # Biblioteca para criptografar a senha

# --- CONFIGURAÇÃO INICIAL ---

def conectar():
    """Conecta ao banco de dados SQLite e retorna a conexão e o cursor."""
    # Cria ou conecta a um banco de dados chamado 'meu_site.db'
    conn = sqlite3.connect('meu_site.db')
    conn.row_factory = sqlite3.Row # Permite acessar as colunas pelo nome
    return conn, conn.cursor()

def criar_tabela_usuarios():
    """Cria a tabela de usuários se ela não existir."""
    try:
        conn, cursor = conectar()
        # SQL para criar a tabela
        # A coluna 'email' é UNIQUE para garantir que não hajam dois cadastros com o mesmo email.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                senha_hash TEXT NOT NULL
            );
        """)
        conn.commit()
    except sqlite3.Error as e:
        print(f"Erro ao criar a tabela: {e}")
    finally:
        if conn:
            conn.close()

# --- FUNÇÕES PRINCIPAIS ---

def _hash_senha(senha):
    """Cria um hash seguro da senha usando o algoritmo SHA-256."""
    return hashlib.sha256(senha.encode('utf-8')).hexdigest()

def cadastrar_usuario(nome, email, senha):
    """Cadastra um novo usuário no banco de dados."""
    # Validação simples
    if not nome or not email or not senha:
        return "Todos os campos são obrigatórios."

    senha_hash = _hash_senha(senha)

    try:
        conn, cursor = conectar()
        # O '?' previne injeção de SQL
        cursor.execute(
            "INSERT INTO usuarios (nome, email, senha_hash) VALUES (?, ?, ?)",
            (nome, email, senha_hash)
        )
        conn.commit()
        return "Usuário cadastrado com sucesso!"
    except sqlite3.IntegrityError:
        # Este erro ocorre quando a restrição UNIQUE do email é violada
        return "Este e-mail já está cadastrado."
    except sqlite3.Error as e:
        return f"Ocorreu um erro no banco de dados: {e}"
    finally:
        if conn:
            conn.close()

def verificar_login(email, senha):
    """Verifica se o email e a senha correspondem a um usuário cadastrado."""
    senha_hash = _hash_senha(senha)

    try:
        conn, cursor = conectar()
        cursor.execute(
            "SELECT * FROM usuarios WHERE email = ? AND senha_hash = ?",
            (email, senha_hash)
        )
        # fetchone() retorna um registro ou None se não encontrar
        usuario = cursor.fetchone()

        if usuario:
            # Retorna os dados do usuário (em formato de dicionário) se o login for bem-sucedido
            return dict(usuario)
        else:
            # Retorna None se o login falhar
            return None
    except sqlite3.Error as e:
        print(f"Ocorreu um erro ao verificar o login: {e}")
        return None
    finally:
        if conn:
            conn.close()

# --- EXEMPLO DE USO ---
if __name__ == "__main__":
    # Esta parte só executa quando o arquivo é rodado diretamente
    # 1. Garante que a tabela exista
    print("Inicializando o banco de dados...")
    criar_tabela_usuarios()
    print("Pronto!")

    # 2. Exemplo de cadastro
    print("\n--- Tentando cadastrar usuários ---")
    print(f"Resultado do cadastro de 'Ana': {cadastrar_usuario('Ana Silva', 'ana@email.com', 'senha123')}")
    print(f"Resultado do cadastro de 'Beto': {cadastrar_usuario('Beto Costa', 'beto@email.com', 'abc456')}")
    # Tentando cadastrar o mesmo email novamente
    print(f"Resultado do cadastro de 'Ana 2': {cadastrar_usuario('Ana Souza', 'ana@email.com', 'outrasenha')}")


    # 3. Exemplo de login
    print("\n--- Tentando fazer login ---")
    # Login correto
    usuario_logado = verificar_login('ana@email.com', 'senha123')
    if usuario_logado:
        print(f"Login bem-sucedido! Bem-vinda, {usuario_logado['nome']}!")
    else:
        print("Login falhou para Ana.")

    # Login com senha errada
    usuario_logado = verificar_login('beto@email.com', 'senha_errada')
    if usuario_logado:
        print(f"Login bem-sucedido! Bem-vindo, {usuario_logado['nome']}!")
    else:
        print("Login falhou para Beto (senha incorreta).")