import sqlite3

def criacao_tabela():
    conn = sqlite3.connect("usuarios.db") # Conecta a tabela
    cur = conn.cursor() # Cursor() cria um cursor para a tabela
    cur.execute("""
            CREATE TABLE IF NOT EXISTS users_DGA (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                senha TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                city TEXT,
                country TEXT
            )
    """) # Executa uma chamada da tabela do SQL
    conn.close() # fecha a tabela
    print("Tabela criada com sucesso")

def add_users(name, senha, email, city, country):
    try:
        conn = sqlite3.connect("usuarios.db")
        cur = conn.cursor()
        cur.execute("""
                INSERT INTO users_DGA (name, senha, email, city, country)
                    VALUES (?, ?, ?, ?, ?)
                    """, (name, senha, email, city, country))
        conn.commit() # Para salvar os dados
        conn.close()
        print(f"O usuario {name} foi adicionado a tabela")
        return True
    except sqlite3.IntegrityError: # Verifica se há emails duplicados
        print(f"Erro: o email: {email} já existe.")
        return False
    
def buscar_usuario_email(email):
    conn = sqlite3.connect("usuarios.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM users_DGA WHERE email = ?", (email,))
    usuario = cur.fetchone() # Busca o primeiro usuario
    conn.close()
    return usuario

if __name__ == "__main__":
     criacao_tabela()

     add_users("Davi Caramori", "9812", "davicaramori.200@gmail.com", "Franca", "SP")
     add_users("Gabriel Souza", "laranja10", "gabsnoul.344@gmail.com", "Delfinopolis", "MG")
     add_users("Antonny Gabriel", "pessego90", "antonioeduardo.69@gmail.com", "Morro Agudo", "SP")

     print("-----Buscando o usuario do DAVI----")
     usuario_encontrado = buscar_usuario_email("davicaramori.200@gmail.com")

     if usuario_encontrado:
         print("Usuario encontrado: ", usuario_encontrado)
     else:
         print("Usuario não existe")
 
    


