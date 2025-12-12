// ========================================
// VARIÁVEIS GLOBAIS
// ========================================
let activeTasks = []; // Array para múltiplas tarefas
let taskTimers = {}; // Objeto para guardar os timers de cada tarefa

// ========================================
// ELEMENTOS DO DOM
// ========================================
const chatMessages = document.getElementById('chatMessages');
const chatForm = document.getElementById('chatForm');
const mensagemInput = document.getElementById('mensagemInput');
const btnLogout = document.getElementById('btnLogout');
const typingIndicator = document.getElementById('typing-indicator');

// Elementos de controle de tarefas
const taskForm = document.getElementById('taskForm');
const clientSearch = document.getElementById('clientSearch');
const clientResults = document.getElementById('clientResults');
const selectedClientCNPJ = document.getElementById('selectedClientCNPJ');
const selectedClientName = document.getElementById('selectedClientName');
const selectedClientDisplay = document.getElementById('selectedClientDisplay');
const selectedClientText = document.getElementById('selectedClientText');
const clearClientBtn = document.getElementById('clearClient');
const taskSelect = document.getElementById('taskSelect');
const btnStartTask = document.getElementById('btnStartTask');
const taskObservacao = document.getElementById('taskObservacao');
const taskObsCounter = document.getElementById('taskObsCounter');
const lateObservacao = document.getElementById('lateObservacao');
const lateObsCounter = document.getElementById('lateObsCounter');

// Container de tarefas
const tasksContainer = document.getElementById('tasksContainer');
const noTasksMessage = document.getElementById('noTasksMessage');

// ========================================
// FUNÇÕES DE CHAT
// ========================================

// Função para atualizar contador de caracteres
function atualizarContador(textarea, counter) {
    const length = textarea.value.length;
    const maxLength = textarea.getAttribute('maxlength') || 1000;
    counter.textContent = length;
    
    // Adicionar classe de aviso quando próximo do limite
    const counterContainer = counter.parentElement;
    if (length >= maxLength * 0.9) {
        counterContainer.classList.add('limit-reached');
    } else {
        counterContainer.classList.remove('limit-reached');
    }
}

// Event listeners para contadores
if (taskObservacao && taskObsCounter) {
    taskObservacao.addEventListener('input', () => {
        atualizarContador(taskObservacao, taskObsCounter);
    });
}

if (lateObservacao && lateObsCounter) {
    lateObservacao.addEventListener('input', () => {
        atualizarContador(lateObservacao, lateObsCounter);
    });
}

function processarFormatacao(texto) {
    let textoSeguro = texto
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    
    let textoFormatado = textoSeguro
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/__(.+?)__/g, '<em>$1</em>')
        .replace(/\n/g, '<br>');
    
    return textoFormatado;
}

function adicionarMensagem(texto, tipo, tempo = new Date()) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${tipo}-message`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    const p = document.createElement('p');
    const textoFormatado = processarFormatacao(texto);
    p.innerHTML = textoFormatado;
    
    contentDiv.appendChild(p);
    
    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = formatarHora(tempo);
    
    messageDiv.appendChild(contentDiv);
    messageDiv.appendChild(timeDiv);
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function formatarHora(data) {
    return data.toLocaleTimeString('pt-BR', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
}

function mostrarDigitando(mostrar) {
    typingIndicator.style.display = mostrar ? 'block' : 'none';
    if (mostrar) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

// ========================================
// BUSCA DE CLIENTES
// ========================================
let searchTimeout = null;

clientSearch.addEventListener('input', function() {
    const query = this.value.trim();
    
    clearTimeout(searchTimeout);
    
    if (query.length < 2) {
        clientResults.classList.remove('show');
        return;
    }
    
    searchTimeout = setTimeout(() => {
        buscarClientes(query);
    }, 300);
});

async function buscarClientes(query) {
    try {
        const response = await fetch('/api/buscar-clientes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query })
        });
        
        const data = await response.json();
        
        if (data.success) {
            mostrarResultadosClientes(data.clientes);
        }
    } catch (error) {
        console.error('Erro ao buscar clientes:', error);
    }
}

function mostrarResultadosClientes(clientes) {
    clientResults.innerHTML = '';
    
    if (clientes.length === 0) {
        clientResults.innerHTML = '<div class="no-results">Nenhum cliente encontrado</div>';
        clientResults.classList.add('show');
        return;
    }
    
    clientes.forEach(cliente => {
        const item = document.createElement('div');
        item.className = 'search-result-item';
        item.innerHTML = `
            <span class="client-name">${cliente.nom_cliente}</span>
            <span class="client-cnpj">CNPJ: ${formatarCNPJ(cliente.num_cnpj_cpf)}</span>
        `;
        
        item.addEventListener('click', () => {
            selecionarCliente(cliente);
        });
        
        clientResults.appendChild(item);
    });
    
    clientResults.classList.add('show');
}

function selecionarCliente(cliente) {
    selectedClientCNPJ.value = cliente.num_cnpj_cpf;
    selectedClientName.value = cliente.nom_cliente;
    
    selectedClientText.textContent = cliente.nom_cliente;
    selectedClientDisplay.style.display = 'flex';
    
    clientSearch.value = '';
    clientResults.classList.remove('show');
    
    carregarTarefasCliente(cliente.num_cnpj_cpf);
}

clearClientBtn.addEventListener('click', () => {
    selectedClientCNPJ.value = '';
    selectedClientName.value = '';
    selectedClientDisplay.style.display = 'none';
    
    taskSelect.innerHTML = '<option value="">Selecione um cliente primeiro</option>';
    taskSelect.disabled = true;
    btnStartTask.disabled = true;
});

function formatarCNPJ(cnpj) {
    if (!cnpj) return '';
    if (cnpj.length === 11) {
        return cnpj.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
    }
    return cnpj.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5');
}

// ========================================
// CARREGAR TAREFAS DO CLIENTE
// ========================================
async function carregarTarefasCliente(cnpj) {
    try {
        const response = await fetch('/api/buscar-tarefas', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ cnpj })
        });
        
        const data = await response.json();
        
        if (data.success) {
            preencherSelectTarefas(data.tarefas);
        }
    } catch (error) {
        console.error('Erro ao buscar tarefas:', error);
        adicionarMensagem('Erro ao buscar tarefas do cliente', 'bot');
    }
}

function preencherSelectTarefas(tarefas) {
    taskSelect.innerHTML = '<option value="">Selecione uma tarefa</option>';
    
    if (tarefas.length === 0) {
        taskSelect.innerHTML = '<option value="">Nenhuma tarefa disponível</option>';
        taskSelect.disabled = true;
        btnStartTask.disabled = true;
        return;
    }
    
    tarefas.forEach(tarefa => {
        const option = document.createElement('option');
        option.value = JSON.stringify({
            id: tarefa.id,
            nome_tarefa: tarefa.nome_tarefa,
            cod_grupo_tarefa: tarefa.cod_grupo_tarefa,
            prioridade: tarefa.prioridade
        });
        option.textContent = `${tarefa.nome_tarefa} (${tarefa.prioridade || 'Sem prioridade'})`;
        taskSelect.appendChild(option);
    });
    
    taskSelect.disabled = false;
}

taskSelect.addEventListener('change', function() {
    btnStartTask.disabled = !this.value;
});

// ========================================
// CRIAR CARD DE TAREFA
// ========================================
function criarCardTarefa(task) {
    console.log('🏗️ Criando card para tarefa:', {
        apontamento_id: task.id,
        tarefa_nome: task.tarefa,
        cliente: task.cliente
    });
    
    const card = document.createElement('div');
    card.className = 'task-card';
    card.id = `task-${task.id}`;
    
    if (task.status === 'pausado') {
        card.classList.add('paused');
    }
    
    card.innerHTML = `
        <div class="task-card-header">
            <div class="task-card-client">${task.cliente}</div>
            <div class="task-card-status">${task.status === 'pausado' ? '⏸️' : '▶️'}</div>
        </div>
        
        <div class="task-card-task">${task.tarefa}</div>
        
        <div class="task-card-timer" id="timer-${task.id}">00:00:00</div>
        
        <div class="task-card-start">Início: ${formatarHora(task.startTime)}</div>
        
        <div class="task-card-actions">
            ${task.status === 'pausado' ? 
                `<button class="task-card-btn btn-resume" onclick="retomarTarefa(${task.id})">
                    ▶️ Retomar
                </button>` : 
                `<button class="task-card-btn btn-pause" onclick="pausarTarefa(${task.id})">
                    ⏸️ Pausar
                </button>`
            }
            <button class="task-card-btn btn-finish" onclick="finalizarTarefa(${task.id})">
                ✅ Finalizar
            </button>
        </div>
    `;
    
    console.log(`✅ Card criado: task-${task.id} | Botões com ID: ${task.id}`);
    
    return card;
}

// ========================================
// ATUALIZAR UI DE TAREFAS
// ========================================
function atualizarUITarefas() {
    if (activeTasks.length === 0) {
        noTasksMessage.style.display = 'block';
    } else {
        noTasksMessage.style.display = 'none';
    }
}

function adicionarTaskCard(task) {
    const card = criarCardTarefa(task);
    tasksContainer.appendChild(card);
    atualizarUITarefas();
    
    // Iniciar timer
    iniciarTimerTarefa(task.id, task.startTime, task.totalPausedTime, task.pauseStartTime);
}

function removerTaskCard(taskId) {
    const card = document.getElementById(`task-${taskId}`);
    if (card) {
        card.remove();
    }
    pararTimerTarefa(taskId);
    atualizarUITarefas();
}

// ========================================
// INICIAR TAREFA
// ========================================
taskForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    if (!selectedClientCNPJ.value || !taskSelect.value) return;
    
    const tarefaData = JSON.parse(taskSelect.value);
    
    btnStartTask.disabled = true;
    btnStartTask.textContent = 'Iniciando...';
    
    try {
        const response = await fetch('/api/iniciar-tarefa', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
            cnpj_cliente: selectedClientCNPJ.value,
            nome_cliente: selectedClientName.value,
            tarefa_id: tarefaData.id,
            nome_tarefa: tarefaData.nome_tarefa,
            observacao: taskObservacao ? taskObservacao.value.trim() : ''
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const newTask = {
                id: data.apontamento_id,
                cliente: selectedClientName.value,
                tarefa: tarefaData.nome_tarefa,
                cnpj: selectedClientCNPJ.value,
                startTime: new Date(data.data_inicio),
                totalPausedTime: 0,
                pauseStartTime: null,
                status: 'em_andamento'
            };
            
            console.log('➕ Adicionando tarefa ao activeTasks:', {
                apontamento_id: newTask.id,
                tarefa_id_original: tarefaData.id,
                nome_tarefa: newTask.tarefa
            });
            
            activeTasks.push(newTask);
            adicionarTaskCard(newTask);
            
            adicionarMensagem(`Tarefa iniciada: ${tarefaData.nome_tarefa} para ${selectedClientName.value}`, 'bot');
            
            clearClientBtn.click();

            // Limpar campo de observação
            if (taskObservacao) {
                taskObservacao.value = '';
                if (taskObsCounter) {
                    taskObsCounter.textContent = '0';
                }
            }

        } else {
            adicionarMensagem('Erro ao iniciar tarefa: ' + data.message, 'bot');
        }
    } catch (error) {
        console.error('Erro ao iniciar tarefa:', error);
        adicionarMensagem('Erro ao iniciar tarefa. Tente novamente.', 'bot');
    } finally {
        btnStartTask.disabled = false;
        btnStartTask.textContent = '🚀 Iniciar Tarefa';
    }
});

// ========================================
// CONTROLE DE TIMERS
// ========================================
function iniciarTimerTarefa(taskId, startTime, totalPausedTime, pauseStartTime) {
    if (taskTimers[taskId]) {
        clearInterval(taskTimers[taskId]);
    }
    
    taskTimers[taskId] = setInterval(() => {
        const timerElement = document.getElementById(`timer-${taskId}`);
        if (!timerElement) {
            clearInterval(taskTimers[taskId]);
            return;
        }
        
        const agora = new Date();
        let tempoDecorrido = agora - startTime;
        
        if (pauseStartTime) {
            tempoDecorrido -= (agora - pauseStartTime);
        } else {
            tempoDecorrido -= totalPausedTime;
        }
        
        timerElement.textContent = formatarDuracao(tempoDecorrido);
    }, 1000);
}

function pararTimerTarefa(taskId) {
    if (taskTimers[taskId]) {
        clearInterval(taskTimers[taskId]);
        delete taskTimers[taskId];
    }
}

function formatarDuracao(ms) {
    const segundos = Math.floor(ms / 1000);
    const horas = Math.floor(segundos / 3600);
    const minutos = Math.floor((segundos % 3600) / 60);
    const segs = segundos % 60;
    
    return `${String(horas).padStart(2, '0')}:${String(minutos).padStart(2, '0')}:${String(segs).padStart(2, '0')}`;
}

// ========================================
// PAUSAR TAREFA
// ========================================
window.pausarTarefa = async function(taskId) {
    // ✅ Garantir que taskId é number
    taskId = Number(taskId);
    
    console.log('🔵 Pausando tarefa:', taskId);
    
    try {
        const response = await fetch('/api/pausar-tarefa', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ apontamento_id: taskId })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const task = activeTasks.find(t => t.id === taskId);
            if (task) {
                task.pauseStartTime = new Date();
                task.status = 'pausado';
                
                // ✅ PARAR O TIMER!
                pararTimerTarefa(taskId);
                console.log('⏹️ Timer parado para tarefa:', taskId);
                
                // Atualizar card
                const card = document.getElementById(`task-${taskId}`);
                if (card) {
                    card.classList.add('paused');
                    card.querySelector('.task-card-status').textContent = '⏸️';
                    
                    const actions = card.querySelector('.task-card-actions');
                    actions.innerHTML = `
                        <button class="task-card-btn btn-resume" onclick="retomarTarefa(${taskId})">
                            ▶️ Retomar
                        </button>
                        <button class="task-card-btn btn-finish" onclick="finalizarTarefa(${taskId})">
                            ✅ Finalizar
                        </button>
                    `;
                }
            }
            
            adicionarMensagem('Tarefa pausada', 'bot');
        }
    } catch (error) {
        console.error('Erro ao pausar:', error);
        adicionarMensagem('Erro ao pausar tarefa', 'bot');
    }
}

// ========================================
// RETOMAR TAREFA
// ========================================
window.retomarTarefa = async function(taskId) {
    // ✅ Garantir que taskId é number
    taskId = Number(taskId);
    
    console.log('🟢 Retomando tarefa:', taskId);
    
    try {
        const response = await fetch('/api/retomar-tarefa', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ apontamento_id: taskId })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const task = activeTasks.find(t => t.id === taskId);
            if (task) {
                task.totalPausedTime += (new Date() - task.pauseStartTime);
                task.pauseStartTime = null;
                task.status = 'em_andamento';
                
                // ✅ REINICIAR O TIMER!
                iniciarTimerTarefa(task.id, task.startTime, task.totalPausedTime, null);
                console.log('▶️ Timer reiniciado para tarefa:', taskId);
                
                // Atualizar card
                const card = document.getElementById(`task-${taskId}`);
                if (card) {
                    card.classList.remove('paused');
                    card.querySelector('.task-card-status').textContent = '▶️';
                    
                    const actions = card.querySelector('.task-card-actions');
                    actions.innerHTML = `
                        <button class="task-card-btn btn-pause" onclick="pausarTarefa(${taskId})">
                            ⏸️ Pausar
                        </button>
                        <button class="task-card-btn btn-finish" onclick="finalizarTarefa(${taskId})">
                            ✅ Finalizar
                        </button>
                    `;
                }
            }
            
            adicionarMensagem('Tarefa retomada', 'bot');
        }
    } catch (error) {
        console.error('Erro ao retomar:', error);
        adicionarMensagem('Erro ao retomar tarefa', 'bot');
    }
}

// ========================================
// FINALIZAR TAREFA
// ========================================
window.finalizarTarefa = async function(taskId) {
    // ✅ Garantir que taskId é number
    taskId = Number(taskId);
    
    console.log('🔴 Finalizando tarefa:', taskId);
    console.log('📋 Tipo do taskId:', typeof taskId);
    console.log('🔍 activeTasks:', activeTasks);
    
    const task = activeTasks.find(t => t.id === taskId);
    if (!task) {
        console.error('❌ Tarefa não encontrada:', taskId);
        console.error('   activeTasks IDs:', activeTasks.map(t => t.id));
        return;
    }
    
    console.log('✅ Tarefa encontrada:', task);
    
    console.log('📤 Enviando para backend - apontamento_id:', taskId);
    
    try {
        const response = await fetch('/api/finalizar-tarefa', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ apontamento_id: taskId })
        });
        
        const data = await response.json();
        console.log('📥 Resposta do backend:');
        console.log('   Status HTTP:', response.status);
        console.log('   Success:', data.success);
        console.log('   Data completo:', JSON.stringify(data, null, 2));
        
        if (data.success) {
            // ✅ Garantir que horas_trabalhadas é number
            const horasTrabalhadas = Number(data.horas_trabalhadas) || 0;
            
            console.log('⏱️ Horas trabalhadas:', horasTrabalhadas, 'Tipo:', typeof horasTrabalhadas);
            
            adicionarMensagem(
                `✔️ Tarefa finalizada!\n\nCliente: ${task.cliente}\nTarefa: ${task.tarefa}\n\nHoras trabalhadas: ${horasTrabalhadas.toFixed(2)}h`, 
                'bot'
            );
            
            // Remover do array e da UI
            activeTasks = activeTasks.filter(t => t.id !== taskId);
            removerTaskCard(taskId);
            console.log('✅ Tarefa removida:', taskId);
        } else {
            console.error('❌ Erro do backend:', data.message);
            adicionarMensagem('Erro ao finalizar tarefa: ' + (data.message || 'Erro desconhecido'), 'bot');
            
            // ⚠️ FALLBACK: Remover card mesmo com erro do backend
            // (a tarefa pode ter sido finalizada no banco, mas o frontend não sabe)
            const confirmarRemocao = confirm('Houve um erro, mas deseja remover o card da tela mesmo assim?');
            if (confirmarRemocao) {
                activeTasks = activeTasks.filter(t => t.id !== taskId);
                removerTaskCard(taskId);
                console.log('⚠️ Card removido manualmente pelo usuário');
            }
        }
    } catch (error) {
        console.error('❌ Erro ao finalizar:', error);
        adicionarMensagem('Erro ao finalizar tarefa: ' + error.message, 'bot');
    }
}

// ========================================
// CHAT COM ASSISTENTE
// ========================================
chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const mensagem = mensagemInput.value.trim();
    if (!mensagem) return;
    
    adicionarMensagem(mensagem, 'user');
    mensagemInput.value = '';
    
    mostrarDigitando(true);
    mensagemInput.disabled = true;
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ mensagem })
        });
        
        const data = await response.json();
        mostrarDigitando(false);
        
        if (data.success) {
            adicionarMensagem(data.resposta, 'bot');
        } else {
            adicionarMensagem('Desculpe, ocorreu um erro. Tente novamente.', 'bot');
        }
    } catch (error) {
        mostrarDigitando(false);
        adicionarMensagem('Erro de conexão. Verifique sua internet.', 'bot');
    } finally {
        mensagemInput.disabled = false;
        mensagemInput.focus();
    }
});

// ========================================
// LOGOUT
// ========================================
btnLogout.addEventListener('click', async () => {
    if (activeTasks.length > 0) {
        const confirmar = confirm('Você tem tarefas ativas. Deseja realmente sair?');
        if (!confirmar) return;
    }
    
    try {
        const response = await fetch('/api/logout', {
            method: 'POST'
        });
        
        if (response.ok) {
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('Erro ao fazer logout:', error);
    }
});

// ========================================
// VERIFICAR TAREFAS ATIVAS AO CARREGAR
// ========================================
async function verificarTarefasAtivas() {
    try {
        const response = await fetch('/api/verificar-tarefas-ativas');
        const data = await response.json();
        
        if (data.success && data.tarefas && data.tarefas.length > 0) {
            data.tarefas.forEach(tarefaData => {
                const task = {
                    id: tarefaData.apontamento_id,
                    cliente: tarefaData.cliente_nome,
                    tarefa: tarefaData.tarefa_nome,
                    cnpj: tarefaData.cnpj,
                    startTime: new Date(tarefaData.data_inicio),
                    totalPausedTime: tarefaData.tempo_pausado_ms || 0,
                    pauseStartTime: tarefaData.data_pausa ? new Date(tarefaData.data_pausa) : null,
                    status: tarefaData.status
                };
                
                activeTasks.push(task);
                adicionarTaskCard(task);
            });
        }
    } catch (error) {
        console.error('Erro ao verificar tarefas ativas:', error);
    }
}

// Fechar resultados ao clicar fora
document.addEventListener('click', (e) => {
    if (!clientSearch.contains(e.target) && !clientResults.contains(e.target)) {
        clientResults.classList.remove('show');
    }
    
    // Fechar resultados do late client search também
    if (!lateClientSearch.contains(e.target) && !lateClientResults.contains(e.target)) {
        lateClientResults.classList.remove('show');
    }
});

// ========================================
// APONTAMENTOS ATRASADOS
// ========================================

// Elementos do formulário de apontamentos atrasados
const lateTaskForm = document.getElementById('lateTaskForm');
const lateClientSearch = document.getElementById('lateClientSearch');
const lateClientResults = document.getElementById('lateClientResults');
const lateSelectedClientCNPJ = document.getElementById('lateSelectedClientCNPJ');
const lateSelectedClientName = document.getElementById('lateSelectedClientName');
const lateSelectedClientDisplay = document.getElementById('lateSelectedClientDisplay');
const lateSelectedClientText = document.getElementById('lateSelectedClientText');
const lateClearClientBtn = document.getElementById('lateClearClient');
const lateTaskSelect = document.getElementById('lateTaskSelect');
const lateStartDateTime = document.getElementById('lateStartDateTime');
const lateEndDateTime = document.getElementById('lateEndDateTime');
const btnRegisterLate = document.getElementById('btnRegisterLate');

let lateSearchTimeout = null;

// Busca de clientes para apontamento atrasado
lateClientSearch.addEventListener('input', function() {
    const query = this.value.trim();
    
    clearTimeout(lateSearchTimeout);
    
    if (query.length < 2) {
        lateClientResults.classList.remove('show');
        return;
    }
    
    lateSearchTimeout = setTimeout(() => {
        buscarClientesLate(query);
    }, 300);
});

async function buscarClientesLate(query) {
    try {
        const response = await fetch('/api/buscar-clientes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query })
        });
        
        const data = await response.json();
        
        if (data.success) {
            mostrarResultadosClientesLate(data.clientes);
        }
    } catch (error) {
        console.error('Erro ao buscar clientes (atrasado):', error);
    }
}

function mostrarResultadosClientesLate(clientes) {
    lateClientResults.innerHTML = '';
    
    if (clientes.length === 0) {
        lateClientResults.innerHTML = '<div class="no-results">Nenhum cliente encontrado</div>';
        lateClientResults.classList.add('show');
        return;
    }
    
    clientes.forEach(cliente => {
        const item = document.createElement('div');
        item.className = 'search-result-item';
        item.innerHTML = `
            <span class="client-name">${cliente.nom_cliente}</span>
            <span class="client-cnpj">CNPJ: ${formatarCNPJ(cliente.num_cnpj_cpf)}</span>
        `;
        
        item.addEventListener('click', () => {
            selecionarClienteLate(cliente);
        });
        
        lateClientResults.appendChild(item);
    });
    
    lateClientResults.classList.add('show');
}

function selecionarClienteLate(cliente) {
    lateSelectedClientCNPJ.value = cliente.num_cnpj_cpf;
    lateSelectedClientName.value = cliente.nom_cliente;
    
    lateSelectedClientText.textContent = cliente.nom_cliente;
    lateSelectedClientDisplay.style.display = 'flex';
    
    lateClientSearch.value = '';
    lateClientResults.classList.remove('show');
    
    // Buscar tarefas deste cliente
    carregarTarefasClienteLate(cliente.num_cnpj_cpf);
}

lateClearClientBtn.addEventListener('click', () => {
    lateSelectedClientCNPJ.value = '';
    lateSelectedClientName.value = '';
    lateSelectedClientDisplay.style.display = 'none';
    
    lateTaskSelect.innerHTML = '<option value="">Selecione um cliente primeiro</option>';
    lateTaskSelect.disabled = true;
    btnRegisterLate.disabled = true;
});

async function carregarTarefasClienteLate(cnpj) {
    try {
        const response = await fetch('/api/buscar-tarefas', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ cnpj })
        });
        
        const data = await response.json();
        
        if (data.success) {
            preencherSelectTarefasLate(data.tarefas);
        }
    } catch (error) {
        console.error('Erro ao buscar tarefas (atrasado):', error);
    }
}

function preencherSelectTarefasLate(tarefas) {
    lateTaskSelect.innerHTML = '<option value="">Selecione uma tarefa</option>';
    
    if (tarefas.length === 0) {
        lateTaskSelect.innerHTML = '<option value="">Nenhuma tarefa disponível</option>';
        lateTaskSelect.disabled = true;
        btnRegisterLate.disabled = true;
        return;
    }
    
    tarefas.forEach(tarefa => {
        const option = document.createElement('option');
        option.value = JSON.stringify({
            id: tarefa.id,
            nome_tarefa: tarefa.nome_tarefa,
            cod_grupo_tarefa: tarefa.cod_grupo_tarefa,
            prioridade: tarefa.prioridade
        });
        option.textContent = `${tarefa.nome_tarefa} (${tarefa.prioridade || 'Sem prioridade'})`;
        lateTaskSelect.appendChild(option);
    });
    
    lateTaskSelect.disabled = false;
    verificarFormLateCompleto();
}

lateTaskSelect.addEventListener('change', verificarFormLateCompleto);
lateStartDateTime.addEventListener('change', verificarFormLateCompleto);
lateEndDateTime.addEventListener('change', verificarFormLateCompleto);

function verificarFormLateCompleto() {
    const temCliente = lateSelectedClientCNPJ.value;
    const temTarefa = lateTaskSelect.value;
    const temInicio = lateStartDateTime.value;
    const temFim = lateEndDateTime.value;
    
    btnRegisterLate.disabled = !(temCliente && temTarefa && temInicio && temFim);
}

// Submeter apontamento atrasado
lateTaskForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    if (!lateSelectedClientCNPJ.value || !lateTaskSelect.value || !lateStartDateTime.value || !lateEndDateTime.value) {
        return;
    }
    
    const tarefaData = JSON.parse(lateTaskSelect.value);
    const dataInicio = new Date(lateStartDateTime.value);
    const dataFim = new Date(lateEndDateTime.value);
    
    // Validar datas
    if (dataFim <= dataInicio) {
        alert('A data/hora de fim deve ser posterior à data/hora de início!');
        return;
    }
    
    // Validar se não é no futuro
    const agora = new Date();
    if (dataInicio > agora || dataFim > agora) {
        alert('Não é possível registrar apontamento no futuro!');
        return;
    }
    
    btnRegisterLate.disabled = true;
    btnRegisterLate.textContent = 'Registrando...';
    
    try {
        const response = await fetch('/api/registrar-atrasado', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
            cnpj_cliente: lateSelectedClientCNPJ.value,
            nome_cliente: lateSelectedClientName.value,
            tarefa_id: tarefaData.id,
            nome_tarefa: tarefaData.nome_tarefa,
            data_inicio: lateStartDateTime.value,
            data_fim: lateEndDateTime.value,
            observacao: lateObservacao ? lateObservacao.value.trim() : ''  // ⭐ NOVO
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const horas = Number(data.horas_trabalhadas) || 0;
            
            adicionarMensagem(
                `✅ Apontamento atrasado registrado!\n\nCliente: ${lateSelectedClientName.value}\nTarefa: ${tarefaData.nome_tarefa}\n\nPeríodo: ${formatarDataHora(dataInicio)} até ${formatarDataHora(dataFim)}\nHoras trabalhadas: ${horas.toFixed(2)}h`,
                'bot'
            );
            
            // Limpar formulário
            lateClearClientBtn.click();
            lateStartDateTime.value = '';
            lateEndDateTime.value = '';
            // Limpar campo de observação
            if (lateObservacao) {
                lateObservacao.value = '';
                if (lateObsCounter) {
                    lateObsCounter.textContent = '0';
                }
            }

            verificarFormLateCompleto();
        } else {
            adicionarMensagem('Erro ao registrar apontamento: ' + data.message, 'bot');
        }
    } catch (error) {
        console.error('Erro ao registrar apontamento atrasado:', error);
        adicionarMensagem('Erro ao registrar apontamento. Tente novamente.', 'bot');
    } finally {
        btnRegisterLate.disabled = false;
        btnRegisterLate.textContent = '⏰ Registrar Apontamento';
    }
});

function formatarDataHora(data) {
    return data.toLocaleString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Inicializar
verificarTarefasAtivas();
mensagemInput.focus();

// ========================================
// SISTEMA DE ABAS
// ========================================
const tabButtons = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

tabButtons.forEach(button => {
    button.addEventListener('click', () => {
        // Remover active de todos
        tabButtons.forEach(btn => btn.classList.remove('active'));
        tabContents.forEach(content => content.classList.remove('active'));
        
        // Adicionar active no clicado
        button.classList.add('active');
        const tabId = button.getAttribute('data-tab');
        document.getElementById(tabId).classList.add('active');
        
        console.log('📑 Aba selecionada:', tabId);
    });
});