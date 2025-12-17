"""
Script para atualizar o campo DEPARTAMENTO dos grupos de tarefas
Atualiza baseado no cod_grupo_tarefa
"""

import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv

# Configurações
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

def atualizar_departamentos(arquivo_excel):
    """Atualiza apenas o campo departamento dos grupos existentes"""
    
    print("Lendo planilha...")
    df = pd.read_excel(arquivo_excel)
    
    # Limpar dados
    df['cod_grupo_tarefa'] = df['cod_grupo_tarefa'].astype(str).str.strip()
    df['departamento'] = df['departamento'].fillna('').astype(str).str.strip()
    df['departamento'] = df['departamento'].replace('', None)
    
    # Conectar no banco
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    print(f"Atualizando departamento de {len(df)} grupos...")
    
    atualizados = 0
    nao_encontrados = []
    
    for _, row in df.iterrows():
        cod = row['cod_grupo_tarefa']
        dept = row['departamento']
        
        # Verificar se o grupo existe
        cursor.execute(
            "SELECT cod_grupo_tarefa FROM apontador_horas.grupo_tarefas WHERE cod_grupo_tarefa = %s",
            (cod,)
        )
        
        if cursor.fetchone():
            # Atualizar departamento
            cursor.execute(
                "UPDATE apontador_horas.grupo_tarefas SET departamento = %s WHERE cod_grupo_tarefa = %s",
                (dept, cod)
            )
            atualizados += 1
        else:
            nao_encontrados.append(cod)
    
    conn.commit()
    
    print(f"\n✓ {atualizados} grupos atualizados")
    
    if nao_encontrados:
        print(f"\n⚠ {len(nao_encontrados)} códigos não encontrados no banco:")
        for cod in nao_encontrados[:10]:
            print(f"  - {cod}")
        if len(nao_encontrados) > 10:
            print(f"  ... e mais {len(nao_encontrados) - 10}")
    
    # Mostrar estatísticas
    cursor.execute("""
        SELECT 
            COALESCE(departamento, 'Sem departamento') as dept,
            COUNT(*) as total
        FROM apontador_horas.grupo_tarefas 
        GROUP BY departamento
        ORDER BY total DESC
    """)
    
    print("\nGrupos por departamento:")
    for dept, total in cursor.fetchall():
        print(f"  {dept}: {total}")
    
    cursor.close()
    conn.close()
    
    print("\n✓ Atualização concluída!")


if __name__ == "__main__":
    arquivo = "/home/jvfalves/documentos/projetos/chatbot_apontamento_horas/files/Grupo tarefas.xlsx"
    atualizar_departamentos(arquivo)