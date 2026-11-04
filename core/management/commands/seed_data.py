from django.core.management.base import BaseCommand
from datetime import date, timedelta
from core.models import DivisaoQuadra, Horario, Quadra


COMPLEXO_NOME = 'Complexo Esportivo Franca'
COMPLEXO_DIVISOES = [
    {'nome': 'Quadra de Areia', 'superficie': 'areia', 'esportes': 'Futevolei, Vôlei de Areia, Beach-Tennis', 'vagas': 4},
    {'nome': 'Ginásio Coberto', 'superficie': 'madeira', 'esportes': 'Basquete, Vôlei, Futsal', 'vagas': 10},
    {'nome': 'Campo Society', 'superficie': 'sintetico', 'esportes': 'Futebol', 'vagas': 14},
]


class Command(BaseCommand):
    help = 'Popula dados de demonstração (quadras e horários)'

    def criar_complexo(self):
        """Exemplo de local com quadras físicas de pisos e esportes diferentes."""
        if Quadra.objects.filter(nome=COMPLEXO_NOME).exists():
            return
        esportes = [e.strip() for d in COMPLEXO_DIVISOES for e in d['esportes'].split(',')]
        quadra = Quadra.objects.create(
            nome=COMPLEXO_NOME,
            descricao='Areia, ginásio coberto e campo society no mesmo lugar',
            localizacao='Av. das Américas, 800',
            cidade='Franca',
            estado='SP',
            esporte=', '.join(esportes),
            tipo='privada',
            quantidade_quadras=len(COMPLEXO_DIVISOES),
            foto='assets/foto_basquete.jpeg',
        )
        hoje = date.today()
        for numero, divisao in enumerate(COMPLEXO_DIVISOES, start=1):
            DivisaoQuadra.objects.create(quadra=quadra, numero=numero, **divisao)
            for i in range(7):
                for hora in range(8, 23):
                    Horario.objects.create(
                        quadra=quadra,
                        numero_quadra=numero,
                        data=hoje + timedelta(days=i),
                        hora_texto=f"{hora:02d}:00 - {hora+1:02d}:00",
                        max_jogadores=divisao['vagas'],
                        preco=60.00,
                    )
        self.stdout.write(self.style.SUCCESS(f'{COMPLEXO_NOME} criado com divisões!'))

    def handle(self, *args, **options):
        ja_tinha_quadras = Quadra.objects.exists()
        self.criar_complexo()
        if ja_tinha_quadras:
            self.stdout.write('Quadras já existem, pulando...')
            return

        quadras_data = [
            {
                'nome': 'Quadra Amazonas',
                'descricao': 'Melhor quadra da região',
                'localizacao': 'Rua Amazonas, 100',
                'cidade': 'Franca',
                'estado': 'SP',
                'esporte': 'Futebol',
                'tipo': 'privada',
                'foto': 'assets/quadraamazonas.jpeg',
            },
            {
                'nome': 'Gol De Placa',
                'descricao': 'Gramado sintético novo',
                'localizacao': 'Av. Brasil, 500',
                'cidade': 'Franca',
                'estado': 'SP',
                'esporte': 'Futebol',
                'foto': 'assets/goldeplaca.jpg',
            },
            {
                'nome': 'Arena Morro Agudo',
                'descricao': 'Quadra para partidas de basquete em Morro Agudo',
                'localizacao': 'Centro',
                'cidade': 'Morro Agudo',
                'estado': 'SP',
                'esporte': 'Basquete',
                'foto': 'assets/residencialpalermo.jpeg',
            },
            {
                'nome': 'Arena Beach Franca',
                'descricao': 'Quadra de areia com iluminação para jogos à noite',
                'localizacao': 'Rua das Palmeiras, 250',
                'cidade': 'Franca',
                'estado': 'SP',
                'esporte': 'Beach-Tennis, Futevolei',
                'tipo': 'privada',
                'foto': 'assets/bitch_tennis.jpeg',
            },
            {
                'nome': 'Quadra do Parque Castelo',
                'descricao': 'Quadra comunitária aberta para partidas de basquete e futebol',
                'localizacao': 'Praça Central do Parque Castelo',
                'cidade': 'Franca',
                'estado': 'SP',
                'esporte': 'Basquete, Futebol',
                'tipo': 'publica',
                'foto': 'assets/parquecastelo.jpeg',
            },
            {
                'nome': 'Clube Vôlei Franca',
                'descricao': 'Quadra coberta com vestiário e estacionamento',
                'localizacao': 'Av. das Nações, 1200',
                'cidade': 'Franca',
                'estado': 'SP',
                'esporte': 'Vôlei',
                'tipo': 'privada',
                'foto': 'assets/volei_foto.jpeg',
            },
            {
                'nome': 'Quadra da Praça Morro Agudo',
                'descricao': 'Espaço público para futevôlei e vôlei de areia',
                'localizacao': 'Praça da Matriz',
                'cidade': 'Morro Agudo',
                'estado': 'SP',
                'esporte': 'Futevolei, Vôlei',
                'tipo': 'publica',
                'foto': 'assets/futevolei.jpg',
            },
            {
                'nome': 'Society Morro Agudo',
                'descricao': 'Campo society com gramado sintético e iluminação',
                'localizacao': 'Rua São Paulo, 340',
                'cidade': 'Morro Agudo',
                'estado': 'SP',
                'esporte': 'Futebol',
                'tipo': 'privada',
                'foto': 'assets/1(1).jpg',
            },
        ]
        hoje = date.today()
        for qd in quadras_data:
            q = Quadra.objects.create(**qd)
            for i in range(7):
                data_atual = hoje + timedelta(days=i)
                for hora in range(18, 22):
                    texto = f"{hora:02d}:00 - {hora+1:02d}:00"
                    Horario.objects.create(
                        quadra=q,
                        data=data_atual,
                        hora_texto=texto,
                        max_jogadores=10 if q.esporte == 'Futebol' else 12,
                        preco=15.00 if q.esporte == 'Futebol' else 12.50,
                    )
        self.stdout.write(self.style.SUCCESS('Quadras e horários criados!'))
