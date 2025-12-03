from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import requests
import os
from datetime import timedelta
import hashlib
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
CORS(app)

# Configurações do Banco de Dados PostgreSQL
DB_CONFIG = {
    'host': os.getenv('HOST_DW'),
    'database': os.getenv('DBNAME_DW'),
    'user': os.getenv('USER_DW'),
    'password': os.getenv('PASS_DW'),
    'port': os.getenv('PORT_DW', '5432'),
    'options': '-c search_path=apontador_horas,public'
}

# URL do webhook do n8n - SUBSTITUA pela sua URL real
N8N_WEBHOOK_URL = "https://n8n.bookerbrasil.com/webhook/9d8f9a85-c21d-4aed-bd52-124af0d116c3/chat"

def get_db_connection():
    """Cria uma conexão com o banco de dados PostgreSQL"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar no banco: {e}")
        return None

def hash_senha(senha):
    """Gera hash SHA-256 da senha"""
    return hashlib.sha256(senha.encode()).hexdigest()

def verificar_usuario(usuario, senha):
    """Verifica se usuário e senha estão corretos no banco de dados"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Buscar usuário primeiro
        cursor.execute("""
            SELECT id, usuario, senha_hash, nome_completo, email, departamento, nivel, ativo
            FROM funcionarios
            WHERE usuario = %s
        """, (usuario,))
        
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ Usuário '{usuario}' não encontrado")
            return None
        
        if not user['ativo']:
            print(f"❌ Usuário '{usuario}' está inativo")
            return None
        
        # Gerar hash da senha fornecida
        senha_hash = hash_senha(senha)
        
        print(f"🔐 Hash gerado: {senha_hash}")
        print(f"🔐 Hash no banco: {user['senha_hash']}")
        
        # Comparar os hashes
        if user['senha_hash'] == senha_hash:
            print(f"✅ Login válido para '{usuario}'")
            return user
        else:
            print(f"❌ Senha incorreta para '{usuario}'")
            return None
        
    except Exception as e:
        print(f"❌ Erro ao verificar usuário: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        conn.close()

@app.route('/')
def index():
    if 'usuario' in session:
        return render_template('chat.html', usuario=session['usuario'])
    return redirect(url_for('login_page'))

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/api/login', methods=['POST'])
def login():
    dados = request.get_json()
    usuario = dados.get('usuario')
    senha = dados.get('senha')
    
    if not usuario or not senha:
        return jsonify({'success': False, 'message': 'Usuário e senha são obrigatórios'}), 400
    
    user = verificar_usuario(usuario, senha)
    
    if user:
        session['usuario'] = user['usuario']
        session['usuario_id'] = user['id']
        session['nome_completo'] = user['nome_completo']
        session['nivel'] = user['nivel']
        session['departamento'] = user['departamento']
        session.permanent = True
        return jsonify({'success': True, 'message': 'Login realizado com sucesso'})
    
    return jsonify({'success': False, 'message': 'Usuário ou senha inválidos'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/chat', methods=['POST'])
def chat():
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    
    dados = request.get_json()
    mensagem = dados.get('mensagem')
    usuario = session.get('usuario')
    nome_completo = session.get('nome_completo')
    usuario_id = session.get('usuario_id')
    
    if not mensagem:
        return jsonify({'success': False, 'message': 'Mensagem vazia'}), 400
    
    try:
        # Enviar mensagem para o n8n AI Agent
        payload = {
            'chatInput': mensagem,
            'usuario': usuario,
            'nome_completo': nome_completo,
            'usuario_id': usuario_id
        }
        
        print(f"📤 Enviando para n8n: {payload}")
        
        response = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Erro HTTP {response.status_code}: {response.text}")
            return jsonify({
                'success': False,
                'message': f'Erro no servidor do chatbot (HTTP {response.status_code})'
            }), 500
        
        data = response.json()
        print(f"📥 Resposta do n8n: {data}")
        
        # Processar resposta do AI Agent
        resposta_bot = None
        
        if isinstance(data, dict):
            resposta_bot = (
                data.get('output') or
                data.get('text') or
                data.get('response') or
                data.get('resposta') or
                data.get('message')
            )
            
            if not resposta_bot and 'data' in data:
                if isinstance(data['data'], dict):
                    resposta_bot = data['data'].get('output') or data['data'].get('text')
                elif isinstance(data['data'], str):
                    resposta_bot = data['data']
                    
        elif isinstance(data, str):
            resposta_bot = data
        
        if not resposta_bot:
            print(f"⚠️ Formato de resposta desconhecido. Dados recebidos: {data}")
            resposta_bot = 'Desculpe, recebi uma resposta em formato inesperado do servidor.'
        
        print(f"✅ Resposta processada: {resposta_bot[:100]}...")
        
        return jsonify({
            'success': True,
            'resposta': resposta_bot
        })
        
    except requests.exceptions.Timeout:
        print(f"⏱️ Timeout ao conectar com n8n")
        return jsonify({
            'success': False,
            'message': 'O chatbot demorou muito para responder. Tente novamente.'
        }), 500
        
    except requests.exceptions.ConnectionError as e:
        print(f"🔌 Erro de conexão: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Não foi possível conectar ao servidor do chatbot. Verifique a URL.'
        }), 500
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de requisição: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro ao conectar com o chatbot: {str(e)}'
        }), 500
        
    except Exception as e:
        print(f"💥 Erro inesperado: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro ao processar resposta: {str(e)}'
        }), 500

@app.route('/api/usuario-info', methods=['GET'])
def usuario_info():
    """Retorna informações do usuário logado"""
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    
    return jsonify({
        'success': True,
        'usuario': session.get('usuario'),
        'nome_completo': session.get('nome_completo'),
        'nivel': session.get('nivel'),
        'departamento': session.get('departamento')
    })

if __name__ == '__main__':
    # Teste de conexão ao iniciar
    print("🔍 Testando conexão com banco de dados...")
    conn = get_db_connection()
    if conn:
        print("✅ Conexão com PostgreSQL estabelecida!")
        conn.close()
    else:
        print("⚠️ AVISO: Não foi possível conectar ao banco de dados!")
        print("Configure as variáveis de ambiente: DB_HOST, DB_NAME, DB_USER, DB_PASSWORD")
    
    app.run(debug=True, host='0.0.0.0', port=5000)