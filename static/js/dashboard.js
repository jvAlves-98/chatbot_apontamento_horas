// ========================================
// DASHBOARD - GRÁFICOS E ESTATÍSTICAS
// ========================================

let chartDepartamentos = null;
let chartGrupoAtividades = null;
let chartTempoMensal = null;

// ========================================
// INICIALIZAÇÃO
// ========================================
document.addEventListener('DOMContentLoaded', () => {
    // Configurar filtro de ano
    const anoAtual = new Date().getFullYear();
    const dashAno = document.getElementById('dashAno');
    
    for (let i = 0; i < 5; i++) {
        const ano = anoAtual - i;
        const option = document.createElement('option');
        option.value = ano;
        option.textContent = ano;
        if (i === 0) option.selected = true;
        dashAno.appendChild(option);
    }
    
    // Configurar mês atual
    const mesAtual = new Date().getMonth() + 1;
    document.getElementById('dashMes').value = mesAtual;
    
    // Event listener do botão atualizar
    const btnAtualizar = document.getElementById('btnAtualizarDash');
    if (btnAtualizar) {
        btnAtualizar.addEventListener('click', carregarDashboard);
    }
    
    // Carregar dashboard se a aba estiver ativa
    const dashboardPage = document.getElementById('page-dashboard');
    if (dashboardPage && dashboardPage.classList.contains('active')) {
        carregarDashboard();
    }
});

// ========================================
// CARREGAR DADOS DO DASHBOARD
// ========================================
async function carregarDashboard() {
    const btnAtualizar = document.getElementById('btnAtualizarDash');
    btnAtualizar.disabled = true;
    btnAtualizar.textContent = '⏳ Carregando...';
    
    const filtros = {
        ano: document.getElementById('dashAno').value,
        mes: document.getElementById('dashMes').value
    };
    
    try {
        const response = await fetch('/api/dashboard-dados', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(filtros)
        });
        
        const data = await response.json();
        
        if (data.success) {
            atualizarCards(data.resumo);
            atualizarGraficoDepartamentos(data.por_departamento);
            atualizarGraficoGrupoAtividades(data.por_grupo_atividade);
            atualizarGraficoTempoMensal(data.tempo_mensal);
        } else {
            alert('Erro ao carregar dashboard: ' + data.message);
        }
    } catch (error) {
        console.error('Erro ao carregar dashboard:', error);
        alert('Erro ao carregar dashboard. Tente novamente.');
    } finally {
        btnAtualizar.disabled = false;
        btnAtualizar.textContent = '🔄 Atualizar Dashboard';
    }
}

// ========================================
// ATUALIZAR CARDS DE RESUMO
// ========================================
function atualizarCards(resumo) {
    document.getElementById('totalTarefas').textContent = resumo.total.toLocaleString('pt-BR');
    document.getElementById('tarefasConcluidas').textContent = resumo.concluidas.toLocaleString('pt-BR');
    document.getElementById('tarefasNaoConcluidas').textContent = resumo.nao_concluidas.toLocaleString('pt-BR');
}

// ========================================
// GRÁFICO: TAREFAS POR DEPARTAMENTO
// ========================================
function atualizarGraficoDepartamentos(dados) {
    const canvas = document.getElementById('chartDepartamentos');
    const ctx = canvas.getContext('2d');
    
    // Destruir gráfico anterior se existir
    if (chartDepartamentos) {
        chartDepartamentos.destroy();
    }
    
    // Ordenar por quantidade (decrescente)
    const dadosOrdenados = dados.sort((a, b) => b.quantidade - a.quantidade);
    
    // Altura fixa de 400px
    canvas.style.height = '300px';
    canvas.height = 300;;
    canvas.height = 400;
    
    chartDepartamentos = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dadosOrdenados.map(item => item.departamento),
            datasets: [{
                label: 'Quantidade de Tarefas',
                data: dadosOrdenados.map(item => item.quantidade),
                backgroundColor: '#2196F3',
                borderColor: '#1976D2',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y', // Barras horizontais
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.parsed.x + ' tarefas';
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

// ========================================
// GRÁFICO: TAREFAS POR GRUPO DE ATIVIDADES
// ========================================
function atualizarGraficoGrupoAtividades(dados) {
    const canvas = document.getElementById('chartGrupoAtividades');
    const ctx = canvas.getContext('2d');
    
    // Destruir gráfico anterior se existir
    if (chartGrupoAtividades) {
        chartGrupoAtividades.destroy();
    }
    
    // Ordenar por quantidade (decrescente)
    const dadosOrdenados = dados.sort((a, b) => b.quantidade - a.quantidade);
    
    // Altura fixa de 400px
    canvas.style.height = '300px';
    canvas.height = 300;;
    canvas.height = 400;
    
    chartGrupoAtividades = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dadosOrdenados.map(item => item.grupo_atividade),
            datasets: [{
                label: 'Quantidade de Tarefas',
                data: dadosOrdenados.map(item => item.quantidade),
                backgroundColor: '#9E9E9E',
                borderColor: '#757575',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y', // Barras horizontais
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.parsed.x + ' tarefas';
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

// ========================================
// GRÁFICO: LINHA DO TEMPO MENSAL
// ========================================
function atualizarGraficoTempoMensal(dados) {
    const canvas = document.getElementById('chartTempoMensal');
    const ctx = canvas.getContext('2d');
    
    // Destruir gráfico anterior se existir
    if (chartTempoMensal) {
        chartTempoMensal.destroy();
    }
    
    // Altura fixa para gráfico de linha
    canvas.style.height = '300px';
    canvas.height = 300;;
    
    chartTempoMensal = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dados.map(item => item.dia),
            datasets: [{
                label: 'Tarefas por Dia',
                data: dados.map(item => item.quantidade),
                backgroundColor: 'rgba(135, 206, 250, 0.3)',
                borderColor: '#2196F3',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#2196F3',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.parsed.y + ' tarefas';
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                },
                x: {
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45
                    }
                }
            }
        }
    });
}

// ========================================
// INTEGRAÇÃO COM NAVEGAÇÃO
// ========================================
// Carregar dashboard quando a aba for ativada
document.querySelectorAll('.header-tab-btn').forEach(button => {
    button.addEventListener('click', function() {
        const pageName = this.dataset.page;
        
        if (pageName === 'dashboard') {
            // Carregar dashboard apenas se ainda não foi carregado
            const totalTarefas = document.getElementById('totalTarefas').textContent;
            if (totalTarefas === '0') {
                setTimeout(() => carregarDashboard(), 100);
            }
        }
    });
});