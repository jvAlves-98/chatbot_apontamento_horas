# 📋 Documentação Completa - Sistema de Apontamento de Horas Booker Brasil

## 📑 Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura do Sistema](#arquitetura-do-sistema)
3. [Tecnologias Utilizadas](#tecnologias-utilizadas)
4. [Estrutura do Banco de Dados](#estrutura-do-banco-de-dados)
5. [Configuração e Instalação](#configuração-e-instalação)
6. [Módulos do Sistema](#módulos-do-sistema)
7. [Fluxo de Autenticação](#fluxo-de-autenticação)
8. [Integração com n8n](#integração-com-n8n)
9. [Frontend](#frontend)
10. [Scripts de Importação](#scripts-de-importação)
11. [Segurança](#segurança)
12. [Troubleshooting](#troubleshooting)
13. [Manutenção](#manutenção)

---

## 🎯 Visão Geral

O Sistema de Apontamento de Horas é uma aplicação web desenvolvida para a **Booker Brasil** que permite aos colaboradores registrarem suas horas de trabalho por cliente através de uma interface conversacional (chatbot).

### Objetivos Principais

- ✅ Registro simplificado de horas através de chat
- ✅ Validação automática de clientes cadastrados
- ✅ Controle de acesso por autenticação
- ✅ Histórico completo de apontamentos
- ✅ Integração com IA para experiência natural

### Capacidade

- **Usuários:** ~80 funcionários
- **Clientes:** +600 registros
- **Grupos de Tarefas:** Múltiplas categorias
- **Apontamentos:** Ilimitados com histórico completo

---

## 🏗️ Arquitetura do Sistema

```
┌─────────────────┐
│   Navegador     │
│   (Frontend)    │
└────────┬────────┘
         │
         │ HTTP/HTTPS
         ▼
┌─────────────────┐
│  Flask Backend  │
│  (app.py)       │
└────────┬────────┘
         │
         ├─────────────────────┐
         │                     │
         ▼                     ▼
┌─────────────────┐   ┌──────────────┐
│   PostgreSQL    │   │   n8n        │
│   Database      │   │   Workflow   │
└─────────────────┘   └──────┬───────┘
                             │
                             ▼
                      ┌──────────────┐
                      │ Claude Haiku │
                      │   AI Agent   │
                      └──────────────┘
```

### Componentes Principais

1. **Frontend (HTML/CSS/JS)**
   - Interface de login
   - Interface de chat
   - Comunicação assíncrona com backend

2. **Backend (Flask)**
   - Gerenciamento de sessões
   - Autenticação de usuários
   - Proxy para n8n
   - Integração com PostgreSQL

3. **Banco de Dados (PostgreSQL)**
   - Armazenamento de usuários
   - Cadastro de clientes
   - Grupos de tarefas
   - Apontamentos

4. **Workflow (n8n)**
   - Orquestração de IA
   - Chat Memory
   - Validação de clientes
   - Registro de tarefas

5. **IA (Claude Haiku)**
   - Processamento de linguagem natural
   - Interpretação de intenções
   - Respostas conversacionais

---

## 🛠️ Tecnologias Utilizadas

### Backend
- **Python 3.x**
- **Flask 3.0.0** - Framework web
- **Flask-CORS 4.0.0** - Cross-Origin Resource Sharing
- **psycopg2-binary 2.9.11** - Driver PostgreSQL
- **python-dotenv 1.2.1** - Gerenciamento de variáveis de ambiente
- **hashlib** - Criptografia de senhas (SHA-256)
- **uuid** - Geração de session IDs únicos

### Frontend
- **HTML5**
- **CSS3** - Design responsivo com gradientes Booker
- **JavaScript (Vanilla)** - Sem frameworks, código nativo

### Banco de Dados
- **PostgreSQL** - Banco de dados relacional
- **Schema:** `apontador_horas`

### Automação
- **n8n** - Workflow automation
- **Claude Haiku (Anthropic)** - Modelo de IA

### Utilitários
- **pandas 2.3.3** - Manipulação de dados para importação
- **openpyxl 3.1.5** - Leitura de arquivos Excel
- **requests 2.31.0** - Requisições HTTP

---

## 🗄️ Estrutura do Banco de Dados

### Schema: `apontador_horas`

#### Tabela: `funcionarios`
Armazena informações dos colaboradores e credenciais de acesso.

```sql
CREATE TABLE apontador_horas.funcionarios (
    id SERIAL PRIMARY KEY,
    usuario VARCHAR(50) UNIQUE NOT NULL,
    senha_hash VARCHAR(64) NOT NULL,  -- SHA-256
    email VARCHAR(100) UNIQUE NOT NULL,
    nome_completo VARCHAR(100) NOT NULL,
    departamento VARCHAR(50),
    nivel VARCHAR(20) DEFAULT 'funcionario',
    gestor VARCHAR(100),
    gestor_id INTEGER,
    nome_gestor VARCHAR(100),
    ativo BOOLEAN DEFAULT TRUE,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Níveis de Acesso:**
- `funcionario` - Nível padrão
- `coordenador` - Coordenação de equipe
- `supervisor` - Supervisão
- `socio` - Sócio da empresa
- `prestador de servico` - Prestador externo
- `admin` - Administrador do sistema

**Índices:**
```sql
CREATE INDEX idx_funcionarios_usuario ON apontador_horas.funcionarios(usuario);
CREATE INDEX idx_funcionarios_email ON apontador_horas.funcionarios(email);
CREATE INDEX idx_funcionarios_ativo ON apontador_horas.funcionarios(ativo);
```

#### Tabela: `clientes`
Cadastro de clientes da Booker Brasil.

```sql
CREATE TABLE apontador_horas.clientes (
    num_cnpj_cpf VARCHAR(14) PRIMARY KEY,  -- 11 dígitos (CPF) ou 14 (CNPJ)
    nom_cliente VARCHAR(200) NOT NULL,
    cod_grupo_cliente INTEGER,
    des_grupo VARCHAR(100),
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Características:**
- CNPJ/CPF normalizado (apenas números)
- Suporta tanto pessoa física (CPF) quanto jurídica (CNPJ)
- Preenchimento automático com zeros à esquerda

**Índices:**
```sql
CREATE INDEX idx_clientes_nome ON apontador_horas.clientes(nom_cliente);
CREATE INDEX idx_clientes_grupo ON apontador_horas.clientes(cod_grupo_cliente);
```

#### Tabela: `grupo_tarefas`
Categorias de tarefas disponíveis.

```sql
CREATE TABLE apontador_horas.grupo_tarefas (
    cod_grupo_tarefa VARCHAR(10) PRIMARY KEY,  -- Ex: "1.01", "1.02"
    nome_grupo_tarefa VARCHAR(100) NOT NULL,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Exemplos de Códigos:**
- `1.01` - Consultoria Tributária
- `1.02` - Auditoria
- `1.10` - Compliance
- `2.01` - Gestão Contábil

#### Tabela: `tarefas_colaborador`
Atribuição de tarefas aos colaboradores por cliente.

```sql
CREATE TABLE apontador_horas.tarefas_colaborador (
    id SERIAL PRIMARY KEY,
    cnpj_cpf VARCHAR(14) NOT NULL,
    nome_empresa VARCHAR(200),
    cod_grupo_tarefa VARCHAR(10) NOT NULL,
    nome_tarefa VARCHAR(200) NOT NULL,
    colaborador_1 VARCHAR(50) NOT NULL,
    colaborador_2 VARCHAR(50),
    estimativa_horas DECIMAL(10,2),
    prioridade VARCHAR(20),
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (cnpj_cpf) REFERENCES apontador_horas.clientes(num_cnpj_cpf),
    FOREIGN KEY (cod_grupo_tarefa) REFERENCES apontador_horas.grupo_tarefas(cod_grupo_tarefa),
    FOREIGN KEY (colaborador_1) REFERENCES apontador_horas.funcionarios(usuario),
    FOREIGN KEY (colaborador_2) REFERENCES apontador_horas.funcionarios(usuario)
);
```

**Índices:**
```sql
CREATE INDEX idx_tarefas_cnpj ON apontador_horas.tarefas_colaborador(cnpj_cpf);
CREATE INDEX idx_tarefas_colaborador1 ON apontador_horas.tarefas_colaborador(colaborador_1);
CREATE INDEX idx_tarefas_grupo ON apontador_horas.tarefas_colaborador(cod_grupo_tarefa);
```

### Relacionamentos

```
funcionarios (usuario) ←─────┐
                              │
                              │ FK
                              │
tarefas_colaborador ──────────┤
      │                       │
      │ FK                    │
      ▼                       │
   clientes            colaborador_2 (FK) ──┘
      │
      │
grupo_tarefas (FK) ───┘
```

---

## ⚙️ Configuração e Instalação

### Pré-requisitos

- Python 3.8+
- PostgreSQL 12+
- n8n instalado e configurado
- Acesso à API do Claude (Anthropic)

### 1. Clonar o Repositório

```bash
git clone <seu-repositorio>
cd chatbot_apontamento_horas
```

### 2. Criar Ambiente Virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

### 3. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# Configurações do PostgreSQL
HOST_DW=seu_host_postgresql
DBNAME_DW=seu_banco
USER_DW=seu_usuario
PASS_DW=sua_senha
PORT_DW=5432

# URL do n8n
N8N_WEBHOOK_URL=https://n8n.bookerbrasil.com/webhook/[seu-webhook-id]/chat
```

### 5. Criar Schema e Tabelas no PostgreSQL

```sql
-- Criar schema
CREATE SCHEMA IF NOT EXISTS apontador_horas;

-- Criar tabelas (ver scripts completos na seção de Banco de Dados)
```

### 6. Importar Dados Iniciais

Execute os scripts de importação na seguinte ordem:

```bash
# 1. Importar clientes
python importar_clientes.py

# 2. Importar funcionários
python importar_funcionarios.py

# 3. Importar grupos de tarefas
python importar_grupo_tarefas.py

# 4. Importar tarefas por colaborador
python importar_tarefas_colaborador.py
```

### 7. Configurar n8n

1. Importe o workflow do arquivo `Chatbot_-_apontamento_horas.json`
2. Configure as credenciais do PostgreSQL
3. Configure a API Key do Claude
4. Ative o workflow

### 8. Iniciar a Aplicação

```bash
python app.py
```

A aplicação estará disponível em: `http://localhost:5000`

---

## 📦 Módulos do Sistema

### 1. `app.py` - Aplicação Principal

**Responsabilidades:**
- Gerenciamento de rotas Flask
- Autenticação de usuários
- Gerenciamento de sessões
- Proxy para n8n
- Conexão com PostgreSQL

**Rotas Principais:**

| Rota | Método | Descrição | Autenticação |
|------|--------|-----------|--------------|
| `/` | GET | Página principal (chat) | Requerida |
| `/login` | GET | Página de login | Não |
| `/api/login` | POST | Autenticar usuário | Não |
| `/api/logout` | POST | Encerrar sessão | Requerida |
| `/api/chat` | POST | Enviar mensagem ao chatbot | Requerida |
| `/api/usuario-info` | GET | Informações do usuário | Requerida |

**Funções Importantes:**

```python
def get_db_connection():
    """Cria conexão com PostgreSQL"""
    
def hash_senha(senha):
    """Gera hash SHA-256 da senha"""
    
def verificar_usuario(usuario, senha):
    """Valida credenciais no banco de dados"""
```

**Session ID Único:**
```python
# Cada login gera um session_id único para isolamento do chat memory
session_id = str(uuid.uuid4())
session['session_id'] = session_id
```

### 2. `gerenciador_funcionarios.py` - Gestão de Usuários

Script interativo para gerenciar funcionários:

**Funcionalidades:**
- ✅ Cadastrar novo funcionário
- ✅ Listar todos os funcionários
- ✅ Buscar funcionário específico
- ✅ Alterar senha
- ✅ Ativar/Desativar usuário
- ✅ Alterar departamento
- ✅ Alterar nível de acesso

**Uso:**
```bash
python gerenciador_funcionarios.py
```

**Menu Interativo:**
```
======================================================
⏱️  SISTEMA DE GERENCIAMENTO DE FUNCIONÁRIOS - BOOKER
======================================================
1 - Cadastrar novo funcionário
2 - Listar todos os funcionários
3 - Buscar funcionário
4 - Alterar senha
5 - Alterar status (ativar/desativar)
6 - Alterar departamento
7 - Alterar nível de acesso
0 - Sair
```

### 3. Scripts de Importação

#### `importar_clientes.py`
Importa cadastro de clientes de planilha Excel.

**Características:**
- Normalização de CNPJ/CPF
- Remoção de duplicatas
- Validação de dados
- Update on conflict

**Normalização de CNPJ/CPF:**
```python
def limpar_cnpj_cpf(valor):
    """
    CPF: 11 dígitos (preenche com zeros à esquerda)
    CNPJ: 14 dígitos (preenche com zeros à esquerda)
    """
    numero = str(int(valor))
    if len(numero) <= 11:
        return numero.zfill(11)  # CPF
    else:
        return numero.zfill(14)  # CNPJ
```

**Uso:**
```bash
python importar_clientes.py
```

#### `importar_funcionarios.py`
Importa funcionários com hash de senhas.

**Características:**
- Hash SHA-256 de senhas
- Validação de duplicatas (usuário e email)
- Normalização de níveis
- Senha padrão: `Booker@1010`

**Geração de Hash:**
```python
def gerar_hash_senha(senha):
    senha_str = str(senha).strip()
    return hashlib.sha256(senha_str.encode('utf-8')).hexdigest()
```

**Uso:**
```bash
python importar_funcionarios.py
```

#### `importar_grupo_tarefas.py`
Importa categorias de tarefas.

**Formato de Códigos:**
- Tipo: STRING
- Formato: `"1.01"`, `"1.02"`, etc.
- Permite códigos customizados

**Uso:**
```bash
python importar_grupo_tarefas.py
```

#### `importar_tarefas_colaborador.py`
Importa atribuições de tarefas com validação de FKs.

**Validações:**
- ✅ CNPJ existe na tabela `clientes`
- ✅ Código de grupo existe em `grupo_tarefas`
- ✅ Colaboradores existem em `funcionarios`
- ✅ Normalização de CNPJ/CPF

**Uso:**
```bash
python importar_tarefas_colaborador.py
```

---

## 🔐 Fluxo de Autenticação

### 1. Login

```
┌──────────┐
│ Usuário  │
│ digita   │
│ credenc. │
└────┬─────┘
     │
     ▼
┌────────────────┐
│ POST /api/login│
└────┬───────────┘
     │
     ▼
┌────────────────────┐
│ verificar_usuario()│
│ - Busca no banco   │
│ - Compara hash     │
└────┬───────────────┘
     │
     ▼
┌────────────────────┐
│ Gerar session_id   │
│ UUID único         │
└────┬───────────────┘
     │
     ▼
┌────────────────────┐
│ Criar sessão Flask │
│ session['usuario'] │
│ session['session_id']│
└────┬───────────────┘
     │
     ▼
┌────────────────────┐
│ Redirecionar para  │
│ página de chat     │
└────────────────────┘
```

### 2. Verificação de Senha

```python
# 1. Buscar usuário no banco
SELECT * FROM funcionarios WHERE usuario = 'joao'

# 2. Verificar se está ativo
if not user['ativo']:
    return None

# 3. Gerar hash da senha fornecida
senha_hash = hashlib.sha256(senha.encode()).hexdigest()

# 4. Comparar hashes
if user['senha_hash'] == senha_hash:
    return user  # Autenticado
else:
    return None  # Senha incorreta
```

### 3. Gerenciamento de Sessão

**Session ID Único:**
- Cada login gera um `UUID` único
- Usado para isolar conversas no n8n Chat Memory
- Permite múltiplos logins do mesmo usuário

**Dados na Sessão:**
```python
session['usuario'] = 'joao'
session['usuario_id'] = 42
session['nome_completo'] = 'João Silva'
session['nivel'] = 'funcionario'
session['departamento'] = 'Contabilidade'
session['session_id'] = 'a1b2c3d4-e5f6-...'
```

**Tempo de Expiração:**
```python
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
```

### 4. Logout

```python
@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()  # Limpa toda a sessão
    return jsonify({'success': True})
```

---

## 🤖 Integração com n8n

### Arquitetura do Workflow

```
┌─────────────┐
│ Chat Trigger│
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ AI Agent        │
│ (Claude Haiku)  │
│ + Chat Memory   │
└──────┬──────────┘
       │
       ├──────────────┐
       │              │
       ▼              ▼
┌──────────────┐  ┌──────────────┐
│ Tool:        │  │ Tool:        │
│ PostgreSQL   │  │ Google       │
│ Validation   │  │ Sheets       │
└──────────────┘  └──────────────┘
```

### Chat Trigger vs Webhook

**❌ Problema com Webhook:**
- IA Agent não seguia instruções corretamente
- Dificuldade em manter contexto
- Respostas inconsistentes

**✅ Solução com Chat Trigger:**
- IA Agent segue instruções fielmente
- Chat Memory funciona perfeitamente
- Respostas consistentes e contextualizadas

### Payload Enviado ao n8n

```json
{
  "chatInput": "iniciar tarefa de auditoria para cliente X",
  "usuario": "joao",
  "nome_completo": "João Silva",
  "usuario_id": 42,
  "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

### Chat Memory

**Configuração:**
- **Session ID:** `{{ $json.sessionId }}`
- **Tipo:** Window Buffer Memory
- **Tamanho da Janela:** Últimas 10 mensagens
- **Isolamento:** Por session_id único

**Benefícios:**
- Cada usuário tem sua própria memória
- Múltiplos logins não se misturam
- Contexto mantido durante a sessão
- Limpa automaticamente no logout

### Tools do AI Agent

#### 1. PostgreSQL - Validação de Cliente

**Função:** Validar se cliente existe e buscar informações

**Query:**
```sql
SELECT 
    num_cnpj_cpf,
    nom_cliente,
    cod_grupo_cliente,
    des_grupo
FROM apontador_horas.clientes
WHERE nom_cliente ILIKE '%{{ $json.query }}%'
ORDER BY nom_cliente
LIMIT 10
```

**Características:**
- Busca case-insensitive (ILIKE)
- Busca aproximada (aceita parte do nome)
- Retorna até 10 resultados
- Apresenta lista numerada ao usuário

**Fluxo:**
```
1. Usuário menciona cliente
   ↓
2. IA extrai nome do cliente
   ↓
3. Query no PostgreSQL
   ↓
4. Se encontrou:
   - 1 resultado: confirma e prossegue
   - 2+ resultados: lista para escolha
   ↓
5. Se não encontrou:
   - Informa que cliente não está cadastrado
   - Sugere verificar o nome
```

#### 2. Google Sheets - Registro de Tarefas

**Função:** Gravar apontamento de horas

**Colunas:**
```
| id_unico | usuario | nome_completo | cliente_cnpj | cliente_nome | 
| tarefa | grupo_tarefa | data_inicio | data_fim | duracao_horas |
```

**ID Único:**
```
formato: usuario_timestamp
exemplo: joao_20250105_143025
```

**Permite:**
- Múltiplas tarefas simultâneas por usuário
- Rastreamento individual de cada tarefa
- Histórico completo
- Análise de produtividade

### Prompts do AI Agent

**System Prompt (resumido):**
```
Você é um assistente de apontamento de horas da Booker Brasil.

ETAPAS OBRIGATÓRIAS:
1. Validar cliente usando a tool PostgreSQL
2. Perguntar o grupo de tarefa
3. Confirmar dados com o usuário
4. Registrar usando Google Sheets

IMPORTANTE:
- Sempre valide o cliente antes de registrar
- Apresente opções numeradas quando houver múltiplos resultados
- Seja claro e objetivo
- Confirme os dados antes de salvar
```

---

## 🎨 Frontend

### Estrutura de Arquivos

```
static/
├── css/
│   └── style.css
└── js/
    ├── login.js
    └── chat.js

templates/
├── login.html
└── chat.html
```

### Design System - Cores Booker

```css
/* Amarelo Booker */
--booker-yellow: #FFD500;

/* Laranja Booker */
--booker-orange: #E59230;

/* Cinza Escuro */
--booker-dark: #3F3F41;

/* Cinza Médio */
--booker-gray: #373739;

/* Gradiente Principal */
background: linear-gradient(135deg, #FFD500 0%, #E59230 100%);
```

### Página de Login (`login.html`)

**Características:**
- Design centralizado e minimalista
- Gradiente de fundo com cores Booker
- Validação de campos obrigatórios
- Mensagens de erro claras
- ~~Usuários de teste removidos~~ ✅

**Campos:**
- Usuário (text input)
- Senha (password input)

### Página de Chat (`chat.html`)

**Layout:**
```
┌─────────────────────────────────┐
│  Header (Nome + Botão Logout)   │
├─────────────────────────────────┤
│                                 │
│    Área de Mensagens            │
│    (scrollable)                 │
│                                 │
├─────────────────────────────────┤
│  Input + Botão Enviar           │
└─────────────────────────────────┘
```

**Características:**
- Mensagens do usuário: gradiente amarelo/laranja (direita)
- Mensagens do bot: fundo branco (esquerda)
- Timestamp em cada mensagem
- Indicador de digitação (3 pontos animados)
- Auto-scroll para última mensagem
- Suporte a formatação Markdown

### Formatação Markdown (`chat.js`)

**Suportado:**
- `**negrito**` → <strong>negrito</strong>
- `__itálico__` → <em>itálico</em>
- Quebras de linha (`\n`)

**Função:**
```javascript
function processarFormatacao(texto) {
    let textoSeguro = texto
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
    
    let textoFormatado = textoSeguro
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/__(.+?)__/g, '<em>$1</em>')
        .replace(/\n/g, '<br>');
    
    return textoFormatado;
}
```

### Responsividade

**Breakpoints:**
```css
@media (max-width: 768px) {
    .chat-container {
        max-width: 100%;
    }
    
    .message-content {
        max-width: 85%;
    }
}
```

---

## 📊 Scripts de Importação

### Ordem de Execução

**IMPORTANTE:** Execute nesta ordem para respeitar Foreign Keys:

```bash
1. importar_clientes.py          # Sem dependências
2. importar_funcionarios.py      # Sem dependências
3. importar_grupo_tarefas.py     # Sem dependências
4. importar_tarefas_colaborador.py  # Depende dos 3 anteriores
```

### Formato das Planilhas Excel

#### `clientes.xlsx`
```
| num_cnpj_cpf | nom_cliente | cod_grupo_cliente | des_grupo |
|--------------|-------------|-------------------|-----------|
| 12345678901  | Cliente A   | 1                 | Grupo X   |
| 98765432100123| Cliente B  | 2                 | Grupo Y   |
```

#### `Funcionarios.xlsx`
```
| usuario | senha | email | nome_completo | departamento | nivel | nome_gestor | ativo |
|---------|-------|-------|---------------|--------------|-------|-------------|-------|
| joao    | 123   | j@... | João Silva    | Contabil     | func  | Maria       | sim   |
```

#### `Grupo_tarefas.xlsx`
```
| cod_grupo_tarefa | nome_grupo_tarefa |
|------------------|-------------------|
| 1.01             | Auditoria         |
| 1.02             | Consultoria       |
```

#### `tarefas_colaborador.xlsx`
```
| cnpj_cpf | nome_empresa | cod_grupo_tarefa | nome_tarefa | colaborador_1 | colaborador_2 | estimativa_horas | prioridade |
|----------|--------------|------------------|-------------|---------------|---------------|------------------|------------|
| 12345... | Cliente X    | 1.01             | Auditoria   | joao          | maria         | 40.0             | alta       |
```

### Tratamento de Dados

#### Normalização de CNPJ/CPF

**Problema:** Excel converte números longos para notação científica

**Solução:**
```python
def normalizar_cnpj_cpf(valor):
    # Remove tudo exceto números
    apenas_numeros = re.sub(r'\D', '', str(valor))
    
    # CPF: preenche até 11 dígitos
    if len(apenas_numeros) <= 11:
        return apenas_numeros.zfill(11)
    
    # CNPJ: preenche até 14 dígitos
    else:
        return apenas_numeros.zfill(14)
```

**Exemplos:**
- `1234567890` → `01234567890` (CPF)
- `12345678000100` → `12345678000100` (CNPJ)
- `1.234567E+13` → `12345678000100` (CNPJ convertido do científico)

#### Validação de Foreign Keys

**Antes de inserir em `tarefas_colaborador`:**

```python
# 1. Buscar todos os CNPJs válidos
cnpjs_validos = set(SELECT num_cnpj_cpf FROM clientes)

# 2. Buscar todos os códigos de grupo válidos
grupos_validos = set(SELECT cod_grupo_tarefa FROM grupo_tarefas)

# 3. Buscar todos os usuários válidos
usuarios_validos = set(SELECT usuario FROM funcionarios)

# 4. Validar cada linha
if cnpj not in cnpjs_validos:
    print(f"❌ CNPJ inválido: {cnpj}")
    
if grupo not in grupos_validos:
    print(f"❌ Grupo inválido: {grupo}")
    
if colaborador1 not in usuarios_validos:
    print(f"❌ Colaborador inválido: {colaborador1}")
```

### Logs de Importação

**Exemplo de saída:**
```
[2025-01-05 14:30:15] Iniciando importação...
[2025-01-05 14:30:15] Lendo planilha...
Total de registros na planilha: 650

[2025-01-05 14:30:16] Preparando dados...
Registros após limpeza: 642

=== VERIFICAÇÃO DE DUPLICATAS ===
CNPJs únicos: 620
Total de linhas: 642
⚠️ AVISO: 22 códigos duplicados encontrados!
Mantido apenas o primeiro registro de cada código duplicado

Registros finais para importação: 620

[2025-01-05 14:30:17] Conectando ao banco de dados...
Conexão estabelecida com sucesso!

[2025-01-05 14:30:18] Inserindo dados...
[2025-01-05 14:30:19] ✔ 620 registros inseridos/atualizados com sucesso!
Total de registros na tabela: 620

[2025-01-05 14:30:19] Importação concluída!
```

---

## 🔒 Segurança

### Autenticação

#### Hash de Senhas - SHA-256

**Por que SHA-256:**
- Rápido e eficiente
- Criptograficamente seguro
- 64 caracteres hexadecimais
- Irreversível

**Implementação:**
```python
import hashlib

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

# Exemplo:
senha = "Booker@1010"
hash_gerado = "a1b2c3d4e5f6..."  # 64 caracteres
```

**Armazenamento:**
```sql
-- Senha NUNCA é armazenada em texto plano
INSERT INTO funcionarios (usuario, senha_hash)
VALUES ('joao', 'a1b2c3d4e5f6...');
```

**Verificação:**
```python
# 1. Usuário envia: "Booker@1010"
# 2. Sistema gera hash: "a1b2c3d4e5f6..."
# 3. Compara com hash do banco
if hash_gerado == hash_banco:
    # Autenticado
```

#### Sessões

**Flask Session:**
- Cookie criptografado
- Secret key aleatória (`os.urandom(24)`)
- Expiração: 2 horas
- HTTPOnly (não acessível via JavaScript)

**Session ID Único:**
- UUID v4 (universalmente único)
- Isolamento total entre usuários
- Permite múltiplos logins

### Proteção CSRF

**Flask-CORS configurado:**
```python
from flask_cors import CORS
CORS(app)
```

### SQL Injection

**Sempre usar prepared statements:**

```python
# ❌ NUNCA FAÇA ISSO:
cursor.execute(f"SELECT * FROM usuarios WHERE usuario = '{usuario}'")

# ✅ SEMPRE FAÇA ASSIM:
cursor.execute("SELECT * FROM usuarios WHERE usuario = %s", (usuario,))
```

### Variáveis de Ambiente

**Nunca versione o `.env`:**
```bash
# .gitignore
.env
*.pyc
__pycache__/
```

**Exemplo `.env.example`:**
```env
HOST_DW=localhost
DBNAME_DW=nome_banco
USER_DW=usuario
PASS_DW=senha
PORT_DW=5432
N8N_WEBHOOK_URL=https://...
```

### Validação de Input

**Frontend:**
```html
<input type="text" required minlength="3" maxlength="50">
```

**Backend:**
```python
if not mensagem or not mensagem.strip():
    return jsonify({'error': 'Mensagem vazia'}), 400
```

---

## 🐛 Troubleshooting

### Problemas Comuns

#### 1. Erro de Conexão com PostgreSQL

**Sintoma:**
```
❌ Erro ao conectar no banco: could not connect to server
```

**Soluções:**
```bash
# 1. Verificar se PostgreSQL está rodando
sudo systemctl status postgresql

# 2. Testar conexão manual
psql -h HOST -U USER -d DATABASE

# 3. Verificar .env
cat .env | grep HOST_DW

# 4. Verificar firewall
sudo ufw status
```

#### 2. Hash de Senha Não Coincide

**Sintoma:**
```
🔍 Hash gerado: abc123...
🔍 Hash no banco: def456...
❌ Senha incorreta
```

**Soluções:**
```python
# 1. Verificar encoding
senha_hash = hashlib.sha256(senha.encode('utf-8')).hexdigest()

# 2. Testar hash manualmente
python
>>> import hashlib
>>> hashlib.sha256('Booker@1010'.encode()).hexdigest()

# 3. Resetar senha
python gerenciador_funcionarios.py
# Opção 4 - Alterar senha
```

#### 3. n8n Não Responde

**Sintoma:**
```
❌ Erro: Connection timeout
```

**Soluções:**
```bash
# 1. Verificar se n8n está rodando
curl https://n8n.bookerbrasil.com/webhook/...

# 2. Verificar URL no .env
echo $N8N_WEBHOOK_URL

# 3. Testar webhook manualmente
curl -X POST https://n8n.bookerbrasil.com/webhook/... \
  -H "Content-Type: application/json" \
  -d '{"chatInput":"teste"}'

# 4. Verificar logs do n8n
```

#### 4. Session ID Não Está Isolando Conversas

**Sintoma:**
- Usuário A vê mensagens do Usuário B
- Chat Memory misturando contextos

**Verificação:**
```python
# No app.py, adicionar log:
print(f"📤 Session ID enviado: {session_id}")

# No n8n, verificar:
# Chat Memory > Session ID: {{ $json.sessionId }}
```

**Solução:**
- Verificar que o campo `sessionId` está sendo enviado no payload
- Confirmar que o Chat Memory está usando `{{ $json.sessionId }}`

#### 5. Clientes Não São Encontrados

**Sintoma:**
```
Cliente "ABC Ltda" não encontrado no banco
```

**Soluções:**
```sql
-- 1. Verificar se o cliente existe
SELECT nom_cliente 
FROM apontador_horas.clientes 
WHERE nom_cliente ILIKE '%ABC%';

-- 2. Verificar normalização do nome
SELECT nom_cliente, LENGTH(nom_cliente), nom_cliente::bytea
FROM apontador_horas.clientes
WHERE num_cnpj_cpf = '12345678000100';

-- 3. Reimportar com normalização
python importar_clientes.py
```

#### 6. Foreign Key Violation

**Sintoma:**
```
psycopg2.errors.ForeignKeyViolation: 
insert or update on table "tarefas_colaborador" 
violates foreign key constraint
```

**Soluções:**
```sql
-- 1. Verificar se o CNPJ existe
SELECT * FROM apontador_horas.clientes 
WHERE num_cnpj_cpf = '12345678000100';

-- 2. Verificar se o grupo existe
SELECT * FROM apontador_horas.grupo_tarefas 
WHERE cod_grupo_tarefa = '1.01';

-- 3. Verificar se o colaborador existe
SELECT * FROM apontador_horas.funcionarios 
WHERE usuario = 'joao';

-- 4. Importar tabelas na ordem correta
```

### Logs para Debug

#### Flask App
```python
# Adicionar no app.py:
import logging
logging.basicConfig(level=logging.DEBUG)

# Logs automáticos:
print(f"📤 [{usuario}] Session: {session_id[:8]}... → {mensagem[:50]}")
print(f"📥 Resposta do n8n: {data}")
```

#### n8n Workflow
- Ativar "Execution Logging"
- Ver histórico de execuções
- Inspecionar dados em cada nó

#### PostgreSQL
```sql
-- Habilitar log de queries
ALTER SYSTEM SET log_statement = 'all';
SELECT pg_reload_conf();

-- Ver logs
tail -f /var/log/postgresql/postgresql-14-main.log
```

---

## 🔧 Manutenção

### Backup do Banco de Dados

#### Backup Completo
```bash
# Backup de todo o banco
pg_dump -h HOST -U USER -d DATABASE > backup_$(date +%Y%m%d).sql

# Backup apenas do schema apontador_horas
pg_dump -h HOST -U USER -d DATABASE -n apontador_horas > backup_apontador_$(date +%Y%m%d).sql

# Backup compactado
pg_dump -h HOST -U USER -d DATABASE | gzip > backup_$(date +%Y%m%d).sql.gz
```

#### Backup por Tabela
```bash
# Somente clientes
pg_dump -h HOST -U USER -d DATABASE -t apontador_horas.clientes > clientes_backup.sql

# Somente funcionários (sem senhas)
psql -h HOST -U USER -d DATABASE -c "
  COPY (
    SELECT usuario, email, nome_completo, departamento, nivel, ativo
    FROM apontador_horas.funcionarios
  ) TO STDOUT WITH CSV HEADER
" > funcionarios_backup.csv
```

#### Restauração
```bash
# Restaurar backup completo
psql -h HOST -U USER -d DATABASE < backup_20250105.sql

# Restaurar backup compactado
gunzip -c backup_20250105.sql.gz | psql -h HOST -U USER -d DATABASE
```

### Limpeza de Dados Antigos

#### Logs de Sessão
```sql
-- Remover sessões antigas (se implementado log de sessões)
DELETE FROM logs_sessao 
WHERE data_criacao < NOW() - INTERVAL '90 days';
```

#### Apontamentos Arquivados
```sql
-- Criar tabela de arquivamento
CREATE TABLE apontador_horas.tarefas_arquivadas (
    LIKE apontador_horas.tarefas_colaborador INCLUDING ALL
);

-- Mover tarefas antigas
INSERT INTO apontador_horas.tarefas_arquivadas
SELECT * FROM apontador_horas.tarefas_colaborador
WHERE data_criacao < '2024-01-01';

-- Remover da tabela principal
DELETE FROM apontador_horas.tarefas_colaborador
WHERE data_criacao < '2024-01-01';
```

### Monitoramento

#### Verificar Espaço no PostgreSQL
```sql
-- Tamanho de cada tabela
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'apontador_horas'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Tamanho total do schema
SELECT 
    pg_size_pretty(SUM(pg_total_relation_size(schemaname||'.'||tablename)))
FROM pg_tables
WHERE schemaname = 'apontador_horas';
```

#### Verificar Conexões Ativas
```sql
SELECT 
    datname,
    usename,
    application_name,
    client_addr,
    state,
    query_start
FROM pg_stat_activity
WHERE datname = 'seu_banco';
```

#### Verificar Performance
```sql
-- Queries mais lentas
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    max_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

### Atualização de Dependências

```bash
# Listar pacotes desatualizados
pip list --outdated

# Atualizar um pacote específico
pip install --upgrade Flask

# Atualizar todas as dependências (cuidado!)
pip install --upgrade -r requirements.txt

# Gerar novo requirements.txt
pip freeze > requirements.txt
```

### Rotação de Logs

#### Flask Application
```python
# Adicionar no app.py:
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'logs/app.log',
    maxBytes=10485760,  # 10MB
    backupCount=10
)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
```

#### Sistema (Logrotate)
```bash
# /etc/logrotate.d/chatbot
/home/user/chatbot_apontamento_horas/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
}
```

### Checklist de Manutenção Mensal

- [ ] Backup do banco de dados
- [ ] Verificar espaço em disco
- [ ] Revisar logs de erro
- [ ] Atualizar dependências de segurança
- [ ] Verificar usuários inativos
- [ ] Limpar sessões expiradas
- [ ] Testar funcionalidades principais
- [ ] Revisar performance do banco
- [ ] Verificar integridade dos dados

---

## 📚 Referências e Recursos

### Documentação Oficial

- **Flask:** https://flask.palletsprojects.com/
- **PostgreSQL:** https://www.postgresql.org/docs/
- **n8n:** https://docs.n8n.io/
- **Claude API:** https://docs.anthropic.com/

### Bibliotecas Python

- **psycopg2:** https://www.psycopg.org/docs/
- **pandas:** https://pandas.pydata.org/docs/
- **Flask-CORS:** https://flask-cors.readthedocs.io/

### Ferramentas Úteis

- **pgAdmin:** Interface gráfica para PostgreSQL
- **Postman:** Testar APIs e webhooks
- **DBeaver:** Cliente SQL universal

---

## 📞 Suporte

Para questões técnicas ou problemas:

1. Verificar logs da aplicação
2. Consultar seção de Troubleshooting
3. Revisar configurações do `.env`
4. Testar conexões individualmente
5. Verificar status dos serviços (PostgreSQL, n8n, Flask)

---

## 📝 Changelog

### Versão Atual
- ✅ Remoção de usuários de teste da página de login
- ✅ Implementação de session_id único por login
- ✅ Migração de Webhook para Chat Trigger no n8n
- ✅ Validação de clientes via PostgreSQL tool
- ✅ Suporte a formatação Markdown no chat
- ✅ Sistema completo de importação de dados
- ✅ Autenticação com hash SHA-256
- ✅ Interface com cores da marca Booker

---

## 🎯 Próximos Passos (Roadmap)

### Funcionalidades Planejadas

1. **Relatórios**
   - Dashboard de horas por funcionário
   - Relatórios por cliente
   - Análise de produtividade

2. **Notificações**
   - Email ao finalizar tarefa
   - Alertas de horas não apontadas
   - Lembretes de tarefas pendentes

3. **Mobile**
   - PWA (Progressive Web App)
   - App nativo iOS/Android

4. **Integrações**
   - Microsoft Teams
   - Slack
   - Google Calendar

5. **Melhorias de UX**
   - Comandos rápidos
   - Atalhos de teclado
   - Tema escuro

---

**Desenvolvido para Booker Brasil**  
**Versão:** 1.0  
**Data:** Janeiro 2025

---
