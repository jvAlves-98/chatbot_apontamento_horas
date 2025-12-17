// ===================================
// SISTEMA DE ALERTAS - FRONTEND
// ===================================

// Variável para controlar polling de alertas
let alertaInterval = null;

// Função para verificar alertas periodicamente
function iniciarMonitoramentoAlertas() {
    // Verificar a cada 30 segundos
    alertaInterval = setInterval(verificarAlertas, 30000);
    // Verificar imediatamente ao carregar
    verificarAlertas();
}

// Função para buscar alertas do servidor
async function verificarAlertas() {
    try {
        const response = await fetch('/api/alertas');
        const data = await response.json();
        
        if (data.success && data.alertas && data.alertas.length > 0) {
            mostrarAlertas(data.alertas);
        }
    } catch (error) {
        console.error('Erro ao verificar alertas:', error);
    }
}

// Função para exibir alertas na tela
function mostrarAlertas(alertas) {
    // Verificar se já existe container de alertas
    let container = document.getElementById('alertas-container');
    
    if (!container) {
        // Criar container se não existir
        container = document.createElement('div');
        container.id = 'alertas-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            max-width: 400px;
        `;
        document.body.appendChild(container);
    }
    
    // Limpar alertas antigos
    container.innerHTML = '';
    
    // Adicionar cada alerta
    alertas.forEach(alerta => {
        const alertaDiv = document.createElement('div');
        alertaDiv.className = 'alerta-item';
        alertaDiv.style.cssText = `
            background: ${alerta.mensagem.includes('✅') ? '#d4edda' : '#fff3cd'};
            border: 2px solid ${alerta.mensagem.includes('✅') ? '#28a745' : '#ffc107'};
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            animation: slideIn 0.3s ease-out;
        `;
        
        alertaDiv.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div style="flex: 1;">
                    <strong style="font-size: 14px;">${alerta.mensagem}</strong>
                    <div style="font-size: 12px; color: #666; margin-top: 5px;">
                        ${alerta.timestamp}
                    </div>
                </div>
                <button onclick="fecharAlerta('${alerta.id}')" 
                        style="background: none; border: none; font-size: 20px; cursor: pointer; color: #666; padding: 0 0 0 10px;">
                    ×
                </button>
            </div>
        `;
        
        container.appendChild(alertaDiv);
    });
}

// Função para fechar um alerta específico
function fecharAlerta(alertaId) {
    // Remover visualmente
    const alerta = document.querySelector(`[onclick*="${alertaId}"]`)?.closest('.alerta-item');
    if (alerta) {
        alerta.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => alerta.remove(), 300);
    }
}

// Função para limpar todos os alertas (opcional)
async function limparTodosAlertas() {
    try {
        await fetch('/api/alertas/limpar', { method: 'POST' });
        const container = document.getElementById('alertas-container');
        if (container) {
            container.innerHTML = '';
        }
    } catch (error) {
        console.error('Erro ao limpar alertas:', error);
    }
}

// Adicionar animações CSS
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
    
    .alerta-item:hover {
        box-shadow: 0 6px 12px rgba(0,0,0,0.15) !important;
    }
`;
document.head.appendChild(style);

// Iniciar monitoramento quando o DOM estiver pronto
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', iniciarMonitoramentoAlertas);
} else {
    iniciarMonitoramentoAlertas();
}