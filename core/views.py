from django.shortcuts import render, redirect, get_object_or_404
from django.db import IntegrityError
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.conf import settings
from django.db.models import Q, Count, Avg, Sum, Prefetch
from django.db import transaction
from django.utils.http import url_has_allowed_host_and_scheme
from datetime import date, datetime, time, timedelta
import re
import unicodedata
from django.utils import timezone
import uuid
import os
import io
import base64

from .models import Usuario, Quadra, Horario, ReservaJogador, PerfilSocial, Post, Avaliacao, MaterialPartida, ComentarioQuadra, CurtidaPost, ComentarioPost, GrupoQuadraPublica, ParticipanteGrupoPublico, MaterialGrupoPublico

try:
    import qrcode
except ImportError:
    qrcode = None


_ESTADOS_BR = {
    'acre': 'AC', 'alagoas': 'AL', 'amapa': 'AP', 'amazonas': 'AM',
    'bahia': 'BA', 'ceara': 'CE', 'distrito federal': 'DF', 'espirito santo': 'ES',
    'goias': 'GO', 'maranhao': 'MA', 'mato grosso': 'MT',
    'mato grosso do sul': 'MS', 'minas gerais': 'MG', 'para': 'PA',
    'paraiba': 'PB', 'parana': 'PR', 'pernambuco': 'PE', 'piaui': 'PI',
    'rio de janeiro': 'RJ', 'rio grande do norte': 'RN',
    'rio grande do sul': 'RS', 'rondonia': 'RO', 'roraima': 'RR',
    'santa catarina': 'SC', 'sao paulo': 'SP', 'sergipe': 'SE',
    'tocantins': 'TO',
}
_ESTADO_POR_UF = {uf.lower(): nome for nome, uf in _ESTADOS_BR.items()}


def _normalizar_texto_busca(valor):
    texto = unicodedata.normalize('NFKD', str(valor or '').casefold())
    return ''.join(caractere for caractere in texto if not unicodedata.combining(caractere)).strip()


def _termos_equivalentes_localidade(termo):
    normalizado = _normalizar_texto_busca(termo)
    uf = _ESTADOS_BR.get(normalizado)
    nome_estado = _ESTADO_POR_UF.get(normalizado)
    equivalentes = [termo]
    if uf:
        equivalentes.extend([uf, termo])
    elif nome_estado:
        equivalentes.extend([nome_estado, nome_estado.title()])
    return list(dict.fromkeys(item for item in equivalentes if item))


def home(request):
    tem_quadra = request.user.is_authenticated and Quadra.objects.filter(proprietario=request.user).exists()
    return render(request, 'DGASports.html', {'tem_quadra': tem_quadra})


def explorar(request):
    localidade_busca = request.GET.get('localidade', '').strip()
    esporte_busca = request.GET.get('esporte', '').strip()
    tipo_busca = request.GET.get('tipo', '').strip()  # Captura privada / publica

    qs = Quadra.objects.annotate(
        total_horarios=Count('horarios', distinct=True),
        total_jogadores_agora=Count('horarios__reservas', distinct=True),
        nota_media=Avg('avaliacoes__nota'),
    ).order_by('-destaque', '-nota_media', 'nome')

    if localidade_busca:
        qs = qs.filter(Q(cidade__icontains=localidade_busca) | Q(estado__icontains=localidade_busca))

    if esporte_busca and esporte_busca != 'Todos':
        if esporte_busca == 'Vôlei':
            qs = qs.filter(Q(esporte__icontains='Vôlei') | Q(esporte__icontains='Volei'))
        elif esporte_busca == 'Futevôlei':
            qs = qs.filter(Q(esporte__icontains='Futevôlei') | Q(esporte__icontains='Futevolei'))
        else:
            qs = qs.filter(esporte__icontains=esporte_busca)

    if tipo_busca and tipo_busca != 'todos':
        qs = qs.filter(tipo=tipo_busca)

    return render(request, 'explorar.html', {
        'quadras': qs,
        'localidade_busca': localidade_busca,
        'esporte_busca': esporte_busca,
        'tipo_busca': tipo_busca,  # Devolve para manter o select selecionado
    })


@require_GET
def api_quadras(request):
    localidade = request.GET.get('localidade', '').strip()
    esporte = request.GET.get('esporte', '').strip()
    tipo = request.GET.get('tipo', '').strip()

    grupos_prefetch = GrupoQuadraPublica.objects.annotate(
        total_participantes=Count('participantes', distinct=True),
        total_materiais=Count('materiais', distinct=True),
    ).prefetch_related('participantes', 'materiais__usuario').order_by(
        '-total_participantes', '-total_materiais', '-criado_em'
    )
    quadras = Quadra.objects.annotate(
        total_horarios=Count('horarios', distinct=True),
        total_jogadores=Count('horarios__reservas', distinct=True),
        total_grupos=Count('grupos_publicos', distinct=True),
        nota_media=Avg('avaliacoes__nota'),
    ).prefetch_related(Prefetch('grupos_publicos', queryset=grupos_prefetch, to_attr='grupos_ordenados')).order_by('-destaque', '-nota_media', 'nome')

    if localidade:
        termos_localidade = [termo.strip() for termo in re.split(r'[,;]', localidade) if termo.strip()]
        for termo in termos_localidade:
            filtro_termo = Q()
            for equivalente in _termos_equivalentes_localidade(termo):
                filtro_termo |= (
                    Q(nome__icontains=equivalente) | Q(localizacao__icontains=equivalente)
                    | Q(cidade__icontains=equivalente) | Q(estado__icontains=equivalente)
                )
            quadras = quadras.filter(filtro_termo)
    if tipo in {'publica', 'privada'}:
        quadras = quadras.filter(tipo=tipo)
    if esporte and esporte.lower() not in {'todos', 'qualquer'}:
        if 'volei' in esporte.lower() or 'vôlei' in esporte.lower():
            quadras = quadras.filter(Q(esporte__icontains='Vôlei') | Q(esporte__icontains='Volei'))
        elif 'futevolei' in esporte.lower() or 'futevôlei' in esporte.lower():
            quadras = quadras.filter(Q(esporte__icontains='Futevôlei') | Q(esporte__icontains='Futevolei'))
        elif 'beach' in esporte.lower():
            quadras = quadras.filter(Q(esporte__icontains='Beach') | Q(esporte__icontains='Tennis'))
        else:
            quadras = quadras.filter(esporte__icontains=esporte)

    resultados = [{
        'id': quadra.id,
        'nome': quadra.nome,
        'descricao': quadra.descricao or '',
        'localizacao': quadra.localizacao or '',
        'cidade': quadra.cidade or '',
        'estado': quadra.estado or '',
        'esportes': quadra.lista_esportes,
        'tipo': quadra.tipo,
        'foto': quadra.foto or '',
        'total_horarios': quadra.total_horarios,
        'total_jogadores': quadra.total_jogadores,
        'total_grupos': quadra.total_grupos,
        'grupos': [{
            'id': grupo.id,
            'esporte': grupo.esporte,
            'data_encontro': grupo.data_encontro.isoformat() if grupo.data_encontro else '',
            'hora_inicio': grupo.hora_inicio.strftime('%H:%M') if grupo.hora_inicio else '',
            'hora_fim': grupo.hora_fim.strftime('%H:%M') if grupo.hora_fim else '',
            'participantes': grupo.total_participantes,
            'materiais': [{'item': material.item, 'usuario': material.usuario.nome} for material in grupo.materiais.all()],
        } for grupo in quadra.grupos_ordenados[:2]] if quadra.tipo == 'publica' else [],
        'nota_media': round(float(quadra.nota_media), 1) if quadra.nota_media is not None else None,
        'url': f'/quadra/{quadra.id}/',
    } for quadra in quadras[:100]]
    return JsonResponse({'status': 'sucesso', 'quadras': resultados, 'total': len(resultados)})


@require_GET
def api_grupos_quadra(request, quadra_id):
    quadra = get_object_or_404(Quadra, pk=quadra_id, tipo='publica')
    grupos = GrupoQuadraPublica.objects.filter(quadra=quadra).annotate(
        total_participantes=Count('participantes', distinct=True),
        total_materiais=Count('materiais', distinct=True),
    ).prefetch_related('participantes', 'materiais__usuario').order_by(
        '-total_participantes', '-total_materiais', '-criado_em'
    )
    resultados = [{
        'id': grupo.id,
        'esporte': grupo.esporte,
        'data_encontro': grupo.data_encontro.isoformat() if grupo.data_encontro else '',
        'hora_inicio': grupo.hora_inicio.strftime('%H:%M') if grupo.hora_inicio else '',
        'hora_fim': grupo.hora_fim.strftime('%H:%M') if grupo.hora_fim else '',
        'participantes': grupo.total_participantes,
        'materiais': [{'item': material.item, 'usuario': material.usuario.nome} for material in grupo.materiais.all()],
    } for grupo in grupos]
    return JsonResponse({'status': 'sucesso', 'total': len(resultados), 'grupos': resultados})


def _horario_para_cliente(horario, usuario_id=None):
    reservas = list(horario.reservas.all())
    responsavel = next(
        (reserva for reserva in reservas if reserva.usuario_id == horario.responsavel_reserva_id),
        reservas[0] if reservas else None,
    )
    return {
        'id': horario.id,
        'data': horario.data.isoformat() if hasattr(horario.data, 'isoformat') else str(horario.data),
        'hora_texto': horario.hora_texto,
        'disponivel': horario.quadra.tipo != 'privada' or not _horario_passou(horario),
        'max_jogadores': horario.max_jogadores,
        'preco': float(horario.preco),
        'esporte_reservado': horario.esporte_reservado,
        'jogadores_atuais': len(reservas),
        'usuario_na_partida': int(any(reserva.usuario_id == usuario_id for reserva in reservas)) if usuario_id else 0,
        'responsavel_reserva_id': responsavel.usuario_id if responsavel else None,
        'responsavel_nome': responsavel.usuario.nome if responsavel else '',
        'responsavel_status': responsavel.status if responsavel else '',
        'responsavel_metodo': responsavel.metodo_pagamento if responsavel else '',
        'aceita_convidados': horario.aceita_convidados,
        'jogadores': [
            {'id': reserva.usuario_id, 'nome': reserva.usuario.nome, 'status': reserva.status,
             'metodo_pagamento': reserva.metodo_pagamento}
            for reserva in reservas
        ],
    }


def _inicio_horario(horario):
    correspondencia = re.search(r'(\d{1,2})\s*[h:]\s*(\d{2})', horario.hora_texto or '', re.IGNORECASE)
    if not correspondencia:
        return None
    try:
        return time(int(correspondencia.group(1)), int(correspondencia.group(2)))
    except ValueError:
        return None


def _horario_passou(horario):
    hoje = timezone.localdate()
    if horario.data < hoje:
        return True
    if horario.data > hoje:
        return False
    inicio = _inicio_horario(horario)
    return bool(inicio and inicio <= timezone.localtime().time().replace(tzinfo=None))


def _chave_ordenacao_horario(horario):
    inicio = _inicio_horario(horario)
    return (horario.data, inicio or time.max, horario.hora_texto or '')


def detalhes_quadra(request, quadra_id):
    quadra = get_object_or_404(Quadra, pk=quadra_id)
    hoje = timezone.localdate()
    usuario_id = request.user.id if request.user.is_authenticated else None
    avaliacoes = quadra.avaliacoes.select_related('usuario').all()[:5]
    pode_avaliar = bool(usuario_id and ReservaJogador.objects.filter(
        usuario_id=usuario_id, horario__quadra=quadra
    ).exists())
    if quadra.tipo == 'publica' and usuario_id:
        pode_avaliar = True

    horarios = list(Horario.objects.filter(quadra=quadra).select_related('quadra', 'responsavel_reserva').prefetch_related(
        'reservas__usuario'
    ))
    grupos_publicos = []
    if quadra.tipo == 'publica':
        grupos = quadra.grupos_publicos.prefetch_related('participantes', 'inscricoes', 'materiais__usuario').all()
        for grupo in grupos:
            participantes = list(grupo.participantes.all())
            grupos_publicos.append({
                'obj': grupo,
                'participantes': participantes,
                'ja_participa': usuario_id in {participante.id for participante in participantes} if usuario_id else False,
                'total_participantes': len(participantes),
            })
    horarios.sort(key=_chave_ordenacao_horario)
    horarios_list = []
    for h in horarios:
        horarios_list.append(_horario_para_cliente(h, usuario_id))

    quadra_dict = {
        'id': quadra.id,
        'nome': quadra.nome,
        'descricao': quadra.descricao,
        'localizacao': quadra.localizacao,
        'cidade': quadra.cidade,
        'estado': quadra.estado,
        'esporte': quadra.esporte,
        'tipo': quadra.tipo,
        'foto': quadra.foto,
        'situacao': quadra.situacao,
        'comentario_admin': quadra.comentario_admin,
        'lista_esportes': quadra.lista_esportes,
        'horarios': horarios_list,
        'datas_disponiveis': [
            {
                'valor': data_iso,
                'rotulo': ('Hoje · ' if data_iso == timezone.localdate().isoformat() else '')
                    + ['segunda-feira', 'terça-feira', 'quarta-feira', 'quinta-feira', 'sexta-feira', 'sábado', 'domingo'][date.fromisoformat(data_iso).weekday()]
                    + ' · ' + date.fromisoformat(data_iso).strftime('%d/%m'),
            }
            for data_iso in sorted({
                h['data'] for h in horarios_list
                if quadra.tipo != 'privada' or date.fromisoformat(h['data']) >= hoje
            })
        ],
    }
    return render(request, 'detalhes_quadra.html', {
        'quadra': quadra_dict,
        'hoje': hoje.isoformat(),
        'avaliacoes': avaliacoes,
        'nota_media': quadra.avaliacoes.aggregate(media=Avg('nota'))['media'],
        'total_avaliacoes': quadra.avaliacoes.count(),
        'pode_avaliar': pode_avaliar,
        'comentarios_publicos': quadra.comentarios.select_related('usuario').all()[:50],
        'grupos_publicos': grupos_publicos,
    })


def campeonatos(request):
    return render(request, 'campeonatos.html')


def register_view(request):
    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        email = request.POST.get('email', '').strip()
        senha = request.POST.get('senha')
        cidade = request.POST.get('cidade', '').strip()
        if not all([nome, email, senha, cidade]):
            messages.error(request, 'Preencha todos os campos obrigatórios.')
            return redirect('register')
        if Usuario.objects.filter(email=email).exists():
            messages.error(request, 'Este e-mail já existe.')
            return redirect('register')
        user = Usuario.objects.create_user(email=email, nome=nome, cidade=cidade, password=senha)
        messages.success(request, 'Usuário cadastrado com sucesso!')
        return redirect('login')
    return render(request, 'register.html')


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        senha = request.POST.get('senha')
        user = authenticate(request, username=email, password=senha)
        if user is not None:
            login(request, user)
            messages.success(request, f'Bem-vindo, {user.nome}!')
            proximo = request.GET.get('proximo') or request.POST.get('proximo')
            if proximo and url_has_allowed_host_and_scheme(proximo, {request.get_host()}):
                return redirect(proximo)
            return redirect('home')
        messages.error(request, 'E-mail ou senha inválidos.')
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    messages.info(request, 'Você saiu da sua conta.')
    return redirect('home')


@login_required(login_url='login')
def admin_cadastrar_quadra(request):
    if not request.user.is_staff:
        messages.error(request, 'Acesso restrito!')
        return redirect('login')

    if request.method == 'POST':
        # Captura garantindo compatibilidade com 'nome' ou 'nome_quadra'
        nome = request.POST.get('nome') or request.POST.get('nome_quadra')
        descricao = request.POST.get('descricao') or request.POST.get('descricao_quadra')
        
        # Junta a rua com o número digitado manualmente
        rua = request.POST.get('localizacao', '').strip()
        numero = request.POST.get('numero', '').strip()
        localizacao = f"{rua}, {numero}" if numero else rua

        cidade = re.sub(r'\s+', ' ', request.POST.get('cidade', '').strip())
        estado_digitado = re.sub(r'\s+', ' ', request.POST.get('estado', '').strip())
        estado_normalizado = _normalizar_texto_busca(estado_digitado)
        estado = _ESTADOS_BR.get(estado_normalizado, estado_digitado.upper())
        esporte = request.POST.get('esporte')
        tipo = request.POST.get('tipo', 'publica')
        email_proprietario = request.POST.get('email_proprietario', '').strip()
        abertura = request.POST.get('hora_abertura')
        fechamento = request.POST.get('hora_fechamento')
        preco = request.POST.get('preco') or 0
        cep = request.POST.get('cep')

        # Upload da foto
        file = request.FILES.get('foto')
        if file and file.name:
            extensao = os.path.splitext(file.name)[1]
            novo_nome = f"{uuid.uuid4()}{extensao}"
            upload_folder = os.path.join(settings.BASE_DIR, 'static', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            with open(os.path.join(upload_folder, novo_nome), 'wb+') as dest:
                for chunk in file.chunks():
                    dest.write(chunk)
            foto_path = f"uploads/{novo_nome}"
        else:
            foto_path = "uploads/default_quadra.jpg"

        # 1. Criação ÚNICA da quadra no banco de dados
        if tipo not in dict(Quadra.TIPO_CHOICES):
            tipo = 'publica'
        proprietario = Usuario.objects.filter(email__iexact=email_proprietario).first() if email_proprietario else None
        if tipo == 'privada' and not proprietario:
            messages.error(request, 'Cadastre primeiro o usuário proprietário e informe o e-mail usado no cadastro.')
            return redirect('admin_cadastrar_quadra')

        quadra = Quadra.objects.create(
            nome=nome,
            descricao=descricao,
            localizacao=localizacao,
            cidade=cidade,
            estado=estado,
            esporte=esporte,
            tipo=tipo,
            proprietario=proprietario,
            foto=foto_path,
            situacao=request.POST.get('situacao', 'Em boas condições').strip() or 'Em boas condições',
            comentario_admin=request.POST.get('comentario_admin', '').strip(),
        )

        # 2. Geração da grade de horários para 7 dias
        try:
            h_inicio = int(abertura.split(':')[0])
            h_fim = int(fechamento.split(':')[0])
        except (ValueError, AttributeError, IndexError):
            h_inicio, h_fim = 8, 22

        if tipo == 'privada':
            hoje = date.today()
            for i in range(7):
                data_atual = hoje + timedelta(days=i)
                for hora in range(h_inicio, h_fim):
                    texto_horario = f"{hora:02d}:00 - {hora+1:02d}:00"
                    Horario.objects.create(
                        quadra=quadra,
                        data=data_atual,
                        hora_texto=texto_horario,
                        max_jogadores=12,
                        preco=preco
                    )

        if tipo == 'privada':
            messages.success(request, 'Quadra particular e agenda de 7 dias criadas com sucesso!')
        else:
            messages.success(request, 'Quadra pública cadastrada com sucesso!')
        return redirect('explorar')

    return render(request, 'cadastrar_novas_quadras.html')


@login_required(login_url='login')
@require_POST
def atualizar_situacao_quadra(request, quadra_id):
    if not request.user.is_staff:
        messages.error(request, 'Apenas a administração pode atualizar a situação oficial da quadra.')
        return redirect('detalhes_quadra', quadra_id=quadra_id)
    quadra = get_object_or_404(Quadra, pk=quadra_id, tipo='publica')
    quadra.situacao = request.POST.get('situacao', '').strip()[:200] or 'Sem atualização oficial.'
    quadra.comentario_admin = request.POST.get('comentario_admin', '').strip()
    quadra.save(update_fields=['situacao', 'comentario_admin'])
    messages.success(request, 'Situação e comentário oficial atualizados.')
    return redirect('detalhes_quadra', quadra_id=quadra.id)


@require_POST
def entrar_na_partida(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'erro', 'mensagem': 'Faça login primeiro.'}, status=401)
    import json
    try:
        dados = json.loads(request.body)
    except json.JSONDecodeError:
        dados = request.POST
    horario_id = dados.get('horario_id')
    esporte = dados.get('esporte_selecionado')
    try:
        with transaction.atomic():
            horario = Horario.objects.select_for_update().select_related('quadra').get(pk=horario_id)
            if horario.quadra.tipo != 'publica':
                return JsonResponse({'status': 'erro', 'mensagem': 'Reservas em quadras particulares devem ser confirmadas pelo fluxo de pagamento.'}, status=400)
            if horario.data < date.today():
                return JsonResponse({'status': 'erro', 'mensagem': 'Este horário já passou.'}, status=400)
            if esporte not in horario.quadra.lista_esportes:
                return JsonResponse({'status': 'erro', 'mensagem': 'Esporte inválido para esta quadra.'}, status=400)
            if horario.esporte_reservado and horario.esporte_reservado != esporte:
                return JsonResponse({'status': 'erro', 'mensagem': 'Este horário já foi reservado para outro esporte.'}, status=400)
            if ReservaJogador.objects.filter(usuario=request.user, horario=horario).exists():
                return JsonResponse({'status': 'erro', 'mensagem': 'Você já está nesta partida.'}, status=409)
            if horario.reservas.count() >= horario.max_jogadores:
                return JsonResponse({'status': 'erro', 'mensagem': 'Este horário está lotado.'}, status=409)
            if not horario.esporte_reservado:
                horario.esporte_reservado = esporte
                horario.save(update_fields=['esporte_reservado'])
            ReservaJogador.objects.create(usuario=request.user, horario=horario)
            return JsonResponse({'status': 'sucesso', 'nova_contagem': horario.reservas.count()})
    except Horario.DoesNotExist:
        return JsonResponse({'status': 'erro', 'mensagem': 'Horário não encontrado.'}, status=404)


@require_POST
def sair_da_partida(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'erro', 'mensagem': 'Faça login primeiro.'}, status=401)
    import json
    try:
        dados = json.loads(request.body)
    except json.JSONDecodeError:
        dados = request.POST
    horario_id = dados.get('horario_id')
    try:
        with transaction.atomic():
            horario = Horario.objects.select_for_update().get(pk=horario_id)
            removidos, _ = ReservaJogador.objects.filter(usuario=request.user, horario=horario).delete()
            if not removidos:
                return JsonResponse({'status': 'erro', 'mensagem': 'Você não está nesta partida.'}, status=400)
            nova_contagem = horario.reservas.count()
            responsavel_alterado = horario.responsavel_reserva_id == request.user.id
            if responsavel_alterado:
                novo_responsavel = horario.reservas.select_related('usuario').order_by('criada_em').first()
                horario.responsavel_reserva = novo_responsavel.usuario if novo_responsavel else None
            esporte_destravado = nova_contagem == 0
            if esporte_destravado:
                horario.esporte_reservado = None
                horario.aceita_convidados = False
                horario.max_jogadores = 12
                horario.save(update_fields=['esporte_reservado', 'responsavel_reserva', 'aceita_convidados', 'max_jogadores'])
            elif responsavel_alterado:
                horario.save(update_fields=['responsavel_reserva'])
            return JsonResponse({'status': 'sucesso', 'nova_contagem': nova_contagem, 'esporte_destravado': esporte_destravado})
    except Horario.DoesNotExist:
        return JsonResponse({'status': 'erro', 'mensagem': 'Horário não encontrado.'}, status=404)

    ReservaJogador.objects.filter(usuario=request.user, horario_id=horario_id).delete()
    return JsonResponse({'status': 'sucesso'})


def api_get_horarios_por_data(request, quadra_id, data_selecionada):
    usuario_id = request.user.id if request.user.is_authenticated else None
    horarios = list(Horario.objects.filter(quadra_id=quadra_id, data=data_selecionada).select_related(
        'quadra', 'responsavel_reserva'
    ).prefetch_related('reservas__usuario'))
    horarios.sort(key=_chave_ordenacao_horario)
    result = []
    for h in horarios:
        result.append(_horario_para_cliente(h, usuario_id))
    return JsonResponse({'status': 'sucesso', 'horarios': result})


@login_required(login_url='login')
def reservar(request, horario_id):
    horario = get_object_or_404(
        Horario.objects.select_related('quadra', 'responsavel_reserva').prefetch_related('reservas__usuario'),
        pk=horario_id,
    )
    if horario.quadra.tipo != 'privada':
        return redirect('detalhes_quadra', quadra_id=horario.quadra_id)
    esporte = request.GET.get('esporte', '').strip()
    if _horario_passou(horario):
        messages.error(request, 'Este horário já passou e está indisponível.')
        return redirect('detalhes_quadra', quadra_id=horario.quadra_id)
    if esporte not in horario.quadra.lista_esportes:
        messages.error(request, 'Selecione um esporte válido para esta quadra.')
        return redirect('detalhes_quadra', quadra_id=horario.quadra_id)
    if horario.esporte_reservado and horario.esporte_reservado != esporte:
        messages.error(request, 'Este horário já está reservado para outro esporte.')
        return redirect('detalhes_quadra', quadra_id=horario.quadra_id)
    modo_reserva = _modo_reserva(horario, request.user)
    if modo_reserva == 'indisponivel':
        messages.error(request, 'Este horário já está reservado e não aceita mais participantes.')
        return redirect('detalhes_quadra', quadra_id=horario.quadra_id)
    reserva = {
        'quadra': {
            'nome': horario.quadra.nome,
            'cidade': horario.quadra.cidade,
            'imagem': horario.quadra.foto,
        },
        'horario': {
            'id': horario.id,
            'hora': horario.hora_texto,
            'preco': float(horario.preco),
            'max_jogadores': horario.max_jogadores,
            'jogadores_atuais': len(horario.reservas.all()),
        }
    }
    jogadores = [
        {'nome': item.usuario.nome, 'status': item.status, 'metodo_pagamento': item.metodo_pagamento}
        for item in horario.reservas.all()
    ]
    return render(request, 'reserva_privada.html', {
        'reserva': reserva,
        'esporte_selecionado': esporte,
        'usuario_atual': request.user,
        'modo_reserva': modo_reserva,
        'jogadores': jogadores,
        'aceita_convidados': horario.aceita_convidados,
    })


def _modo_reserva(horario, usuario):
    reservas = list(horario.reservas.all())
    propria = next((item for item in reservas if item.usuario_id == usuario.id), None)
    responsavel = next(
        (item for item in reservas if item.usuario_id == horario.responsavel_reserva_id),
        reservas[0] if reservas else None,
    )
    if propria:
        if (propria.usuario_id == (responsavel.usuario_id if responsavel else None)
                and propria.status == 'pendente' and propria.metodo_pagamento == 'caixa'):
            return 'quitar_caixa'
        return 'indisponivel'
    if not reservas:
        return 'nova'
    if responsavel and responsavel.status == 'pendente' and responsavel.metodo_pagamento == 'caixa':
        if horario.aceita_convidados and len(reservas) < horario.max_jogadores:
            return 'grupo'
        if len(reservas) == 1:
            return 'assumir'
    if horario.aceita_convidados and len(reservas) < horario.max_jogadores:
        return 'grupo'
    return 'indisponivel'


def _concluir_reserva_privada(usuario, horario_id, esporte, modo, forma_pagamento,
                               max_jogadores=None, aceita_convidados=False):
    with transaction.atomic():
        horario = Horario.objects.select_for_update().select_related('quadra').get(pk=horario_id)
        if horario.quadra.tipo != 'privada':
            raise ValueError('Este fluxo é exclusivo para quadras particulares.')
        if _horario_passou(horario):
            raise ValueError('Este horário já passou e está indisponível.')
        if esporte not in horario.quadra.lista_esportes:
            raise ValueError('Esporte inválido para esta quadra.')
        modo_atual = _modo_reserva(horario, usuario)
        if modo_atual != modo:
            raise ValueError('A situação deste horário mudou. Atualize a página e tente novamente.')
        reservas = list(horario.reservas.select_related('usuario').order_by('criada_em'))
        pago = forma_pagamento == 'sistema'

        if modo == 'quitar_caixa':
            reserva = next(item for item in reservas if item.usuario_id == usuario.id)
            if not pago:
                raise ValueError('Para garantir este horário, pague pelo sistema.')
            reserva.status = 'pago'
            reserva.metodo_pagamento = 'sistema'
            reserva.pago_em = timezone.now()
            reserva.save(update_fields=['status', 'metodo_pagamento', 'pago_em'])
            return horario

        if modo == 'grupo':
            if not pago:
                raise ValueError('Para entrar nesta partida, é necessário pagar pelo sistema.')
            if not horario.aceita_convidados or len(reservas) >= horario.max_jogadores:
                raise ValueError('Esta partida não tem mais vagas disponíveis.')
            ReservaJogador.objects.create(
                usuario=usuario, horario=horario, status='pago',
                metodo_pagamento='sistema', pago_em=timezone.now(),
            )
            if not horario.responsavel_reserva_id and reservas:
                horario.responsavel_reserva = reservas[0].usuario
                horario.save(update_fields=['responsavel_reserva'])
            return horario

        if modo == 'assumir':
            responsavel = next(
                (item for item in reservas if item.usuario_id == horario.responsavel_reserva_id),
                reservas[0] if reservas else None,
            )
            if not pago or not responsavel or responsavel.status != 'pendente' or responsavel.metodo_pagamento != 'caixa' or len(reservas) != 1:
                raise ValueError('Este horário só pode ser assumido com pagamento pelo sistema.')
            responsavel.delete()

        elif modo != 'nova':
            raise ValueError('Este horário não está disponível.')
        elif reservas:
            raise ValueError('Este horário já foi reservado.')

        if forma_pagamento == 'caixa' and modo != 'nova':
            raise ValueError('O pagamento no caixa só está disponível para horários livres.')
        if aceita_convidados:
            try:
                capacidade = int(max_jogadores)
            except (TypeError, ValueError):
                raise ValueError('Escolha a capacidade máxima da partida.')
            if capacidade < 2 or capacidade > 30:
                raise ValueError('A capacidade deve ser entre 2 e 30 pessoas.')
        else:
            capacidade = 1

        if forma_pagamento == 'caixa':
            status = 'pendente'
            metodo = 'caixa'
            pago_em = None
        elif forma_pagamento == 'sistema':
            status = 'pago'
            metodo = 'sistema'
            pago_em = timezone.now()
        else:
            raise ValueError('Selecione uma forma de pagamento válida.')

        ReservaJogador.objects.create(
            usuario=usuario, horario=horario, status=status,
            metodo_pagamento=metodo, pago_em=pago_em,
        )
        horario.esporte_reservado = esporte
        horario.max_jogadores = capacidade
        horario.aceita_convidados = aceita_convidados
        horario.responsavel_reserva = usuario
        horario.save(update_fields=[
            'esporte_reservado', 'max_jogadores', 'aceita_convidados', 'responsavel_reserva'
        ])
        return horario


def registrar_reserva(usuario, horario_id, esporte):
    """Registra uma reserva com bloqueio de linha para evitar excesso de vagas."""
    with transaction.atomic():
        horario = Horario.objects.select_for_update().select_related('quadra').get(pk=horario_id)
        if horario.data < date.today():
            raise ValueError('Este horário já passou.')
        if esporte not in horario.quadra.lista_esportes:
            raise ValueError('Esporte inválido para esta quadra.')
        if horario.esporte_reservado and horario.esporte_reservado != esporte:
            raise ValueError('Este horário já está reservado para outro esporte.')
        ja_reservou = horario.reservas.filter(usuario=usuario).exists()
        if not ja_reservou and horario.reservas.count() >= horario.max_jogadores:
            raise ValueError('Este horário está lotado.')
        if not horario.esporte_reservado:
            horario.esporte_reservado = esporte
            horario.save(update_fields=['esporte_reservado'])
        ReservaJogador.objects.get_or_create(usuario=usuario, horario=horario)
        return horario


@login_required(login_url='login')
@require_POST
def confirmar_reserva(request):
    metodo = request.POST.get('metodo')
    horario_id = request.POST.get('horario_id')
    esporte = request.POST.get('esporte_selecionado')
    horario = get_object_or_404(Horario.objects.select_related('quadra').prefetch_related('reservas__usuario'), pk=horario_id)
    if horario.quadra.tipo != 'privada':
        messages.error(request, 'O pagamento de reservas particulares não se aplica a esta quadra.')
        return redirect('detalhes_quadra', quadra_id=horario.quadra_id)
    modo = request.POST.get('modo_reserva') or _modo_reserva(horario, request.user)
    aceita_convidados = request.POST.get('aceita_convidados') == 'on'
    max_jogadores = request.POST.get('max_jogadores')

    if metodo == 'caixa':
        try:
            _concluir_reserva_privada(
                request.user, horario_id, esporte, modo, 'caixa', max_jogadores, aceita_convidados
            )
            messages.warning(request, 'Reserva provisória: o horário pode ser assumido por alguém que pagar pelo sistema antes de você.')
            return redirect('minhas_reservas')
        except (Horario.DoesNotExist, ValueError, IntegrityError) as erro:
            messages.error(request, str(erro))
            return redirect('detalhes_quadra', quadra_id=horario.quadra_id)

    if metodo == 'pix':
        if modo == 'indisponivel':
            messages.error(request, 'Este horário já está reservado e não aceita mais participantes.')
            return redirect('detalhes_quadra', quadra_id=horario.quadra_id)
        return render(request, 'pagamento_pix.html', {
            'horario_id': horario_id,
            'esporte_selecionado': esporte,
            'modo_reserva': modo,
            'max_jogadores': max_jogadores,
            'aceita_convidados': aceita_convidados,
            'valor': horario.preco,
            'quadra': horario.quadra,
            'horario': horario,
        })

    if metodo != 'pix':
        messages.error(request, 'Escolha pagar pelo sistema ou no caixa da quadra.')
        return redirect('detalhes_quadra', quadra_id=horario.quadra_id)


@login_required(login_url='login')
@require_POST
def finalizar_pix(request):
    horario_id = request.POST.get('horario_id')
    esporte = request.POST.get('esporte_selecionado')
    modo = request.POST.get('modo_reserva')
    horario = get_object_or_404(Horario.objects.select_related('quadra'), pk=horario_id)
    if horario.quadra.tipo != 'privada':
        messages.error(request, 'Este pagamento de demonstração só vale para quadras particulares.')
        return redirect('detalhes_quadra', quadra_id=horario.quadra_id)
    max_jogadores = request.POST.get('max_jogadores')
    aceita_convidados = request.POST.get('aceita_convidados') == 'on'
    try:
        _concluir_reserva_privada(
            request.user, horario_id, esporte, modo, 'sistema',
            max_jogadores, aceita_convidados,
        )
        messages.success(request, 'Pagamento confirmado em modo de demonstração. Reserva garantida.')
    except (Horario.DoesNotExist, ValueError, IntegrityError) as erro:
        messages.error(request, str(erro))
    return redirect('minhas_reservas')


@login_required(login_url='login')
def social(request):
    try:
        perfil = request.user.perfil_social
        dados = {
            'usuario_social': perfil.usuario_social,
            'bio': perfil.bio,
            'foto_perfil': perfil.foto_perfil,
        }
    except PerfilSocial.DoesNotExist:
        dados = {}

    posts_qs = Post.objects.select_related('usuario').prefetch_related(
        'usuario__perfil_social', 'curtidas', 'comentarios__usuario'
    ).all()
    curtidas_do_usuario = set(CurtidaPost.objects.filter(usuario=request.user).values_list('post_id', flat=True))
    feed_items = []
    for p in posts_qs:
        foto = 'images/default_avatar.png'
        usuario_social = None
        try:
            foto = p.usuario.perfil_social.foto_perfil
            usuario_social = p.usuario.perfil_social.usuario_social
        except PerfilSocial.DoesNotExist:
            pass
        feed_items.append({
            'is_partida': False,
            'id': p.id,
            'usuario_id': p.usuario_id,
            'texto': p.texto,
            'imagem': p.imagem,
            'tipo': p.tipo,
            'data_postagem': p.data_postagem,
            'nome_usuario': p.usuario.nome,
            'usuario_social': usuario_social,
            'foto_perfil': foto,
            'curtidas_total': p.curtidas.count(),
            'curtido_por_mim': p.id in curtidas_do_usuario,
            'comentarios': p.comentarios.all(),
        })
    quadras_publicas = Quadra.objects.filter(tipo='publica').order_by('cidade', 'nome')
    grupos = (GrupoQuadraPublica.objects.filter(quadra__tipo='publica')
        .select_related('quadra', 'criador').prefetch_related('participantes', 'inscricoes', 'materiais__usuario')[:100])
    for grupo in grupos:
        inscricoes = list(grupo.inscricoes.all())
        minha_inscricao = next((inscricao for inscricao in inscricoes if inscricao.usuario_id == request.user.id), None)
        feed_items.append({
            'is_grupo': True,
            'id': grupo.id,
            'obj': grupo,
            'data_postagem': grupo.criado_em,
            'ja_participa': minha_inscricao is not None,
            'presencas': minha_inscricao.presencas if minha_inscricao else 0,
        })
    feed_items.sort(key=lambda item: item['data_postagem'], reverse=True)
    return render(request, 'dga.social.html', {
        'dados': dados, 'posts': feed_items, 'quadras_publicas': quadras_publicas,
    })


def _social_action_response(request, message, success, status=400):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'ok': success, 'message': message}, status=200 if success else status)
    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)
    return redirect('social')


@login_required(login_url='login')
@require_POST
def criar_partida_comunidade(request):
    quadra = get_object_or_404(Quadra, pk=request.POST.get('quadra_id'), tipo='publica')
    esporte = request.POST.get('esporte', '').strip()
    try:
        hora_inicio = time.fromisoformat(request.POST.get('hora_inicio', '').strip())
        hora_fim = time.fromisoformat(request.POST.get('hora_fim', '').strip())
    except ValueError:
        return _social_action_response(request, 'Informe o hor\u00e1rio de in\u00edcio e a previs\u00e3o de t\u00e9rmino.', False)
    if esporte not in quadra.lista_esportes:
        return _social_action_response(request, 'Escolha um esporte oferecido por esta quadra.', False)
    if hora_fim <= hora_inicio:
        return _social_action_response(request, 'A previs\u00e3o de t\u00e9rmino precisa ser depois do in\u00edcio.', False)
    with transaction.atomic():
        grupo = GrupoQuadraPublica.objects.create(
            quadra=quadra, esporte=esporte, hora_inicio=hora_inicio, hora_fim=hora_fim,
            criador=request.user,
        )
        ParticipanteGrupoPublico.objects.create(grupo=grupo, usuario=request.user)
    return _social_action_response(request, 'Grupo criado e publicado na comunidade!', True)


@login_required(login_url='login')
@require_POST
def criar_grupo_quadra_publica(request, quadra_id):
    quadra = get_object_or_404(Quadra, pk=quadra_id, tipo='publica')
    esporte = request.POST.get('esporte', '').strip()
    try:
        hora_inicio = time.fromisoformat(request.POST.get('hora_inicio', '').strip())
        hora_fim = time.fromisoformat(request.POST.get('hora_fim', '').strip())
    except ValueError:
        messages.error(request, 'Informe o horário em que o grupo começa e a previsão de término.')
        return redirect(f'/quadra/{quadra.id}/#grupos')
    if esporte not in quadra.lista_esportes:
        messages.error(request, 'Escolha um esporte oferecido por esta quadra.')
        return redirect(f'/quadra/{quadra.id}/#grupos')
    if hora_fim <= hora_inicio:
        messages.error(request, 'A previsão de término precisa ser depois do horário de início.')
        return redirect(f'/quadra/{quadra.id}/#grupos')

    with transaction.atomic():
        grupo = GrupoQuadraPublica.objects.create(
            quadra=quadra, esporte=esporte, hora_inicio=hora_inicio, hora_fim=hora_fim,
            criador=request.user,
        )
        ParticipanteGrupoPublico.objects.create(grupo=grupo, usuario=request.user)
    messages.success(request, f'Grupo de {esporte} criado. Convide outras pessoas para participar!')
    return redirect(f'/quadra/{quadra.id}/#grupo-{grupo.id}')


@login_required(login_url='login')
@require_POST
def participar_grupo_quadra_publica(request, grupo_id):
    grupo = get_object_or_404(GrupoQuadraPublica.objects.select_related('quadra'), pk=grupo_id)
    with transaction.atomic():
        participacao, criada = ParticipanteGrupoPublico.objects.get_or_create(
            grupo=grupo, usuario=request.user,
        )
        if not criada:
            participacao.presencas += 1
            participacao.ultima_confirmacao = timezone.now()
            participacao.save(update_fields=['presencas', 'ultima_confirmacao'])
    if criada:
        messages.success(request, f'Você entrou no grupo de {grupo.esporte}!')
    else:
        messages.success(request, f'Presença confirmada novamente no grupo de {grupo.esporte}!')
    if request.POST.get('retornar') == 'comunidade':
        return redirect('social')
    return redirect(f'/quadra/{grupo.quadra_id}/#grupo-{grupo.id}')


@login_required(login_url='login')
@require_POST
def indicar_material_grupo_publico(request, grupo_id):
    grupo = get_object_or_404(GrupoQuadraPublica, pk=grupo_id)
    item = request.POST.get('item', '').strip()[:100]
    if not grupo.participantes.filter(pk=request.user.pk).exists():
        messages.error(request, 'Entre no grupo antes de informar um material.')
    elif not item:
        messages.error(request, 'Informe qual material sera levado.')
    elif grupo.materiais.filter(item__iexact=item).exists():
            messages.error(request, 'Esse material ja foi indicado por outra pessoa.')
    else:
        MaterialGrupoPublico.objects.create(grupo=grupo, usuario=request.user, item=item)
        messages.success(request, f'Voce informou que levara {item}.')
    if request.POST.get('retornar') == 'comunidade':
        return redirect('social')
    return redirect(f'/quadra/{grupo.quadra_id}/#grupo-{grupo.id}')


@login_required(login_url='login')
@require_POST
def indicar_material_partida(request):
    horario = get_object_or_404(Horario, pk=request.POST.get('horario_id'), quadra__tipo='publica')
    item = request.POST.get('item', '').strip()[:100]
    if not horario.reservas.filter(usuario=request.user).exists():
        messages.error(request, 'Entre na partida antes de indicar que levará um material.')
    elif not item:
        messages.error(request, 'Informe qual material você vai levar.')
    else:
        _, created = MaterialPartida.objects.get_or_create(horario=horario, item__iexact=item,
            defaults={'usuario': request.user, 'item': item})
        if created:
            messages.success(request, f'Você ficou responsável por levar {item}.')
        else:
            messages.error(request, 'Esse material ja foi indicado por outra pessoa.')
    return redirect('social')


@login_required(login_url='login')
@require_POST
def postar(request):
    texto = request.POST.get('texto', '').strip()
    file = request.FILES.get('imagem')

    if not texto and not file:
        return _social_action_response(request, 'Escreva algo ou anexe uma foto para publicar.', False)

    if file and file.name:
        extensao = os.path.splitext(file.name)[1].lower()
        if extensao not in {'.jpg', '.jpeg', '.png', '.gif', '.webp'}:
            return _social_action_response(request, 'Use uma imagem JPG, PNG, GIF ou WEBP.', False)
        if file.size > 10 * 1024 * 1024:
            return _social_action_response(request, 'A imagem deve ter no máximo 10 MB.', False)

    tipo = 'admin' if request.user.email == 'admin@gmail.com' else 'atleta'
    foto_path = None
    if file and file.name:
        novo_nome = f"post_{uuid.uuid4().hex}{extensao}"
        upload_folder = os.path.join(settings.BASE_DIR, 'static', 'uploads', 'posts')
        os.makedirs(upload_folder, exist_ok=True)
        with open(os.path.join(upload_folder, novo_nome), 'wb+') as dest:
            for chunk in file.chunks():
                dest.write(chunk)
        foto_path = f"uploads/posts/{novo_nome}"
    Post.objects.create(usuario=request.user, texto=texto, imagem=foto_path, tipo=tipo)
    return _social_action_response(request, 'Postagem publicada!', True)


@login_required(login_url='login')
@require_POST
def curtir_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    curtida, criada = CurtidaPost.objects.get_or_create(post=post, usuario=request.user)
    if not criada:
        curtida.delete()
    return redirect(f'/social/#post-{post.id}')


@login_required(login_url='login')
@require_POST
def comentar_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    texto = request.POST.get('texto', '').strip()
    if not texto:
        messages.error(request, 'Escreva um comentário antes de enviar.')
    else:
        ComentarioPost.objects.create(post=post, usuario=request.user, texto=texto[:1000])
        messages.success(request, 'Comentário publicado.')
    return redirect(f'/social/#comentarios-{post.id}')


@login_required(login_url='login')
def editar_perfil(request):
    try:
        perfil = request.user.perfil_social
        dados = {
            'usuario_social': perfil.usuario_social,
            'bio': perfil.bio,
            'foto_perfil': perfil.foto_perfil,
        }
    except PerfilSocial.DoesNotExist:
        perfil = None
        dados = {}

    if request.method == 'POST':
        usuario_social = request.POST.get('usuario_social')
        bio = request.POST.get('bio')
        file = request.FILES.get('foto_perfil')
        foto_path = None
        if file and file.name:
            extensao = os.path.splitext(file.name)[1]
            novo_nome = f"perfil_{request.user.id}{extensao}"
            upload_folder = os.path.join(settings.BASE_DIR, 'static', 'uploads', 'perfis')
            os.makedirs(upload_folder, exist_ok=True)
            with open(os.path.join(upload_folder, novo_nome), 'wb+') as dest:
                for chunk in file.chunks():
                    dest.write(chunk)
            foto_path = f"uploads/perfis/{novo_nome}"

        if perfil:
            perfil.usuario_social = usuario_social
            perfil.bio = bio
            if foto_path:
                perfil.foto_perfil = foto_path
            perfil.save()
        else:
            PerfilSocial.objects.create(
                usuario=request.user,
                usuario_social=usuario_social,
                bio=bio,
                foto_perfil=foto_path or 'images/default_avatar.png',
            )
        messages.success(request, 'Perfil atualizado com sucesso!')
        return redirect('social')

    return render(request, 'cadastro_social.html', {'dados': dados})


def mensagem(request):
    return render(request, 'DGAmensagem.html')


@login_required(login_url='login')
def perfil(request):
    tem_quadra = Quadra.objects.filter(proprietario=request.user).exists()
    return render(request, 'perfil.html', {'tem_quadra': tem_quadra})


def suporte(request):
    if request.method == 'POST':
        messages.success(request, 'Sua mensagem foi enviada com sucesso!')
        return redirect('home')
    return render(request, 'suporte.html')


@login_required(login_url='login')
def minhas_reservas(request):
    reservas = ReservaJogador.objects.filter(usuario=request.user).select_related('horario__quadra').order_by(
        'horario__data', 'horario__hora_texto'
    )
    return render(request, 'minhas_reservas.html', {'reservas': reservas, 'hoje': date.today()})


@login_required(login_url='login')
@require_POST
def cancelar_reserva(request, reserva_id):
    reserva = get_object_or_404(ReservaJogador, pk=reserva_id, usuario=request.user)
    if reserva.horario.data < date.today():
        messages.error(request, 'Não é possível cancelar uma reserva já realizada.')
    else:
        with transaction.atomic():
            horario = Horario.objects.select_for_update().get(pk=reserva.horario_id)
            era_responsavel = horario.responsavel_reserva_id == request.user.id
            reserva.delete()
            restantes = horario.reservas.select_related('usuario').order_by('criada_em')
            if era_responsavel:
                proximo = restantes.first()
                horario.responsavel_reserva = proximo.usuario if proximo else None
            if not restantes.exists():
                horario.esporte_reservado = None
                horario.aceita_convidados = False
                horario.max_jogadores = 12
                horario.save(update_fields=['esporte_reservado', 'responsavel_reserva', 'aceita_convidados', 'max_jogadores'])
            elif era_responsavel:
                horario.save(update_fields=['responsavel_reserva'])
        messages.success(request, 'Reserva cancelada e vaga liberada.')
    return redirect('minhas_reservas')


@login_required(login_url='login')
@require_POST
def avaliar_quadra(request, quadra_id):
    quadra = get_object_or_404(Quadra, pk=quadra_id)
    if quadra.tipo == 'publica':
        texto = request.POST.get('comentario', '').strip()
        if texto:
            ComentarioQuadra.objects.create(quadra=quadra, usuario=request.user, texto=texto[:1000])
            messages.success(request, 'Comentário enviado para a comunidade.')
        else:
            messages.error(request, 'Escreva um comentário sobre a situação da quadra.')
        return redirect('detalhes_quadra', quadra_id=quadra.id)
    if not ReservaJogador.objects.filter(usuario=request.user, horario__quadra=quadra).exists():
        messages.error(request, 'Você só pode avaliar quadras em que participou.')
        return redirect('detalhes_quadra', quadra_id=quadra.id)
    try:
        nota = int(request.POST.get('nota', 0))
    except (TypeError, ValueError):
        nota = 0
    if nota not in range(1, 6):
        messages.error(request, 'Escolha uma nota de 1 a 5.')
        return redirect('detalhes_quadra', quadra_id=quadra.id)
    Avaliacao.objects.update_or_create(
        usuario=request.user,
        quadra=quadra,
        defaults={'nota': nota, 'comentario': request.POST.get('comentario', '').strip()[:1000]},
    )
    messages.success(request, 'Obrigado pela sua avaliação!')
    return redirect('detalhes_quadra', quadra_id=quadra.id)


@login_required(login_url='login')
def painel_proprietario(request):
    quadras = Quadra.objects.filter(proprietario=request.user).annotate(
        reservas_total=Count('horarios__reservas', distinct=True),
        nota_media=Avg('avaliacoes__nota'),
    ).order_by('nome')
    if not quadras.exists():
        messages.info(request, 'Sua conta ainda não está vinculada a nenhuma quadra.')
        return redirect('perfil')
    reservas_recentes = ReservaJogador.objects.filter(
        horario__quadra__in=quadras
    ).select_related('usuario', 'horario__quadra').order_by('-horario__data', '-horario__hora_texto')[:12]
    receita_estimada = sum(reserva.horario.preco for reserva in reservas_recentes)
    return render(request, 'painel_proprietario.html', {
        'quadras': quadras,
        'reservas_recentes': reservas_recentes,
        'receita_estimada': receita_estimada,
    })
