"""
Script para importar grupos de tarefas do Excel para PostgreSQL
"""

import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv
from psycopg2.extras import execute_values
from datetime import datetime
from decimal import Decimal

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
# FUNÇÃO PARA CONVERTER CÓDIGO
# =====================================================
def converter_codigo(valor):
    """
    Converte o código para string (texto)
    """
    if pd.isna(valor):
        return None
    try:
        # Converter para string mantendo o formato
        codigo_str = str(valor).strip()
        # Se for float (como 1.01), formatar corretamente
        if isinstance(valor, float):
            # Garantir duas casas decimais
            codigo_str = f"{valor:.2f}"
        return codigo_str
    except:
        return None

def normalizar_texto(texto):
    """Normaliza texto removendo espaços extras"""
    if pd.isna(texto) or texto is None:
        return None
    return str(texto).strip()

# =====================================================
# FUNÇÃO PRINCIPAL DE IMPORTAÇÃO
# =====================================================
def importar_grupo_tarefas(arquivo_excel):
    """
    Importa grupos de tarefas da planilha Excel para o PostgreSQL
    """
    
    print(f"[{datetime.now()}] Iniciando importação de grupos de tarefas...")
    
    # 1. Ler a planilha
    print(f"[{datetime.now()}] Lendo planilha...")
    df = pd.read_excel(arquivo_excel)
    print(f"Total de registros na planilha: {len(df)}")
    
    # 2. Preparar os dados
    print(f"[{datetime.now()}] Preparando dados...")
    
    # Converter código para Decimal
    df['cod_grupo_tarefa'] = df['cod_grupo_tarefa'].apply(converter_codigo)
    
    # Normalizar nome
    df['nome_grupo_tarefa'] = df['nome_grupo_tarefa'].apply(normalizar_texto)
    
    # Remover linhas sem código ou nome
    df_limpo = df.dropna(subset=['cod_grupo_tarefa', 'nome_grupo_tarefa'], how='any')
    print(f"Registros após limpeza: {len(df_limpo)}")
    
    # Verificar duplicatas
    print(f"\n=== VERIFICAÇÃO DE DUPLICATAS ===")
    print(f"Códigos únicos: {df_limpo['cod_grupo_tarefa'].nunique()}")
    print(f"Total de linhas: {len(df_limpo)}")
    
    duplicados = df_limpo[df_limpo.duplicated(subset=['cod_grupo_tarefa'], keep=False)]
    if len(duplicados) > 0:
        print(f"\n⚠️ AVISO: {len(duplicados)} códigos duplicados encontrados!")
        print(duplicados[['cod_grupo_tarefa', 'nome_grupo_tarefa']])
        df_limpo = df_limpo.drop_duplicates(subset=['cod_grupo_tarefa'], keep='first')
        print(f"Mantido apenas o primeiro registro de cada código duplicado")
    else:
        print("✓ Não há duplicatas!")
    
    print(f"\nRegistros finais para importação: {len(df_limpo)}")
    
    # Debug: mostrar todos os registros
    print("\n=== GRUPOS A SEREM IMPORTADOS ===")
    for idx, row in df_limpo.iterrows():
        print(f"  {row['cod_grupo_tarefa']} - {row['nome_grupo_tarefa']}")
    
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
                row['cod_grupo_tarefa'],  # Já é string
                row['nome_grupo_tarefa']
            )
            for _, row in df_limpo.iterrows()
        ]
        
        # Query de inserção (com ON CONFLICT para evitar duplicatas)
        insert_query = """
            INSERT INTO apontador_horas.grupo_tarefas 
            (cod_grupo_tarefa, nome_grupo_tarefa)
            VALUES %s
            ON CONFLICT (cod_grupo_tarefa) 
            DO UPDATE SET
                nome_grupo_tarefa = EXCLUDED.nome_grupo_tarefa
        """
        
        # Executar inserção em lote
        execute_values(cursor, insert_query, dados)
        
        # Commit
        conn.commit()
        
        print(f"[{datetime.now()}] ✓ {len(dados)} grupos de tarefas inseridos/atualizados com sucesso!")
        
        # 5. Verificar resultado
        cursor.execute("SELECT COUNT(*) FROM apontador_horas.grupo_tarefas")
        total = cursor.fetchone()[0]
        print(f"Total de grupos na tabela: {total}")
        
        # Mostrar todos os grupos cadastrados
        print("\n=== GRUPOS CADASTRADOS NO BANCO ===")
        cursor.execute("""
            SELECT cod_grupo_tarefa, nome_grupo_tarefa 
            FROM apontador_horas.grupo_tarefas 
            ORDER BY cod_grupo_tarefa
        """)
        for cod, nome in cursor.fetchall():
            print(f"  {cod} - {nome}")
        
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
# EXECUÇÃO
# =====================================================
if __name__ == "__main__":
    # Caminho do arquivo
    arquivo = "/home/jvfalves/documentos/projetos/chatbot_apontamento_horas/files/Grupo tarefas.xlsx"
    
    # Executar importação
    importar_grupo_tarefas(arquivo)
    
    print("\n" + "="*60)
    print("INFORMAÇÕES IMPORTANTES:")
    print("="*60)
    print("1. cod_grupo_tarefa é a chave primária da tabela")
    print("2. Os códigos são do tipo DECIMAL(4,2)")
    print("3. Exemplos: 1.01, 1.02, 1.10, 1.11, etc")
    print("4. Use ON CONFLICT para atualizar registros existentes")
    print("="*60)