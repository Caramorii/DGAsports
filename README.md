# DGA Sports — Django

Projeto convertido de Flask para Django.

## Como rodar

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

Acesse: http://127.0.0.1:8000/

### Login admin
- E-mail: `admin@gmail.com`
- Senha: `senha_admin_123`

### Estrutura
- `core/` — app principal (models, views, urls)
- `templates/` — templates HTML (adaptados do Flask)
- `static/` — CSS, JS, imagens e uploads
- `dgasports_project/` — configurações do projeto

### Funcionalidades
- Cadastro e login de usuários
- Explorar e filtrar quadras
- Detalhes da quadra e horários
- Entrar/sair de partidas (API JSON)
- Reserva privada + pagamento PIX (QR Code)
- Rede social (posts, perfil)
- Cadastro de novas quadras (apenas admin)
- Campeonatos e suporte
