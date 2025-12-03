"""
Script para importar dados de clientes do Excel para PostgreSQL
"""

import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv
from psycopg2.extras import execute_values
from datetime import datetime

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
# FUNÇÃO PARA LIMPAR CNPJ/CPF
# =====================================================
def limpar_cnpj_cpf(valor):
    """
    Converte o número científico para string de 11 dígitos (CPF) ou 14 dígitos (CNPJ)
    """
    if pd.isna(valor):
        return None
    try:
        # Converter para inteiro primeiro, depois para string
        numero = str(int(valor))
        
        # Determinar se é CPF ou CNPJ pelo tamanho
        tamanho = len(numero)
        
        if tamanho <= 11:
            # É CPF - preencher com zeros até 11 dígitos
            return numero.zfill(11)
        else:
            # É CNPJ - preencher com zeros até 14 dígitos
            return numero.zfill(14)
    except:
        return None

# =====================================================
# FUNÇÃO PRINCIPAL DE IMPORTAÇÃO
# =====================================================
def importar_clientes(arquivo_excel):
    """
    Importa clientes da planilha Excel para o PostgreSQL
    """
    
    print(f"[{datetime.now()}] Iniciando importação...")
    
    # 1. Ler a planilha
    print(f"[{datetime.now()}] Lendo planilha...")
    df = pd.read_excel(arquivo_excel)
    print(f"Total de registros na planilha: {len(df)}")
    
    # 2. Limpar e preparar os dados
    print(f"[{datetime.now()}] Preparando dados...")
    
    # Limpar CNPJ/CPF
    df['num_cnpj_cpf'] = df['num_cnpj_cpf'].apply(limpar_cnpj_cpf)
    
    # Converter cod_grupo_cliente para inteiro ou None
    def converter_grupo(valor):
        # Primeiro verifica se é NaN/None
        if valor is None or pd.isna(valor) or valor != valor:  # valor != valor é True para NaN
            return None
        try:
            num = float(valor)
            # Verifica novamente se não é NaN após conversão
            if pd.isna(num) or num != num:
                return None
            return int(num)
        except (ValueError, TypeError, OverflowError):
            return None
    
    df['cod_grupo_cliente'] = df['cod_grupo_cliente'].apply(converter_grupo)
    
    # Substituir NaN por None nas colunas de texto
    df['nom_cliente'] = df['nom_cliente'].apply(lambda x: x if pd.notna(x) else None)
    df['des_grupo'] = df['des_grupo'].apply(lambda x: x if pd.notna(x) else None)
    
    # Remover linhas onde tanto CNPJ quanto nome são nulos
    df_limpo = df.dropna(subset=['num_cnpj_cpf', 'nom_cliente'], how='all')
    print(f"Registros após limpeza: {len(df_limpo)}")
    
    # Remover duplicatas de CNPJ, mantendo o registro mais completo
    # Prioridade: registros COM grupo > registros SEM grupo
    print(f"\n=== TRATAMENTO DE DUPLICATAS ===")
    print(f"Registros antes de remover duplicatas: {len(df_limpo)}")
    print(f"CNPJs únicos: {df_limpo['num_cnpj_cpf'].nunique()}")
    
    # Ordenar para manter o registro mais completo primeiro
    # Registros com grupo (não None) vêm primeiro
    df_limpo = df_limpo.sort_values(
        by=['num_cnpj_cpf', 'cod_grupo_cliente'],
        ascending=[True, False],
        na_position='last'
    )
    
    # Remover duplicatas mantendo o primeiro (mais completo)
    df_limpo = df_limpo.drop_duplicates(subset=['num_cnpj_cpf'], keep='first')
    print(f"Registros após remover duplicatas: {len(df_limpo)}")
    print(f"CNPJs únicos após limpeza: {df_limpo['num_cnpj_cpf'].nunique()}")
    
    # Debug: mostrar alguns registros
    print("\nPrimeiros registros preparados:")
    for idx, row in df_limpo.head(5).iterrows():
        print(f"  CNPJ: {row['num_cnpj_cpf']}, "
              f"Nome: {row['nom_cliente'][:30] if row['nom_cliente'] else 'NULL'}..., "
              f"Grupo: {row['cod_grupo_cliente']} (tipo: {type(row['cod_grupo_cliente']).__name__}), "
              f"Desc: {row['des_grupo']}")
    
    # 3. Conectar ao banco de dados
    print(f"[{datetime.now()}] Conectando ao banco de dados...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("Conexão estabelecida com sucesso!")
        
        # 4. Inserir dados
        print(f"[{datetime.now()}] Inserindo dados...")
        
        # Preparar dados para inserção
        dados = [
            (
                row['num_cnpj_cpf'],
                row['nom_cliente'],
                row['cod_grupo_cliente'],
                row['des_grupo']
            )
            for _, row in df_limpo.iterrows()
        ]
        
        # Query de inserção (com ON CONFLICT para evitar duplicatas)
        insert_query = """
            INSERT INTO clientes (num_cnpj_cpf, nom_cliente, cod_grupo_cliente, des_grupo)
            VALUES %s
            ON CONFLICT (num_cnpj_cpf) 
            DO UPDATE SET
                nom_cliente = EXCLUDED.nom_cliente,
                cod_grupo_cliente = EXCLUDED.cod_grupo_cliente,
                des_grupo = EXCLUDED.des_grupo
        """
        
        # Executar inserção em lote
        execute_values(cursor, insert_query, dados)
        
        # Commit
        conn.commit()
        
        print(f"[{datetime.now()}] ✓ {len(dados)} registros inseridos/atualizados com sucesso!")
        
        # 5. Verificar resultado
        cursor.execute("SELECT COUNT(*) FROM clientes")
        total = cursor.fetchone()[0]
        print(f"Total de registros na tabela: {total}")
        
        # Fechar conexão
        cursor.close()
        conn.close()
        
        print(f"[{datetime.now()}] Importação concluída!")
        
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
    arquivo = "/home/jvfalves/documentos/projetos/chatbot_apontamento_horas/files/clientes.xlsx"
    
    # Executar importação
    importar_clientes(arquivo)