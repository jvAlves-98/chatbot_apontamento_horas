# 📚 Documentação Técnica - Sistema de Apontamento de Horas Booker Brasil

**Versão**: 3.0  
**Data**: Dezembro 2024  
**Autor**: João Vitor

---

## 📑 Índice

1. [Visão Geral do Sistema](#1-visão-geral-do-sistema)
2. [Arquitetura e Componentes](#2-arquitetura-e-componentes)
3. [Banco de Dados](#3-banco-de-dados)
4. [API Reference](#4-api-reference)
5. [Fluxos de Uso](#5-fluxos-de-uso)
6. [Segurança](#6-segurança)
7. [Instalação e Deploy](#7-instalação-e-deploy)
8. [Manutenção](#8-manutenção)

---

## 1. Visão Geral do Sistema

### 1.1 Propósito

Sistema completo de gestão de horas trabalhadas para a **Booker Brasil**, permitindo que ~80 funcionários registrem suas horas de trabalho em mais de 600 clientes, com controle administrativo, relatórios hierárquicos e integração com IA.

### 1.2 Funcionalidades Principais

| Módulo | Funcionalidades |
|--------|-----------------|
| **Apontamento** | Multi-tarefa, timer real-time, pausas, apontamento tardio |
| **Administrativo** | CRUD usuários, CRUD tarefas, dashboard executivo |
| **Relatórios** | 3 níveis hierárquicos, filtros avançados, export Excel |
| **Chat IA** | Linguagem natural, validação automática, histórico |

### 1.3 Métricas do Sistema

- **Usuários Ativos**: 78 funcionários
- **Clientes**: 642 empresas
- **Tarefas Cadastradas**: ~2.500
- **Apontamentos/Mês**: ~10.000
- **Disponibilidade**: 99.5%
- **Tempo Resposta Médio**: <500ms

---

## 2. Arquitetura e Componentes

### 2.1 Diagrama de Arquitetura

```
┌─────────────────────────────────────────────────┐
│             FRONTEND (Browser)                  │
│  • HTML5 / CSS3 / JavaScript                    │
│  • Chart.js para visualizações                  │
│  • Fetch API para comunicação assíncrona        │
└────────────────┬────────────────────────────────┘
                 │ HTTPS
                 ▼
┌─────────────────────────────────────────────────┐
│              BACKEND (Flask)                    │
│  ┌──────────────┐      ┌──────────────┐        │
│  │ App Principal│      │  Admin App   │        │
│  │  (Porta 5000)│      │ (Porta 5001) │        │
│  └──────┬───────┘      └──────┬───────┘        │
└─────────┼──────────────────────┼─────────────────┘
          │                      │
          ├──────────────────────┤
          ▼                      ▼
┌──────────────────┐    ┌────────────────┐
│   PostgreSQL     │    │  n8n Workflow  │
│  apontador_horas │    │ + Claude Haiku │
└──────────────────┘    └────────────────┘
```

### 2.2 Tecnologias

#### Backend
- **Python 3.8+**: Linguagem principal
- **Flask 3.0.0**: Framework web
- **psycopg2-binary 2.9.11**: Driver PostgreSQL
- **openpyxl 3.1.5**: Geração de Excel

#### Frontend
- **HTML5/CSS3**: Interface responsiva
- **JavaScript (Vanilla)**: Lógica client-side
- **Chart.js**: Visualizações gráficas

#### Database
- **PostgreSQL 12+**: Banco relacional
- **Schema**: apontador_horas

#### Integração
- **n8n**: Orquestração de workflows
- **Claude Haiku 4.5**: Processamento IA

---

## 3. Banco de Dados

### 3.1 Schema: apontador_horas

#### Tabelas Principais

**funcionarios**
```sql
CREATE TABLE funcionarios (
    id SERIAL PRIMARY KEY,
    usuario VARCHAR(50) UNIQUE NOT NULL,
    senha_hash VARCHAR(64) NOT NULL,  -- SHA-256
    email VARCHAR(100) UNIQUE NOT NULL,
    nome_completo VARCHAR(100) NOT NULL,
    departamento VARCHAR(50),
    nivel VARCHAR(20) DEFAULT 'funcionario',
    gestor_id INTEGER REFERENCES funcionarios(id),
    ativo BOOLEAN DEFAULT TRUE,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Níveis**: `funcionario`, `coordenador`, `supervisor`, `socio`, `prestador de servico`, `admin`

**clientes**
```sql
CREATE TABLE clientes (
    num_cnpj_cpf VARCHAR(14) PRIMARY KEY,  -- Normalizado (só números)
    nom_cliente VARCHAR(200) NOT NULL,
    cod_grupo_cliente INTEGER,
    des_grupo VARCHAR(100),
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**grupo_tarefas**
```sql
CREATE TABLE grupo_tarefas (
    cod_grupo_tarefa VARCHAR(10) PRIMARY KEY,  -- Ex: "1.01"
    nome_grupo_tarefa VARCHAR(100) NOT NULL,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**tarefas_colaborador**
```sql
CREATE TABLE tarefas_colaborador (
    id SERIAL PRIMARY KEY,
    cnpj_cpf VARCHAR(14) REFERENCES clientes,
    cod_grupo_tarefa VARCHAR(10) REFERENCES grupo_tarefas,
    nome_tarefa VARCHAR(200) NOT NULL,
    colaborador_1 VARCHAR(50) REFERENCES funcionarios(usuario),
    colaborador_2 VARCHAR(50) REFERENCES funcionarios(usuario),
    estimativa_horas DECIMAL(10,2),
    prioridade VARCHAR(20),
    status VARCHAR(20) DEFAULT 'ativa',
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**⚠️ CRÍTICO**: IDs de tarefas **NUNCA** devem ser deletados (usar `status = 'cancelada'`)

**apontamentos_horas**
```sql
CREATE TABLE apontamentos_horas (
    id SERIAL PRIMARY KEY,
    usuario VARCHAR(50) REFERENCES funcionarios(usuario),
    usuario_id INTEGER NOT NULL,
    tarefa_id INTEGER REFERENCES tarefas_colaborador(id),
    cliente_cnpj VARCHAR(14) REFERENCES clientes,
    grupo_tarefa_codigo VARCHAR(10) REFERENCES grupo_tarefas,
    nome_tarefa VARCHAR(200),      -- Desnormalizado (histórico)
    nome_cliente VARCHAR(200),     -- Desnormalizado (histórico)
    data_inicio TIMESTAMP NOT NULL,
    data_fim TIMESTAMP,
    horas_trabalhadas DECIMAL(10,2),
    status VARCHAR(20) DEFAULT 'em_andamento',
    observacoes TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**pausas_tarefa**
```sql
CREATE TABLE pausas_tarefa (
    id SERIAL PRIMARY KEY,
    apontamento_id INTEGER REFERENCES apontamentos_horas(id) ON DELETE CASCADE,
    data_inicio_pausa TIMESTAMP NOT NULL,
    data_fim_pausa TIMESTAMP,
    duracao_minutos INTEGER,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.2 Relacionamentos e Integridade

```
funcionarios
    ↓ (usuario)
tarefas_colaborador
    ↓ (id, cnpj_cpf, cod_grupo_tarefa)
apontamentos_horas
    ↓ (id)
pausas_tarefa
```

**Regras de Integridade**:
1. Todos os FKs têm `ON DELETE CASCADE` ou `ON DELETE SET NULL`
2. Campos desnormalizados (`nome_tarefa`, `nome_cliente`) preservam histórico
3. Timezone: `America/Sao_Paulo` em todas as operações

---

## 4. API Reference

### 4.1 App Principal (Porta 5000)

#### Autenticação

**POST /login**
```json
Request:
{
    "usuario": "joao.silva",
    "senha": "senha123"
}

Response (Success):
{
    "success": true,
    "redirect": "/chat"
}

Response (Error):
{
    "success": false,
    "message": "Credenciais inválidas"
}
```

#### Gestão de Tarefas

**POST /api/iniciar-tarefa**
```json
Request:
{
    "cliente_cnpj": "12345678000100",
    "tarefa_id": 42,
    "observacoes": "Iniciando análise"  // opcional
}

Response:
{
    "success": true,
    "apontamento_id": 123,
    "data_inicio": "2024-12-12T14:30:00-03:00"
}
```

**POST /api/pausar-tarefa**
```json
Request:
{
    "apontamento_id": 123
}

Response:
{
    "success": true,
    "pausa_id": 45,
    "data_pausa": "2024-12-12T15:00:00-03:00"
}
```

**POST /api/retomar-tarefa**
```json
Request:
{
    "apontamento_id": 123
}

Response:
{
    "success": true,
    "data_retomada": "2024-12-12T15:30:00-03:00"
}
```

**POST /api/finalizar-tarefa**
```json
Request:
{
    "apontamento_id": 123,
    "observacoes": "Concluída"  // opcional
}

Response:
{
    "success": true,
    "resumo": {
        "apontamento_id": 123,
        "data_inicio": "2024-12-12T14:30:00",
        "data_fim": "2024-12-12T18:45:00",
        "duracao_total": "04:15:00",
        "tempo_pausado": "00:30:00",
        "horas_efetivas": 3.75
    }
}
```

**GET /api/listar-tarefas-ativas**
```json
Response:
{
    "success": true,
    "tarefas": [
        {
            "apontamento_id": 123,
            "cliente": "ACME Corp",
            "nome_tarefa": "Consultoria Fiscal",
            "data_inicio": "2024-12-12T14:30:00",
            "status": "em_andamento",
            "pausas": []
        }
    ]
}
```

#### Relatórios

**POST /api/relatorios/dados**
```json
Request:
{
    "data_inicio": "2024-12-01",
    "data_fim": "2024-12-31",
    "departamento": ["Fiscal", "Contábil"],
    "funcionario": ["joao.silva"],
    "cliente_grupo": [10, 15],
    "grupo_tarefa": ["1.01", "1.02"],
    "status": "finalizado",
    "nivel_agregacao": "funcionario"  // ou "grupo", "empresa"
}

Response:
{
    "success": true,
    "dados": [
        {
            "usuario": "joao.silva",
            "nome_completo": "João Silva",
            "departamento": "Fiscal",
            "total_tarefas": 45,
            "total_horas": 180.5,
            "media_horas_tarefa": 4.01
        }
    ],
    "totais": {
        "funcionarios": 15,
        "tarefas": 650,
        "horas": 2650.75
    }
}
```

**POST /api/relatorios/exportar-excel**
```
Request: (mesmo formato de /api/relatorios/dados)

Response:
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="relatorio_20241201_20241231.xlsx"
[Binary Excel File]
```

### 4.2 App Admin (Porta 5001)

#### Dashboard

**GET /admin/dashboard**
```
Response: (HTML template com dados)
- usuarios_ativos: 78
- tarefas_ativas: 156
- total_clientes: 642
- apontamentos_hoje: 45
- horas_hoje: 180.5
```

#### CRUD Usuários

**GET /admin/usuarios**
- Lista todos os usuários (HTML)

**POST /admin/usuarios/criar**
```json
Request (Form Data):
{
    "usuario": "novo.usuario",
    "senha": "senha_temp",
    "email": "novo@booker.com.br",
    "nome_completo": "Novo Usuário",
    "departamento": "Fiscal",
    "nivel": "funcionario",
    "gestor_id": 5
}

Response: Redirect /admin/usuarios
Flash: "Usuário criado com sucesso"
```

**POST /admin/usuarios/<id>/atualizar**
```json
Request (Form Data):
{
    "nome_completo": "Nome Atualizado",
    "departamento": "Contábil",
    "nivel": "coordenador",
    "ativo": true
}
```

#### CRUD Tarefas

**POST /admin/tarefas/criar**
```json
Request (Form Data):
{
    "cliente_cnpj": "12345678000100",
    "cod_grupo_tarefa": "1.01",
    "nome_tarefa": "Nova Tarefa",
    "colaborador_1": "joao.silva",
    "colaborador_2": "maria.santos",  // opcional
    "estimativa_horas": 40.0,
    "prioridade": "alta"
}
```

---

## 5. Fluxos de Uso

### 5.1 Apontamento Normal (Multi-tarefa)

```
1. Login no sistema (porta 5000)
   GET /login → POST /login

2. Buscar cliente
   Input: "acme" → POST /api/buscar-clientes
   Response: Lista de clientes matching

3. Selecionar tarefa
   onChange cliente → POST /api/buscar-tarefas
   Response: Tarefas do usuário para aquele cliente

4. Iniciar tarefa
   Click "Iniciar" → POST /api/iniciar-tarefa
   Response: apontamento_id, data_inicio

5. Timer inicia automaticamente
   setInterval(1000) → atualiza display HH:MM:SS

6. [Opcional] Pausar
   Click "Pausar" → POST /api/pausar-tarefa
   Timer congela, mostra tempo pausado

7. [Opcional] Retomar
   Click "Retomar" → POST /api/retomar-tarefa
   Timer continua

8. Finalizar
   Click "Finalizar" → Confirm dialog
   POST /api/finalizar-tarefa
   Response: Resumo com horas efetivas

9. Exibe resumo no chat
   Libera para nova tarefa
```

### 5.2 Apontamento Tardio

```
1. Acessar aba "Apontamento Tardio"
   
2. Selecionar data passada
   Input type="date"

3. Escolher cliente e tarefa
   POST /api/buscar-clientes
   POST /api/buscar-tarefas

4. Informar horários
   Input: hora_inicio (ex: 14:30)
   Input: hora_fim (ex: 18:00)

5. Validação de sobreposição
   POST /api/validar-horario
   Response: ok ou erro se conflito

6. Adicionar observações (opcional)
   Textarea

7. Confirmar registro
   POST /api/registrar-horas-manual
   
8. Sistema salva diretamente como "finalizado"
   Calcula horas automaticamente
```

### 5.3 Geração de Relatórios

```
1. Acessar "Relatórios" no menu

2. Aplicar filtros
   - Período: data_inicio, data_fim
   - Departamento: multi-select
   - Funcionário: multi-select
   - Cliente: por grupo
   - Tarefa: por grupo de tarefa

3. Escolher visualização
   - Tabela simples
   - Hierárquica (3 níveis)
   - Dashboard com gráficos

4. Aplicar filtros
   POST /api/relatorios/dados
   Response: dados agregados

5. Visualizar resultados
   Renderização dinâmica (JavaScript)

6. Exportar Excel
   Click "Exportar" → POST /api/relatorios/exportar-excel
   Download automático do XLSX
```

---

## 6. Segurança

### 6.1 Autenticação

**Hash de Senhas**:
```python
import hashlib

def hash_senha(senha):
    return hashlib.sha256(senha.encode('utf-8')).hexdigest()

# Exemplo:
# senha: "minha_senha"
# hash: "a665a45920422f9d417e4867efdc4fb8..."
```

- Algoritmo: SHA-256 (64 caracteres hex)
- Armazenamento: Apenas hash no banco
- Verificação: Compara hashes

**Sessões**:
```python
# Configuração
app.secret_key = os.urandom(24)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

# Criação
session['usuario'] = usuario
session['session_id'] = str(uuid.uuid4())
session.permanent = True

# Verificação
if 'usuario' not in session:
    return redirect('/login')
```

### 6.2 Controle de Acesso (RBAC)

**Hierarquia**:
```python
admin (100)         # Acesso total
    ↓
socio (90)          # Relatórios estratégicos
    ↓
supervisor (70)     # Visão departamental
    ↓
coordenador (50)    # Equipe direta
    ↓
funcionario (10)    # Apenas próprio
```

**Aplicação**:
```python
def get_usuarios_permitidos(usuario, nivel):
    if nivel in ['admin', 'socio']:
        return todos_usuarios()
    elif nivel in ['coordenador', 'supervisor']:
        return proprios_subordinados(usuario)
    else:
        return [usuario]
```

### 6.3 Proteções

**SQL Injection**:
```python
# ✅ CORRETO
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

# ❌ NUNCA FAZER
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
```

**XSS**:
```html
<!-- Jinja2 escapa automaticamente -->
<p>{{ user_input }}</p>

<!-- JavaScript: usar textContent -->
element.textContent = userInput;
```

**CORS**:
```python
from flask_cors import CORS
CORS(app, origins=['https://horas.bookerbrasil.com'])
```

---

## 7. Instalação e Deploy

### 7.1 Pré-requisitos

```bash
# Versões
Python 3.8+
PostgreSQL 12+
n8n (latest)
```

### 7.2 Setup Rápido

```bash
# 1. Clone
git clone <repo>
cd sistema-apontamento-horas

# 2. Ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Dependências
pip install -r requirements.txt

# 4. Variáveis de ambiente
cp .env.example .env
# Editar .env com credenciais

# 5. Banco de dados
psql -h HOST -U USER -d DATABASE -f scripts/create_schema.sql
psql -h HOST -U USER -d DATABASE -f scripts/create_tables.sql

# 6. Importar dados
python importar_funcionarios.py
python importar_clientes.py
python importar_grupo_tarefas.py
python importar_tarefas_colaborador.py

# 7. Iniciar apps
# Terminal 1
python app.py

# Terminal 2
python admin_app.py
```

### 7.3 Variáveis de Ambiente (.env)

```env
# PostgreSQL
HOST_DW=localhost
DBNAME_DW=seu_banco
USER_DW=seu_usuario
PASS_DW=sua_senha
PORT_DW=5432

# n8n
N8N_WEBHOOK_URL=https://n8n.bookerbrasil.com/webhook/[id]/chat

# Flask (opcional)
FLASK_ENV=production
FLASK_DEBUG=False
```

### 7.4 Deploy em Produção

**Usando Gunicorn**:
```bash
# Instalar
pip install gunicorn

# App principal
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# App admin
gunicorn -w 2 -b 0.0.0.0:5001 admin_app:app
```

**Nginx (reverse proxy)**:
```nginx
# /etc/nginx/sites-available/booker-horas

server {
    listen 80;
    server_name horas.bookerbrasil.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

server {
    listen 80;
    server_name admin.bookerbrasil.com;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Systemd Services**:
```ini
# /etc/systemd/system/booker-horas.service

[Unit]
Description=Booker Horas - App Principal
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/booker-horas
Environment="PATH=/var/www/booker-horas/venv/bin"
ExecStart=/var/www/booker-horas/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app

[Install]
WantedBy=multi-user.target
```

```bash
# Ativar
sudo systemctl enable booker-horas
sudo systemctl start booker-horas
sudo systemctl status booker-horas
```

---

## 8. Manutenção

### 8.1 Backup

**Script Diário**:
```bash
#!/bin/bash
# /usr/local/bin/backup-booker.sh

DATA=$(date +%Y%m%d)
DIR="/backups/booker-horas"

# Backup PostgreSQL
pg_dump -h localhost -U postgres -d booker \
  -n apontador_horas \
  -f "$DIR/backup_$DATA.sql"

# Compactar
gzip "$DIR/backup_$DATA.sql"

# Manter últimos 30 dias
find $DIR -name "*.sql.gz" -mtime +30 -delete
```

**Crontab**:
```cron
# Executar às 2h da manhã
0 2 * * * /usr/local/bin/backup-booker.sh
```

### 8.2 Monitoramento

**Queries Úteis**:
```sql
-- Usuários ativos hoje
SELECT COUNT(DISTINCT usuario) 
FROM apontamentos_horas
WHERE DATE(data_inicio) = CURRENT_DATE;

-- Total de horas (mês atual)
SELECT SUM(horas_trabalhadas)
FROM apontamentos_horas
WHERE data_inicio >= DATE_TRUNC('month', CURRENT_DATE);

-- Top 5 colaboradores
SELECT f.nome_completo, SUM(a.horas_trabalhadas) as total
FROM apontamentos_horas a
JOIN funcionarios f ON a.usuario = f.usuario
WHERE a.data_inicio >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY f.nome_completo
ORDER BY total DESC
LIMIT 5;

-- Tamanho das tabelas
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'apontador_horas'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### 8.3 Logs

**Flask App**:
```python
# Em app.py
import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'logs/app.log',
    maxBytes=10485760,  # 10MB
    backupCount=10
)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
```

**Ver logs**:
```bash
# Flask
tail -f logs/app.log

# PostgreSQL
tail -f /var/log/postgresql/postgresql-14-main.log

# Nginx
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### 8.4 Troubleshooting

**Problema**: Timer não inicia
```javascript
// Verificar console (F12)
// Procurar erros em chat.js
// Limpar cache do navegador
```

**Problema**: Cliente não aparece
```sql
-- Verificar normalização
SELECT num_cnpj_cpf, nom_cliente 
FROM apontador_horas.clientes 
WHERE nom_cliente ILIKE '%termo%';
```

**Problema**: Foreign key violation
```bash
# Ordem correta de importação:
python importar_funcionarios.py
python importar_clientes.py
python importar_grupo_tarefas.py
python importar_tarefas_colaborador.py
```

**Problema**: Relatório vazio
```sql
-- Verificar dados no período
SELECT COUNT(*) 
FROM apontador_horas.apontamentos_horas
WHERE data_inicio BETWEEN '2024-01-01' AND '2024-12-31';
```

---

## 📞 Suporte Técnico

### Checklist de Debug

1. ✅ Verificar logs do Flask
2. ✅ Verificar console do navegador (F12)
3. ✅ Verificar logs do PostgreSQL
4. ✅ Testar conectividade de rede
5. ✅ Verificar variáveis de ambiente
6. ✅ Revisar status do n8n

### Contato

- **Desenvolvedor**: João Vitor
- **Email**: (contato interno Booker Brasil)
- **Documentação**: Este arquivo + README.md

---

## 📝 Changelog

### Versão 3.0 (Dezembro 2024)
- ✅ Interface multi-tarefa com cards visuais
- ✅ Sistema administrativo completo (porta 5001)
- ✅ Relatórios hierárquicos (3 níveis)
- ✅ Dashboard com Chart.js
- ✅ Apontamento tardio com validações
- ✅ Exportação Excel (XLSX) com formatação
- ✅ Controle de acesso hierárquico (RBAC)
- ✅ Normalização completa do banco
- ✅ Preservação de IDs de tarefas (histórico)

### Versão 2.0 (Novembro 2024)
- ✅ Layout 2 colunas (70% controle + 30% chat)
- ✅ Timer em tempo real com atualização por segundo
- ✅ Sistema de pausas e retomadas
- ✅ Busca inteligente de clientes
- ✅ Persistência de sessão

### Versão 1.0 (Outubro 2024)
- ✅ Chat básico com n8n
- ✅ Autenticação com hash SHA-256
- ✅ Integração PostgreSQL
- ✅ Design System Booker
- ✅ Funcionalidades básicas de apontamento

---

**Desenvolvido para Booker Brasil**  
**© 2024-2025 - Todos os direitos reservados**  
**Sistema em Produção desde Outubro/2024**