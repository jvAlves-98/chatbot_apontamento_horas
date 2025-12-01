document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const usuario = document.getElementById('usuario').value;
    const senha = document.getElementById('senha').value;
    const mensagemErro = document.getElementById('mensagemErro');
    
    // Limpar mensagem de erro anterior
    mensagemErro.style.display = 'none';
    
    // Desabilitar botão durante o envio
    const btnSubmit = e.target.querySelector('button[type="submit"]');
    btnSubmit.disabled = true;
    btnSubmit.textContent = 'Entrando...';
    
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ usuario, senha })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Redirecionar para o chat
            window.location.href = '/';
        } else {
            // Mostrar erro
            mensagemErro.textContent = data.message || 'Erro ao fazer login';
            mensagemErro.style.display = 'block';
        }
    } catch (error) {
        mensagemErro.textContent = 'Erro de conexão. Tente novamente.';
        mensagemErro.style.display = 'block';
    } finally {
        // Reabilitar botão
        btnSubmit.disabled = false;
        btnSubmit.textContent = 'Entrar';
    }
});