# DGA Sports

Site para marcar jogos de vários esportes, na quadra preferida e no horário mais conveniente.

O projeto foi desenvolvido em Django como uma plataforma para encontrar quadras, visualizar horários, reservar espaços, gerenciar pagamentos e interagir em uma rede social voltada ao esporte.

## Visão geral

DGA Sports é uma aplicação web para:
- encontrar quadras por esporte, localização e disponibilidade;
- visualizar horários e reservar vagas;
- confirmar pagamentos via PIX;
- acompanhar as próprias reservas;
- interagir em uma área social com posts e perfil do usuário;
- gerenciar quadras e campeonatos por parte do administrador.

## Stack

- Python 3
- Django 5
- SQLite
- HTML, CSS e JavaScript
- Pillow
- qrcode

## Funcionalidades principais

- Cadastro e login de usuários
- Exploração de quadras por filtros
- Detalhes da quadra e horários disponíveis
- Entrada e saída de partidas em tempo real por API JSON
- Reserva privada e confirmação de pagamento via QR Code PIX
- Rede social com posts e perfil de usuário
- Cadastro de novas quadras apenas para administradores
- Campeonatos e área de suporte
- Painel administrativo para gestão de espaços e reservas

## Estrutura do projeto

```text
DGAsports/
├── core/                          # Aplicação principal
│   ├── management/
│   │   └── commands/
│   │       └── seed_data.py       # Dados iniciais para demo
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── dgasports_project/             # Configurações do projeto Django
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── static/                        # Arquivos estáticos (CSS, JS, imagens)
├── templates/                     # Templates HTML
├── media/                         # Arquivos enviados pelo usuário
├── db.sqlite3                     # Banco de dados SQLite local
├── manage.py
├── requirements.txt
├── README.md
├── .gitignore
└── LICENSE (se existir no repositório)
```

## Pré-requisitos

- Python 3.10 ou superior
- pip
- Ambiente virtual (opcional, mas recomendado)

## Como rodar localmente

1. Clone o repositório:

```bash
git clone https://github.com/Caramorii/DGAsports.git
cd DGAsports
```

2. Crie e ative um ambiente virtual:

```bash
python -m venv venv
```

Linux/macOS:

```bash
source venv/bin/activate
```

Windows:

```bash
venv\Scripts\activate
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

4. Aplique as migrações do banco:

```bash
python manage.py migrate
```

5. Carregue os dados iniciais de demonstração:

```bash
python manage.py seed_data
```

6. Inicie o servidor:

```bash
python manage.py runserver
```

7. Acesse no navegador:

```text
http://127.0.0.1:8000/
```

## Login administrativo

O projeto inclui um usuário administrativo de exemplo, que normalmente é criado pelo comando de seed:

- E-mail: `admin@gmail.com`
- Senha: `senha_admin_123`

Se precisar criar outro usuário administrador manualmente:

```bash
python manage.py createsuperuser
```

## Comandos úteis

### Executar testes

```bash
python manage.py test
```

### Recriar o banco de dados em ambiente local

```bash
rm db.sqlite3
python manage.py migrate
python manage.py seed_data
```

### Verificar dados do app

```bash
python manage.py shell
```

## Observações da configuração

- O projeto usa `sqlite3` em desenvolvimento.
- A pasta `static/` armazena CSS, JavaScript e imagens globais.
- O diretório `media/` é utilizado para arquivos enviados e imagens relacionadas ao sistema.
- A autenticação e a sessão do Django estão configuradas para uso padrão do framework.

## Fluxo de uso típico

1. Usuário se cadastra ou faz login.
2. Explora as quadras disponíveis.
3. Seleciona data e horário.
4. Realiza a reserva.
5. Confirma o pagamento por PIX, quando necessário.
6. Acompanha seu histórico de reservas e interações na plataforma.

## Status do projeto

Este repositório está em desenvolvimento ativo e foi estruturado como uma aplicação web completa para agendamento esportivo, com foco em experiência de usuário, gestão de quadras e ações sociais dentro da plataforma.

## Licença

A licença do projeto não foi especificada no repositório. Caso deseje redistribuir ou reutilizar o código em produção, verifique se há uma licença definida no GitHub antes de publicar ou comercializar a aplicação.

## Contribuição

Contribuições são bem-vindas. Para cada alteração, é recomendável:

- criar uma branch separada;
- manter commits claros e objetivos;
- validar a funcionalidade localmente antes de abrir um pull request.

---

Se quiser, posso também preparar uma versão do README em inglês, uma documentação técnica mais detalhada por módulos, ou até um guia de deploy para produção.
