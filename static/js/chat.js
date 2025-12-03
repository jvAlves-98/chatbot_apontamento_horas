const chatMessages = document.getElementById('chatMessages');
const chatForm = document.getElementById('chatForm');
const mensagemInput = document.getElementById('mensagemInput');
const btnLogout = document.getElementById('btnLogout');
const typingIndicator = document.getElementById('typing-indicator');

// Função para adicionar mensagem ao chat
function adicionarMensagem(texto, tipo, tempo = new Date()) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${tipo}-message`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    const strong = document.createElement('strong');
    strong.textContent = tipo === 'user' ? 'Você:' : 'Assistente:';
    
    const p = document.createElement('p');
    p.textContent = texto;
    
    // Adicione esta linha logo abaixo:
    p.style.whiteSpace = 'pre-line';

    contentDiv.appendChild(strong);
    contentDiv.appendChild(p);
    
    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = formatarHora(tempo);
    
    messageDiv.appendChild(contentDiv);
    messageDiv.appendChild(timeDiv);
    
    chatMessages.appendChild(messageDiv);
    
    // Scroll para a última mensagem
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Função para formatar hora
function formatarHora(data) {
    return data.toLocaleTimeString('pt-BR', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
}

// Função para mostrar/esconder indicador de digitação
function mostrarDigitando(mostrar) {
    typingIndicator.style.display = mostrar ? 'block' : 'none';
    if (mostrar) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

// Enviar mensagem
chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const mensagem = mensagemInput.value.trim();
    if (!mensagem) return;
    
    // Adicionar mensagem do usuário
    adicionarMensagem(mensagem, 'user');
    
    // Limpar input
    mensagemInput.value = '';
    
    // Mostrar indicador de digitação
    mostrarDigitando(true);
    
    // Desabilitar input durante o envio
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
        
        // Esconder indicador de digitação
        mostrarDigitando(false);
        
        if (data.success) {
            // Adicionar resposta do bot
            adicionarMensagem(data.resposta, 'bot');
        } else {
            // Mostrar erro
            adicionarMensagem('Desculpe, ocorreu um erro. Tente novamente.', 'bot');
        }
    } catch (error) {
        mostrarDigitando(false);
        adicionarMensagem('Erro de conexão. Verifique sua internet e tente novamente.', 'bot');
    } finally {
        // Reabilitar input
        mensagemInput.disabled = false;
        mensagemInput.focus();
    }
});

// Logout
btnLogout.addEventListener('click', async () => {
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

// Focar no input ao carregar a página
mensagemInput.focus();