from django.shortcuts import render, redirect, get_object_or_404
from django.db import IntegrityError
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings
from django.db.models import Q, Count, Avg, Sum
from django.db import transaction
from django.utils.http import url_has_allowed_host_and_scheme
from datetime import date, timedelta
import uuid
import os
import io
import base64

from .models import Usuario, Quadra, Horario, ReservaJogador, PerfilSocial, Post, Avaliacao

try:
    import qrcode
except ImportError:
    qrcode = None


def home(request):
    return render(request, 'DGASports.html')


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
        qs = qs.filter(esporte__icontains=esporte_busca)

    if tipo_busca and tipo_busca != 'todos':
        qs = qs.filter(tipo=tipo_busca)

    return render(request, 'explorar.html', {
        'quadras': qs,
        'localidade_busca': localidade_busca,
        'esporte_busca': esporte_busca,
        'tipo_busca': tipo_busca,  # Devolve para manter o select selecionado
    })


def detalhes_quadra(request, quadra_id):
    quadra = get_object_or_404(Quadra, pk=quadra_id)
    usuario_id = request.user.id if request.user.is_authenticated else None
    avaliacoes = quadra.avaliacoes.select_related('usuario').all()[:5]
    pode_avaliar = bool(usuario_id and ReservaJogador.objects.filter(
        usuario_id=usuario_id, horario__quadra=quadra
    ).exists())

    horarios = Horario.objects.filter(quadra=quadra).order_by('data', 'hora_texto')
    horarios_list = []
    for h in horarios:
        jogadores_atuais = h.reservas.count()
        usuario_na_partida = 0
        if usuario_id:
            usuario_na_partida = 1 if h.reservas.filter(usuario_id=usuario_id).exists() else 0
        horarios_list.append({
            'id': h.id,
            'data': h.data.isoformat() if hasattr(h.data, 'isoformat') else str(h.data),
            'hora_texto': h.hora_texto,
            'max_jogadores': h.max_jogadores,
            'preco': float(h.preco),
            'esporte_reservado': h.esporte_reservado,
            'jogadores_atuais': jogadores_atuais,
            'usuario_na_partida': usuario_na_partida,
        })

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
        'lista_esportes': quadra.lista_esportes,
        'horarios': horarios_list,
        'datas_disponiveis': sorted(list(set(h['data'] for h in horarios_list))),
    }
    return render(request, 'detalhes_quadra.html', {
        'quadra': quadra_dict,
        'hoje': date.today().isoformat(),
        'avaliacoes': avaliacoes,
        'nota_media': quadra.avaliacoes.aggregate(media=Avg('nota'))['media'],
        'pode_avaliar': pode_avaliar,
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

        cidade = request.POST.get('cidade')
        estado = request.POST.get('estado')
        esporte = request.POST.get('esporte')
        tipo = request.POST.get('tipo', 'publica')
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

        quadra = Quadra.objects.create(
            nome=nome,
            descricao=descricao,
            localizacao=localizacao,
            cidade=cidade,
            estado=estado,
            esporte=esporte,
            tipo=tipo,
            proprietario=request.user,
            foto=foto_path
        )

        # 2. Geração da grade de horários para 7 dias
        try:
            h_inicio = int(abertura.split(':')[0])
            h_fim = int(fechamento.split(':')[0])
        except (ValueError, AttributeError, IndexError):
            h_inicio, h_fim = 8, 22

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

        messages.success(request, 'Quadra e agenda de 7 dias criadas com sucesso!')
        return redirect('explorar')

    return render(request, 'cadastrar_novas_quadras.html')


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

    try:
        horario = Horario.objects.get(pk=horario_id)
        ReservaJogador.objects.create(usuario=request.user, horario=horario)
        if esporte and not horario.esporte_reservado:
            horario.esporte_reservado = esporte
            horario.save(update_fields=['esporte_reservado'])
        return JsonResponse({'status': 'sucesso'})
    except IntegrityError:
        return JsonResponse({'status': 'erro', 'mensagem': 'Você já está nesta partida.'})
    except Exception as e:
        return JsonResponse({'status': 'erro', 'mensagem': str(e)})


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
            esporte_destravado = nova_contagem == 0
            if esporte_destravado:
                horario.esporte_reservado = None
                horario.save(update_fields=['esporte_reservado'])
            return JsonResponse({'status': 'sucesso', 'nova_contagem': nova_contagem, 'esporte_destravado': esporte_destravado})
    except Horario.DoesNotExist:
        return JsonResponse({'status': 'erro', 'mensagem': 'Horário não encontrado.'}, status=404)

    ReservaJogador.objects.filter(usuario=request.user, horario_id=horario_id).delete()
    return JsonResponse({'status': 'sucesso'})


def api_get_horarios_por_data(request, quadra_id, data_selecionada):
    usuario_id = request.user.id if request.user.is_authenticated else None
    horarios = Horario.objects.filter(quadra_id=quadra_id, data=data_selecionada)
    result = []
    for h in horarios:
        jogadores_atuais = h.reservas.count()
        usuario_na_partida = 0
        if usuario_id:
            usuario_na_partida = 1 if h.reservas.filter(usuario_id=usuario_id).exists() else 0
        result.append({
            'id': h.id,
            'data': str(h.data),
            'hora_texto': h.hora_texto,
            'max_jogadores': h.max_jogadores,
            'preco': float(h.preco),
            'esporte_reservado': h.esporte_reservado,
            'jogadores_atuais': jogadores_atuais,
            'usuario_na_partida': usuario_na_partida,
        })
    return JsonResponse({'status': 'sucesso', 'horarios': result})


@login_required(login_url='login')
def reservar(request, horario_id):
    horario = get_object_or_404(Horario, pk=horario_id)
    esporte = request.GET.get('esporte', '').strip()
    if horario.data < date.today() or horario.reservas.count() >= horario.max_jogadores:
        messages.error(request, 'Este horário não está mais disponível.')
        return redirect('detalhes_quadra', quadra_id=horario.quadra_id)
    if esporte not in horario.quadra.lista_esportes:
        messages.error(request, 'Selecione um esporte válido para esta quadra.')
        return redirect('detalhes_quadra', quadra_id=horario.quadra_id)
    if horario.esporte_reservado and horario.esporte_reservado != esporte:
        messages.error(request, 'Este horário já está reservado para outro esporte.')
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
        }
    }
    return render(request, 'reserva_privada.html', {
        'reserva': reserva,
        'esporte_selecionado': esporte,
        'usuario_atual': request.user,
    })


@login_required(login_url='login')
@require_POST
def confirmar_reserva(request):
    metodo = request.POST.get('metodo')
    horario_id = request.POST.get('horario_id')
    esporte = request.POST.get('esporte_selecionado')
    horario = get_object_or_404(Horario, pk=horario_id)
    if horario.data < date.today() or horario.reservas.count() >= horario.max_jogadores:
        messages.error(request, 'Este horário não está mais disponível.')
        return redirect('detalhes_quadra', quadra_id=horario.quadra_id)
    if esporte not in horario.quadra.lista_esportes:
        messages.error(request, 'Esporte inválido para esta quadra.')
        return redirect('detalhes_quadra', quadra_id=horario.quadra_id)
    if horario.esporte_reservado and horario.esporte_reservado != esporte:
        messages.error(request, 'Este horário já está reservado para outro esporte.')
        return redirect('detalhes_quadra', quadra_id=horario.quadra_id)

    if metodo == 'pix':
        chave_pix = str(uuid.uuid4())
        img_str = ''
        if qrcode:
            qr = qrcode.make(chave_pix)
            buf = io.BytesIO()
            qr.save(buf, format='PNG')
            img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
        return render(request, 'pagamento_pix.html', {
            'chave_pix': chave_pix,
            'qr_code_data_uri': f'data:image/png;base64,{img_str}',
            'horario_id': horario_id,
            'esporte_selecionado': esporte,
        })

    try:
        horario = Horario.objects.get(pk=horario_id)
        ReservaJogador.objects.get_or_create(usuario=request.user, horario=horario)
        if esporte and not horario.esporte_reservado:
            horario.esporte_reservado = esporte
            horario.save(update_fields=['esporte_reservado'])
        messages.success(request, 'Pagamento aprovado! Sua reserva está garantida.')
    except Exception as e:
        messages.error(request, str(e))
    return redirect('home')


@login_required(login_url='login')
@require_POST
def finalizar_pix(request):
    horario_id = request.POST.get('horario_id')
    esporte = request.POST.get('esporte_selecionado')
    try:
        horario = Horario.objects.get(pk=horario_id)
        if horario.data < date.today():
            raise ValueError('Este horário já passou.')
        if esporte not in horario.quadra.lista_esportes:
            raise ValueError('Esporte inválido para esta quadra.')
        if horario.esporte_reservado and horario.esporte_reservado != esporte:
            raise ValueError('Este horário já está reservado para outro esporte.')
        if horario.reservas.count() >= horario.max_jogadores and not horario.reservas.filter(usuario=request.user).exists():
            raise ValueError('Este horário está lotado.')
        ReservaJogador.objects.get_or_create(usuario=request.user, horario=horario)
        if esporte and not horario.esporte_reservado:
            horario.esporte_reservado = esporte
            horario.save(update_fields=['esporte_reservado'])
        messages.success(request, 'PIX Confirmado! Reserva efetuada com sucesso.')
    except Exception as e:
        messages.error(request, str(e))
    return redirect('home')


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

    posts_qs = Post.objects.select_related('usuario').prefetch_related('usuario__perfil_social').all()
    posts = []
    for p in posts_qs:
        foto = 'images/default_avatar.png'
        usuario_social = None
        try:
            foto = p.usuario.perfil_social.foto_perfil
            usuario_social = p.usuario.perfil_social.usuario_social
        except PerfilSocial.DoesNotExist:
            pass
        posts.append({
            'id': p.id,
            'texto': p.texto,
            'imagem': p.imagem,
            'tipo': p.tipo,
            'data_postagem': p.data_postagem,
            'nome_usuario': p.usuario.nome,
            'usuario_social': usuario_social,
            'foto_perfil': foto,
        })
    return render(request, 'dga.social.html', {'dados': dados, 'posts': posts})


@login_required(login_url='login')
@require_POST
def postar(request):
    texto = request.POST.get('texto')
    file = request.FILES.get('imagem')
    tipo = 'admin' if request.user.email == 'admin@gmail.com' else 'atleta'
    foto_path = None
    if file and file.name:
        extensao = os.path.splitext(file.name)[1]
        novo_nome = f"post_{uuid.uuid4().hex}{extensao}"
        upload_folder = os.path.join(settings.BASE_DIR, 'static', 'uploads', 'posts')
        os.makedirs(upload_folder, exist_ok=True)
        with open(os.path.join(upload_folder, novo_nome), 'wb+') as dest:
            for chunk in file.chunks():
                dest.write(chunk)
        foto_path = f"uploads/posts/{novo_nome}"
    Post.objects.create(usuario=request.user, texto=texto, imagem=foto_path, tipo=tipo)
    messages.success(request, 'Postagem realizada!')
    return redirect('social')


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


def perfil(request):
    return render(request, 'perfil.html')


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
        horario = reserva.horario
        reserva.delete()
        if not horario.reservas.exists():
            horario.esporte_reservado = None
            horario.save(update_fields=['esporte_reservado'])
        messages.success(request, 'Reserva cancelada e vaga liberada.')
    return redirect('minhas_reservas')


@login_required(login_url='login')
@require_POST
def avaliar_quadra(request, quadra_id):
    quadra = get_object_or_404(Quadra, pk=quadra_id)
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
    filtro_quadras = Q(proprietario=request.user)
    if request.user.is_staff:
        filtro_quadras |= Q(proprietario__isnull=True)
    quadras = Quadra.objects.filter(filtro_quadras).annotate(
        reservas_total=Count('horarios__reservas', distinct=True),
        nota_media=Avg('avaliacoes__nota'),
    ).order_by('nome')
    reservas_recentes = ReservaJogador.objects.filter(
        horario__quadra__in=quadras
    ).select_related('usuario', 'horario__quadra').order_by('-horario__data', '-horario__hora_texto')[:12]
    receita_estimada = sum(reserva.horario.preco for reserva in reservas_recentes)
    return render(request, 'painel_proprietario.html', {
        'quadras': quadras,
        'reservas_recentes': reservas_recentes,
        'receita_estimada': receita_estimada,
    })
