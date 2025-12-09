// ========================================
// VARIÃVEIS GLOBAIS
// ========================================
let currentTask = null;
let taskStartTime = null;
let taskTimer = null;
let pauseStartTime = null;
let totalPausedTime = 0;

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

// Elementos de status
const noTaskActive = document.getElementById('noTaskActive');
const taskActive = document.getElementById('taskActive');
const activeClientName = document.getElementById('activeClientName');
const activeTaskName = document.getElementById('activeTaskName');
const activeTaskStart = document.getElementById('activeTaskStart');
const activeTaskDuration = document.getElementById('activeTaskDuration');
const pausedTimeRow = document.getElementById('pausedTimeRow');
const pausedTime = document.getElementById('pausedTime');

// BotÃµes de controle
const btnPause = document.getElementById('btnPause');
const btnResume = document.getElementById('btnResume');
const btnFinish = document.getElementById('btnFinish');

// ========================================
// FUNÃ‡Ã•ES DE CHAT
// ========================================
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
    
    // Buscar tarefas deste cliente
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
        // ✅ CORRIGIDO: Agora inclui o ID da tarefa
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
                tarefa_id: tarefaData.id,  // ✅ CORRIGIDO: Enviar tarefa_id
                nome_tarefa: tarefaData.nome_tarefa  // Para exibição
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentTask = {
                id: data.apontamento_id,
                cliente: selectedClientName.value,
                tarefa: tarefaData.nome_tarefa,
                cnpj: selectedClientCNPJ.value
            };
            
            taskStartTime = new Date();
            totalPausedTime = 0;
            pauseStartTime = null;
            
            atualizarUITarefaAtiva();
            iniciarTimer();
            
            adicionarMensagem(`Tarefa iniciada: ${tarefaData.nome_tarefa} para ${selectedClientName.value}`, 'bot');
            
            // Limpar formulário
            clearClientBtn.click();
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
// CONTROLE DE TIMER
// ========================================
function iniciarTimer() {
    if (taskTimer) clearInterval(taskTimer);
    
    taskTimer = setInterval(() => {
        if (!taskStartTime) return;
        
        const agora = new Date();
        let tempoDecorrido = agora - taskStartTime;
        
        // Descontar tempo pausado
        if (pauseStartTime) {
            tempoDecorrido -= (agora - pauseStartTime);
        } else {
            tempoDecorrido -= totalPausedTime;
        }
        
        activeTaskDuration.textContent = formatarDuracao(tempoDecorrido);
    }, 1000);
}

function pararTimer() {
    if (taskTimer) {
        clearInterval(taskTimer);
        taskTimer = null;
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
// ATUALIZAR UI
// ========================================
function atualizarUITarefaAtiva() {
    noTaskActive.style.display = 'none';
    taskActive.style.display = 'block';
    
    activeClientName.textContent = currentTask.cliente;
    activeTaskName.textContent = currentTask.tarefa;
    activeTaskStart.textContent = formatarHora(taskStartTime);
}

function atualizarUISemTarefa() {
    noTaskActive.style.display = 'block';
    taskActive.style.display = 'none';
    
    currentTask = null;
    taskStartTime = null;
    totalPausedTime = 0;
    pauseStartTime = null;
    
    pararTimer();
}

// ========================================
// PAUSAR TAREFA
// ========================================
btnPause.addEventListener('click', async () => {
    if (!currentTask) return;
    
    btnPause.disabled = true;
    
    try {
        const response = await fetch('/api/pausar-tarefa', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            pauseStartTime = new Date();
            
            btnPause.style.display = 'none';
            btnResume.style.display = 'block';
            
            pausedTimeRow.style.display = 'flex';
            
            adicionarMensagem('Tarefa pausada', 'bot');
        } else {
            adicionarMensagem('Erro ao pausar tarefa', 'bot');
        }
    } catch (error) {
        console.error('Erro ao pausar:', error);
        adicionarMensagem('Erro ao pausar tarefa', 'bot');
    } finally {
        btnPause.disabled = false;
    }
});

// ========================================
// RETOMAR TAREFA
// ========================================
btnResume.addEventListener('click', async () => {
    if (!currentTask || !pauseStartTime) return;
    
    btnResume.disabled = true;
    
    try {
        const response = await fetch('/api/retomar-tarefa', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Acumular tempo pausado
            totalPausedTime += (new Date() - pauseStartTime);
            pauseStartTime = null;
            
            btnResume.style.display = 'none';
            btnPause.style.display = 'block';
            
            pausedTime.textContent = formatarDuracao(totalPausedTime);
            
            adicionarMensagem('Tarefa retomada', 'bot');
        } else {
            adicionarMensagem('Erro ao retomar tarefa', 'bot');
        }
    } catch (error) {
        console.error('Erro ao retomar:', error);
        adicionarMensagem('Erro ao retomar tarefa', 'bot');
    } finally {
        btnResume.disabled = false;
    }
});

// ========================================
// FINALIZAR TAREFA
// ========================================
btnFinish.addEventListener('click', async () => {
    if (!currentTask) return;
    
    const confirmar = confirm(`Finalizar tarefa "${currentTask.tarefa}"?`);
    if (!confirmar) return;
    
    btnFinish.disabled = true;
    btnFinish.textContent = 'Finalizando...';
    
    try {
        const response = await fetch('/api/finalizar-tarefa', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            const horasTrabalhadas = data.horas_trabalhadas || 0;
            
            adicionarMensagem(
                `âœ… Tarefa finalizada!\n\nCliente: ${currentTask.cliente}\nTarefa: ${currentTask.tarefa}\n\nHoras trabalhadas: ${horasTrabalhadas.toFixed(2)}h`, 
                'bot'
            );
            
            atualizarUISemTarefa();
        } else {
            adicionarMensagem('Erro ao finalizar tarefa: ' + data.message, 'bot');
        }
    } catch (error) {
        console.error('Erro ao finalizar:', error);
        adicionarMensagem('Erro ao finalizar tarefa', 'bot');
    } finally {
        btnFinish.disabled = false;
        btnFinish.textContent = 'âœ… Finalizar';
    }
});

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
        adicionarMensagem('Erro de conexÃ£o. Verifique sua internet.', 'bot');
    } finally {
        mensagemInput.disabled = false;
        mensagemInput.focus();
    }
});

// ========================================
// LOGOUT
// ========================================
btnLogout.addEventListener('click', async () => {
    if (currentTask) {
        const confirmar = confirm('VocÃª tem uma tarefa ativa. Deseja realmente sair?');
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
// VERIFICAR TAREFA ATIVA AO CARREGAR
// ========================================
async function verificarTarefaAtiva() {
    try {
        const response = await fetch('/api/verificar-tarefa-ativa');
        const data = await response.json();
        
        if (data.success && data.tem_tarefa_ativa) {
            currentTask = {
                id: data.apontamento_id,
                cliente: data.cliente_nome,
                tarefa: data.tarefa_nome,
                cnpj: data.cnpj
            };
            
            taskStartTime = new Date(data.data_inicio);
            totalPausedTime = data.tempo_pausado_ms || 0;
            
            if (data.status === 'pausado') {
                pauseStartTime = new Date(data.data_pausa);
                btnPause.style.display = 'none';
                btnResume.style.display = 'block';
                pausedTimeRow.style.display = 'flex';
            }
            
            atualizarUITarefaAtiva();
            iniciarTimer();
        }
    } catch (error) {
        console.error('Erro ao verificar tarefa ativa:', error);
    }
}

// Fechar resultados ao clicar fora
document.addEventListener('click', (e) => {
    if (!clientSearch.contains(e.target) && !clientResults.contains(e.target)) {
        clientResults.classList.remove('show');
    }
});

// Inicializar
verificarTarefaAtiva();
mensagemInput.focus();