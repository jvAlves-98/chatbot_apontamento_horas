from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import requests
import os
from datetime import timedelta, datetime
import hashlib
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import uuid

# Carregar variáveis de ambiente
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

# URL do webhook do n8n
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
        
        senha_hash = hash_senha(senha)
        
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

# ========================================
# ROTAS DE AUTENTICAÇÃO
# ========================================

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
        session_id = str(uuid.uuid4())
        
        session['usuario'] = user['usuario']
        session['usuario_id'] = user['id']
        session['nome_completo'] = user['nome_completo']
        session['nivel'] = user['nivel']
        session['departamento'] = user['departamento']
        session['session_id'] = session_id
        session.permanent = True
        
        print(f"✅ Login: {user['usuario']} | Session ID: {session_id}")
        
        return jsonify({'success': True, 'message': 'Login realizado com sucesso'})
    
    return jsonify({'success': False, 'message': 'Usuário ou senha inválidos'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    usuario = session.get('usuario', 'desconhecido')
    session_id = session.get('session_id', 'sem-session')
    
    print(f"🚪 Logout: {usuario} | Session ID: {session_id}")
    
    session.clear()
    return jsonify({'success': True})

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

# ========================================
# ROTAS DE BUSCA
# ========================================

@app.route('/api/buscar-clientes', methods=['POST'])
def buscar_clientes():
    """Busca clientes por nome"""
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    
    dados = request.get_json()
    query = dados.get('query', '').strip()
    
    if len(query) < 2:
        return jsonify({'success': True, 'clientes': []})
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Erro de conexão'}), 500
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT num_cnpj_cpf, nom_cliente, cod_grupo_cliente, des_grupo
            FROM clientes
            WHERE LOWER(nom_cliente) LIKE LOWER(%s)
               OR LOWER(des_grupo) LIKE LOWER(%s)
            ORDER BY 
                CASE 
                    WHEN LOWER(nom_cliente) = LOWER(%s) THEN 1
                    WHEN LOWER(nom_cliente) LIKE LOWER(%s) THEN 2
                    ELSE 3
                END,
                nom_cliente
            LIMIT 10
        """, (f'%{query}%', f'%{query}%', query, f'{query}%'))
        
        clientes = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'clientes': [dict(c) for c in clientes]
        })
        
    except Exception as e:
        print(f"❌ Erro ao buscar clientes: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/buscar-tarefas', methods=['POST'])
def buscar_tarefas():
    """Busca tarefas de um cliente para o usuário logado"""
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    
    dados = request.get_json()
    cnpj = dados.get('cnpj', '').strip()
    usuario = session.get('usuario')
    
    if not cnpj:
        return jsonify({'success': False, 'message': 'CNPJ não fornecido'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Erro de conexão'}), 500
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # ✅ CORRIGIDO: Agora retorna o ID da tarefa
        cursor.execute("""
            SELECT 
                id,
                nome_tarefa,
                cod_grupo_tarefa,
                prioridade,
                estimativa_horas
            FROM tarefas_colaborador
            WHERE cnpj_cpf = %s
              AND (colaborador_1 = %s OR colaborador_2 = %s)
            ORDER BY 
                CASE 
                    WHEN LOWER(prioridade) LIKE '%%alta%%' OR LOWER(prioridade) LIKE '%%p2%%' THEN 1
                    WHEN LOWER(prioridade) LIKE '%%média%%' OR LOWER(prioridade) LIKE '%%media%%' OR LOWER(prioridade) LIKE '%%p1%%' THEN 2
                    WHEN LOWER(prioridade) LIKE '%%baixa%%' OR LOWER(prioridade) LIKE '%%p3%%' THEN 3
                    ELSE 4
                END,
                nome_tarefa
        """, (cnpj, usuario, usuario))
        
        tarefas = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'tarefas': [dict(t) for t in tarefas]
        })
        
    except Exception as e:
        print(f"❌ Erro ao buscar tarefas: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

# ========================================
# ROTAS DE CONTROLE DE TAREFAS
# ========================================

@app.route('/api/iniciar-tarefa', methods=['POST'])
def iniciar_tarefa():
    """Inicia uma nova tarefa"""
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    
    dados = request.get_json()
    cnpj_cliente = dados.get('cnpj_cliente')
    nome_cliente = dados.get('nome_cliente')
    tarefa_id = dados.get('tarefa_id')  # ✅ CORRIGIDO: Recebe tarefa_id
    nome_tarefa = dados.get('nome_tarefa')  # Para log apenas
    usuario = session.get('usuario')
    
    if not all([cnpj_cliente, tarefa_id]):
        return jsonify({'success': False, 'message': 'Dados incompletos'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Erro de conexão'}), 500
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Verificar se já tem tarefa ativa
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM apontamentos_horas a
            INNER JOIN funcionarios f ON a.funcionario_id = f.id
            WHERE f.usuario = %s
              AND a.status IN ('em_andamento', 'pausado')
        """, (usuario,))
        
        result = cursor.fetchone()
        if result['count'] > 0:
            return jsonify({'success': False, 'message': 'Você já tem uma tarefa ativa'}), 400
        
        # ✅ CORRIGIDO: Usar tarefa_id ao invés de nome_tarefa
        cursor.execute("""
            WITH ids_resolvidos AS (
                SELECT 
                    f.id AS funcionario_id,
                    c.id AS cliente_id,
                    f.nome_completo,
                    c.nom_cliente
                FROM funcionarios f
                CROSS JOIN clientes c
                WHERE f.usuario = %s
                  AND c.num_cnpj_cpf = %s
                LIMIT 1
            )
            INSERT INTO apontamentos_horas (
                funcionario_id,
                cliente_id,
                tarefa_id,
                data_inicio,
                status
            )
            SELECT 
                funcionario_id,
                cliente_id,
                %s,
                NOW(),
                'em_andamento'
            FROM ids_resolvidos
            RETURNING 
                id,
                TO_CHAR(data_inicio AT TIME ZONE 'America/Sao_Paulo', 'YYYY-MM-DD HH24:MI:SS') AS data_inicio_br
        """, (usuario, cnpj_cliente, tarefa_id))
        
        resultado = cursor.fetchone()
        conn.commit()
        
        print(f"✅ Tarefa iniciada: {usuario} | ID: {tarefa_id} | {nome_tarefa} | Cliente: {nome_cliente}")
        
        return jsonify({
            'success': True,
            'apontamento_id': resultado['id'],
            'data_inicio': resultado['data_inicio_br'],
            'message': 'Tarefa iniciada com sucesso'
        })
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao iniciar tarefa: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/pausar-tarefa', methods=['POST'])
def pausar_tarefa():
    """Pausa a tarefa ativa"""
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    
    usuario = session.get('usuario')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Erro de conexão'}), 500
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            WITH tarefa_atual AS (
                SELECT a.id AS apontamento_id
                FROM apontamentos_horas a
                INNER JOIN funcionarios f ON a.funcionario_id = f.id
                WHERE f.usuario = %s
                  AND a.status = 'em_andamento'
                ORDER BY a.data_inicio DESC
                LIMIT 1
            ),
            atualizar_status AS (
                UPDATE apontamentos_horas
                SET status = 'pausado',
                    atualizado_em = NOW()
                WHERE id = (SELECT apontamento_id FROM tarefa_atual)
                RETURNING id
            ),
            inserir_pausa AS (
                INSERT INTO pausas (apontamento_id, data_pausa)
                SELECT apontamento_id, NOW()
                FROM tarefa_atual
                RETURNING id, TO_CHAR(data_pausa AT TIME ZONE 'America/Sao_Paulo', 'HH24:MI:SS') AS horario_pausa
            )
            SELECT 
                CASE WHEN EXISTS(SELECT 1 FROM atualizar_status) THEN true ELSE false END AS sucesso,
                p.horario_pausa
            FROM inserir_pausa p
        """, (usuario,))
        
        resultado = cursor.fetchone()
        conn.commit()
        
        if resultado and resultado['sucesso']:
            print(f"⏸️ Tarefa pausada: {usuario}")
            return jsonify({'success': True, 'horario_pausa': resultado['horario_pausa']})
        else:
            return jsonify({'success': False, 'message': 'Nenhuma tarefa ativa para pausar'}), 400
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao pausar tarefa: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/retomar-tarefa', methods=['POST'])
def retomar_tarefa():
    """Retoma a tarefa pausada"""
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    
    usuario = session.get('usuario')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Erro de conexão'}), 500
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            WITH tarefa_pausada AS (
                SELECT 
                    a.id AS apontamento_id,
                    (SELECT p.id FROM pausas p 
                     WHERE p.apontamento_id = a.id 
                       AND p.data_retomada IS NULL 
                     LIMIT 1) AS pausa_id
                FROM apontamentos_horas a
                INNER JOIN funcionarios f ON a.funcionario_id = f.id
                WHERE f.usuario = %s
                  AND a.status = 'pausado'
                ORDER BY a.data_inicio DESC
                LIMIT 1
            ),
            fechar_pausa AS (
                UPDATE pausas
                SET data_retomada = NOW()
                WHERE id = (SELECT pausa_id FROM tarefa_pausada)
                RETURNING TO_CHAR(data_retomada AT TIME ZONE 'America/Sao_Paulo', 'HH24:MI:SS') AS horario_retomada
            ),
            atualizar_status AS (
                UPDATE apontamentos_horas
                SET status = 'em_andamento',
                    atualizado_em = NOW()
                WHERE id = (SELECT apontamento_id FROM tarefa_pausada)
                RETURNING id
            )
            SELECT 
                CASE WHEN EXISTS(SELECT 1 FROM atualizar_status) THEN true ELSE false END AS sucesso,
                p.horario_retomada
            FROM fechar_pausa p
        """, (usuario,))
        
        resultado = cursor.fetchone()
        conn.commit()
        
        if resultado and resultado['sucesso']:
            print(f"▶️ Tarefa retomada: {usuario}")
            return jsonify({'success': True, 'horario_retomada': resultado['horario_retomada']})
        else:
            return jsonify({'success': False, 'message': 'Nenhuma tarefa pausada para retomar'}), 400
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao retomar tarefa: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/finalizar-tarefa', methods=['POST'])
def finalizar_tarefa():
    """Finaliza a tarefa ativa"""
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    
    usuario = session.get('usuario')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Erro de conexão'}), 500
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            WITH tarefa_ativa AS (
                SELECT 
                    a.id AS apontamento_id,
                    (SELECT p.id FROM pausas p 
                     WHERE p.apontamento_id = a.id 
                       AND p.data_retomada IS NULL 
                     LIMIT 1) AS pausa_aberta_id
                FROM apontamentos_horas a
                INNER JOIN funcionarios f ON a.funcionario_id = f.id
                WHERE f.usuario = %s
                  AND a.status IN ('em_andamento', 'pausado')
                ORDER BY a.data_inicio DESC
                LIMIT 1
            ),
            fechar_pausa_se_existe AS (
                UPDATE pausas
                SET data_retomada = NOW()
                WHERE id = (SELECT pausa_aberta_id FROM tarefa_ativa WHERE pausa_aberta_id IS NOT NULL)
                RETURNING id
            ),
            finalizar AS (
                UPDATE apontamentos_horas
                SET data_fim = NOW(),
                    status = 'finalizado',
                    atualizado_em = NOW()
                WHERE id = (SELECT apontamento_id FROM tarefa_ativa)
                RETURNING 
                    id,
                    data_inicio,
                    data_fim,
                    TO_CHAR(data_fim AT TIME ZONE 'America/Sao_Paulo', 'HH24:MI:SS') AS horario_fim
            ),
            calcular_tempos AS (
                SELECT 
                    f.id,
                    f.horario_fim,
                    EXTRACT(EPOCH FROM (f.data_fim - t.data_inicio))/3600 AS horas_totais,
                    COALESCE(
                        (SELECT SUM(EXTRACT(EPOCH FROM (
                            COALESCE(p.data_retomada, NOW()) - p.data_pausa
                        )))/3600
                        FROM pausas p
                        WHERE p.apontamento_id = (SELECT apontamento_id FROM tarefa_ativa)),
                        0
                    ) AS horas_pausadas
                FROM finalizar f
                CROSS JOIN (SELECT data_inicio FROM apontamentos_horas 
                           WHERE id = (SELECT apontamento_id FROM tarefa_ativa)) t
            )
            SELECT 
                CASE WHEN EXISTS(SELECT 1 FROM finalizar) THEN true ELSE false END AS sucesso,
                c.horario_fim,
                ROUND(c.horas_totais::numeric, 2) AS horas_totais,
                ROUND(c.horas_pausadas::numeric, 2) AS horas_pausadas,
                ROUND((c.horas_totais - c.horas_pausadas)::numeric, 2) AS horas_trabalhadas
            FROM calcular_tempos c
        """, (usuario,))
        
        resultado = cursor.fetchone()
        conn.commit()
        
        if resultado and resultado['sucesso']:
            print(f"✅ Tarefa finalizada: {usuario} | {resultado['horas_trabalhadas']}h")
            return jsonify({
                'success': True,
                'horario_fim': resultado['horario_fim'],
                'horas_totais': float(resultado['horas_totais']),
                'horas_pausadas': float(resultado['horas_pausadas']),
                'horas_trabalhadas': float(resultado['horas_trabalhadas'])
            })
        else:
            return jsonify({'success': False, 'message': 'Nenhuma tarefa ativa para finalizar'}), 400
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao finalizar tarefa: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/verificar-tarefa-ativa', methods=['GET'])
def verificar_tarefa_ativa():
    """Verifica se o usuário tem tarefa ativa"""
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    
    usuario = session.get('usuario')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Erro de conexão'}), 500
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # ✅ CORRIGIDO: JOIN com tarefas_colaborador para buscar nome_tarefa
        cursor.execute("""
            SELECT 
                a.id AS apontamento_id,
                a.status,
                c.nom_cliente AS cliente_nome,
                c.num_cnpj_cpf AS cnpj,
                t.nome_tarefa AS tarefa_nome,
                a.tarefa_id,
                TO_CHAR(a.data_inicio AT TIME ZONE 'America/Sao_Paulo', 'YYYY-MM-DD HH24:MI:SS') AS data_inicio,
                CASE 
                    WHEN a.status = 'pausado' THEN 
                        (SELECT TO_CHAR(p.data_pausa AT TIME ZONE 'America/Sao_Paulo', 'YYYY-MM-DD HH24:MI:SS')
                         FROM apontador_horas.pausas p 
                         WHERE p.apontamento_id = a.id 
                           AND p.data_retomada IS NULL 
                         LIMIT 1)
                    ELSE NULL
                END AS data_pausa,
                COALESCE(
                    (SELECT SUM(EXTRACT(EPOCH FROM (
                        COALESCE(p.data_retomada, NOW()) - p.data_pausa
                    )) * 1000)
                    FROM apontador_horas.pausas p
                    WHERE p.apontamento_id = a.id),
                    0
                ) AS tempo_pausado_ms
            FROM apontador_horas.apontamentos_horas a
            INNER JOIN apontador_horas.funcionarios f ON a.funcionario_id = f.id
            INNER JOIN apontador_horas.clientes c ON a.cliente_id = c.id
            INNER JOIN apontador_horas.tarefas_colaborador t ON a.tarefa_id = t.id
            WHERE f.usuario = %s
              AND a.status IN ('em_andamento', 'pausado')
            ORDER BY a.data_inicio DESC
            LIMIT 1
        """, (usuario,))
        
        tarefa = cursor.fetchone()
        
        if tarefa:
            return jsonify({
                'success': True,
                'tem_tarefa_ativa': True,
                'apontamento_id': tarefa['apontamento_id'],
                'status': tarefa['status'],
                'cliente_nome': tarefa['cliente_nome'],
                'cnpj': tarefa['cnpj'],
                'tarefa_nome': tarefa['tarefa_nome'],
                'tarefa_id': tarefa['tarefa_id'],
                'data_inicio': tarefa['data_inicio'],
                'data_pausa': tarefa['data_pausa'],
                'tempo_pausado_ms': int(tarefa['tempo_pausado_ms'])
            })
        else:
            return jsonify({
                'success': True,
                'tem_tarefa_ativa': False
            })
        
    except Exception as e:
        print(f"❌ Erro ao verificar tarefa ativa: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

# ========================================
# ROTA DE CHAT (mantém compatibilidade)
# ========================================

@app.route('/api/chat', methods=['POST'])
def chat():
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    
    dados = request.get_json()
    mensagem = dados.get('mensagem')
    usuario = session.get('usuario')
    nome_completo = session.get('nome_completo')
    usuario_id = session.get('usuario_id')
    session_id = session.get('session_id')
    
    if not session_id:
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
    
    if not mensagem:
        return jsonify({'success': False, 'message': 'Mensagem vazia'}), 400
    
    try:
        payload = {
            'chatInput': mensagem,
            'usuario': usuario,
            'nome_completo': nome_completo,
            'usuario_id': usuario_id,
            'sessionId': session_id
        }
        
        response = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=30)
        
        if response.status_code != 200:
            return jsonify({
                'success': False,
                'message': f'Erro no servidor do chatbot (HTTP {response.status_code})'
            }), 500
        
        data = response.json()
        
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
            resposta_bot = 'Desculpe, recebi uma resposta em formato inesperado do servidor.'
        
        return jsonify({
            'success': True,
            'resposta': resposta_bot
        })
        
    except requests.exceptions.Timeout:
        return jsonify({
            'success': False,
            'message': 'O chatbot demorou muito para responder. Tente novamente.'
        }), 500
    except Exception as e:
        print(f"❌ Erro no chat: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro ao processar resposta: {str(e)}'
        }), 500

if __name__ == '__main__':
    # Teste de conexão ao iniciar
    print("🔍 Testando conexão com banco de dados...")
    conn = get_db_connection()
    if conn:
        print("✅ Conexão com PostgreSQL estabelecida!")
        conn.close()
    else:
        print("⚠️ AVISO: Não foi possível conectar ao banco de dados!")
    
    app.run(debug=True, host='0.0.0.0', port=5000)