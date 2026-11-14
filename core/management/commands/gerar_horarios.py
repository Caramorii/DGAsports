from datetime import date, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Max

from core.models import Horario, Quadra


class Command(BaseCommand):
    help = (
        'Preenche a agenda dos próximos dias repetindo a grade de horários mais recente de cada quadra. '
        'Horários que já existem não são alterados.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--dias', type=int, default=7, help='Quantos dias a partir de hoje (padrão: 7)')
        parser.add_argument('--quadra', type=int, help='ID de uma quadra específica (padrão: todas)')

    def handle(self, *args, **options):
        dias = options['dias']
        if dias < 1:
            raise CommandError('--dias precisa ser pelo menos 1.')

        quadras = Quadra.objects.prefetch_related('divisoes')
        if options['quadra'] is not None:
            quadras = quadras.filter(pk=options['quadra'])
            if not quadras.exists():
                raise CommandError(f"Quadra {options['quadra']} não encontrada.")

        hoje = date.today()
        datas = [hoje + timedelta(days=i) for i in range(dias)]
        total = 0
        for quadra in quadras:
            criados = self.preencher_quadra(quadra, datas)
            total += criados
            if criados:
                self.stdout.write(f'{quadra.nome}: {criados} horário(s) criado(s)')
        self.stdout.write(self.style.SUCCESS(
            f'{total} horário(s) criado(s) de {datas[0]:%d/%m} até {datas[-1]:%d/%m}.'
        ))

    def preencher_quadra(self, quadra, datas):
        """Usa o último dia com horários como modelo da grade (quadra física, faixa e preço)."""
        ultima_data = quadra.horarios.aggregate(ultima=Max('data'))['ultima']
        if ultima_data is None:
            self.stdout.write(self.style.WARNING(f'{quadra.nome}: sem horários de referência, pulando.'))
            return 0

        grade = quadra.horarios.filter(data=ultima_data)
        existentes = set(
            quadra.horarios.filter(data__in=datas).values_list('data', 'numero_quadra', 'hora_texto')
        )
        novos = []
        for data_atual in datas:
            for modelo in grade:
                chave = (data_atual, modelo.numero_quadra, modelo.hora_texto)
                if chave in existentes:
                    continue
                # Vagas vêm da divisão, pois max_jogadores do modelo pode ter sido alterado por uma reserva.
                novos.append(Horario(
                    quadra=quadra,
                    numero_quadra=modelo.numero_quadra,
                    data=data_atual,
                    hora_texto=modelo.hora_texto,
                    preco=modelo.preco,
                    max_jogadores=modelo.vagas_maximas,
                ))
        Horario.objects.bulk_create(novos)
        return len(novos)
