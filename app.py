#!/usr/bin/env python3
"""
Aplicação Quiz - Sistema de Perguntas e Respostas
VERSÃO CORRIGIDA - Modo Recuperação Funcionando
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_file
import json
import random
import os
from datetime import datetime, timedelta
import logging
import sys
import urllib.parse
import bcrypt
import uuid
import shutil
import glob
import requests
from dotenv import load_dotenv

# Google Cloud integrations
try:
    from google.cloud import secretmanager
    from google.cloud import storage as gcs
    from google.cloud import logging as cloud_logging
    GOOGLE_CLOUD_AVAILABLE = True
except ImportError:
    GOOGLE_CLOUD_AVAILABLE = False
    print("Google Cloud libraries não disponíveis. Usando configuração local.")

load_dotenv()

# Configuração do Google Cloud Logging
if GOOGLE_CLOUD_AVAILABLE and os.environ.get('FLASK_ENV') == 'production':
    try:
        client = cloud_logging.Client()
        client.setup_logging()
        print("Google Cloud Logging configurado")
    except Exception as e:
        print(f"Erro ao configurar Google Cloud Logging: {e}")

# Função para obter secrets do Google Secret Manager
def get_secret(secret_name, default_value=None):
    """Obtém um secret do Google Secret Manager ou usa valor padrão"""
    if not GOOGLE_CLOUD_AVAILABLE or os.environ.get('FLASK_ENV') != 'production':
        return os.environ.get(secret_name, default_value)
    
    try:
        client = secretmanager.SecretManagerServiceClient()
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT') or os.environ.get('PROJECT_ID')
        if not project_id:
            return os.environ.get(secret_name, default_value)
        
        name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        print(f"Erro ao obter secret {secret_name}: {e}")
        return os.environ.get(secret_name, default_value)



# Configuração de logging sem emojis
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configurações usando Google Secret Manager ou variáveis de ambiente
app.secret_key = get_secret('SECRET_KEY', 'sua_chave_secreta_super_segura_123456')
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
if os.environ.get('FLASK_ENV') == 'production':
    app.config['SESSION_COOKIE_SECURE'] = True

# Configurações de segurança admin usando Secret Manager
ADMIN_EMAIL = get_secret('ADMIN_EMAIL', 'j.f.s.r95@gmail.com')
ADMIN_DEFAULT_PASSWORD = get_secret('ADMIN_DEFAULT_PASSWORD', 'Samu@220107')
GCS_BUCKET_NAME = get_secret('GCS_BUCKET_NAME', None)

ADMIN_FILE = 'admin_user.json'
MAX_LOGIN_ATTEMPTS = 5
LOGIN_TIMEOUT = 300  # 5 minutos

# Configurações do usuário
USER_CONFIG_FILE = 'user_config.json'

# Caminho centralizado do banco principal de perguntas
PERGUNTAS_JSON_PATH = os.environ.get(
    'PERGUNTAS_JSON_PATH',
    'data/perguntas.json'
)

# Variáveis globais
perguntas_db = []
perguntas_recuperacao_db = {}

# Variáveis globais para o quiz
quiz_session = {}
quiz_questions = {}
quiz_answers = {}

# Controle de tentativas de login
login_attempts = {}

SESSOES_DIR = os.path.join('data', 'sessoes')
os.makedirs(SESSOES_DIR, exist_ok=True)

def safe_write_json(file_path, data):
    """Escreve JSON de forma atômica (evita corrupção em caso de falha)."""
    tmp_path = f"{file_path}.tmp"
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, file_path)

def carregar_admin_user():
    """Carrega ou cria o usuário admin"""
    try:
        if os.path.exists(ADMIN_FILE):
            with open(ADMIN_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Cria admin padrão se não existir
            admin_data = {
                'email': ADMIN_EMAIL,
                'password_hash': hash_password(ADMIN_DEFAULT_PASSWORD),
                'name': 'Administrador',
                'created_at': datetime.now().isoformat(),
                'last_login': None
            }
            salvar_admin_user(admin_data)
            return admin_data
    except Exception as e:
        logger.error(f"Erro ao carregar admin: {e}")
        return None

def salvar_admin_user(admin_data):
    """Salva dados do admin"""
    try:
        with open(ADMIN_FILE, 'w', encoding='utf-8') as f:
            json.dump(admin_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar admin: {e}")
        return False

# ==========================
# Utilitários de senha
# ==========================
def hash_password(plain_password: str) -> str:
    try:
        return bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    except Exception:
        try:
            from passlib.hash import bcrypt as passlib_bcrypt  # type: ignore
            return passlib_bcrypt.hash(plain_password)
        except Exception as exc:
            logger.error(f"Falha ao gerar hash de senha: {exc}")
            raise


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bool(bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8')))
    except Exception:
        try:
            from passlib.hash import bcrypt as passlib_bcrypt  # type: ignore
            return bool(passlib_bcrypt.verify(plain_password, hashed_password))
        except Exception as exc:
            logger.error(f"Falha ao verificar senha: {exc}")
            return False

def verificar_login_attempts(ip):
    """Verifica se o IP está bloqueado por tentativas excessivas"""
    if ip in login_attempts:
        attempts, last_attempt = login_attempts[ip]
        if attempts >= MAX_LOGIN_ATTEMPTS:
            if datetime.now() - last_attempt < timedelta(seconds=LOGIN_TIMEOUT):
                return False
            else:
                # Reset após timeout
                del login_attempts[ip]
    return True

def registrar_login_attempt(ip, success=False):
    """Registra tentativa de login"""
    if success:
        if ip in login_attempts:
            del login_attempts[ip]
    else:
        if ip in login_attempts:
            attempts, _ = login_attempts[ip]
            login_attempts[ip] = (attempts + 1, datetime.now())
        else:
            login_attempts[ip] = (1, datetime.now())

def admin_required(f):
    """Decorator para proteger rotas admin"""
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def get_client_ip():
    """Obtém IP do cliente"""
    if request.environ.get('HTTP_X_FORWARDED_FOR'):
        return request.environ['HTTP_X_FORWARDED_FOR'].split(',')[0]
    return request.environ.get('REMOTE_ADDR', 'unknown')

# Adiciona o filtro chr para converter números em letras (A, B, C, D)
@app.template_filter('chr')
def chr_filter(i, base=65):
    return chr(base + i)

def carregar_perguntas():
    """Carrega perguntas do arquivo JSON principal"""
    global perguntas_db
    try:
        with open(PERGUNTAS_JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            if isinstance(data, list):
                perguntas_db = data
            elif isinstance(data, dict) and 'perguntas' in data:
                perguntas_db = data['perguntas']
            else:
                print("ERRO: Formato do JSON não reconhecido!")
                return False
                
            print(f"SUCESSO: {len(perguntas_db)} perguntas carregadas!")
            return True
            
    except FileNotFoundError:
        print(f"ERRO: Arquivo {PERGUNTAS_JSON_PATH} não encontrado!")
        criar_arquivo_exemplo()
        return carregar_perguntas()
    except Exception as e:
        print(f"ERRO ao carregar perguntas: {e}")
        return False

def debug_perguntas():
    """Função para debugar carregamento de perguntas"""
    print("\n" + "="*50)
    print("DEBUG - VERIFICANDO PERGUNTAS")
    print("="*50)
    print(f"Total de perguntas carregadas: {len(perguntas_db)}")
    
    if perguntas_db:
        print(f"Primeira pergunta: {perguntas_db[0].get('pergunta', 'SEM PERGUNTA')[:100]}...")
        print(f"Campos da primeira pergunta: {list(perguntas_db[0].keys())}")
        
        # Verifica períodos
        periodos = [p.get('periodo') for p in perguntas_db]
        print(f"Períodos encontrados: {set(periodos)}")
        
        # Verifica disciplinas
        disciplinas = [p.get('disciplina') for p in perguntas_db]
        print(f"Disciplinas encontradas: {set(disciplinas)}")
    else:
        print("NENHUMA PERGUNTA CARREGADA!")
    print("="*50 + "\n")

def carregar_perguntas_recuperacao():
    """Carrega perguntas de recuperação de todos os arquivos na pasta data/"""
    global perguntas_recuperacao_db
    perguntas_recuperacao_db = {}
    arquivos = glob.glob(os.path.join('data', 'perguntas_recuperacao*.json')) + glob.glob(os.path.join('data', 'RECUP_*.json'))
    total_perguntas = 0
    for arquivo in arquivos:
        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for disciplina, topicos in data.items():
                    if disciplina not in perguntas_recuperacao_db:
                        perguntas_recuperacao_db[disciplina] = {}
                    for topico, perguntas in topicos.items():
                        if topico not in perguntas_recuperacao_db[disciplina]:
                            perguntas_recuperacao_db[disciplina][topico] = []
                        for pergunta in perguntas:
                            perguntas_recuperacao_db[disciplina][topico].append(pergunta)
                            total_perguntas += 1
        except Exception as e:
            print(f"ERRO ao carregar {arquivo}: {e}")
    print(f"SUCESSO: {total_perguntas} perguntas de recuperação carregadas de {len(arquivos)} arquivos!")
    return True

def criar_arquivo_exemplo():
    """Cria arquivo exemplo"""
    exemplo = [
        {
            "pergunta": "Qual é a frequência cardíaca normal de um adulto?",
            "opcoes": ["40-60 bpm", "60-100 bpm", "100-120 bpm", "120-140 bpm"],
            "resposta_correta": "60-100 bpm",
            "categoria": "Fisiologia",
            "periodo": 1,
            "disciplina": "Fisiologia Humana",
            "dificuldade": "facil",
            "explicacao": "A frequência cardíaca normal de um adulto varia entre 60-100 bpm."
        }
    ]
    
    try:
        safe_write_json(PERGUNTAS_JSON_PATH, exemplo)
        print(f"SUCESSO: Arquivo {PERGUNTAS_JSON_PATH} criado!")
    except Exception as e:
        print(f"ERRO ao criar arquivo: {e}")

def criar_arquivo_recuperacao_exemplo():
    """Cria arquivo recuperação exemplo"""
    exemplo = {
        "ESF": {
            "1 - Importância Atenção Básica": [
                {
                    "pergunta": "Qual é o principal objetivo da Atenção Básica no SUS?",
                    "opcoes": [
                        "Realizar apenas procedimentos de alta complexidade",
                        "Ser a porta de entrada preferencial do sistema de saúde",
                        "Atender somente emergências médicas",
                        "Focar exclusivamente em tratamentos especializados"
                    ],
                    "resposta_correta": "Ser a porta de entrada preferencial do sistema de saúde",
                    "categoria": "Unidade 1",
                    "disciplina": "ESF",
                    "topico": "1 - Importância Atenção Básica",
                    "dificuldade": "facil",
                    "explicacao": "A Atenção Básica é caracterizada por ser a porta de entrada preferencial do SUS.",
                    "referencia": "BRASIL. Ministério da Saúde. Política Nacional de Atenção Básica. Brasília: MS, 2017."
                }
            ]
        }
    }
    
    try:
        with open('data/perguntas_recuperacao.json', 'w', encoding='utf-8') as f:
            json.dump(exemplo, f, ensure_ascii=False, indent=2)
        print("SUCESSO: Arquivo data/perguntas_recuperacao.json criado!")
    except Exception as e:
        print(f"ERRO ao criar arquivo recuperação: {e}")

def validar_pergunta(pergunta, numero):
    """Valida pergunta"""
    campos_obrigatorios = ['pergunta', 'opcoes', 'resposta_correta']
    
    for campo in campos_obrigatorios:
        if campo not in pergunta:
            print(f"AVISO: Pergunta {numero}: Campo '{campo}' não encontrado")
            return False
    
    if len(pergunta['opcoes']) not in [4, 5]:
        print(f"AVISO: Pergunta {numero}: Deve ter 4 ou 5 opções")
        return False
    
    if pergunta['resposta_correta'] not in pergunta['opcoes']:
        print(f"AVISO: Pergunta {numero}: Resposta correta não está nas opções")
        return False
    
    return True

def get_periodos_disciplinas():
    """Retorna períodos e disciplinas"""
    periodos = {}
    for pergunta in perguntas_db:
        periodo = pergunta.get('periodo')
        disciplina = pergunta.get('disciplina', 'Geral')
        
        if periodo not in periodos:
            periodos[periodo] = set()
        periodos[periodo].add(disciplina)
    
    for periodo in periodos:
        periodos[periodo] = sorted(list(periodos[periodo]))
    
    return periodos

def get_disciplinas_recuperacao():
    """Retorna disciplinas de recuperação"""
    if not perguntas_recuperacao_db:
        return []
    return sorted(list(perguntas_recuperacao_db.keys()))

def get_disciplinas_por_periodo():
    """Retorna disciplinas organizadas por período"""
    disciplinas_por_periodo = {}
    
    for pergunta in perguntas_db:
        periodo = pergunta.get('periodo')
        disciplina = pergunta.get('disciplina')
        
        if periodo and disciplina:
            if periodo not in disciplinas_por_periodo:
                disciplinas_por_periodo[periodo] = set()
            disciplinas_por_periodo[periodo].add(disciplina)
    
    # Converte sets para listas
    return {periodo: list(disciplinas) for periodo, disciplinas in disciplinas_por_periodo.items()}

def get_topicos_recuperacao():
    """Retorna os tópicos disponíveis para o quiz de recuperação (ESF)."""
    if "ESF" in perguntas_recuperacao_db:
        return list(perguntas_recuperacao_db["ESF"].keys())
    return []

# ROTAS
@app.route('/')
def index():
    disciplinas_por_periodo = get_disciplinas_por_periodo()
    topicos_recuperacao = get_topicos_recuperacao()
    return render_template(
        'index.html',
        periodos_disciplinas=get_periodos_disciplinas(),
        disciplinas_por_periodo=disciplinas_por_periodo,
        topicos_recuperacao=topicos_recuperacao,
        perguntas_recuperacao_db=perguntas_recuperacao_db
    )

@app.route('/configuracao-inicial', methods=['GET'])
def configuracao_inicial():
    """Configuração inicial do usuário"""
    return render_template('configuracao_inicial.html')

@app.route('/atualizar-configuracao', methods=['POST'])
def atualizar_configuracao():
    """Atualiza configuração do usuário"""
    config_atual = carregar_config_usuario()
    if not config_atual:
        return jsonify({'erro': 'Usuário não configurado'}), 400
    
    ler_perguntas = request.form.get('ler_perguntas') == 'on'
    
    config_atual['ler_perguntas'] = ler_perguntas
    config_atual['ultimo_acesso'] = datetime.now().isoformat()
    
    if salvar_config_usuario(config_atual):
        return jsonify({'sucesso': True, 'mensagem': 'Configuração atualizada!'})
    else:
        return jsonify({'erro': 'Erro ao atualizar configuração'}), 500

@app.route('/api/topicos-disciplina')
def api_topicos_disciplina():
    """API para obter tópicos de uma disciplina específica"""
    disciplina = request.args.get('disciplina', '')
    
    if not disciplina:
        return jsonify({'erro': 'Disciplina é obrigatória'}), 400
    
    if disciplina not in perguntas_recuperacao_db:
        return jsonify({'erro': f'Disciplina {disciplina} não encontrada'}), 404
    
    topicos = {}
    for topico, perguntas in perguntas_recuperacao_db[disciplina].items():
        topicos[topico] = {
            'total_perguntas': len(perguntas),
            'disciplina': disciplina
        }
    
    return jsonify(topicos)

@app.route('/debug/recuperacao')
def debug_recuperacao():
    """Debug recuperação"""
    disciplina = request.args.get('disciplina', '')
    topico = request.args.get('topico', '')
    
    disciplina_decoded = urllib.parse.unquote_plus(disciplina)
    topico_decoded = urllib.parse.unquote_plus(topico)
    
    debug_info = {
        'disciplina_original': disciplina,
        'disciplina_decodificada': disciplina_decoded,
        'topico_original': topico,
        'topico_decodificado': topico_decoded,
        'disciplinas_disponiveis': list(perguntas_recuperacao_db.keys()),
        'dados_completos': perguntas_recuperacao_db
    }
    
    if disciplina_decoded in perguntas_recuperacao_db:
        debug_info['topicos_disciplina'] = list(perguntas_recuperacao_db[disciplina_decoded].keys())
        
        if topico_decoded in perguntas_recuperacao_db[disciplina_decoded]:
            debug_info['perguntas_topico'] = perguntas_recuperacao_db[disciplina_decoded][topico_decoded]
            debug_info['total_perguntas'] = len(perguntas_recuperacao_db[disciplina_decoded][topico_decoded])
    
    return jsonify(debug_info)

@app.route('/quiz')
def quiz():
    """Inicia o quiz"""
    config_usuario = carregar_config_usuario()  # Pode ser vazio
    modo = request.args.get('modo', 'normal')
    disciplina = request.args.get('disciplina', '')
    topico = request.args.get('topico', '')
    periodo = request.args.get('periodo', '')
    quantidade_questoes = int(request.args.get('quantidade_questoes', 15))
    quantidade_questoes = max(1, min(quantidade_questoes, 50))
    session_id = str(uuid.uuid4())
    if modo == 'recuperacao':
        if not disciplina or not topico:
            flash('Disciplina e tópico são obrigatórios para o modo recuperação.', 'error')
            return redirect(url_for('index'))
        if disciplina not in perguntas_recuperacao_db:
            flash('Disciplina de recuperação não encontrada.', 'error')
            return redirect(url_for('index'))
        perguntas_selecionadas = []
        session_topico_name = topico
        if topico == 'revisao_geral':
            session_topico_name = "Revisão Geral Mista"
            todas_as_perguntas = []
            for lista_perguntas in perguntas_recuperacao_db[disciplina].values():
                todas_as_perguntas.extend(lista_perguntas)
            perguntas_selecionadas = todas_as_perguntas
        else:
            if topico not in perguntas_recuperacao_db[disciplina]:
                flash('Tópico de recuperação não encontrado.', 'error')
                return redirect(url_for('index'))
            perguntas_selecionadas = perguntas_recuperacao_db[disciplina][topico]
        perguntas_selecionadas = perguntas_selecionadas.copy()
        random.shuffle(perguntas_selecionadas)
        perguntas = perguntas_selecionadas[:quantidade_questoes]
        if not perguntas:
            flash('Nenhuma pergunta encontrada para os critérios selecionados.', 'error')
            return redirect(url_for('index'))
        perguntas = embaralhar_opcoes(perguntas)
        quiz_session[session_id] = {
            'modo': 'recuperacao',
            'disciplina': disciplina,
            'topico': session_topico_name,
            'perguntas': perguntas,
            'pergunta_atual': 0,
            'respostas': [],
            'inicio': datetime.now(),
            'config_usuario': config_usuario,
            'quantidade_questoes': quantidade_questoes
        }
    else:
        if not periodo or not disciplina:
            flash('Período e disciplina são obrigatórios.', 'error')
            return redirect(url_for('index'))
        # Filtrar perguntas por período e disciplina
        perguntas_filtradas = [p for p in perguntas_db 
                             if p.get('periodo') == int(periodo) and 
                             p.get('disciplina', '').lower() == disciplina.lower()]
        
        # Implementar distribuição 70% professor / 30% oficial se há material do professor
        perguntas_professor = [p for p in perguntas_filtradas if p.get('fonte_material') == 'professor']
        perguntas_oficiais = [p for p in perguntas_filtradas if p.get('fonte_material') != 'professor']
        
        if perguntas_professor:
            # Aplicar distribuição 70/30
            qtd_professor = int(quantidade_questoes * 0.7)
            qtd_oficial = quantidade_questoes - qtd_professor
            
            # Garantir que não exceda o disponível
            qtd_professor = min(qtd_professor, len(perguntas_professor))
            qtd_oficial = min(qtd_oficial, len(perguntas_oficiais))
            
            # Ajustar se não há perguntas suficientes
            if qtd_professor + qtd_oficial < quantidade_questoes:
                # Completar com o que estiver disponível
                restante = quantidade_questoes - qtd_professor - qtd_oficial
                if len(perguntas_professor) > qtd_professor:
                    qtd_professor = min(qtd_professor + restante, len(perguntas_professor))
                elif len(perguntas_oficiais) > qtd_oficial:
                    qtd_oficial = min(qtd_oficial + restante, len(perguntas_oficiais))
            
            perguntas_selecionadas = []
            if qtd_professor > 0:
                random.shuffle(perguntas_professor)
                perguntas_selecionadas.extend(perguntas_professor[:qtd_professor])
            if qtd_oficial > 0:
                random.shuffle(perguntas_oficiais)
                perguntas_selecionadas.extend(perguntas_oficiais[:qtd_oficial])
            
            random.shuffle(perguntas_selecionadas)  # Embaralhar ordem final
        else:
            # Sem material professor, seleção normal
            random.shuffle(perguntas_filtradas)
            perguntas_selecionadas = perguntas_filtradas[:quantidade_questoes]
        if not perguntas_selecionadas:
            flash('Nenhuma pergunta encontrada para os critérios selecionados.', 'error')
            return redirect(url_for('index'))
        perguntas = embaralhar_opcoes(perguntas_selecionadas)
        quiz_session[session_id] = {
            'modo': 'normal',
            'periodo': periodo,
            'disciplina': disciplina,
            'perguntas': perguntas,
            'pergunta_atual': 0,
            'respostas': [],
            'inicio': datetime.now(),
            'config_usuario': config_usuario,
            'quantidade_questoes': quantidade_questoes
        }
    salvar_sessao_quiz(session_id, quiz_session[session_id])
    return redirect(url_for('proxima_pergunta', session_id=session_id))

@app.route('/proxima_pergunta')
def proxima_pergunta():
    """Mostra a próxima pergunta"""
    session_id = request.args.get('session_id')
    
    if not session_id or session_id not in quiz_session:
        flash('Sessão de quiz inválida.', 'error')
        return redirect(url_for('index'))
    
    quiz_data = quiz_session[session_id]
    pergunta_atual = quiz_data['pergunta_atual']
    perguntas = quiz_data['perguntas']
    
    if pergunta_atual >= len(perguntas):
        # Quiz terminou
        return redirect(url_for('finalizar_quiz', session_id=session_id))
    
    pergunta = perguntas[pergunta_atual]
    
    # Tempo: 90 segundos por questão
    tempo_por_pergunta = 90
    tempo_total = len(perguntas) * tempo_por_pergunta
    tempo_decorrido = (datetime.now() - parse_datetime(quiz_data['inicio'])).total_seconds()
    tempo_restante = max(0, tempo_total - tempo_decorrido)
    
    salvar_sessao_quiz(session_id, quiz_data)
    return render_template('quiz.html', 
                         pergunta=pergunta,
                         pergunta_numero=pergunta_atual + 1,
                         total_perguntas=len(perguntas),
                         session_id=session_id,
                         tempo_restante=int(tempo_restante),
                         config_usuario=quiz_data['config_usuario'])

@app.route('/responder', methods=['POST'])
def responder():
    """Processa a resposta do usuário"""
    session_id = request.form.get('session_id')
    resposta = request.form.get('resposta')
    
    if not session_id or session_id not in quiz_session:
        return jsonify({'erro': 'Sessão de quiz inválida'}), 400
    
    if not resposta:
        return jsonify({'erro': 'Resposta não fornecida'}), 400
    
    quiz_data = quiz_session[session_id]
    pergunta_atual = quiz_data['pergunta_atual']
    perguntas = quiz_data['perguntas']
    
    if pergunta_atual >= len(perguntas):
        return jsonify({'erro': 'Quiz já terminou'}), 400
    
    # Tempo: 90 segundos por pergunta para todos os modos
    inicio = parse_datetime(quiz_data['inicio'])
    tempo_decorrido = (datetime.now() - inicio).total_seconds()
    tempo_por_pergunta = 90
    tempo_total = len(perguntas) * tempo_por_pergunta

    # Verifica se o tempo não esgotou
    if tempo_decorrido > tempo_total:
        return jsonify({'erro': 'Tempo esgotado'}), 400
    
    # Obtém a pergunta atual
    pergunta = perguntas[pergunta_atual]
    
    # Verifica se a resposta está correta
    correta = resposta == pergunta['resposta_correta']
    
    # Calcula pontuação baseada no tempo de resposta
    tempo_resposta = tempo_decorrido - (pergunta_atual * tempo_por_pergunta)
    tempo_restante_pergunta = max(0, tempo_por_pergunta - tempo_resposta)
    
    # Pontuação: 10 pontos se correto, 0 se errado
    # Bônus de tempo: até 5 pontos extras baseado no tempo restante
    pontos = 0
    if correta:
        pontos = 10
        # Bônus de tempo (máximo 5 pontos)
        bonus_tempo = min(5, int(tempo_restante_pergunta / 18))  # 90/5=18
        pontos += bonus_tempo
    
    # Salva a resposta
    quiz_data['respostas'].append({
        'pergunta': pergunta['pergunta'],
        'resposta_usuario': resposta,
        'resposta_correta': pergunta['resposta_correta'],
        'correta': correta,
        'pontos': pontos,
        'tempo_resposta': tempo_resposta,
        'explicacao': pergunta.get('explicacao', ''),
        'dificuldade': pergunta.get('dificuldade', 'medio')
    })
    
    # Avança para a próxima pergunta
    quiz_data['pergunta_atual'] += 1
    
    # Verifica se o quiz terminou
    if quiz_data['pergunta_atual'] >= len(perguntas):
        return jsonify({
            'fim': True,
            'correta': correta,
            'resposta_correta': pergunta['resposta_correta'],
            'pontos': pontos,
            'explicacao': pergunta.get('explicacao', ''),
            'session_id': session_id
        })
    
    salvar_sessao_quiz(session_id, quiz_data)
    return jsonify({
        'correta': correta,
        'resposta_correta': pergunta['resposta_correta'],
        'pontos': pontos,
        'explicacao': pergunta.get('explicacao', ''),
        'proxima_pergunta': True,
        'session_id': session_id
    })

@app.route('/finalizar_quiz')
def finalizar_quiz():
    """Finaliza o quiz e redireciona para resultado"""
    session_id = request.args.get('session_id') or session.get('quiz_session_id')
    quiz_data = quiz_session.get(session_id) or carregar_sessao_quiz(session_id)
    if not session_id or not quiz_data:
        return redirect(url_for('erro', mensagem='Sua sessão expirou ou não foi encontrada. O relatório não está disponível. Por favor, inicie um novo quiz.'))
    quiz_data['fim'] = str(datetime.now())
    # Garante que todas as perguntas não respondidas sejam marcadas
    respostas = quiz_data.get('respostas', [])
    respondidas = set(r['pergunta'] for r in respostas)
    for pergunta in quiz_data['perguntas']:
        if pergunta['pergunta'] not in respondidas:
            respostas.append({
                'pergunta': pergunta['pergunta'],
                'resposta_usuario': '',
                'resposta_correta': pergunta.get('resposta_correta', ''),
                'correta': False,
                'nao_respondida': True
            })
    quiz_data['respostas'] = respostas
    salvar_sessao_quiz(session_id, quiz_data)
    return redirect(url_for('resultado', session_id=session_id))

@app.route('/erro')
def erro():
    mensagem = request.args.get('mensagem', 'Ocorreu um erro inesperado.')
    return render_template('erro.html', mensagem=mensagem)

@app.route('/resultado')
def resultado():
    """Página de resultado do quiz"""
    session_id = request.args.get('session_id') or session.get('quiz_session_id')
    quiz_data = quiz_session.get(session_id) or carregar_sessao_quiz(session_id)
    if not session_id or not quiz_data:
        return redirect(url_for('index'))
    # Filtrar apenas respostas respondidas
    respostas_respondidas = [r for r in quiz_data['respostas'] if not r.get('nao_respondida')]
    total_perguntas = len(respostas_respondidas)
    acertos = sum(1 for r in respostas_respondidas if r.get('correta', r.get('correto', r.get('acertou', False))))
    precisao = (acertos / total_perguntas * 100) if total_perguntas > 0 else 0
    inicio = parse_datetime(quiz_data.get('inicio'))
    fim = parse_datetime(quiz_data.get('fim', datetime.now()))
    tempo_total = fim - inicio
    tempo_minutos = int(tempo_total.total_seconds() // 60)
    tempo_segundos = int(tempo_total.total_seconds() % 60)
    tempo_gasto = f"{tempo_minutos:02d}:{tempo_segundos:02d}"
    respostas_formatadas = []
    for i, resposta in enumerate(respostas_respondidas):
        pergunta_original = None
        for p in quiz_data['perguntas']:
            if p['pergunta'] == resposta['pergunta']:
                pergunta_original = p
                break
        respostas_formatadas.append({
            'numero': i + 1,
            'pergunta': resposta['pergunta'],
            'opcoes': pergunta_original['opcoes'] if pergunta_original else [],
            'resposta_usuario': resposta.get('resposta_usuario', resposta.get('sua_resposta', '')),
            'resposta_correta': resposta.get('resposta_correta', ''),
            'acertou': resposta.get('correta', resposta.get('correto', resposta.get('acertou', False))),
            'explicacao': pergunta_original.get('explicacao', '') if pergunta_original else ''
        })
    resultado_data = {
        'percentual': round(precisao, 1),
        'acertos': acertos,
        'total': total_perguntas,
        'tempo_gasto': tempo_gasto,
        'respostas': respostas_formatadas,
        'tipo': quiz_data['modo']
    }
    session.pop('quiz_session_id', None)
    salvar_sessao_quiz(session_id, quiz_data)
    return render_template('resultado.html', **resultado_data)

@app.route('/admin')
@admin_required
def admin():
    """Página administrativa para gerenciar perguntas de recuperação"""
    disciplinas_existentes = list(perguntas_recuperacao_db.keys())
    
    # Estatísticas
    stats = {}
    for disciplina, topicos in perguntas_recuperacao_db.items():
        stats[disciplina] = {
            'total_topicos': len(topicos),
            'total_perguntas': sum(len(perguntas) for perguntas in topicos.values()),
            'topicos': {topico: len(perguntas) for topico, perguntas in topicos.items()}
        }
    
    return render_template('admin.html', 
                         disciplinas_existentes=disciplinas_existentes,
                         stats=stats)

@app.route('/admin/listar-topicos/<disciplina>')
@admin_required
def listar_topicos_disciplina(disciplina):
    """Lista os tópicos de uma disciplina específica"""
    if disciplina not in perguntas_recuperacao_db:
        return jsonify({'erro': 'Disciplina não encontrada'}), 404
    
    topicos = {}
    for topico, perguntas in perguntas_recuperacao_db[disciplina].items():
        topicos[topico] = {
            'total_perguntas': len(perguntas),
            'perguntas': perguntas
        }
    
    return jsonify(topicos)

@app.route('/admin/adicionar-pergunta', methods=['POST'])
@admin_required
def adicionar_pergunta_recuperacao():
    """Adiciona uma nova pergunta ao sistema de recuperação"""
    try:
        data = request.get_json()
        
        # Validação dos dados
        campos_obrigatorios = ['disciplina', 'topico', 'pergunta', 'opcoes', 'resposta_correta']
        for campo in campos_obrigatorios:
            if not data.get(campo):
                return jsonify({'erro': f'Campo {campo} é obrigatório'}), 400
        
        disciplina = data['disciplina'].strip()
        topico = data['topico'].strip()
        
        # Validação das opções
        opcoes = data['opcoes']
        if not isinstance(opcoes, list) or len(opcoes) not in [4, 5]:
            return jsonify({'erro': 'Deve haver 4 ou 5 opções'}), 400
        
        # Validação da resposta correta
        resposta_correta = data['resposta_correta'].strip()
        if resposta_correta not in opcoes:
            return jsonify({'erro': 'A resposta correta deve estar entre as opções'}), 400
        
        # Cria a estrutura da pergunta
        nova_pergunta = {
            'pergunta': data['pergunta'].strip(),
            'opcoes': [opcao.strip() for opcao in opcoes],
            'resposta_correta': resposta_correta,
            'categoria': data.get('categoria', '').strip(),
            'disciplina': disciplina,
            'topico': topico,
            'dificuldade': data.get('dificuldade', 'medio'),
            'explicacao': data.get('explicacao', '').strip(),
            'referencia': data.get('referencia', '').strip()
        }
        
        # Adiciona ao banco de dados em memória
        if disciplina not in perguntas_recuperacao_db:
            perguntas_recuperacao_db[disciplina] = {}
        
        if topico not in perguntas_recuperacao_db[disciplina]:
            perguntas_recuperacao_db[disciplina][topico] = []
        
        perguntas_recuperacao_db[disciplina][topico].append(nova_pergunta)
        
        # Salva no arquivo
        salvar_perguntas_recuperacao()
        
        return jsonify({
            'sucesso': True,
            'mensagem': f'Pergunta adicionada com sucesso ao tópico "{topico}" da disciplina "{disciplina}"',
            'total_perguntas': len(perguntas_recuperacao_db[disciplina][topico])
        })
        
    except Exception as e:
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500

@app.route('/admin/excluir-pergunta', methods=['POST'])
@admin_required
def excluir_pergunta_recuperacao():
    """Exclui uma pergunta específica"""
    try:
        data = request.get_json()
        disciplina = data.get('disciplina')
        topico = data.get('topico')
        indice = data.get('indice')
        
        if not all([disciplina, topico, indice is not None]):
            return jsonify({'erro': 'Disciplina, tópico e índice são obrigatórios'}), 400
        
        if disciplina not in perguntas_recuperacao_db:
            return jsonify({'erro': 'Disciplina não encontrada'}), 404
        
        if topico not in perguntas_recuperacao_db[disciplina]:
            return jsonify({'erro': 'Tópico não encontrado'}), 404
        
        perguntas = perguntas_recuperacao_db[disciplina][topico]
        if indice < 0 or indice >= len(perguntas):
            return jsonify({'erro': 'Índice inválido'}), 400
        
        # Remove a pergunta
        pergunta_removida = perguntas.pop(indice)
        
        # Remove tópico se ficou vazio
        if len(perguntas) == 0:
            del perguntas_recuperacao_db[disciplina][topico]
            
            # Remove disciplina se ficou vazia
            if len(perguntas_recuperacao_db[disciplina]) == 0:
                del perguntas_recuperacao_db[disciplina]
        
        # Salva no arquivo
        salvar_perguntas_recuperacao()
        
        return jsonify({
            'sucesso': True,
            'mensagem': 'Pergunta excluída com sucesso',
            'pergunta_removida': pergunta_removida['pergunta'][:100] + '...'
        })
        
    except Exception as e:
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500

@app.route('/admin/editar-pergunta', methods=['POST'])
@admin_required
def editar_pergunta_recuperacao():
    """Edita uma pergunta existente"""
    try:
        data = request.get_json()
        
        # Validação dos dados
        campos_obrigatorios = ['disciplina', 'topico', 'indice', 'pergunta', 'opcoes', 'resposta_correta']
        for campo in campos_obrigatorios:
            if not data.get(campo):
                return jsonify({'erro': f'Campo {campo} é obrigatório'}), 400
        
        disciplina = data['disciplina'].strip()
        topico = data['topico'].strip()
        indice = data['indice']
        
        # Validação das opções
        opcoes = data['opcoes']
        if not isinstance(opcoes, list) or len(opcoes) not in [4, 5]:
            return jsonify({'erro': 'Deve haver 4 ou 5 opções'}), 400
        
        # Validação da resposta correta
        resposta_correta = data['resposta_correta'].strip()
        if resposta_correta not in opcoes:
            return jsonify({'erro': 'A resposta correta deve estar entre as opções'}), 400
        
        # Verifica se a pergunta existe
        if disciplina not in perguntas_recuperacao_db:
            return jsonify({'erro': 'Disciplina não encontrada'}), 404
        
        if topico not in perguntas_recuperacao_db[disciplina]:
            return jsonify({'erro': 'Tópico não encontrado'}), 404
        
        perguntas = perguntas_recuperacao_db[disciplina][topico]
        if indice < 0 or indice >= len(perguntas):
            return jsonify({'erro': 'Índice inválido'}), 400
        
        # Atualiza a pergunta
        perguntas[indice] = {
            'pergunta': data['pergunta'].strip(),
            'opcoes': [opcao.strip() for opcao in opcoes],
            'resposta_correta': resposta_correta,
            'categoria': data.get('categoria', '').strip(),
            'disciplina': disciplina,
            'topico': topico,
            'dificuldade': data.get('dificuldade', 'medio'),
            'explicacao': data.get('explicacao', '').strip(),
            'referencia': data.get('referencia', '').strip()
        }
        
        # Salva no arquivo
        salvar_perguntas_recuperacao()
        
        return jsonify({
            'sucesso': True,
            'mensagem': f'Pergunta editada com sucesso no tópico "{topico}" da disciplina "{disciplina}"',
            'pergunta_editada': perguntas[indice]
        })
        
    except Exception as e:
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500

@app.route('/admin/obter-pergunta/<disciplina>/<topico>/<int:indice>')
@admin_required
def obter_pergunta_recuperacao(disciplina, topico, indice):
    """Obtém uma pergunta específica para edição"""
    try:
        if disciplina not in perguntas_recuperacao_db:
            return jsonify({'erro': 'Disciplina não encontrada'}), 404
        
        if topico not in perguntas_recuperacao_db[disciplina]:
            return jsonify({'erro': 'Tópico não encontrado'}), 404
        
        perguntas = perguntas_recuperacao_db[disciplina][topico]
        if indice < 0 or indice >= len(perguntas):
            return jsonify({'erro': 'Índice inválido'}), 400
        
        return jsonify({
            'pergunta': perguntas[indice],
            'indice': indice
        })
        
    except Exception as e:
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500

def salvar_perguntas_recuperacao():
    """Salva as perguntas de recuperação no arquivo JSON"""
    try:
        safe_write_json('data/perguntas_recuperacao.json', perguntas_recuperacao_db)
        return True
    except Exception as e:
        print(f"ERRO ao salvar perguntas de recuperação: {e}")
        return False

@app.route('/admin/exemplo-json')
@admin_required
def exemplo_json():
    """Retorna exemplo de JSON para upload"""
    exemplo = {
        "ESF": {
            "1 - Importância Atenção Básica": [
                {
                    "pergunta": "Qual é o principal objetivo da Atenção Básica no SUS?",
                    "opcoes": [
                        "Realizar apenas procedimentos de alta complexidade",
                        "Ser a porta de entrada preferencial do sistema de saúde",
                        "Atender somente emergências médicas",
                        "Focar exclusivamente em tratamentos especializados"
                    ],
                    "resposta_correta": "Ser a porta de entrada preferencial do sistema de saúde",
                    "categoria": "Unidade 1",
                    "disciplina": "ESF",
                    "topico": "1 - Importância Atenção Básica",
                    "dificuldade": "facil",
                    "explicacao": "A Atenção Básica é caracterizada por ser a porta de entrada preferencial do SUS.",
                    "referencia": "BRASIL. Ministério da Saúde. Política Nacional de Atenção Básica. Brasília: MS, 2017."
                }
            ]
        }
    }
    return jsonify(exemplo)

@app.route('/admin/upload-perguntas', methods=['POST'])
@admin_required
def upload_perguntas():
    """Upload de perguntas via JSON"""
    try:
        if 'file' not in request.files:
            return jsonify({'erro': 'Nenhum arquivo enviado'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'erro': 'Nenhum arquivo selecionado'}), 400
        if not file.filename or not file.filename.endswith('.json'):
            return jsonify({'erro': 'Arquivo deve ser JSON'}), 400
        # Lê o arquivo
        content = file.read().decode('utf-8')
        data = json.loads(content)
        # Valida a estrutura
        if not isinstance(data, dict):
            return jsonify({'erro': 'JSON deve ser um objeto'}), 400
        # Processa as perguntas
        total_perguntas = 0
        for disciplina, topicos in data.items():
            if not isinstance(topicos, dict):
                continue
            for topico, perguntas in topicos.items():
                if not isinstance(perguntas, list):
                    continue
                # Inicializa estrutura se não existir
                if disciplina not in perguntas_recuperacao_db:
                    perguntas_recuperacao_db[disciplina] = {}
                if topico not in perguntas_recuperacao_db[disciplina]:
                    perguntas_recuperacao_db[disciplina][topico] = []
                # Adiciona perguntas
                for pergunta in perguntas:
                    if validar_pergunta(pergunta, len(perguntas_recuperacao_db[disciplina][topico]) + 1):
                        pergunta['disciplina'] = disciplina
                        pergunta['topico'] = topico
                        perguntas_recuperacao_db[disciplina][topico].append(pergunta)
                        total_perguntas += 1
        # Salva no arquivo
        salvar_perguntas_recuperacao()
        # Recarrega o banco de perguntas de recuperação do arquivo salvo
        carregar_perguntas_recuperacao()
        return jsonify({
            'sucesso': True,
            'mensagem': f'{total_perguntas} perguntas importadas com sucesso!',
            'total_perguntas': total_perguntas
        })
    except json.JSONDecodeError:
        return jsonify({'erro': 'Arquivo JSON inválido'}), 400
    except Exception as e:
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500

def salvar_perguntas_principais():
    """Salva as perguntas principais no arquivo JSON"""
    try:
        safe_write_json(PERGUNTAS_JSON_PATH, perguntas_db)
        return True
    except Exception as e:
        print(f"ERRO ao salvar perguntas principais: {e}")
        return False

@app.route('/admin/quiz-principal')
@admin_required
def admin_quiz_principal():
    """Página administrativa para gerenciar perguntas principais"""
    # Estatísticas
    stats = {
        'total_perguntas': len(perguntas_db),
        'disciplinas': {}
    }
    
    for pergunta in perguntas_db:
        disciplina = pergunta.get('disciplina', 'Sem disciplina')
        if disciplina not in stats['disciplinas']:
            stats['disciplinas'][disciplina] = 0
        stats['disciplinas'][disciplina] += 1
    
    return render_template('admin_quiz_principal.html', stats=stats)

@app.route('/admin/adicionar-pergunta-principal', methods=['POST'])
@admin_required
def adicionar_pergunta_principal():
    """Adiciona uma nova pergunta ao quiz principal"""
    try:
        data = request.get_json()
        
        # Validação dos dados
        campos_obrigatorios = ['pergunta', 'opcoes', 'resposta_correta', 'periodo', 'disciplina']
        for campo in campos_obrigatorios:
            if not data.get(campo):
                return jsonify({'erro': f'Campo {campo} é obrigatório'}), 400
        
        # Validação das opções
        opcoes = data['opcoes']
        if not isinstance(opcoes, list) or len(opcoes) not in [4, 5]:
            return jsonify({'erro': 'Deve haver 4 ou 5 opções'}), 400
        
        # Validação da resposta correta
        resposta_correta = data['resposta_correta'].strip()
        if resposta_correta not in opcoes:
            return jsonify({'erro': 'A resposta correta deve estar entre as opções'}), 400
        
        # Cria a nova pergunta
        nova_pergunta = {
            'pergunta': data['pergunta'].strip(),
            'opcoes': [opcao.strip() for opcao in opcoes],
            'resposta_correta': resposta_correta,
            'categoria': data.get('categoria', '').strip(),
            'periodo': int(data['periodo']),
            'disciplina': data['disciplina'].strip(),
            'dificuldade': data.get('dificuldade', 'medio'),
            'explicacao': data.get('explicacao', '').strip()
        }
        
        # Adiciona ao banco de dados
        perguntas_db.append(nova_pergunta)
        
        # Salva no arquivo
        salvar_perguntas_principais()
        
        return jsonify({
            'sucesso': True,
            'mensagem': f'Pergunta adicionada com sucesso ao período {data["periodo"]}, disciplina "{data["disciplina"]}"',
            'total_perguntas': len(perguntas_db)
        })
        
    except Exception as e:
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500

@app.route('/admin/editar-pergunta-principal', methods=['POST'])
@admin_required
def editar_pergunta_principal():
    """Edita uma pergunta existente do quiz principal"""
    try:
        data = request.get_json()
        
        # Validação dos dados
        campos_obrigatorios = ['indice', 'pergunta', 'opcoes', 'resposta_correta', 'periodo', 'disciplina']
        for campo in campos_obrigatorios:
            if not data.get(campo):
                return jsonify({'erro': f'Campo {campo} é obrigatório'}), 400
        
        indice = data['indice']
        if indice < 0 or indice >= len(perguntas_db):
            return jsonify({'erro': 'Índice inválido'}), 400
        
        # Validação das opções
        opcoes = data['opcoes']
        if not isinstance(opcoes, list) or len(opcoes) not in [4, 5]:
            return jsonify({'erro': 'Deve haver 4 ou 5 opções'}), 400
        
        # Validação da resposta correta
        resposta_correta = data['resposta_correta'].strip()
        if resposta_correta not in opcoes:
            return jsonify({'erro': 'A resposta correta deve estar entre as opções'}), 400
        
        # Atualiza a pergunta
        perguntas_db[indice] = {
            'pergunta': data['pergunta'].strip(),
            'opcoes': [opcao.strip() for opcao in opcoes],
            'resposta_correta': resposta_correta,
            'categoria': data.get('categoria', '').strip(),
            'periodo': int(data['periodo']),
            'disciplina': data['disciplina'].strip(),
            'dificuldade': data.get('dificuldade', 'medio'),
            'explicacao': data.get('explicacao', '').strip()
        }
        
        # Salva no arquivo
        salvar_perguntas_principais()
        
        return jsonify({
            'sucesso': True,
            'mensagem': f'Pergunta editada com sucesso',
            'pergunta_editada': perguntas_db[indice]
        })
        
    except Exception as e:
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500

@app.route('/admin/excluir-pergunta-principal', methods=['POST'])
@admin_required
def excluir_pergunta_principal():
    """Exclui uma pergunta do quiz principal"""
    try:
        data = request.get_json()
        indice = data.get('indice')
        
        if indice is None:
            return jsonify({'erro': 'Índice é obrigatório'}), 400
        
        if indice < 0 or indice >= len(perguntas_db):
            return jsonify({'erro': 'Índice inválido'}), 400
        
        # Remove a pergunta
        pergunta_removida = perguntas_db.pop(indice)
        
        # Salva no arquivo
        salvar_perguntas_principais()
        
        return jsonify({
            'sucesso': True,
            'mensagem': 'Pergunta excluída com sucesso',
            'pergunta_removida': pergunta_removida['pergunta'][:100] + '...'
        })
        
    except Exception as e:
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500

@app.route('/admin/obter-pergunta-principal/<int:indice>')
@admin_required
def obter_pergunta_principal(indice):
    """Obtém uma pergunta específica do quiz principal para edição"""
    try:
        if indice < 0 or indice >= len(perguntas_db):
            return jsonify({'erro': 'Índice inválido'}), 400
        
        return jsonify({
            'pergunta': perguntas_db[indice],
            'indice': indice
        })
        
    except Exception as e:
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500

@app.route('/admin/listar-perguntas-principais')
@admin_required
def listar_perguntas_principais():
    """Lista todas as perguntas do quiz principal com paginação"""
    try:
        pagina = int(request.args.get('pagina', 1))
        por_pagina = int(request.args.get('por_pagina', 20))
        disciplina = request.args.get('disciplina', '')
        periodo = request.args.get('periodo', '')
        
        # Filtra perguntas
        perguntas_filtradas = perguntas_db
        
        if disciplina:
            perguntas_filtradas = [p for p in perguntas_filtradas if p.get('disciplina') == disciplina]
        
        if periodo:
            perguntas_filtradas = [p for p in perguntas_filtradas if p.get('periodo') == int(periodo)]
        
        # Calcula paginação
        total = len(perguntas_filtradas)
        inicio = (pagina - 1) * por_pagina
        fim = inicio + por_pagina
        
        perguntas_pagina = perguntas_filtradas[inicio:fim]
        
        return jsonify({
            'perguntas': perguntas_pagina,
            'total': total,
            'pagina': pagina,
            'por_pagina': por_pagina,
            'total_paginas': (total + por_pagina - 1) // por_pagina
        })
        
    except Exception as e:
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500

# Rotas de autenticação admin
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Página de login admin"""
    if request.method == 'GET':
        return render_template('admin/login.html')
    
    # POST - Processar login
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    
    # Verificar se IP não está bloqueado
    client_ip = get_client_ip()
    if not verificar_login_attempts(client_ip):
        remaining_time = LOGIN_TIMEOUT - (datetime.now() - login_attempts[client_ip][1]).seconds
        flash(f'Muitas tentativas de login. Tente novamente em {remaining_time//60} minutos.', 'error')
        return render_template('admin/login.html')
    
    # Validar e-mail autorizado
    if email != ADMIN_EMAIL:
        registrar_login_attempt(client_ip, success=False)
        flash('E-mail não autorizado para acesso administrativo.', 'error')
        return render_template('admin/login.html')
    
    # Carregar dados do admin
    admin_data = carregar_admin_user()
    if not admin_data:
        flash('Erro interno do sistema. Contate o administrador.', 'error')
        return render_template('admin/login.html')
    
    # Verificar senha
    try:
        if verify_password(password, admin_data['password_hash']):
            # Login bem-sucedido
            registrar_login_attempt(client_ip, success=True)
            session['admin_logged_in'] = True
            session['admin_user'] = {
                'email': admin_data['email'],
                'name': admin_data['name']
            }
            
            # Atualizar último login
            admin_data['last_login'] = datetime.now().isoformat()
            salvar_admin_user(admin_data)
            
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            registrar_login_attempt(client_ip, success=False)
            flash('Senha incorreta.', 'error')
            return render_template('admin/login.html')
    except Exception as e:
        logger.error(f"Erro ao verificar senha: {e}")
        flash('Erro interno do sistema.', 'error')
        return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    """Logout admin"""
    session.pop('admin_logged_in', None)
    session.pop('admin_user', None)
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin/setup', methods=['GET', 'POST'])
def admin_setup():
    """Setup inicial do admin (primeira vez)"""
    if os.path.exists(ADMIN_FILE):
        flash('Admin já configurado. Use o login normal.', 'info')
        return redirect(url_for('admin_login'))
    
    if request.method == 'GET':
        return render_template('admin/setup.html')
    
    # POST - Processar setup
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')
    name = request.form.get('name', '').strip()
    
    # Validações
    if not all([email, password, confirm_password, name]):
        flash('Todos os campos são obrigatórios.', 'error')
        return render_template('admin/setup.html')
    
    if email != ADMIN_EMAIL:
        flash('E-mail deve ser o autorizado para acesso administrativo.', 'error')
        return render_template('admin/setup.html')
    
    if password != confirm_password:
        flash('As senhas não coincidem.', 'error')
        return render_template('admin/setup.html')
    
    if len(password) < 6:
        flash('A senha deve ter pelo menos 6 caracteres.', 'error')
        return render_template('admin/setup.html')
    
    # Criar admin
    admin_data = {
        'email': email,
            'password_hash': hash_password(password),
        'name': name,
        'created_at': datetime.now().isoformat(),
        'last_login': None
    }
    
    if salvar_admin_user(admin_data):
        flash('Administrador configurado com sucesso! Faça login para continuar.', 'success')
        return redirect(url_for('admin_login'))
    else:
        flash('Erro ao salvar configuração do administrador.', 'error')
        return render_template('admin/setup.html')

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Dashboard administrativo"""
    # Estatísticas
    stats = {
        'total_perguntas': len(perguntas_db),
        'disciplinas': len(set(p.get('disciplina', '') for p in perguntas_db)),
        'ultimo_acesso': datetime.now().strftime('%d/%m/%Y %H:%M')
    }
    
    return render_template('admin/dashboard.html', stats=stats)

@app.route('/admin/listar-disciplinas')
@admin_required
def listar_disciplinas():
    """Lista todas as disciplinas disponíveis no sistema de recuperação"""
    try:
        disciplinas = list(perguntas_recuperacao_db.keys())
        return jsonify({
            'disciplinas': disciplinas,
            'total': len(disciplinas)
        })
    except Exception as e:
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500

def carregar_config_usuario():
    """Carrega configuração do usuário"""
    try:
        if os.path.exists(USER_CONFIG_FILE):
            with open(USER_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}  # Retorna dicionário vazio se não existir
    except Exception as e:
        logger.error(f"Erro ao carregar config usuário: {e}")
        return {}

def salvar_config_usuario(config):
    """Salva configuração do usuário"""
    try:
        with open(USER_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar config usuário: {e}")
        return False

def embaralhar_perguntas(perguntas):
    """Embaralha completamente as perguntas"""
    perguntas_embaralhadas = perguntas.copy()
    random.shuffle(perguntas_embaralhadas)
    return perguntas_embaralhadas

def embaralhar_opcoes(perguntas):
    """Embaralha as opções de cada pergunta mantendo a resposta correta"""
    for pergunta in perguntas:
        # Guarda a resposta correta
        resposta_correta = pergunta['resposta_correta']
        
        # Embaralha as opções
        opcoes = pergunta['opcoes'].copy()
        random.shuffle(opcoes)
        
        # Atualiza as opções e a resposta correta
        pergunta['opcoes'] = opcoes
        pergunta['resposta_correta'] = resposta_correta
        
        # Atualiza o índice da resposta correta
        pergunta['indice_resposta_correta'] = opcoes.index(resposta_correta)
    
    return perguntas

@app.route('/admin/estatisticas')
def admin_estatisticas():
    """Retorna estatísticas do banco de questões para o painel admin."""
    # Estatísticas do quiz comum
    total_perguntas_comum = len(perguntas_db)
    perguntas_por_disciplina = {}
    perguntas_por_dificuldade = {}
    perguntas_sem_explicacao = 0
    pergunta_mais_longa = None
    pergunta_mais_curta = None
    max_len = 0
    min_len = 9999

    for p in perguntas_db:
        # Por disciplina
        disciplina = p.get('disciplina', 'Indefinida')
        perguntas_por_disciplina[disciplina] = perguntas_por_disciplina.get(disciplina, 0) + 1
        # Por dificuldade
        dificuldade = p.get('dificuldade', 'Indefinida')
        perguntas_por_dificuldade[dificuldade] = perguntas_por_dificuldade.get(dificuldade, 0) + 1
        # Sem explicação
        if not p.get('explicacao'):
            perguntas_sem_explicacao += 1
        # Mais longa/curta
        plen = len(p.get('pergunta', ''))
        if plen > max_len:
            max_len = plen
            pergunta_mais_longa = p.get('pergunta', '')
        if plen < min_len:
            min_len = plen
            pergunta_mais_curta = p.get('pergunta', '')

    # Estatísticas do quiz de recuperação (ESF)
    total_perguntas_recuperacao = 0
    perguntas_por_topico = {}
    if 'ESF' in perguntas_recuperacao_db:
        for topico, perguntas in perguntas_recuperacao_db['ESF'].items():
            perguntas_por_topico[topico] = len(perguntas)
            total_perguntas_recuperacao += len(perguntas)

    return {
        'total_perguntas_comum': total_perguntas_comum,
        'perguntas_por_disciplina': perguntas_por_disciplina,
        'perguntas_por_dificuldade': perguntas_por_dificuldade,
        'perguntas_sem_explicacao': perguntas_sem_explicacao,
        'pergunta_mais_longa': pergunta_mais_longa,
        'pergunta_mais_curta': pergunta_mais_curta,
        'total_perguntas_recuperacao': total_perguntas_recuperacao,
        'perguntas_por_topico': perguntas_por_topico
    }

@app.route('/admin/alterar_senha', methods=['POST'])
def admin_alterar_senha():
    data = request.get_json()
    nova_senha = data.get('nova_senha')
    if not nova_senha or len(nova_senha) < 6:
        return {'erro': 'Senha muito curta.'}
    try:
        with open(ADMIN_FILE, 'r', encoding='utf-8') as f:
            admin_data = json.load(f)
        hashed = hash_password(nova_senha)
        admin_data['password_hash'] = hashed
        with open(ADMIN_FILE, 'w', encoding='utf-8') as f:
            json.dump(admin_data, f, ensure_ascii=False, indent=2)
        return {'sucesso': True}
    except Exception as e:
        return {'erro': str(e)}

@app.route('/admin/alterar_email', methods=['POST'])
def admin_alterar_email():
    data = request.get_json()
    novo_email = data.get('novo_email')
    if not novo_email or '@' not in novo_email:
        return {'erro': 'Email inválido.'}
    try:
        with open(ADMIN_FILE, 'r', encoding='utf-8') as f:
            admin_data = json.load(f)
        admin_data['email'] = novo_email
        with open(ADMIN_FILE, 'w', encoding='utf-8') as f:
            json.dump(admin_data, f, ensure_ascii=False, indent=2)
        return {'sucesso': True}
    except Exception as e:
        return {'erro': str(e)}

@app.route('/admin/redefinir_banco', methods=['POST'])
def admin_redefinir_banco():
    try:
        # Restaurar os arquivos de backup
        shutil.copy('data/perguntas_recuperacao_backup.json', 'data/perguntas_recuperacao_organizado.json')
        # (Opcional) Restaurar perguntas.json se desejar
        # shutil.copy('data/perguntas_backup.json', 'G:/Meu Drive/prjetos python/quiz/quiz_1/data/perguntas.json')
        return {'sucesso': True}
    except Exception as e:
        return {'erro': str(e)}

@app.route('/admin/exportar_banco')
def admin_exportar_banco():
    # Exporta o banco de perguntas principal como download
    return send_file(PERGUNTAS_JSON_PATH, as_attachment=True, download_name='perguntas.json')

def salvar_sessao_quiz(session_id, quiz_data):
    path = os.path.join(SESSOES_DIR, f'{session_id}.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(quiz_data, f, ensure_ascii=False, default=str)

def carregar_sessao_quiz(session_id):
    path = os.path.join(SESSOES_DIR, f'{session_id}.json')
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def parse_datetime(dt):
    if isinstance(dt, datetime):
        return dt
    try:
        return datetime.fromisoformat(dt)
    except Exception:
        return datetime.now()

@app.route('/admin/limpar_banco_recuperacao', methods=['POST'])
@admin_required
def limpar_banco_recuperacao():
    """Remove todos os arquivos de perguntas de recuperação e recarrega o banco."""
    import glob
    import os
    arquivos = glob.glob(os.path.join('data', 'perguntas_recuperacao*.json')) + glob.glob(os.path.join('data', 'RECUP_*.json'))
    for arquivo in arquivos:
        try:
            os.remove(arquivo)
        except Exception as e:
            print(f"Erro ao remover {arquivo}: {e}")
    # Recarrega banco vazio
    carregar_perguntas_recuperacao()
    return jsonify({'status': 'ok', 'msg': 'Banco de recuperação limpo com sucesso.'})

# ========================================
# FUNÇÕES DE BACKUP E RESTAURAÇÃO
# ========================================

def criar_backup_disciplina(disciplina):
    """Cria backup de uma disciplina específica"""
    try:
        if disciplina not in perguntas_recuperacao_db:
            return None, "Disciplina não encontrada"
        
        # Cria diretório de backup se não existir
        backup_dir = os.path.join('data', 'backups')
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # Gera timestamp único
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"backup_{disciplina}_{timestamp}.json"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Salva backup
        backup_data = {
            'disciplina': disciplina,
            'timestamp': timestamp,
            'data': perguntas_recuperacao_db[disciplina],
            'total_perguntas': sum(len(perguntas) for perguntas in perguntas_recuperacao_db[disciplina].values())
        }
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        return backup_path, None
    except Exception as e:
        return None, str(e)

def listar_backups_disponiveis():
    """Lista todos os backups disponíveis"""
    try:
        backup_dir = os.path.join('data', 'backups')
        if not os.path.exists(backup_dir):
            return []
        
        backups = []
        for filename in os.listdir(backup_dir):
            if filename.startswith('backup_') and filename.endswith('.json'):
                filepath = os.path.join(backup_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        backup_data = json.load(f)
                    
                    backups.append({
                        'filename': filename,
                        'disciplina': backup_data.get('disciplina', 'Desconhecida'),
                        'timestamp': backup_data.get('timestamp', ''),
                        'total_perguntas': backup_data.get('total_perguntas', 0),
                        'data_criacao': datetime.strptime(backup_data['timestamp'], '%Y%m%d_%H%M%S').strftime('%d/%m/%Y %H:%M:%S')
                    })
                except Exception as e:
                    print(f"Erro ao ler backup {filename}: {e}")
        
        # Ordena por timestamp (mais recente primeiro)
        backups.sort(key=lambda x: x['timestamp'], reverse=True)
        return backups
    except Exception as e:
        print(f"Erro ao listar backups: {e}")
        return []

@app.route('/admin/remover-disciplina', methods=['POST'])
@admin_required
def remover_disciplina():
    """Remove uma disciplina específica com backup automático"""
    try:
        data = request.get_json()
        disciplina = data.get('disciplina')
        
        if not disciplina:
            return jsonify({'erro': 'Disciplina é obrigatória'}), 400
        
        if disciplina not in perguntas_recuperacao_db:
            return jsonify({'erro': 'Disciplina não encontrada'}), 404
        
        # Cria backup antes de remover
        backup_path, erro_backup = criar_backup_disciplina(disciplina)
        if erro_backup:
            return jsonify({'erro': f'Erro ao criar backup: {erro_backup}'}), 500
        
        # Conta perguntas que serão removidas
        total_perguntas = sum(len(perguntas) for perguntas in perguntas_recuperacao_db[disciplina].values())
        total_topicos = len(perguntas_recuperacao_db[disciplina])
        
        # Remove a disciplina
        disciplina_removida = perguntas_recuperacao_db.pop(disciplina)
        
        # Salva no arquivo
        salvar_perguntas_recuperacao()
        
        return jsonify({
            'sucesso': True,
            'mensagem': f'Disciplina "{disciplina}" removida com sucesso',
            'backup_criado': backup_path,
            'total_perguntas_removidas': total_perguntas,
            'total_topicos_removidos': total_topicos
        })
        
    except Exception as e:
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500

@app.route('/admin/listar-backups')
@admin_required
def listar_backups():
    """Lista todos os backups disponíveis"""
    try:
        backups = listar_backups_disponiveis()
        return jsonify({
            'sucesso': True,
            'backups': backups
        })
    except Exception as e:
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500

@app.route('/admin/restaurar-backup', methods=['POST'])
@admin_required
def restaurar_backup():
    """Restaura uma disciplina a partir de um backup"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'erro': 'Nome do arquivo de backup é obrigatório'}), 400
        
        backup_path = os.path.join('data', 'backups', filename)
        if not os.path.exists(backup_path):
            return jsonify({'erro': 'Arquivo de backup não encontrado'}), 404
        
        # Carrega backup
        with open(backup_path, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        disciplina = backup_data.get('disciplina')
        dados_disciplina = backup_data.get('data', {})
        
        if not disciplina or not dados_disciplina:
            return jsonify({'erro': 'Dados de backup inválidos'}), 400
        
        # Verifica se a disciplina já existe
        disciplina_existente = disciplina in perguntas_recuperacao_db
        
        # Restaura a disciplina
        perguntas_recuperacao_db[disciplina] = dados_disciplina
        
        # Salva no arquivo
        salvar_perguntas_recuperacao()
        
        total_perguntas = sum(len(perguntas) for perguntas in dados_disciplina.values())
        total_topicos = len(dados_disciplina)
        
        return jsonify({
            'sucesso': True,
            'mensagem': f'Disciplina "{disciplina}" restaurada com sucesso',
            'disciplina_existente_substituida': disciplina_existente,
            'total_perguntas_restauradas': total_perguntas,
            'total_topicos_restaurados': total_topicos
        })
        
    except Exception as e:
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500

@app.route('/admin/excluir-backup', methods=['POST'])
@admin_required
def excluir_backup():
    """Exclui um arquivo de backup específico"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'erro': 'Nome do arquivo de backup é obrigatório'}), 400
        
        backup_path = os.path.join('data', 'backups', filename)
        if not os.path.exists(backup_path):
            return jsonify({'erro': 'Arquivo de backup não encontrado'}), 404
        
        # Remove o arquivo
        os.remove(backup_path)
        
        return jsonify({
            'sucesso': True,
            'mensagem': f'Backup "{filename}" excluído com sucesso'
        })
        
    except Exception as e:
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500

@app.route('/admin/restaurar-todos-backups', methods=['POST'])
@admin_required
def restaurar_todos_backups():
    """Restaura todos os backups disponíveis de uma vez"""
    try:
        backups = listar_backups_disponiveis()
        
        if not backups:
            return jsonify({'erro': 'Nenhum backup disponível para restauração'}), 404
        
        # Cria backup do estado atual antes da restauração
        timestamp_atual = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_atual_path = os.path.join('data', 'backups', f'backup_estado_atual_{timestamp_atual}.json')
        
        backup_atual_data = {
            'disciplina': 'ESTADO_ATUAL',
            'timestamp': timestamp_atual,
            'data': perguntas_recuperacao_db.copy(),
            'total_perguntas': sum(
                sum(len(perguntas) for perguntas in topicos.values()) 
                for topicos in perguntas_recuperacao_db.values()
            )
        }
        
        with open(backup_atual_path, 'w', encoding='utf-8') as f:
            json.dump(backup_atual_data, f, ensure_ascii=False, indent=2)
        
        # Restaura todos os backups
        disciplinas_restauradas = []
        disciplinas_substituidas = []
        total_perguntas_restauradas = 0
        total_topicos_restaurados = 0
        
        for backup_info in backups:
            try:
                backup_path = os.path.join('data', 'backups', backup_info['filename'])
                
                with open(backup_path, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
                
                disciplina = backup_data.get('disciplina')
                dados_disciplina = backup_data.get('data', {})
                
                if disciplina and dados_disciplina:
                    # Verifica se a disciplina já existe
                    disciplina_existente = disciplina in perguntas_recuperacao_db
                    
                    # Restaura a disciplina
                    perguntas_recuperacao_db[disciplina] = dados_disciplina
                    
                    total_perguntas = sum(len(perguntas) for perguntas in dados_disciplina.values())
                    total_topicos = len(dados_disciplina)
                    
                    total_perguntas_restauradas += total_perguntas
                    total_topicos_restaurados += total_topicos
                    
                    if disciplina_existente:
                        disciplinas_substituidas.append(disciplina)
                    else:
                        disciplinas_restauradas.append(disciplina)
                        
            except Exception as e:
                print(f"Erro ao restaurar backup {backup_info['filename']}: {e}")
                continue
        
        # Salva o banco atualizado
        salvar_perguntas_recuperacao()
        
        return jsonify({
            'sucesso': True,
            'mensagem': f'Restauração completa realizada com sucesso!',
            'backup_estado_atual': backup_atual_path,
            'total_backups_restaurados': len(backups),
            'disciplinas_restauradas': disciplinas_restauradas,
            'disciplinas_substituidas': disciplinas_substituidas,
            'total_perguntas_restauradas': total_perguntas_restauradas,
            'total_topicos_restaurados': total_topicos_restaurados
        })
        
    except Exception as e:
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500

@app.route('/admin/limpar-todos-backups', methods=['POST'])
@admin_required
def limpar_todos_backups():
    """Remove todos os arquivos de backup de uma vez"""
    try:
        backups = listar_backups_disponiveis()
        
        if not backups:
            return jsonify({'erro': 'Nenhum backup encontrado para exclusão'}), 404
        
        # Cria backup do estado atual antes da limpeza
        timestamp_atual = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_atual_path = os.path.join('data', 'backups', f'backup_estado_atual_{timestamp_atual}.json')
        
        backup_atual_data = {
            'disciplina': 'ESTADO_ATUAL',
            'timestamp': timestamp_atual,
            'data': perguntas_recuperacao_db.copy(),
            'total_perguntas': sum(
                sum(len(perguntas) for perguntas in topicos.values()) 
                for topicos in perguntas_recuperacao_db.values()
            )
        }
        
        with open(backup_atual_path, 'w', encoding='utf-8') as f:
            json.dump(backup_atual_data, f, ensure_ascii=False, indent=2)
        
        # Remove todos os backups
        arquivos_removidos = []
        for backup_info in backups:
            try:
                backup_path = os.path.join('data', 'backups', backup_info['filename'])
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                    arquivos_removidos.append(backup_info['filename'])
            except Exception as e:
                print(f"Erro ao remover backup {backup_info['filename']}: {e}")
                continue
        
        return jsonify({
            'sucesso': True,
            'mensagem': f'Limpeza de backups realizada com sucesso!',
            'backup_estado_atual': backup_atual_path,
            'total_backups_removidos': len(arquivos_removidos),
            'arquivos_removidos': arquivos_removidos
        })
        
    except Exception as e:
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500

# ========================================
# FUNÇÕES DE GERENCIAMENTO DO QUIZ PRINCIPAL
# ========================================

def criar_backup_disciplina_principal(disciplina, periodo=None):
    """Cria backup de uma disciplina específica do quiz principal"""
    try:
        # Filtra perguntas da disciplina
        perguntas_disciplina = []
        if periodo:
            perguntas_disciplina = [p for p in perguntas_db if p.get('disciplina') == disciplina and p.get('periodo') == int(periodo)]
        else:
            perguntas_disciplina = [p for p in perguntas_db if p.get('disciplina') == disciplina]
        
        if not perguntas_disciplina:
            return None, "Disciplina não encontrada"
        
        # Cria diretório de backup se não existir
        backup_dir = os.path.join('data', 'backups_principal')
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # Gera timestamp único
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if periodo:
            backup_filename = f"backup_principal_{disciplina}_periodo{periodo}_{timestamp}.json"
        else:
            backup_filename = f"backup_principal_{disciplina}_{timestamp}.json"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Salva backup
        backup_data = {
            'disciplina': disciplina,
            'periodo': periodo,
            'timestamp': timestamp,
            'data': perguntas_disciplina,
            'total_perguntas': len(perguntas_disciplina)
        }
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        return backup_path, None
    except Exception as e:
        return None, str(e)

def listar_backups_principal_disponiveis():
    """Lista todos os backups do quiz principal disponíveis"""
    try:
        backup_dir = os.path.join('data', 'backups_principal')
        if not os.path.exists(backup_dir):
            return []
        
        backups = []
        for filename in os.listdir(backup_dir):
            if filename.startswith('backup_principal_') and filename.endswith('.json'):
                filepath = os.path.join(backup_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        backup_data = json.load(f)
                    
                    backups.append({
                        'filename': filename,
                        'disciplina': backup_data.get('disciplina', 'Desconhecida'),
                        'periodo': backup_data.get('periodo'),
                        'timestamp': backup_data.get('timestamp', ''),
                        'total_perguntas': backup_data.get('total_perguntas', 0),
                        'data_criacao': datetime.strptime(backup_data['timestamp'], '%Y%m%d_%H%M%S').strftime('%d/%m/%Y %H:%M:%S')
                    })
                except Exception as e:
                    print(f"Erro ao ler backup {filename}: {e}")
        
        # Ordena por timestamp (mais recente primeiro)
        backups.sort(key=lambda x: x['timestamp'], reverse=True)
        return backups
    except Exception as e:
        print(f"Erro ao listar backups principal: {e}")
        return []

@app.route('/admin/remover-disciplina-principal', methods=['POST'])
@admin_required
def remover_disciplina_principal():
    """Remove uma disciplina específica do quiz principal com backup automático"""
    try:
        data = request.get_json()
        disciplina = data.get('disciplina')
        periodo = data.get('periodo')  # Opcional
        
        if not disciplina:
            return jsonify({'erro': 'Disciplina é obrigatória'}), 400
        
        # Filtra perguntas da disciplina
        if periodo:
            perguntas_disciplina = [p for p in perguntas_db if p.get('disciplina') == disciplina and p.get('periodo') == int(periodo)]
        else:
            perguntas_disciplina = [p for p in perguntas_db if p.get('disciplina') == disciplina]
        
        if not perguntas_disciplina:
            return jsonify({'erro': 'Disciplina não encontrada'}), 404
        
        # Cria backup antes de remover
        backup_path, erro_backup = criar_backup_disciplina_principal(disciplina, periodo)
        if erro_backup:
            return jsonify({'erro': f'Erro ao criar backup: {erro_backup}'}), 500
        
        # Remove as perguntas
        if periodo:
            perguntas_db[:] = [p for p in perguntas_db if not (p.get('disciplina') == disciplina and p.get('periodo') == int(periodo))]
        else:
            perguntas_db[:] = [p for p in perguntas_db if p.get('disciplina') != disciplina]
        
        # Salva no arquivo
        salvar_perguntas_principais()
        
        return jsonify({
            'sucesso': True,
            'mensagem': f'Disciplina "{disciplina}"{" - Período " + str(periodo) if periodo else ""} removida com sucesso',
            'backup_criado': backup_path,
            'total_perguntas_removidas': len(perguntas_disciplina)
        })
        
    except Exception as e:
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500

@app.route('/admin/listar-backups-principal')
@admin_required
def listar_backups_principal():
    """Lista todos os backups do quiz principal disponíveis"""
    try:
        backups = listar_backups_principal_disponiveis()
        return jsonify({
            'sucesso': True,
            'backups': backups
        })
    except Exception as e:
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500

@app.route('/admin/restaurar-backup-principal', methods=['POST'])
@admin_required
def restaurar_backup_principal():
    """Restaura uma disciplina do quiz principal a partir de um backup"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'erro': 'Nome do arquivo de backup é obrigatório'}), 400
        
        backup_path = os.path.join('data', 'backups_principal', filename)
        if not os.path.exists(backup_path):
            return jsonify({'erro': 'Arquivo de backup não encontrado'}), 404
        
        # Carrega backup
        with open(backup_path, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        disciplina = backup_data.get('disciplina')
        periodo = backup_data.get('periodo')
        dados_disciplina = backup_data.get('data', [])
        
        if not disciplina or not dados_disciplina:
            return jsonify({'erro': 'Dados de backup inválidos'}), 400
        
        # Verifica se a disciplina já existe
        if periodo:
            disciplina_existente = any(p.get('disciplina') == disciplina and p.get('periodo') == int(periodo) for p in perguntas_db)
        else:
            disciplina_existente = any(p.get('disciplina') == disciplina for p in perguntas_db)
        
        # Remove disciplinas existentes se necessário
        if periodo:
            perguntas_db[:] = [p for p in perguntas_db if not (p.get('disciplina') == disciplina and p.get('periodo') == int(periodo))]
        else:
            perguntas_db[:] = [p for p in perguntas_db if p.get('disciplina') != disciplina]
        
        # Adiciona as perguntas do backup
        perguntas_db.extend(dados_disciplina)
        
        # Salva no arquivo
        salvar_perguntas_principais()
        
        return jsonify({
            'sucesso': True,
            'mensagem': f'Disciplina "{disciplina}"{" - Período " + str(periodo) if periodo else ""} restaurada com sucesso',
            'disciplina_existente_substituida': disciplina_existente,
            'total_perguntas_restauradas': len(dados_disciplina)
        })
        
    except Exception as e:
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500

@app.route('/admin/excluir-backup-principal', methods=['POST'])
@admin_required
def excluir_backup_principal():
    """Exclui um arquivo de backup do quiz principal específico"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'erro': 'Nome do arquivo de backup é obrigatório'}), 400
        
        backup_path = os.path.join('data', 'backups_principal', filename)
        if not os.path.exists(backup_path):
            return jsonify({'erro': 'Arquivo de backup não encontrado'}), 404
        
        # Remove o arquivo
        os.remove(backup_path)
        
        return jsonify({
            'sucesso': True,
            'mensagem': f'Backup "{filename}" excluído com sucesso'
        })
        
    except Exception as e:
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500

@app.route('/admin/restaurar-todos-backups-principal', methods=['POST'])
@admin_required
def restaurar_todos_backups_principal():
    """Restaura todos os backups do quiz principal de uma vez"""
    try:
        backups = listar_backups_principal_disponiveis()
        
        if not backups:
            return jsonify({'erro': 'Nenhum backup disponível para restauração'}), 404
        
        # Cria backup do estado atual antes da restauração
        timestamp_atual = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_atual_path = os.path.join('data', 'backups_principal', f'backup_estado_atual_{timestamp_atual}.json')
        
        backup_atual_data = {
            'disciplina': 'ESTADO_ATUAL',
            'timestamp': timestamp_atual,
            'data': perguntas_db.copy(),
            'total_perguntas': len(perguntas_db)
        }
        
        with open(backup_atual_path, 'w', encoding='utf-8') as f:
            json.dump(backup_atual_data, f, ensure_ascii=False, indent=2)
        
        # Restaura todos os backups
        disciplinas_restauradas = []
        disciplinas_substituidas = []
        total_perguntas_restauradas = 0
        
        for backup_info in backups:
            try:
                backup_path = os.path.join('data', 'backups_principal', backup_info['filename'])
                
                with open(backup_path, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
                
                disciplina = backup_data.get('disciplina')
                periodo = backup_data.get('periodo')
                dados_disciplina = backup_data.get('data', [])
                
                if disciplina and dados_disciplina:
                    # Verifica se a disciplina já existe
                    if periodo:
                        disciplina_existente = any(p.get('disciplina') == disciplina and p.get('periodo') == int(periodo) for p in perguntas_db)
                    else:
                        disciplina_existente = any(p.get('disciplina') == disciplina for p in perguntas_db)
                    
                    # Remove disciplinas existentes se necessário
                    if periodo:
                        perguntas_db[:] = [p for p in perguntas_db if not (p.get('disciplina') == disciplina and p.get('periodo') == int(periodo))]
                    else:
                        perguntas_db[:] = [p for p in perguntas_db if p.get('disciplina') != disciplina]
                    
                    # Adiciona as perguntas do backup
                    perguntas_db.extend(dados_disciplina)
                    
                    total_perguntas_restauradas += len(dados_disciplina)
                    
                    if disciplina_existente:
                        disciplinas_substituidas.append(f"{disciplina}{' - Período ' + str(periodo) if periodo else ''}")
                    else:
                        disciplinas_restauradas.append(f"{disciplina}{' - Período ' + str(periodo) if periodo else ''}")
                        
            except Exception as e:
                print(f"Erro ao restaurar backup {backup_info['filename']}: {e}")
                continue
        
        # Salva o banco atualizado
        salvar_perguntas_principais()
        
        return jsonify({
            'sucesso': True,
            'mensagem': f'Restauração completa do quiz principal realizada com sucesso!',
            'backup_estado_atual': backup_atual_path,
            'total_backups_restaurados': len(backups),
            'disciplinas_restauradas': disciplinas_restauradas,
            'disciplinas_substituidas': disciplinas_substituidas,
            'total_perguntas_restauradas': total_perguntas_restauradas
        })
        
    except Exception as e:
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500

@app.route('/admin/limpar-todos-backups-principal', methods=['POST'])
@admin_required
def limpar_todos_backups_principal():
    """Remove todos os arquivos de backup do quiz principal de uma vez"""
    try:
        backups = listar_backups_principal_disponiveis()
        
        if not backups:
            return jsonify({'erro': 'Nenhum backup encontrado para exclusão'}), 404
        
        # Cria backup do estado atual antes da limpeza
        timestamp_atual = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_atual_path = os.path.join('data', 'backups_principal', f'backup_estado_atual_{timestamp_atual}.json')
        
        backup_atual_data = {
            'disciplina': 'ESTADO_ATUAL',
            'timestamp': timestamp_atual,
            'data': perguntas_db.copy(),
            'total_perguntas': len(perguntas_db)
        }
        
        with open(backup_atual_path, 'w', encoding='utf-8') as f:
            json.dump(backup_atual_data, f, ensure_ascii=False, indent=2)
        
        # Remove todos os backups
        arquivos_removidos = []
        for backup_info in backups:
            try:
                backup_path = os.path.join('data', 'backups_principal', backup_info['filename'])
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                    arquivos_removidos.append(backup_info['filename'])
            except Exception as e:
                print(f"Erro ao remover backup {backup_info['filename']}: {e}")
                continue
        
        return jsonify({
            'sucesso': True,
            'mensagem': f'Limpeza de backups do quiz principal realizada com sucesso!',
            'backup_estado_atual': backup_atual_path,
            'total_backups_removidos': len(arquivos_removidos),
            'arquivos_removidos': arquivos_removidos
        })
        
    except Exception as e:
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500

# Carrega perguntas na inicialização
if not carregar_perguntas():
    print("ERRO: Não foi possível carregar as perguntas principais!")
    exit(1)
else:
    debug_perguntas()

if not carregar_perguntas_recuperacao():
    print("AVISO: Não foi possível carregar as perguntas de recuperação. Modo recuperação pode não funcionar.")

# Health check endpoint
@app.route('/health')
def health_check():
    """Health check endpoint for Google Cloud"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'quiz-app'
    }), 200

if __name__ == "__main__":
      port = int(os.environ.get("PORT", 8080))
      app.run(host="0.0.0.0", port=port)
