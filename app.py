from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import requests
import os
from datetime import timedelta
import hashlib

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Chave secreta para sessões
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
CORS(app)

# Banco de dados simples (em produção, use um banco real)
# Senhas devem ser hash em produção real
usuarios = {
    "admin": hashlib.sha256("admin123".encode()).hexdigest(),
    "usuario": hashlib.sha256("senha123".encode()).hexdigest()
}

# URL do webhook do n8n - SUBSTITUA pela sua URL real
N8N_WEBHOOK_URL = "https://joaoalvesn8n.app.n8n.cloud/webhook/a8d390dc-053e-4f22-9c7e-d0525ce6d8f2/chat"

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
    
    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
    
    if usuario in usuarios and usuarios[usuario] == senha_hash:
        session['usuario'] = usuario
        session.permanent = True
        return jsonify({'success': True, 'message': 'Login realizado com sucesso'})
    
    return jsonify({'success': False, 'message': 'Usuário ou senha inválidos'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('usuario', None)
    return jsonify({'success': True})

@app.route('/api/chat', methods=['POST'])
def chat():
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    
    dados = request.get_json()
    mensagem = dados.get('mensagem')
    usuario = session.get('usuario')
    
    if not mensagem:
        return jsonify({'success': False, 'message': 'Mensagem vazia'}), 400
    
    try:
        # Enviar mensagem para o n8n AI Agent
        # IMPORTANTE: O AI Agent espera o campo 'chatInput'
        payload = {
            'chatInput': mensagem,  # Campo que o AI Agent reconhece
            'usuario': usuario       # Informação extra do usuário
        }
        
        print(f"📤 Enviando para n8n: {payload}")  # Debug
        
        response = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=30)
        
        # Verificar se a requisição foi bem sucedida
        if response.status_code != 200:
            print(f"❌ Erro HTTP {response.status_code}: {response.text}")
            return jsonify({
                'success': False,
                'message': f'Erro no servidor do chatbot (HTTP {response.status_code})'
            }), 500
        
        data = response.json()
        print(f"📥 Resposta do n8n: {data}")  # Debug
        
        # O AI Agent pode retornar em diferentes formatos
        resposta_bot = None
        
        if isinstance(data, dict):
            # Tenta diferentes campos possíveis que o n8n/AI Agent pode retornar
            resposta_bot = (
                data.get('output') or      # Formato comum do AI Agent
                data.get('text') or        # Formato alternativo
                data.get('response') or    # Outro formato possível
                data.get('resposta') or    # Formato customizado
                data.get('message')        # Outro formato
            )
            
            # Se ainda não encontrou, tenta acessar estruturas aninhadas
            if not resposta_bot and 'data' in data:
                if isinstance(data['data'], dict):
                    resposta_bot = data['data'].get('output') or data['data'].get('text')
                elif isinstance(data['data'], str):
                    resposta_bot = data['data']
                    
        elif isinstance(data, str):
            # Se a resposta é uma string direta
            resposta_bot = data
        
        if not resposta_bot:
            print(f"⚠️ Formato de resposta desconhecido. Dados recebidos: {data}")
            resposta_bot = 'Desculpe, recebi uma resposta em formato inesperado do servidor.'
        
        print(f"✅ Resposta processada: {resposta_bot[:100]}...")  # Debug (primeiros 100 chars)
        
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

@app.route('/api/registrar', methods=['POST'])
def registrar():
    dados = request.get_json()
    usuario = dados.get('usuario')
    senha = dados.get('senha')
    
    if not usuario or not senha:
        return jsonify({'success': False, 'message': 'Usuário e senha são obrigatórios'}), 400
    
    if usuario in usuarios:
        return jsonify({'success': False, 'message': 'Usuário já existe'}), 400
    
    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
    usuarios[usuario] = senha_hash
    
    return jsonify({'success': True, 'message': 'Usuário registrado com sucesso'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)