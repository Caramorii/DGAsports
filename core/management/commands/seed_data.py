from django.core.management.base import BaseCommand
from datetime import date, timedelta
from core.models import Quadra, Horario


class Command(BaseCommand):
    help = 'Popula dados de demonstração (quadras e horários)'

    def handle(self, *args, **options):
        if Quadra.objects.exists():
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
