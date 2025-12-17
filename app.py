from flask import Flask
from routes import init_routes
from banco_de_dados import criar_tabelas_iniciais, popular_dados_iniciais, criar_usuario_admin

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_super_segura_12345'

# Conecta as rotas ao aplicativo
init_routes(app)

if __name__ == '__main__':
    criar_tabelas_iniciais()
    popular_dados_iniciais() # Se o banco mudar, apague o arquivo .db para ele recriar
    criar_usuario_admin() # Cria o login admin@gmail.com
    app.run(debug=True)