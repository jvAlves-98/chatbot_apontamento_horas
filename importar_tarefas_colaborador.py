"""
Script para importar tarefas de colaboradores do Excel para PostgreSQL
Com normalização de CNPJ/CPF e validação de Foreign Keys
"""

import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv
from psycopg2.extras import execute_values, RealDictCursor
from datetime import datetime
import re

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
    'port': os.getenv('PORT_DW')
}

# =====================================================
# FUNÇÕES DE NORMALIZAÇÃO
# =====================================================
def normalizar_cnpj_cpf(valor):
    """
    Remove pontos, traços, barras e espaços do CNPJ/CPF
    CPF: 11 dígitos
    CNPJ: 14 dígitos
    
    Trata casos especiais:
    - Menos de 11 dígitos → preenche com zeros até 11 (CPF)
    - 12-13 dígitos → preenche com zeros até 14 (CNPJ)
    - Mais de 14 dígitos → considera inválido
    - Vazio ou só caracteres especiais → None
    """
    if pd.isna(valor) or valor is None:
        return None
    
    # Converter para string e remover espaços em branco
    valor_str = str(valor).strip()
    
    # Se estiver vazio após strip, retornar None
    if not valor_str or valor_str == '-':
        return None
    
    # Remover tudo que não for número
    apenas_numeros = re.sub(r'\D', '', valor_str)
    
    # Se não tem números ou está vazio, retornar None
    if not apenas_numeros or len(apenas_numeros) == 0:
        return None
    
    # Determinar se é CPF ou CNPJ pelo tamanho
    tamanho = len(apenas_numeros)
    
    if tamanho <= 11:
        # É CPF - preencher com zeros até 11 dígitos
        return apenas_numeros.zfill(11)
    elif tamanho <= 14:
        # É CNPJ - preencher com zeros até 14 dígitos
        return apenas_numeros.zfill(14)
    else:
        # Mais de 14 dígitos - considerar inválido
        print(f"⚠️ CNPJ/CPF com mais de 14 dígitos ignorado: {valor_str} ({apenas_numeros})")
        return None

def normalizar_cod_grupo_tarefa(valor):
    """Converte código do grupo para string formatada"""
    if pd.isna(valor):
        return None
    try:
        # Se for float, formatar com 2 casas decimais
        if isinstance(valor, float):
            return f"{valor:.2f}"
        return str(valor).strip()
    except:
        return None

def normalizar_texto(texto):
    """Normaliza texto removendo espaços extras"""
    if pd.isna(texto) or texto is None:
        return None
    return str(texto).strip()

def normalizar_decimal(valor):
    """Converte valor para decimal"""
    if pd.isna(valor) or valor is None:
        return None
    try:
        return float(valor)
    except:
        return None

# =====================================================
# FUNÇÕES DE VALIDAÇÃO
# =====================================================
def buscar_dados_referencia(conn):
    """Busca os dados das tabelas referenciadas para validação"""
    cursor = conn.cursor()
    
    # Buscar CNPJs válidos
    cursor.execute("SELECT num_cnpj_cpf FROM apontador_horas.clientes")
    cnpjs_validos = set([row[0] for row in cursor.fetchall()])
    
    # Buscar códigos de grupo válidos
    cursor.execute("SELECT cod_grupo_tarefa FROM apontador_horas.grupo_tarefas")
    grupos_validos = set([row[0] for row in cursor.fetchall()])
    
    # Buscar usuários válidos
    cursor.execute("SELECT usuario FROM apontador_horas.funcionarios")
    usuarios_validos = set([row[0] for row in cursor.fetchall()])
    
    cursor.close()
    
    return cnpjs_validos, grupos_validos, usuarios_validos

# =====================================================
# FUNÇÃO PRINCIPAL DE IMPORTAÇÃO
# =====================================================
def importar_tarefas_colaborador(arquivo_excel):
    """
    Importa tarefas de colaboradores da planilha Excel para o PostgreSQL
    """
    
    print(f"[{datetime.now()}] Iniciando importação de tarefas de colaboradores...")
    
    # 1. Ler a planilha
    print(f"[{datetime.now()}] Lendo planilha...")
    df = pd.read_excel(arquivo_excel)
    print(f"Total de registros na planilha: {len(df)}")
    
    # 2. Conectar ao banco para buscar dados de referência
    print(f"[{datetime.now()}] Conectando ao banco para validação...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cnpjs_validos, grupos_validos, usuarios_validos = buscar_dados_referencia(conn)
        conn.close()
        
        print(f"✓ {len(cnpjs_validos)} clientes encontrados")
        print(f"✓ {len(grupos_validos)} grupos de tarefa encontrados")
        print(f"✓ {len(usuarios_validos)} funcionários encontrados")
        
    except Exception as e:
        print(f"Erro ao buscar dados de referência: {e}")
        return
    
    # 3. Preparar os dados
    print(f"\n[{datetime.now()}] Preparando e validando dados...")
    
    # Normalizar campos
    df['cnpj_cpf_normalizado'] = df['cnpj_cpf'].apply(normalizar_cnpj_cpf)
    df['cod_grupo_tarefa_normalizado'] = df['cod_grupo_tarefa'].apply(normalizar_cod_grupo_tarefa)
    df['nome_empresa'] = df['nome_empresa'].apply(normalizar_texto)
    df['nome_tarefa'] = df['nome_tarefa'].apply(normalizar_texto)
    df['colaborador_1'] = df['colaborador_1'].apply(normalizar_texto)
    df['colaborador_2'] = df['colaborador_2'].apply(normalizar_texto)
    df['estimativa_horas'] = df['estimativa_horas'].apply(normalizar_decimal)
    df['prioridade'] = df['prioridade'].apply(normalizar_texto)
    
    # Remover linhas sem dados essenciais
    df_limpo = df.dropna(subset=['cnpj_cpf_normalizado', 'cod_grupo_tarefa_normalizado', 
                                   'nome_tarefa', 'colaborador_1'], how='any')
    
    registros_removidos = len(df) - len(df_limpo)
    if registros_removidos > 0:
        print(f"\n⚠️ {registros_removidos} registros removidos por dados incompletos:")
        
        # Mostrar exemplos de registros removidos
        df_removidos = df[~df.index.isin(df_limpo.index)]
        print("\nExemplos de registros removidos:")
        for idx, row in df_removidos.head(5).iterrows():
            motivos = []
            if pd.isna(row['cnpj_cpf_normalizado']):
                motivos.append(f"CNPJ/CPF inválido: '{row['cnpj_cpf']}'")
            if pd.isna(row['cod_grupo_tarefa_normalizado']):
                motivos.append("Grupo inválido")
            if pd.isna(row['nome_tarefa']):
                motivos.append("Sem nome de tarefa")
            if pd.isna(row['colaborador_1']):
                motivos.append("Sem colaborador_1")
            
            print(f"  - {row.get('nome_empresa', 'N/A')[:40]}: {', '.join(motivos)}")
    
    print(f"\nRegistros após limpeza inicial: {len(df_limpo)}")
    
    # 4. Validar Foreign Keys
    print(f"\n=== VALIDAÇÃO DE FOREIGN KEYS ===")
    
    # Validar CNPJs
    cnpjs_invalidos = df_limpo[~df_limpo['cnpj_cpf_normalizado'].isin(cnpjs_validos)]
    if len(cnpjs_invalidos) > 0:
        print(f"\n⚠️ AVISO: {len(cnpjs_invalidos)} registros com CNPJ/CPF não encontrado na tabela clientes:")
        for idx, row in cnpjs_invalidos.head(10).iterrows():
            print(f"  - {row['cnpj_cpf']} (normalizado: {row['cnpj_cpf_normalizado']}) - {row['nome_empresa']}")
        if len(cnpjs_invalidos) > 10:
            print(f"  ... e mais {len(cnpjs_invalidos) - 10} registros")
        
        resposta = input("\nRemover registros com CNPJ/CPF inválido? (s/n): ")
        if resposta.lower() == 's':
            df_limpo = df_limpo[df_limpo['cnpj_cpf_normalizado'].isin(cnpjs_validos)]
            print(f"✓ Removidos {len(cnpjs_invalidos)} registros")
        else:
            print("❌ Importação cancelada. Corrija os CNPJs/CPFs inválidos primeiro.")
            return
    else:
        print("✓ Todos os CNPJs/CPFs são válidos")
    
    # Validar grupos de tarefa
    grupos_invalidos = df_limpo[~df_limpo['cod_grupo_tarefa_normalizado'].isin(grupos_validos)]
    if len(grupos_invalidos) > 0:
        print(f"\n⚠️ AVISO: {len(grupos_invalidos)} registros com cod_grupo_tarefa não encontrado:")
        print(f"Códigos inválidos: {grupos_invalidos['cod_grupo_tarefa_normalizado'].unique()}")
        print("❌ Importação cancelada. Adicione esses grupos na tabela grupo_tarefas primeiro.")
        return
    else:
        print("✓ Todos os códigos de grupo são válidos")
    
    # Validar colaborador_1
    colab1_invalidos = df_limpo[~df_limpo['colaborador_1'].isin(usuarios_validos)]
    if len(colab1_invalidos) > 0:
        print(f"\n⚠️ AVISO: {len(colab1_invalidos)} registros com colaborador_1 não encontrado:")
        print(f"Usuários inválidos: {colab1_invalidos['colaborador_1'].unique()}")
        print("❌ Importação cancelada. Cadastre esses usuários na tabela funcionarios primeiro.")
        return
    else:
        print("✓ Todos os colaborador_1 são válidos")
    
    # Validar colaborador_2 (apenas os não-nulos)
    df_com_colab2 = df_limpo[df_limpo['colaborador_2'].notna()]
    colab2_invalidos = df_com_colab2[~df_com_colab2['colaborador_2'].isin(usuarios_validos)]
    if len(colab2_invalidos) > 0:
        print(f"\n⚠️ AVISO: {len(colab2_invalidos)} registros com colaborador_2 não encontrado:")
        print(f"Usuários inválidos: {colab2_invalidos['colaborador_2'].unique()}")
        print("❌ Importação cancelada. Cadastre esses usuários na tabela funcionarios primeiro.")
        return
    else:
        print("✓ Todos os colaborador_2 são válidos")
    
    print(f"\n✓ Todas as validações passaram!")
    print(f"Registros finais para importação: {len(df_limpo)}")
    
    # Debug: mostrar alguns registros
    print("\n=== PRIMEIROS REGISTROS PREPARADOS ===")
    for idx, row in df_limpo.head(3).iterrows():
        print(f"  Cliente: {row['cnpj_cpf_normalizado']} - {row['nome_empresa'][:30]}...")
        print(f"  Grupo: {row['cod_grupo_tarefa_normalizado']} - {row['nome_tarefa'][:40]}...")
        print(f"  Colaboradores: {row['colaborador_1']} + {row['colaborador_2']}")
        print()
    
    # 5. Conectar ao banco de dados para inserção
    print(f"[{datetime.now()}] Conectando ao banco de dados...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("Conexão estabelecida com sucesso!")
        
        # 6. Inserir dados
        print(f"[{datetime.now()}] Inserindo dados...")
        
        # Preparar dados para inserção
        dados = [
            (
                row['cnpj_cpf_normalizado'],
                row['nome_empresa'],
                row['cod_grupo_tarefa_normalizado'],
                row['nome_tarefa'],
                row['colaborador_1'],
                row['colaborador_2'],
                row['estimativa_horas'],
                row['prioridade']
            )
            for _, row in df_limpo.iterrows()
        ]
        
        # Query de inserção
        insert_query = """
            INSERT INTO apontador_horas.tarefas_colaborador 
            (cnpj_cpf, nome_empresa, cod_grupo_tarefa, nome_tarefa, 
             colaborador_1, colaborador_2, estimativa_horas, prioridade)
            VALUES %s
        """
        
        # Executar inserção em lote
        execute_values(cursor, insert_query, dados)
        
        # Commit
        conn.commit()
        
        print(f"[{datetime.now()}] ✓ {len(dados)} tarefas inseridas com sucesso!")
        
        # 7. Verificar resultado
        cursor.execute("SELECT COUNT(*) FROM apontador_horas.tarefas_colaborador")
        total = cursor.fetchone()[0]
        print(f"Total de tarefas na tabela: {total}")
        
        # Estatísticas
        print("\n=== ESTATÍSTICAS ===")
        
        cursor.execute("""
            SELECT prioridade, COUNT(*) as total 
            FROM apontador_horas.tarefas_colaborador 
            GROUP BY prioridade 
            ORDER BY total DESC
        """)
        print("\nTarefas por prioridade:")
        for prioridade, count in cursor.fetchall():
            print(f"  {prioridade}: {count}")
        
        cursor.execute("""
            SELECT colaborador_1, COUNT(*) as total 
            FROM apontador_horas.tarefas_colaborador 
            GROUP BY colaborador_1 
            ORDER BY total DESC
        """)
        print("\nTarefas por colaborador principal:")
        for colab, count in cursor.fetchall():
            print(f"  {colab}: {count}")
        
        cursor.execute("""
            SELECT cod_grupo_tarefa, COUNT(*) as total 
            FROM apontador_horas.tarefas_colaborador 
            GROUP BY cod_grupo_tarefa 
            ORDER BY total DESC
        """)
        print("\nTarefas por grupo:")
        for grupo, count in cursor.fetchall():
            print(f"  {grupo}: {count}")
        
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
    arquivo = "/home/jvfalves/documentos/projetos/chatbot_apontamento_horas/files/tarefas_colaborador.xlsx"
    
    # Executar importação
    importar_tarefas_colaborador(arquivo)
    
    print("\n" + "="*60)
    print("INFORMAÇÕES IMPORTANTES:")
    print("="*60)
    print("1. CNPJs/CPFs foram normalizados para 14 dígitos")
    print("2. Todas as Foreign Keys foram validadas")
    print("3. Registros inválidos foram identificados antes da importação")
    print("4. Certifique-se de que as tabelas clientes, grupo_tarefas")
    print("   e funcionarios estejam populadas antes de importar")
    print("="*60)