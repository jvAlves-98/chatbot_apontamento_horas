# 🎯 Sistema de Apontamento de Horas - Booker Brasil

## 📋 Visão Geral

Sistema completo de gestão de horas trabalhadas desenvolvido para a **Booker Brasil**, integrando múltiplas interfaces para apontamento, controle administrativo e relatórios hierárquicos.

### Características Principais

- ✅ **Interface Multi-tarefa**: Gerenciamento simultâneo de múltiplas tarefas com cards visuais
- ✅ **Sistema Administrativo**: Controle completo de usuários e tarefas (porta 5001)
- ✅ **Relatórios Hierárquicos**: 3 níveis (Grupo → Empresa → Funcionário → Tarefas)
- ✅ **Dashboard Analítico**: Visualizações com Chart.js e métricas em tempo real
- ✅ **Integração IA**: Processamento de linguagem natural via n8n + Claude Haiku
- ✅ **Controle de Acesso**: Sistema hierárquico (Funcionário → Admin)
- ✅ **Apontamento Tardio**: Interface com abas para registro retroativo

### Capacidade do Sistema

- **Usuários**: ~80 funcionários ativos
- **Clientes**: +600 empresas cadastradas
- **Tarefas**: Sistema normalizado com IDs preservados
- **Apontamentos**: Histórico completo com integridade referencial

---

## 🏗️ Arquitetura

```
┌─────────────────┐
│   Navegador     │
│   (Frontend)    │
└────────┬────────┘
         │ HTTP/HTTPS
         ▼
┌─────────────────┐
│  Flask Apps     │
│  Porto 5000     │ ← App Principal (Apontamento)
│  Porto 5001     │ ← App Admin (Gestão)
└────────┬────────┘
         │
         ├───────────────────────┐
         │                       │
         ▼                       ▼
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

### Componentes

1. **App Principal (5000)** - Apontamento de horas
2. **App Administrativo (5001)** - Gestão de usuários e tarefas
3. **PostgreSQL** - Banco de dados normalizado
4. **n8n Workflow** - Orquestração e IA
5. **Frontend Responsivo** - HTML/CSS/JS vanilla

---

## 🛠️ Tecnologias

### Backend
```
Python 3.8+
Flask 3.0.0
Flask-CORS 4.0.0
psycopg2-binary 2.9.11
python-dotenv 1.2.1
openpyxl 3.1.5 (relatórios Excel)
```

### Frontend
```
HTML5 + CSS3 (Design System Booker)
JavaScript Vanilla
Chart.js (visualizações)
```

### Database
```
PostgreSQL 12+
Schema: apontador_horas
```

### Integração
```
n8n (workflow automation)
Claude Haiku 4.5 (IA)
```

---

## 📊 Estrutura do Banco de Dados

### Tabelas Principais

#### `funcionarios`
```sql
id, usuario, senha_hash, email, nome_completo, 
departamento, nivel, gestor, gestor_id, nome_gestor, 
ativo, data_criacao
```

**Níveis**: `funcionario`, `coordenador`, `supervisor`, `socio`, `prestador de servico`, `admin`

#### `clientes`
```sql
num_cnpj_cpf (PK), nom_cliente, cod_grupo_cliente, 
des_grupo, data_criacao
```

#### `grupo_tarefas`
```sql
cod_grupo_tarefa (PK), nome_grupo_tarefa, data_criacao
```

#### `tarefas_colaborador`
```sql
id (PK), cnpj_cpf (FK), cod_grupo_tarefa (FK), 
nome_tarefa, colaborador_1 (FK), colaborador_2 (FK), 
estimativa_horas, prioridade, data_criacao
```

#### `apontamentos_horas`
```sql
id (PK), usuario (FK), usuario_id, tarefa_id (FK), 
cliente_cnpj (FK), grupo_tarefa_codigo (FK), 
data_inicio, data_fim, horas_trabalhadas, 
status, observacoes
```

#### `pausas_tarefa`
```sql
id (PK), apontamento_id (FK), data_inicio_pausa, 
data_fim_pausa, duracao_minutos
```

### Relacionamentos

```
funcionarios
    ↓ (FK usuario)
tarefas_colaborador
    ↓ (FK cnpj_cpf, cod_grupo_tarefa, tarefa_id)
apontamentos_horas
    ↓ (FK apontamento_id)
pausas_tarefa
```

**IMPORTANTE**: IDs de tarefas são preservados para manter histórico.

---

## 🎨 Interface Multi-tarefa (App Principal)

### Layout de Cards

#### Card de Tarefa Ativa
```
┌─────────────────────────────────┐
│ 🏢 Cliente: ACME Corp           │
│ 📋 Tarefa: Consultoria Fiscal   │
│ 🕒 Início: 14:30:00             │
│ ⏱️ Duração: 02:15:30            │
│ ⏸️ Pausado: 00:05:00            │
│                                 │
│ [⏸️ Pausar] [✅ Finalizar]     │
└─────────────────────────────────┘
```

#### Múltiplas Tarefas
- Gerenciamento visual de até 5 tarefas simultâneas
- Timer individual por tarefa
- Controle de pausas independente
- Finalização com confirmação

### Recursos Visuais

- **Timer em Tempo Real**: Atualização a cada segundo
- **Busca de Clientes**: Autocompletar com CNPJ formatado
- **Status Visual**: Cores por estado (ativa, pausada, finalizada)
- **Confirmações**: Dialogs para ações críticas
- **Feedback Instantâneo**: Toasts e animações

### Apontamento Tardio

Interface com abas para registro retroativo:
- **Data Selecionada**: Escolha do dia
- **Cliente e Tarefa**: Seleção via dropdown
- **Horários**: Início e fim manuais
- **Validações**: Sobreposição e limites

---

## 👨‍💼 Sistema Administrativo (Porta 5001)

### Dashboard

```
┌──────────────────────────────────────────┐
│  📊 DASHBOARD ADMINISTRATIVO             │
├──────────────────────────────────────────┤
│                                          │
│  Usuários Ativos: 78                     │
│  Tarefas Ativas: 156                     │
│  Clientes: 642                           │
│                                          │
│  [Gráfico de Horas] [Top Colaboradores]  │
│                                          │
└──────────────────────────────────────────┘
```

### Funcionalidades Admin

#### Gestão de Usuários
- ✅ Listar, criar, editar, desativar
- ✅ Definir níveis de acesso
- ✅ Configurar hierarquia (gestor)
- ✅ Reset de senha (hash SHA-256)

#### Gestão de Tarefas
- ✅ CRUD completo de tarefas
- ✅ Atribuição a colaboradores (1 e 2)
- ✅ Definir prioridades e estimativas
- ✅ Vincular a clientes e grupos

#### Controles
- ✅ Acesso restrito (Admin/Sócio)
- ✅ Logs de alterações
- ✅ Interface responsiva

---

## 📈 Sistema de Relatórios

### Relatórios Hierárquicos (3 Níveis)

#### Nível 1: Grupo de Clientes
```sql
SELECT des_grupo, SUM(horas) as total_horas
FROM apontamentos_horas a
JOIN clientes c ON a.cliente_cnpj = c.num_cnpj_cpf
GROUP BY des_grupo
```

#### Nível 2: Empresa dentro do Grupo
```sql
-- Drill-down por cliente específico
```

#### Nível 3: Funcionário dentro da Empresa
```sql
-- Detalhamento por colaborador e tarefa
```

### Filtros Disponíveis

- **Período**: Data início/fim, últimos 7/30 dias
- **Departamento**: Filtro por área
- **Funcionário**: Individual ou múltiplo
- **Cliente**: Por CNPJ ou grupo
- **Tarefa**: Por código de grupo
- **Status**: Finalizada, em andamento

### Visualizações

#### Dashboard com Chart.js
```javascript
// Gráfico de barras - Horas por funcionário
// Gráfico de pizza - Distribuição por cliente
// Gráfico de linhas - Tendência temporal
```

### Exportação

**Excel (XLSX)**:
- Formatação automática
- Múltiplas planilhas (por nível)
- Fórmulas calculadas
- Estilos Booker

---

## 🔐 Sistema de Autenticação

### Fluxo de Login

1. **Usuário acessa sistema**
2. **Credenciais validadas** (hash SHA-256)
3. **Session ID único** gerado (UUID)
4. **Nível de acesso** verificado
5. **Redirecionamento** para interface apropriada

### Hierarquia de Acesso

| Nível | Permissões |
|-------|-----------|
| `funcionario` | Apenas próprios apontamentos |
| `coordenador` | Subordinados diretos |
| `supervisor` | Equipe completa |
| `socio` | Todos usuários e relatórios |
| `admin` | Gestão completa do sistema |

### Segurança

- ✅ **Senhas**: Hash SHA-256 (não reversível)
- ✅ **Sessões**: Timeout de 2 horas
- ✅ **SQL Injection**: Prepared statements
- ✅ **XSS**: Sanitização de inputs
- ✅ **CORS**: Configurado apropriadamente

---

## 🚀 Instalação e Configuração

### 1. Pré-requisitos

```bash
# Versões necessárias
Python 3.8+
PostgreSQL 12+
n8n (latest)
```

### 2. Clonar Repositório

```bash
git clone <seu-repositorio>
cd sistema-apontamento-horas
```

### 3. Ambiente Virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 4. Dependências

```bash
pip install -r requirements.txt
```

### 5. Variáveis de Ambiente

Criar arquivo `.env`:

```env
# PostgreSQL
HOST_DW=localhost
DBNAME_DW=seu_banco
USER_DW=seu_usuario
PASS_DW=sua_senha
PORT_DW=5432

# n8n Webhook
N8N_WEBHOOK_URL=https://n8n.bookerbrasil.com/webhook/[id]/chat
```

### 6. Banco de Dados

```bash
# Executar scripts de criação
psql -h HOST -U USER -d DATABASE -f scripts/create_schema.sql
psql -h HOST -U USER -d DATABASE -f scripts/create_tables.sql
```

### 7. Importar Dados Iniciais

```bash
# Na ordem:
python importar_funcionarios.py
python importar_clientes.py
python importar_grupo_tarefas.py
python importar_tarefas_colaborador.py
```

### 8. Iniciar Aplicações

```bash
# Terminal 1 - App Principal
python app.py
# Acesso: http://localhost:5000

# Terminal 2 - App Admin
python admin_app.py
# Acesso: http://localhost:5001
```

---

## 📁 Estrutura de Arquivos

```
sistema-apontamento-horas/
├── app.py                          # App principal (5000)
├── admin_app.py                    # App admin (5001)
├── requirements.txt                # Dependências
├── .env                            # Variáveis (não commitar)
│
├── templates/                      # Templates HTML
│   ├── login.html
│   ├── chat.html                   # Interface multi-tarefa
│   ├── admin_login.html
│   ├── admin_dashboard.html
│   ├── admin_usuarios.html
│   ├── admin_tarefas.html
│   ├── admin_usuario_form.html
│   └── admin_tarefa_form.html
│
├── static/
│   ├── css/
│   │   └── style.css              # Design System Booker
│   └── js/
│       ├── login.js
│       ├── chat.js                # Lógica multi-tarefa
│       ├── dashboard.js           # Visualizações Chart.js
│       └── relatorios.js          # Sistema de relatórios
│
├── scripts/                        # Scripts de importação
│   ├── importar_funcionarios.py
│   ├── importar_clientes.py
│   ├── importar_grupo_tarefas.py
│   └── importar_tarefas_colaborador.py
│
├── data/                           # Arquivos Excel
│   ├── Funcionarios.xlsx
│   ├── clientes.xlsx
│   ├── Grupo_tarefas.xlsx
│   └── tarefas_colaborador.xlsx
│
└── docs/
    ├── README.md                   # Este arquivo
    └── DOCUMENTACAO_COMPLETA.md    # Doc técnica detalhada
```

---

## 🎯 Fluxos de Uso

### 1. Apontamento Normal (Multi-tarefa)

```
1. Login no sistema (porta 5000)
2. Buscar cliente (autocompletar)
3. Selecionar tarefa do dropdown
4. Clicar "🚀 Iniciar Tarefa"
5. Timer inicia automaticamente
6. [Opcional] Pausar/Retomar
7. Finalizar quando concluir
8. Confirmar no dialog
9. Sistema registra com cálculo automático
```

### 2. Apontamento Tardio

```
1. Acessar aba "Apontamento Tardio"
2. Selecionar data passada
3. Escolher cliente e tarefa
4. Informar horário início e fim
5. Adicionar observações (opcional)
6. Confirmar registro
7. Sistema valida e salva
```

### 3. Gestão Administrativa

```
1. Login admin (porta 5001)
2. Dashboard com visão geral
3. Gerenciar usuários:
   - Criar novo
   - Editar existente
   - Desativar/Reativar
4. Gerenciar tarefas:
   - Atribuir a colaboradores
   - Definir prioridades
   - Ajustar estimativas
```

### 4. Geração de Relatórios

```
1. Acessar seção "Relatórios"
2. Aplicar filtros desejados:
   - Período
   - Funcionário
   - Cliente
   - Departamento
3. Escolher visualização:
   - Hierárquica (3 níveis)
   - Detalhada
   - Dashboard
4. Exportar para Excel (XLSX)
```

---

## 🔧 API Endpoints

### App Principal (5000)

#### Autenticação
```
POST /login
POST /logout
```

#### Tarefas
```
POST /api/buscar-clientes
POST /api/buscar-tarefas
POST /api/iniciar-tarefa
POST /api/pausar-tarefa
POST /api/retomar-tarefa
POST /api/finalizar-tarefa
GET  /api/verificar-tarefa-ativa
GET  /api/listar-tarefas-ativas
```

#### Apontamento Tardio
```
POST /api/registrar-horas-manual
POST /api/validar-horario
```

#### Relatórios
```
POST /api/relatorios/dados
POST /api/relatorios/exportar-excel
GET  /api/relatorios/filtros
```

### App Admin (5001)

#### Usuários
```
GET    /admin/usuarios
GET    /admin/usuarios/novo
POST   /admin/usuarios/criar
GET    /admin/usuarios/<id>/editar
POST   /admin/usuarios/<id>/atualizar
POST   /admin/usuarios/<id>/desativar
```

#### Tarefas
```
GET    /admin/tarefas
GET    /admin/tarefas/nova
POST   /admin/tarefas/criar
GET    /admin/tarefas/<id>/editar
POST   /admin/tarefas/<id>/atualizar
DELETE /admin/tarefas/<id>/deletar
```

---

## 🎨 Design System Booker

### Cores

```css
--booker-yellow: #FFD500
--booker-orange: #E59230
--booker-dark-gray: #3F3F41
--booker-medium-gray: #373739
--booker-light-gray: #F5F5F5

/* Status */
--status-ativa: #4CAF50
--status-pausada: #FF9800
--status-finalizada: #757575
```

### Componentes

- **Cards**: Border-radius 8-12px, sombra suave
- **Botões**: Gradientes, hover com elevação
- **Inputs**: Border-bottom animado
- **Toasts**: Notificações não-intrusivas
- **Modals**: Confirmações elegantes

### Responsividade

```css
/* Desktop: Layout 70/30 */
@media (min-width: 1200px)

/* Tablet: Stack com prioridade */
@media (min-width: 768px) and (max-width: 1199px)

/* Mobile: Full stack */
@media (max-width: 767px)
```

---

## 🐛 Troubleshooting

### Problema: Timer não inicia

**Causa**: JavaScript com erro
```javascript
// Verificar console do navegador (F12)
// Procurar por erros em chat.js
```

**Solução**: 
```bash
# Limpar cache do navegador
Ctrl + Shift + Delete

# Verificar arquivo chat.js está correto
```

### Problema: Cliente não aparece na busca

**Causa**: CNPJ não normalizado
```sql
-- Verificar formato no banco
SELECT num_cnpj_cpf, nom_cliente 
FROM apontador_horas.clientes 
WHERE nom_cliente ILIKE '%termo%';
```

**Solução**:
```bash
# Reimportar clientes com normalização
python importar_clientes.py
```

### Problema: Foreign Key Violation

**Causa**: Ordem incorreta de importação
```
Ordem correta:
1. funcionarios
2. clientes
3. grupo_tarefas
4. tarefas_colaborador
```

**Solução**:
```bash
# Limpar e reimportar na ordem
python scripts/limpar_dados.py
python importar_funcionarios.py
# ... sequência completa
```

### Problema: Relatório vazio

**Causa**: Filtros muito restritivos ou sem dados

**Verificação**:
```sql
-- Contar apontamentos no período
SELECT COUNT(*) 
FROM apontador_horas.apontamentos_horas
WHERE data_inicio BETWEEN '2024-01-01' AND '2024-12-31';
```

### Problema: Session timeout

**Causa**: Inatividade > 2 horas

**Solução**:
```python
# Ajustar em app.py
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=4)
```

---

## 📊 Monitoramento

### Métricas Importantes

```sql
-- Usuários ativos hoje
SELECT COUNT(DISTINCT usuario) 
FROM apontador_horas.apontamentos_horas
WHERE DATE(data_inicio) = CURRENT_DATE;

-- Total de horas apontadas (mês)
SELECT SUM(horas_trabalhadas)
FROM apontador_horas.apontamentos_horas
WHERE data_inicio >= DATE_TRUNC('month', CURRENT_DATE);

-- Top 5 colaboradores (horas)
SELECT f.nome_completo, SUM(a.horas_trabalhadas) as total
FROM apontador_horas.apontamentos_horas a
JOIN apontador_horas.funcionarios f ON a.usuario = f.usuario
WHERE data_inicio >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY f.nome_completo
ORDER BY total DESC
LIMIT 5;
```

### Logs

```bash
# Logs do Flask
tail -f logs/app.log

# Logs do PostgreSQL
tail -f /var/log/postgresql/postgresql-14-main.log

# Logs do n8n
# Acessar interface web do n8n
```

---

## 🔄 Backup e Manutenção

### Backup Diário

```bash
#!/bin/bash
# backup_diario.sh

DATA=$(date +%Y%m%d)
DIR_BACKUP="/backups/apontamento"

# Backup do schema completo
pg_dump -h HOST -U USER -d DATABASE \
  -n apontador_horas \
  -f "$DIR_BACKUP/backup_$DATA.sql"

# Compactar
gzip "$DIR_BACKUP/backup_$DATA.sql"

# Manter últimos 30 dias
find $DIR_BACKUP -name "*.sql.gz" -mtime +30 -delete
```

### Limpeza Mensal

```sql
-- Arquivar apontamentos antigos (> 1 ano)
INSERT INTO apontador_horas.apontamentos_arquivados
SELECT * FROM apontador_horas.apontamentos_horas
WHERE data_inicio < CURRENT_DATE - INTERVAL '1 year';

-- Remover após confirmação
DELETE FROM apontador_horas.apontamentos_horas
WHERE data_inicio < CURRENT_DATE - INTERVAL '1 year';

-- Vacuum
VACUUM ANALYZE apontador_horas.apontamentos_horas;
```

---

## 📈 Roadmap

### Próximas Funcionalidades

#### Q1 2025
- [ ] PWA (Progressive Web App) para mobile
- [ ] Notificações push (tarefas pendentes)
- [ ] Integração Microsoft Teams
- [ ] Relatórios com BI avançado

#### Q2 2025
- [ ] App nativo iOS/Android
- [ ] Reconhecimento de voz para apontamento
- [ ] Dashboard executivo em tempo real
- [ ] API pública documentada

#### Q3 2025
- [ ] Machine Learning para sugestão de tarefas
- [ ] Integração com sistemas de billing
- [ ] Gamificação (ranking, badges)
- [ ] Modo offline com sincronização

---

## 📞 Suporte

### Canais de Suporte

- **Técnico**: Verificar logs e documentação
- **Funcional**: Consultar seção de uso
- **Banco de Dados**: Ver troubleshooting

### Checklist de Debug

1. ✅ Logs do Flask (terminal)
2. ✅ Console do navegador (F12)
3. ✅ Logs do PostgreSQL
4. ✅ Status do n8n workflow
5. ✅ Conectividade de rede
6. ✅ Variáveis de ambiente (.env)

---

## 📝 Changelog

### Versão 3.0 (Dezembro 2024)
- ✅ Interface multi-tarefa com cards
- ✅ Sistema administrativo completo (porta 5001)
- ✅ Relatórios hierárquicos (3 níveis)
- ✅ Dashboard com Chart.js
- ✅ Apontamento tardio com validações
- ✅ Exportação para Excel (XLSX)
- ✅ Controle de acesso hierárquico
- ✅ Normalização do banco de dados

### Versão 2.0 (Novembro 2024)
- ✅ Interface de 2 colunas (70/30)
- ✅ Timer em tempo real
- ✅ Sistema de pausas
- ✅ Busca inteligente de clientes
- ✅ Persistência de sessão

### Versão 1.0 (Outubro 2024)
- ✅ Chat básico com n8n
- ✅ Autenticação SHA-256
- ✅ Integração PostgreSQL
- ✅ Design System Booker

---

## 🤝 Contribuindo

### Guidelines

1. Seguir padrões do Design System Booker
2. Manter compatibilidade com versões anteriores
3. Documentar mudanças no banco de dados
4. Testar em múltiplos navegadores
5. Preservar IDs de tarefas (histórico)

### Desenvolvimento

```bash
# Criar branch
git checkout -b feature/nova-funcionalidade

# Desenvolver e testar
python app.py  # Porta 5000
python admin_app.py  # Porta 5001

# Commit com mensagem descritiva
git commit -m "feat: adiciona funcionalidade X"

# Push e Pull Request
git push origin feature/nova-funcionalidade
```

---

## 📄 Licença

Sistema proprietário desenvolvido para **Booker Brasil**.  
Todos os direitos reservados © 2024-2025

---

## 👥 Créditos

**Desenvolvido por**: João Vitor  
**Para**: Booker Brasil  
**Período**: Outubro 2024 - Dezembro 2024  
**Versão Atual**: 3.0

---

**🚀 Sistema em Produção desde Outubro/2024**  
**📊 +600 clientes | 80 usuários ativos | Milhares de apontamentos registrados**