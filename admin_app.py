from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_cors import CORS
import os
from datetime import timedelta
import hashlib
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Carregar variáveis de ambiente
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=4)
CORS(app)

# Configurações do Banco de Dados
DB_CONFIG = {
    'host': os.getenv('HOST_DW'),
    'database': os.getenv('DBNAME_DW'),
    'user': os.getenv('USER_DW'),
    'password': os.getenv('PASS_DW'),
    'port': os.getenv('PORT_DW', '5432'),
    'options': '-c search_path=apontador_horas,public'
}

def get_db_connection():
    """Cria uma conexão com o banco de dados"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar no banco: {e}")
        return None

def hash_senha(senha):
    """Gera hash SHA-256 da senha"""
    return hashlib.sha256(senha.encode()).hexdigest()

def verificar_admin(usuario, senha):
    """Verifica se usuário é admin"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT id, usuario, nivel, nome_completo, ativo
            FROM funcionarios
            WHERE usuario = %s AND senha_hash = %s
        """, (usuario, hash_senha(senha)))
        
        user = cursor.fetchone()
        
        if user and user['ativo'] and user['nivel'] in ['admin', 'socio']:
            return user
        return None
        
    except Exception as e:
        print(f"❌ Erro ao verificar admin: {e}")
        return None
    finally:
        conn.close()

# ========================================
# ROTAS DE AUTENTICAÇÃO
# ========================================

@app.route('/')
def index():
    if 'admin_usuario' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        senha = request.form.get('senha')
        
        user = verificar_admin(usuario, senha)
        
        if user:
            session['admin_usuario'] = user['usuario']
            session['admin_nome'] = user['nome_completo']
            session['admin_nivel'] = user['nivel']
            session.permanent = True
            
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuário ou senha inválidos, ou sem permissão de administrador', 'error')
    
    return render_template('admin_login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('login'))

# ========================================
# DASHBOARD
# ========================================

@app.route('/dashboard')
def dashboard():
    if 'admin_usuario' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    if not conn:
        flash('Erro de conexão com banco de dados', 'error')
        return redirect(url_for('login'))
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Estatísticas
        cursor.execute("SELECT COUNT(*) as total FROM funcionarios WHERE ativo = true")
        total_usuarios = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM clientes")
        total_clientes = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM tarefas_colaborador")
        total_tarefas = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM grupo_tarefas")
        total_grupos = cursor.fetchone()['total']
        
        stats = {
            'usuarios': total_usuarios,
            'clientes': total_clientes,
            'tarefas': total_tarefas,
            'grupos': total_grupos
        }
        
        return render_template('admin_dashboard.html', stats=stats)
        
    except Exception as e:
        flash(f'Erro ao carregar dashboard: {str(e)}', 'error')
        return redirect(url_for('login'))
    finally:
        conn.close()

# ========================================
# GERENCIAMENTO DE USUÁRIOS
# ========================================

@app.route('/usuarios')
def listar_usuarios():
    if 'admin_usuario' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    if not conn:
        flash('Erro de conexão', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT id, usuario, nome_completo, email, departamento, 
                   nivel, nome_gestor, ativo
            FROM funcionarios
            ORDER BY nome_completo
        """)
        
        usuarios = cursor.fetchall()
        return render_template('admin_usuarios.html', usuarios=usuarios)
        
    except Exception as e:
        flash(f'Erro ao listar usuários: {str(e)}', 'error')
        return redirect(url_for('dashboard'))
    finally:
        conn.close()

@app.route('/usuarios/novo', methods=['GET', 'POST'])
def novo_usuario():
    if 'admin_usuario' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        senha = request.form.get('senha', 'Booker@1010')
        email = request.form.get('email')
        nome_completo = request.form.get('nome_completo')
        departamento = request.form.get('departamento')
        nivel = request.form.get('nivel', 'funcionario')
        nome_gestor = request.form.get('nome_gestor')
        
        conn = get_db_connection()
        if not conn:
            flash('Erro de conexão', 'error')
            return redirect(url_for('listar_usuarios'))
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO funcionarios 
                (usuario, senha_hash, email, nome_completo, departamento, nivel, nome_gestor, ativo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, true)
            """, (usuario, hash_senha(senha), email, nome_completo, departamento, nivel, nome_gestor))
            
            conn.commit()
            flash(f'Usuário {usuario} cadastrado com sucesso!', 'success')
            return redirect(url_for('listar_usuarios'))
            
        except psycopg2.IntegrityError:
            conn.rollback()
            flash('Usuário ou email já existe', 'error')
        except Exception as e:
            conn.rollback()
            flash(f'Erro ao cadastrar: {str(e)}', 'error')
        finally:
            conn.close()
    
    return render_template('admin_usuario_form.html', usuario=None)

@app.route('/usuarios/editar/<int:id>', methods=['GET', 'POST'])
def editar_usuario(id):
    if 'admin_usuario' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    if not conn:
        flash('Erro de conexão', 'error')
        return redirect(url_for('listar_usuarios'))
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        if request.method == 'POST':
            email = request.form.get('email')
            nome_completo = request.form.get('nome_completo')
            departamento = request.form.get('departamento')
            nivel = request.form.get('nivel')
            nome_gestor = request.form.get('nome_gestor')
            ativo = request.form.get('ativo') == 'on'
            nova_senha = request.form.get('nova_senha')
            
            if nova_senha:
                cursor.execute("""
                    UPDATE funcionarios
                    SET email = %s, nome_completo = %s, departamento = %s,
                        nivel = %s, nome_gestor = %s, ativo = %s, senha_hash = %s
                    WHERE id = %s
                """, (email, nome_completo, departamento, nivel, nome_gestor, 
                      ativo, hash_senha(nova_senha), id))
            else:
                cursor.execute("""
                    UPDATE funcionarios
                    SET email = %s, nome_completo = %s, departamento = %s,
                        nivel = %s, nome_gestor = %s, ativo = %s
                    WHERE id = %s
                """, (email, nome_completo, departamento, nivel, nome_gestor, ativo, id))
            
            conn.commit()
            flash('Usuário atualizado com sucesso!', 'success')
            return redirect(url_for('listar_usuarios'))
        
        # GET - carregar dados do usuário
        cursor.execute("SELECT * FROM funcionarios WHERE id = %s", (id,))
        usuario = cursor.fetchone()
        
        if not usuario:
            flash('Usuário não encontrado', 'error')
            return redirect(url_for('listar_usuarios'))
        
        return render_template('admin_usuario_form.html', usuario=usuario)
        
    except Exception as e:
        if conn:
            conn.rollback()
        flash(f'Erro ao editar usuário: {str(e)}', 'error')
        return redirect(url_for('listar_usuarios'))
    finally:
        conn.close()

# ========================================
# GERENCIAMENTO DE TAREFAS
# ========================================

@app.route('/tarefas')
def listar_tarefas():
    if 'admin_usuario' not in session:
        return redirect(url_for('login'))
    
    # Filtros
    busca = request.args.get('busca', '')
    cliente = request.args.get('cliente', '')
    colaborador = request.args.get('colaborador', '')
    
    conn = get_db_connection()
    if not conn:
        flash('Erro de conexão', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Query com filtros
        query = """
            SELECT 
                t.id,
                t.cnpj_cpf,
                c.nom_cliente,
                t.cod_grupo_tarefa,
                g.nome_grupo_tarefa,
                t.nome_tarefa,
                t.colaborador_1,
                t.colaborador_2,
                t.estimativa_horas,
                t.prioridade
            FROM tarefas_colaborador t
            LEFT JOIN clientes c ON t.cnpj_cpf = c.num_cnpj_cpf
            LEFT JOIN grupo_tarefas g ON t.cod_grupo_tarefa = g.cod_grupo_tarefa
            WHERE 1=1
        """
        params = []
        
        if busca:
            query += " AND (t.nome_tarefa ILIKE %s OR c.nom_cliente ILIKE %s)"
            params.extend([f'%{busca}%', f'%{busca}%'])
        
        if cliente:
            query += " AND c.nom_cliente ILIKE %s"
            params.append(f'%{cliente}%')
        
        if colaborador:
            query += " AND (t.colaborador_1 = %s OR t.colaborador_2 = %s)"
            params.extend([colaborador, colaborador])
        
        query += " ORDER BY c.nom_cliente, t.nome_tarefa"
        
        cursor.execute(query, params)
        tarefas = cursor.fetchall()
        
        # Buscar clientes para dropdown
        cursor.execute("SELECT DISTINCT nom_cliente FROM clientes ORDER BY nom_cliente")
        clientes = [row['nom_cliente'] for row in cursor.fetchall()]
        
        # Buscar colaboradores para dropdown
        cursor.execute("SELECT DISTINCT usuario FROM funcionarios WHERE ativo = true ORDER BY usuario")
        colaboradores = [row['usuario'] for row in cursor.fetchall()]
        
        return render_template('admin_tarefas.html', 
                             tarefas=tarefas,
                             clientes=clientes,
                             colaboradores=colaboradores,
                             filtros={'busca': busca, 'cliente': cliente, 'colaborador': colaborador})
        
    except Exception as e:
        flash(f'Erro ao listar tarefas: {str(e)}', 'error')
        return redirect(url_for('dashboard'))
    finally:
        conn.close()

@app.route('/tarefas/nova', methods=['GET', 'POST'])
def nova_tarefa():
    if 'admin_usuario' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    if not conn:
        flash('Erro de conexão', 'error')
        return redirect(url_for('listar_tarefas'))
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        if request.method == 'POST':
            cnpj_cpf = request.form.get('cnpj_cpf')
            cod_grupo_tarefa = request.form.get('cod_grupo_tarefa')
            nome_tarefa = request.form.get('nome_tarefa')
            colaborador_1 = request.form.get('colaborador_1')
            colaborador_2 = request.form.get('colaborador_2') or None
            estimativa_horas = request.form.get('estimativa_horas') or None
            prioridade = request.form.get('prioridade') or None
            
            # Buscar nome da empresa
            cursor.execute("SELECT nom_cliente FROM clientes WHERE num_cnpj_cpf = %s", (cnpj_cpf,))
            cliente = cursor.fetchone()
            nome_empresa = cliente['nom_cliente'] if cliente else None
            
            cursor.execute("""
                INSERT INTO tarefas_colaborador
                (cnpj_cpf, nome_empresa, cod_grupo_tarefa, nome_tarefa, 
                 colaborador_1, colaborador_2, estimativa_horas, prioridade)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (cnpj_cpf, nome_empresa, cod_grupo_tarefa, nome_tarefa,
                  colaborador_1, colaborador_2, estimativa_horas, prioridade))
            
            conn.commit()
            flash('Tarefa cadastrada com sucesso!', 'success')
            return redirect(url_for('listar_tarefas'))
        
        # GET - carregar dados para form
        cursor.execute("SELECT num_cnpj_cpf, nom_cliente FROM clientes ORDER BY nom_cliente")
        clientes = cursor.fetchall()
        
        cursor.execute("SELECT cod_grupo_tarefa, nome_grupo_tarefa FROM grupo_tarefas ORDER BY cod_grupo_tarefa")
        grupos = cursor.fetchall()
        
        cursor.execute("SELECT usuario, nome_completo FROM funcionarios WHERE ativo = true ORDER BY nome_completo")
        colaboradores = cursor.fetchall()
        
        return render_template('admin_tarefa_form.html', 
                             tarefa=None,
                             clientes=clientes,
                             grupos=grupos,
                             colaboradores=colaboradores)
        
    except Exception as e:
        if conn:
            conn.rollback()
        flash(f'Erro ao cadastrar tarefa: {str(e)}', 'error')
        return redirect(url_for('listar_tarefas'))
    finally:
        conn.close()

@app.route('/tarefas/editar/<int:id>', methods=['GET', 'POST'])
def editar_tarefa(id):
    if 'admin_usuario' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    if not conn:
        flash('Erro de conexão', 'error')
        return redirect(url_for('listar_tarefas'))
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        if request.method == 'POST':
            # ✅ CRÍTICO: NÃO alteramos o ID, apenas os outros campos
            cnpj_cpf = request.form.get('cnpj_cpf')
            cod_grupo_tarefa = request.form.get('cod_grupo_tarefa')
            nome_tarefa = request.form.get('nome_tarefa')
            colaborador_1 = request.form.get('colaborador_1')
            colaborador_2 = request.form.get('colaborador_2') or None
            estimativa_horas = request.form.get('estimativa_horas') or None
            prioridade = request.form.get('prioridade') or None
            
            # Buscar nome da empresa
            cursor.execute("SELECT nom_cliente FROM clientes WHERE num_cnpj_cpf = %s", (cnpj_cpf,))
            cliente = cursor.fetchone()
            nome_empresa = cliente['nom_cliente'] if cliente else None
            
            cursor.execute("""
                UPDATE tarefas_colaborador
                SET cnpj_cpf = %s, nome_empresa = %s, cod_grupo_tarefa = %s,
                    nome_tarefa = %s, colaborador_1 = %s, colaborador_2 = %s,
                    estimativa_horas = %s, prioridade = %s
                WHERE id = %s
            """, (cnpj_cpf, nome_empresa, cod_grupo_tarefa, nome_tarefa,
                  colaborador_1, colaborador_2, estimativa_horas, prioridade, id))
            
            conn.commit()
            flash('Tarefa atualizada com sucesso! (ID preservado)', 'success')
            return redirect(url_for('listar_tarefas'))
        
        # GET - carregar dados
        cursor.execute("SELECT * FROM tarefas_colaborador WHERE id = %s", (id,))
        tarefa = cursor.fetchone()
        
        if not tarefa:
            flash('Tarefa não encontrada', 'error')
            return redirect(url_for('listar_tarefas'))
        
        cursor.execute("SELECT num_cnpj_cpf, nom_cliente FROM clientes ORDER BY nom_cliente")
        clientes = cursor.fetchall()
        
        cursor.execute("SELECT cod_grupo_tarefa, nome_grupo_tarefa FROM grupo_tarefas ORDER BY cod_grupo_tarefa")
        grupos = cursor.fetchall()
        
        cursor.execute("SELECT usuario, nome_completo FROM funcionarios WHERE ativo = true ORDER BY nome_completo")
        colaboradores = cursor.fetchall()
        
        return render_template('admin_tarefa_form.html',
                             tarefa=tarefa,
                             clientes=clientes,
                             grupos=grupos,
                             colaboradores=colaboradores)
        
    except Exception as e:
        if conn:
            conn.rollback()
        flash(f'Erro ao editar tarefa: {str(e)}', 'error')
        return redirect(url_for('listar_tarefas'))
    finally:
        conn.close()

@app.route('/tarefas/deletar/<int:id>', methods=['POST'])
def deletar_tarefa(id):
    if 'admin_usuario' not in session:
        return jsonify({'success': False, 'message': 'Não autorizado'}), 401
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Erro de conexão'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Verificar se tem apontamentos vinculados
        cursor.execute("SELECT COUNT(*) as total FROM apontamentos_horas WHERE tarefa_id = %s", (id,))
        result = cursor.fetchone()
        
        if result[0] > 0:
            return jsonify({
                'success': False,
                'message': f'Não é possível deletar! Esta tarefa tem {result[0]} apontamento(s) vinculado(s).'
            }), 400
        
        cursor.execute("DELETE FROM tarefas_colaborador WHERE id = %s", (id,))
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Tarefa deletada com sucesso!'})
        
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

# ========================================
# API AUXILIAR
# ========================================

@app.route('/api/buscar-cliente/<cnpj>')
def api_buscar_cliente(cnpj):
    """Retorna dados do cliente pelo CNPJ"""
    if 'admin_usuario' not in session:
        return jsonify({'success': False}), 401
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False}), 500
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM clientes WHERE num_cnpj_cpf = %s", (cnpj,))
        cliente = cursor.fetchone()
        
        if cliente:
            return jsonify({'success': True, 'cliente': dict(cliente)})
        return jsonify({'success': False})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    print("🔒 Sistema Administrativo - Booker Brasil")
    print("📊 Gerenciamento de Usuários e Tarefas")
    print("="*50)
    
    # Teste de conexão
    conn = get_db_connection()
    if conn:
        print("✅ Conexão com PostgreSQL OK!")
        conn.close()
    else:
        print("⚠️ Erro na conexão com PostgreSQL!")
    
    print("\n🌐 Acesse: http://localhost:5001")
    print("="*50)
    
    app.run(debug=True, host='0.0.0.0', port=5001)