"""
Script para importar funcionários do Excel para PostgreSQL
Com hash de senha usando SHA-256
"""

import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv
from psycopg2.extras import execute_values
from datetime import datetime
import hashlib

# =====================================================
# CONFIGURAÇÕES DE CONEXÃO
# =====================================================
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

DB_CONFIG = {
    'host': os.getenv('HOST_DW'),
    'database': os.getenv('DBNAME_DW'),
    'user': os.getenv('USER_DW'),
    'password': os.getenv('PASS_DW'),
    'port': os.getenv('PORT_DW'),
    'options': '-c search_path=apontador_horas,public'
}


# =====================================================
# FUNÇÃO PARA GERAR HASH DE SENHA
# =====================================================
def gerar_hash_senha(senha):
    """
    Gera hash SHA-256 da senha
    """
    if pd.isna(senha) or senha is None:
        # Se não tem senha, usar uma senha padrão
        senha = "Booker@1010"
    
    # Converter para string e gerar hash
    senha_str = str(senha).strip()
    hash_senha = hashlib.sha256(senha_str.encode('utf-8')).hexdigest()
    return hash_senha

# =====================================================
# FUNÇÃO PARA NORMALIZAR VALORES
# =====================================================
def normalizar_nivel(nivel):
    """Normaliza o valor do nível"""
    if pd.isna(nivel):
        return 'funcionario'
    
    nivel_lower = str(nivel).lower().strip()
    
    # Mapeamento de valores aceitos
    niveis_validos = [
        'funcionario', 'coordenador', 'supervisor', 
        'socio', 'prestador de servico', 'admin'
    ]
    
    if nivel_lower in niveis_validos:
        return nivel_lower
    
    return 'funcionario'

def normalizar_ativo(ativo):
    """Converte valores de ativo para boolean"""
    if pd.isna(ativo):
        return True
    
    ativo_str = str(ativo).lower().strip()
    
    # Valores considerados como True
    valores_true = ['sim', 'yes', 's', 'y', 'true', '1', 'ativo']
    
    return ativo_str in valores_true

def normalizar_texto(texto):
    """Normaliza texto removendo espaços extras"""
    if pd.isna(texto) or texto is None:
        return None
    return str(texto).strip()

# =====================================================
# FUNÇÃO PRINCIPAL DE IMPORTAÇÃO
# =====================================================
def importar_funcionarios(arquivo_excel):
    """
    Importa funcionários da planilha Excel para o PostgreSQL
    """
    
    print(f"[{datetime.now()}] Iniciando importação de funcionários...")
    
    # 1. Ler a planilha
    print(f"[{datetime.now()}] Lendo planilha...")
    df = pd.read_excel(arquivo_excel)
    print(f"Total de registros na planilha: {len(df)}")
    
    # 2. Preparar os dados
    print(f"[{datetime.now()}] Preparando dados...")
    
    # Normalizar campos de texto
    df['usuario'] = df['usuario'].apply(normalizar_texto)
    df['email'] = df['email'].apply(normalizar_texto)
    df['nome_completo'] = df['nome_completo'].apply(normalizar_texto)
    df['departamento'] = df['departamento'].apply(normalizar_texto)
    df['nome_gestor'] = df['nome_gestor'].apply(normalizar_texto)
    
    # Normalizar nível e ativo
    df['nivel'] = df['nivel'].apply(normalizar_nivel)
    df['ativo'] = df['ativo'].apply(normalizar_ativo)
    
    # Gerar hash das senhas
    print(f"[{datetime.now()}] Gerando hash das senhas...")
    df['senha_hash'] = df['senha'].apply(gerar_hash_senha)
    
    # Remover coluna de senha em texto plano (não será mais necessária)
    df = df.drop(columns=['senha'])
    
    # Remover linhas sem usuário ou email
    df_limpo = df.dropna(subset=['usuario', 'email'], how='any')
    print(f"Registros após limpeza: {len(df_limpo)}")
    
    # Verificar duplicatas
    print(f"\n=== VERIFICAÇÃO DE DUPLICATAS ===")
    print(f"Usuários únicos: {df_limpo['usuario'].nunique()}")
    print(f"E-mails únicos: {df_limpo['email'].nunique()}")
    
    # Remover duplicatas de usuário (manter primeiro)
    duplicados_usuario = df_limpo[df_limpo.duplicated(subset=['usuario'], keep=False)]
    if len(duplicados_usuario) > 0:
        print(f"\nAVISO: {len(duplicados_usuario)} usuários duplicados encontrados!")
        print(duplicados_usuario[['usuario', 'email', 'nome_completo']])
        df_limpo = df_limpo.drop_duplicates(subset=['usuario'], keep='first')
        print(f"Mantido apenas o primeiro registro de cada usuário duplicado")
    
    # Remover duplicatas de email (manter primeiro)
    duplicados_email = df_limpo[df_limpo.duplicated(subset=['email'], keep=False)]
    if len(duplicados_email) > 0:
        print(f"\nAVISO: {len(duplicados_email)} e-mails duplicados encontrados!")
        print(duplicados_email[['usuario', 'email', 'nome_completo']])
        df_limpo = df_limpo.drop_duplicates(subset=['email'], keep='first')
        print(f"Mantido apenas o primeiro registro de cada e-mail duplicado")
    
    print(f"\nRegistros finais para importação: {len(df_limpo)}")
    
    # Debug: mostrar alguns registros
    print("\n=== PRIMEIROS REGISTROS PREPARADOS ===")
    for idx, row in df_limpo.head(3).iterrows():
        print(f"  Usuário: {row['usuario']}, "
              f"Email: {row['email']}, "
              f"Nome: {row['nome_completo'][:30]}..., "
              f"Nível: {row['nivel']}, "
              f"Ativo: {row['ativo']}")
    
    # 3. Conectar ao banco de dados
    print(f"\n[{datetime.now()}] Conectando ao banco de dados...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("Conexão estabelecida com sucesso!")
        
        # 4. Inserir dados
        print(f"[{datetime.now()}] Inserindo dados...")
        
        # Preparar dados para inserção
        dados = [
            (
                row['usuario'],
                row['senha_hash'],
                row['email'],
                row['nome_completo'],
                row['departamento'],
                row['nivel'],
                row['nome_gestor'],
                row['ativo']
            )
            for _, row in df_limpo.iterrows()
        ]
        
        # Query de inserção (com ON CONFLICT para evitar duplicatas)
        insert_query = """
            INSERT INTO apontador_horas.funcionarios 
            (usuario, senha_hash, email, nome_completo, departamento, nivel, nome_gestor, ativo)
            VALUES %s
            ON CONFLICT (usuario) 
            DO UPDATE SET
                senha_hash = EXCLUDED.senha_hash,
                email = EXCLUDED.email,
                nome_completo = EXCLUDED.nome_completo,
                departamento = EXCLUDED.departamento,
                nivel = EXCLUDED.nivel,
                nome_gestor = EXCLUDED.nome_gestor,
                ativo = EXCLUDED.ativo
        """
        
        # Executar inserção em lote
        execute_values(cursor, insert_query, dados)
        
        # Commit
        conn.commit()
        
        print(f"[{datetime.now()}] ✓ {len(dados)} funcionários inseridos/atualizados com sucesso!")
        
        # 5. Verificar resultado
        cursor.execute("SELECT COUNT(*) FROM apontador_horas.funcionarios")
        total = cursor.fetchone()[0]
        print(f"Total de funcionários na tabela: {total}")
        
        # Mostrar estatísticas
        cursor.execute("""
            SELECT nivel, COUNT(*) as total 
            FROM apontador_horas.funcionarios 
            GROUP BY nivel 
            ORDER BY total DESC
        """)
        print("\n=== FUNCIONÁRIOS POR NÍVEL ===")
        for nivel, count in cursor.fetchall():
            print(f"  {nivel}: {count}")
        
        cursor.execute("""
            SELECT ativo, COUNT(*) as total 
            FROM apontador_horas.funcionarios 
            GROUP BY ativo 
            ORDER BY ativo DESC
        """)
        print("\n=== FUNCIONÁRIOS POR STATUS ===")
        for ativo, count in cursor.fetchall():
            status = "Ativo" if ativo else "Inativo"
            print(f"  {status}: {count}")
        
        # Fechar conexão
        cursor.close()
        conn.close()
        
        print(f"\n[{datetime.now()}] Importação concluída!")
        
    except psycopg2.Error as e:
        print(f"Erro no PostgreSQL: {e}")
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        print(f"Erro: {e}")
        raise

# =====================================================
# FUNÇÃO AUXILIAR: VERIFICAR SENHA
# =====================================================
def verificar_senha(senha_texto, senha_hash_bd):
    """
    Verifica se uma senha em texto plano corresponde ao hash
    """
    hash_gerado = gerar_hash_senha(senha_texto)
    return hash_gerado == senha_hash_bd

# =====================================================
# EXECUÇÃO
# =====================================================
if __name__ == "__main__":
    # Caminho do arquivo
    arquivo = "/home/jvfalves/documentos/projetos/chatbot_apontamento_horas/files/Funcionarios.xlsx"
    
    # Executar importação
    importar_funcionarios(arquivo)
    
    print("\n" + "="*60)
    print("INFORMAÇÕES IMPORTANTES:")
    print("="*60)
    print("1. As senhas foram convertidas para hash SHA-256")
    print("2. Senha padrão para todos: Booker@1010")
    print("3. Hash da senha padrão:", gerar_hash_senha("Booker@1010"))
    print("4. Para login, compare o hash da senha digitada com o hash no banco")
    print("="*60)