#!/usr/bin/env python3
"""
Script Simples de Alertas de Tarefas Abertas
Executa às 17:00h e insere notificações no banco
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from dotenv import load_dotenv

# Carregar variáveis de ambiente
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

DB_CONFIG = {
    'host': os.getenv('HOST_DW'),
    'database': os.getenv('DBNAME_DW'),
    'user': os.getenv('USER_DW'),
    'password': os.getenv('PASS_DW'),
    'port': os.getenv('PORT_DW', '5432'),
    'options': '-c search_path=apontador_horas,public'
}

def main():
    print(f"🔔 Verificando tarefas abertas - {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    # Conectar no banco
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Buscar tarefas abertas hoje
    cursor.execute("""
        SELECT DISTINCT
            f.usuario,
            f.nome_completo,
            c.nom_cliente,
            t.nome_tarefa,
            gt.nome_grupo_tarefa,
            a.hora_inicio,
            a.status,
            EXTRACT(EPOCH FROM (NOW() - (a.data_inicio || ' ' || a.hora_inicio)::timestamp)) / 3600 AS horas_abertas
        FROM apontamentos_horas a
        INNER JOIN funcionarios f ON a.funcionario_id = f.id
        INNER JOIN tarefas_colaborador t ON a.tarefa_id = t.id
        INNER JOIN clientes c ON t.cnpj_cpf = c.num_cnpj_cpf
        INNER JOIN grupo_tarefas gt ON t.cod_grupo_tarefa = gt.cod_grupo_tarefa
        WHERE a.data_inicio = CURRENT_DATE
            AND a.status IN ('em_andamento', 'pausado')
            AND f.ativo = true
        ORDER BY a.funcionario_id;
    """)
    
    tarefas = cursor.fetchall()
    
    if not tarefas:
        print("✅ Nenhuma tarefa aberta")
        conn.close()
        return
    
    # Agrupar por usuário
    usuarios = {}
    for t in tarefas:
        if t['usuario'] not in usuarios:
            usuarios[t['usuario']] = {
                'nome': t['nome_completo'].split()[0],
                'tarefas': []
            }
        usuarios[t['usuario']]['tarefas'].append(t)
    
    print(f"⚠️ {len(usuarios)} colaborador(es) com tarefas abertas")
    
    # Inserir notificação para cada usuário
    for usuario, dados in usuarios.items():
        qtd = len(dados['tarefas'])
        
        # Montar mensagem
        mensagem = f"⚠️ Olá {dados['nome']}!\n\n"
        mensagem += f"São 17:00h e você tem {qtd} tarefa(s) aberta(s):\n\n"
        
        for i, tarefa in enumerate(dados['tarefas'], 1):
            status_emoji = "▶️" if tarefa['status'] == 'em_andamento' else "⏸️"
            mensagem += f"{status_emoji} {i}. {tarefa['cliente_nome']} - {tarefa['nome_tarefa']}\n"
            mensagem += f"   • Início: {tarefa['hora_inicio']} ({round(tarefa['horas_abertas'], 1)}h)\n\n"
        
        mensagem += "🔔 Lembre-se de finalizar suas tarefas antes de sair!"
        
        # Inserir no banco
        cursor.execute("""
            INSERT INTO notificacoes_enviadas 
            (usuario, tipo_notificacao, mensagem, canal, lida)
            VALUES (%s, 'alerta_tarefa_aberta', %s, 'sistema', false);
        """, (usuario, mensagem))
        
        print(f"✅ Notificação enviada para {usuario}")
    
    conn.commit()
    conn.close()
    print(f"✅ Total: {len(usuarios)} notificação(ões) criada(s)")

if __name__ == '__main__':
    main()