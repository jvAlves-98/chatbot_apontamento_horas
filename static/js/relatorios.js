// ========================================
// SISTEMA DE NAVEGAÇÃO ENTRE PÁGINAS
// ========================================

document.addEventListener('DOMContentLoaded', () => {
    // Gerenciar navegação entre páginas
    const headerTabButtons = document.querySelectorAll('.header-tab-btn');
    const pageContents = document.querySelectorAll('.page-content');
    
    headerTabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const pageName = button.dataset.page;
            
            // Remover active de todos
            headerTabButtons.forEach(btn => btn.classList.remove('active'));
            pageContents.forEach(content => content.classList.remove('active'));
            
            // Adicionar active no selecionado
            button.classList.add('active');
            document.getElementById(`page-${pageName}`).classList.add('active');
            
            // Se mudou para relatórios, carregar filtros
            if (pageName === 'relatorios') {
                carregarFiltros();
            }
        });
    });
    
    // Event listeners dos filtros
    const btnAplicar = document.getElementById('btnAplicarFiltros');
    const btnLimpar = document.getElementById('btnLimparFiltros');
    
    if (btnAplicar) {
        btnAplicar.addEventListener('click', gerarRelatorio);
    }
    
    if (btnLimpar) {
        btnLimpar.addEventListener('click', limparFiltros);
    }
});

// ========================================
// CARREGAR OPÇÕES DE FILTROS
// ========================================

async function carregarFiltros() {
    try {
        const response = await fetch('/api/filtros-relatorio');
        const data = await response.json();
        
        if (data.success) {
            // Preencher ano (últimos 5 anos)
            const anoAtual = new Date().getFullYear();
            const filtroAno = document.getElementById('filtroAno');
            filtroAno.innerHTML = '<option value="">Todos</option>';
            for (let i = 0; i < 5; i++) {
                const ano = anoAtual - i;
                const option = document.createElement('option');
                option.value = ano;
                option.textContent = ano;
                if (i === 0) option.selected = true; // Ano atual selecionado
                filtroAno.appendChild(option);
            }
            
            // Preencher mês (mês atual)
            const mesAtual = new Date().getMonth() + 1;
            document.getElementById('filtroMes').value = mesAtual;
            
            // Preencher departamentos
            const filtroDept = document.getElementById('filtroDepartamento');
            filtroDept.innerHTML = '<option value="">Todos</option>';
            data.departamentos.forEach(dept => {
                const option = document.createElement('option');
                option.value = dept;
                option.textContent = dept;
                filtroDept.appendChild(option);
            });
            
            // Preencher funcionários
            const filtroFunc = document.getElementById('filtroFuncionario');
            filtroFunc.innerHTML = '<option value="">Todos</option>';
            data.funcionarios.forEach(func => {
                const option = document.createElement('option');
                option.value = func.usuario;
                option.textContent = func.nome_completo;
                filtroFunc.appendChild(option);
            });
            
            // Preencher grupos de clientes
            const filtroGrupo = document.getElementById('filtroGrupo');
            filtroGrupo.innerHTML = '<option value="">Todos</option>';
            data.grupos_clientes.forEach(grupo => {
                const option = document.createElement('option');
                option.value = grupo.cod_grupo_cliente;
                option.textContent = grupo.des_grupo;
                filtroGrupo.appendChild(option);
            });
            
            // Preencher grupos de tarefas
            const filtroTarefa = document.getElementById('filtroTarefa');
            filtroTarefa.innerHTML = '<option value="">Todos</option>';
            data.grupos_tarefas.forEach(tarefa => {
                const option = document.createElement('option');
                option.value = tarefa.cod_grupo_tarefa;
                option.textContent = `${tarefa.cod_grupo_tarefa} - ${tarefa.nome_grupo_tarefa}`;
                filtroTarefa.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Erro ao carregar filtros:', error);
    }
}

// ========================================
// GERAR RELATÓRIO
// ========================================

async function gerarRelatorio() {
    const btnAplicar = document.getElementById('btnAplicarFiltros');
    btnAplicar.disabled = true;
    btnAplicar.textContent = '⏳ Gerando...';
    
    try {
        const filtros = {
            ano: document.getElementById('filtroAno').value,
            mes: document.getElementById('filtroMes').value,
            departamento: document.getElementById('filtroDepartamento').value,
            funcionario: document.getElementById('filtroFuncionario').value,
            grupo: document.getElementById('filtroGrupo').value,
            tarefa: document.getElementById('filtroTarefa').value
        };
        
        const response = await fetch('/api/relatorio-tempo', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(filtros)
        });
        
        const data = await response.json();
        
        if (data.success) {
            renderizarRelatorio(data.dados);
        } else {
            alert('Erro ao gerar relatório: ' + data.message);
        }
    } catch (error) {
        console.error('Erro ao gerar relatório:', error);
        alert('Erro ao gerar relatório. Tente novamente.');
    } finally {
        btnAplicar.disabled = false;
        btnAplicar.textContent = '🔍 Aplicar Filtros';
    }
}

// ========================================
// RENDERIZAR TABELA DE RELATÓRIO
// ========================================

function renderizarRelatorio(dados) {
    const headerRow = document.getElementById('headerRow');
    const tbody = document.getElementById('tabelaBody');
    
    // Limpar tabela
    headerRow.innerHTML = '<th class="col-sticky">Grupo de Empresas</th>';
    tbody.innerHTML = '';
    
    if (Object.keys(dados).length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="100" class="no-data">
                    📭 Nenhum dado encontrado para os filtros selecionados
                </td>
            </tr>
        `;
        return;
    }
    
    // Coletar todas as tarefas únicas para criar colunas
    const tarefasUnicas = new Set();
    Object.values(dados).forEach(grupo => {
        Object.values(grupo).forEach(cliente => {
            Object.values(cliente).forEach(funcionario => {
                Object.keys(funcionario).forEach(tarefa => {
                    tarefasUnicas.add(tarefa);
                });
            });
        });
    });
    
    const tarefasArray = Array.from(tarefasUnicas).sort();
    
    // Criar header com tarefas
    tarefasArray.forEach(tarefa => {
        const th = document.createElement('th');
        th.textContent = tarefa;
        th.className = 'col-tarefa';
        headerRow.appendChild(th);
    });
    
    // Total
    const thTotal = document.createElement('th');
    thTotal.textContent = 'TOTAL';
    thTotal.className = 'col-total';
    headerRow.appendChild(thTotal);
    
    // Criar linhas de dados
    Object.keys(dados).sort().forEach(grupoNome => {
        const grupo = dados[grupoNome];
        
        // ===== LINHA DO GRUPO (Nível 1 - expandível) =====
        const trGrupo = document.createElement('tr');
        trGrupo.className = 'row-grupo expandable';
        trGrupo.dataset.level = '1';
        trGrupo.innerHTML = `
            <td class="col-sticky col-grupo">
                <span class="expand-icon">▶</span> ${grupoNome}
            </td>
        `;
        
        // Calcular totais do grupo por tarefa
        const totaisGrupo = {};
        let totalGeralGrupo = 0;
        
        Object.values(grupo).forEach(cliente => {
            Object.values(cliente).forEach(funcionario => {
                Object.entries(funcionario).forEach(([tarefa, horas]) => {
                    totaisGrupo[tarefa] = (totaisGrupo[tarefa] || 0) + horas;
                    totalGeralGrupo += horas;
                });
            });
        });
        
        // Adicionar células de tarefas do grupo
        tarefasArray.forEach(tarefa => {
            const td = document.createElement('td');
            const valor = totaisGrupo[tarefa] || 0;
            td.textContent = formatarHoras(valor);
            td.className = 'col-numero';
            if (valor > 0) td.classList.add('has-value');
            trGrupo.appendChild(td);
        });
        
        // Total do grupo
        const tdTotalGrupo = document.createElement('td');
        tdTotalGrupo.textContent = formatarHoras(totalGeralGrupo);
        tdTotalGrupo.className = 'col-numero col-total has-value';
        trGrupo.appendChild(tdTotalGrupo);
        
        tbody.appendChild(trGrupo);
        
        // Toggle expand/collapse para o grupo
        trGrupo.addEventListener('click', (e) => {
            if (e.target.tagName !== 'TD' && !e.target.classList.contains('expand-icon')) return;
            
            const icon = trGrupo.querySelector('.expand-icon');
            const isExpanded = icon.textContent === '▼';
            
            // Toggle icon
            icon.textContent = isExpanded ? '▶' : '▼';
            
            // Toggle apenas as empresas (próximo nível)
            let nextRow = trGrupo.nextElementSibling;
            while (nextRow && nextRow.classList.contains('row-empresa')) {
                nextRow.style.display = isExpanded ? 'none' : 'table-row';
                
                // Se estiver fechando, fechar também todos os filhos dessa empresa
                if (isExpanded) {
                    const empresaIcon = nextRow.querySelector('.expand-icon');
                    if (empresaIcon) empresaIcon.textContent = '▶';
                    
                    let empresaChild = nextRow.nextElementSibling;
                    while (empresaChild && empresaChild.classList.contains('row-funcionario')) {
                        empresaChild.style.display = 'none';
                        empresaChild = empresaChild.nextElementSibling;
                    }
                }
                
                nextRow = nextRow.nextElementSibling;
                // Pular funcionários já que eles pertencem às empresas
                while (nextRow && nextRow.classList.contains('row-funcionario')) {
                    nextRow = nextRow.nextElementSibling;
                }
            }
        });
        
        // ===== LINHAS DAS EMPRESAS (Nível 2 - expandível) =====
        Object.keys(grupo).sort().forEach(clienteNome => {
            const cliente = grupo[clienteNome];
            
            const trEmpresa = document.createElement('tr');
            trEmpresa.className = 'row-empresa expandable';
            trEmpresa.dataset.level = '2';
            trEmpresa.style.display = 'none';
            trEmpresa.innerHTML = `
                <td class="col-sticky col-empresa">
                    &nbsp;&nbsp;&nbsp;<span class="expand-icon">▶</span> 🏢 ${clienteNome}
                </td>
            `;
            
            // Calcular totais da empresa por tarefa
            const totaisEmpresa = {};
            let totalGeralEmpresa = 0;
            
            Object.values(cliente).forEach(funcionario => {
                Object.entries(funcionario).forEach(([tarefa, horas]) => {
                    totaisEmpresa[tarefa] = (totaisEmpresa[tarefa] || 0) + horas;
                    totalGeralEmpresa += horas;
                });
            });
            
            // Adicionar células de tarefas da empresa
            tarefasArray.forEach(tarefa => {
                const td = document.createElement('td');
                const valor = totaisEmpresa[tarefa] || 0;
                td.textContent = formatarHoras(valor);
                td.className = 'col-numero';
                if (valor > 0) td.classList.add('has-value');
                trEmpresa.appendChild(td);
            });
            
            // Total da empresa
            const tdTotalEmpresa = document.createElement('td');
            tdTotalEmpresa.textContent = formatarHoras(totalGeralEmpresa);
            tdTotalEmpresa.className = 'col-numero col-total has-value';
            trEmpresa.appendChild(tdTotalEmpresa);
            
            tbody.appendChild(trEmpresa);
            
            // Toggle expand/collapse para a empresa
            trEmpresa.addEventListener('click', (e) => {
                if (e.target.tagName !== 'TD' && !e.target.classList.contains('expand-icon')) return;
                
                const icon = trEmpresa.querySelector('.expand-icon');
                const isExpanded = icon.textContent === '▼';
                
                // Toggle icon
                icon.textContent = isExpanded ? '▶' : '▼';
                
                // Toggle funcionários desta empresa
                let nextRow = trEmpresa.nextElementSibling;
                while (nextRow && nextRow.classList.contains('row-funcionario')) {
                    nextRow.style.display = isExpanded ? 'none' : 'table-row';
                    nextRow = nextRow.nextElementSibling;
                }
            });
            
            // ===== LINHAS DOS FUNCIONÁRIOS (Nível 3 - não expandível) =====
            Object.keys(cliente).sort().forEach(funcionarioNome => {
                const funcionario = cliente[funcionarioNome];
                
                const trFunc = document.createElement('tr');
                trFunc.className = 'row-funcionario';
                trFunc.dataset.level = '3';
                trFunc.style.display = 'none';
                trFunc.innerHTML = `
                    <td class="col-sticky col-funcionario">
                        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;👤 ${funcionarioNome}
                    </td>
                `;
                
                // Calcular total do funcionário
                let totalFunc = 0;
                
                // Adicionar células de tarefas do funcionário
                tarefasArray.forEach(tarefa => {
                    const td = document.createElement('td');
                    const valor = funcionario[tarefa] || 0;
                    td.textContent = formatarHoras(valor);
                    td.className = 'col-numero';
                    if (valor > 0) {
                        td.classList.add('has-value');
                        totalFunc += valor;
                    }
                    trFunc.appendChild(td);
                });
                
                // Total do funcionário
                const tdTotalFunc = document.createElement('td');
                tdTotalFunc.textContent = formatarHoras(totalFunc);
                tdTotalFunc.className = 'col-numero col-total';
                if (totalFunc > 0) tdTotalFunc.classList.add('has-value');
                trFunc.appendChild(tdTotalFunc);
                
                tbody.appendChild(trFunc);
            });
        });
    });
}

// ========================================
// FUNÇÕES AUXILIARES
// ========================================

function formatarHoras(horas) {
    if (!horas || horas === 0) return '-';
    
    const h = Math.floor(horas);
    const m = Math.round((horas - h) * 60);
    
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

function limparFiltros() {
    document.getElementById('filtroAno').value = new Date().getFullYear();
    document.getElementById('filtroMes').value = new Date().getMonth() + 1;
    document.getElementById('filtroDepartamento').value = '';
    document.getElementById('filtroFuncionario').value = '';
    document.getElementById('filtroGrupo').value = '';
    document.getElementById('filtroTarefa').value = '';
    
    // Limpar tabela
    const tbody = document.getElementById('tabelaBody');
    tbody.innerHTML = `
        <tr>
            <td colspan="100" class="no-data">
                📊 Selecione os filtros e clique em "Aplicar Filtros"
            </td>
        </tr>
    `;
}