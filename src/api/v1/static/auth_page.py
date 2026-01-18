"""
Página HTML de autenticação que roda no navegador do cliente.

Este arquivo é servido para que o usuário faça login via Gov.br
enquanto a API roda em Docker ou servidor remoto.
"""

HTML_AUTH_PAGE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Autenticação Gov.br - API Gov-Auth</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            max-width: 600px;
            width: 100%;
            padding: 40px;
        }
        h1 { color: #333; margin-bottom: 10px; }
        .subtitle { color: #666; margin-bottom: 30px; }
        .status {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .status.info { background: #e3f2fd; color: #1976d2; border-left: 4px solid #1976d2; }
        .status.success { background: #e8f5e9; color: #388e3c; border-left: 4px solid #388e3c; }
        .status.error { background: #ffebee; color: #d32f2f; border-left: 4px solid #d32f2f; }
        .status.warning { background: #fff3e0; color: #f57c00; border-left: 4px solid #f57c00; }
        .step { padding: 15px; background: #f5f5f5; border-radius: 8px; margin: 15px 0; }
        .step h3 { color: #333; margin-bottom: 10px; }
        .step p { color: #666; font-size: 14px; }
        .step code { background: #e0e0e0; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
        button {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            margin: 5px;
        }
        .btn-primary { background: #667eea; color: white; }
        .btn-primary:hover { background: #5568d3; }
        .btn-success { background: #4caf50; color: white; }
        .btn-secondary { background: #e0e0e0; color: #333; }
        textarea {
            width: 100%;
            height: 120px;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-family: monospace;
            font-size: 12px;
            margin: 10px 0;
        }
        .hidden { display: none; }
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 Autenticação Gov.br</h1>
        <p class="subtitle">API Gov-Auth - Autenticação via SIGEF</p>
        
        <div id="status" class="status info">
            <strong>Instruções:</strong> Siga os passos abaixo para autenticar.
        </div>
        
        <!-- Step 1: Abrir SIGEF -->
        <div id="step1" class="step">
            <h3>Passo 1: Abrir SIGEF e fazer login</h3>
            <p>Clique no botão abaixo. Uma nova aba será aberta com o SIGEF.</p>
            <p style="margin-top:10px">Faça login com seu certificado digital Gov.br.</p>
            <button class="btn-primary" onclick="openSigef()">🌐 Abrir SIGEF</button>
        </div>
        
        <!-- Step 2: Copiar cookies -->
        <div id="step2" class="step hidden">
            <h3>Passo 2: Copiar cookies do navegador</h3>
            <p>Após fazer login no SIGEF:</p>
            <ol style="margin: 10px 0 10px 20px; color: #666; font-size: 14px;">
                <li>Pressione <code>F12</code> para abrir DevTools</li>
                <li>Vá na aba <code>Application</code> (ou <code>Aplicação</code>)</li>
                <li>No menu lateral, clique em <code>Cookies</code> → <code>https://sigef.incra.gov.br</code></li>
                <li>Copie os valores dos cookies listados</li>
            </ol>
            <p>Ou use o console (F12 → Console) e execute:</p>
            <code style="display:block; padding:10px; background:#1e1e1e; color:#4ec9b0; border-radius:4px; margin:10px 0;">
                copy(document.cookie)
            </code>
            <p style="margin-top:15px">Cole os cookies aqui:</p>
            <textarea id="cookiesInput" placeholder="Cole os cookies aqui...&#10;&#10;Formato: cookie1=valor1; cookie2=valor2; ..."></textarea>
            <button class="btn-success" onclick="submitCookies()">✓ Enviar Cookies</button>
            <button class="btn-secondary" onclick="skipCookies()">Pular (testar sem cookies)</button>
        </div>
        
        <!-- Step 3: Concluído -->
        <div id="step3" class="step hidden">
            <h3>✅ Autenticação Concluída!</h3>
            <p>Os cookies foram enviados para a API.</p>
            <p style="margin-top:10px; color:#388e3c;">Você pode fechar esta janela e voltar para o aplicativo.</p>
        </div>
        
        <!-- Loading -->
        <div id="loading" class="hidden">
            <div class="spinner"></div>
            <p style="text-align:center; color:#666;">Enviando dados...</p>
        </div>
        
        <!-- Error -->
        <div id="errorDiv" class="step hidden">
            <div class="status error">
                <strong>❌ Erro</strong>
                <p id="errorMessage"></p>
            </div>
            <button class="btn-secondary" onclick="location.reload()">Tentar Novamente</button>
        </div>
    </div>
    
    <script>
        const urlParams = new URLSearchParams(window.location.search);
        const authToken = urlParams.get('token');
        const apiBase = window.location.origin + '/api';
        
        if (!authToken) {
            showError('Token de autenticação não fornecido na URL');
        }
        
        function openSigef() {
            // Abre o SIGEF em nova aba - o usuário fará login lá
            window.open('https://sigef.incra.gov.br/oauth2/authorization/govbr', '_blank');
            
            // Mostra step 2
            document.getElementById('step1').classList.add('hidden');
            document.getElementById('step2').classList.remove('hidden');
            
            document.getElementById('status').innerHTML = 
                '<strong>Aguardando:</strong> Faça login no SIGEF e depois cole os cookies aqui.';
        }
        
        async function submitCookies() {
            const cookiesText = document.getElementById('cookiesInput').value.trim();
            
            if (!cookiesText) {
                alert('Por favor, cole os cookies antes de enviar.');
                return;
            }
            
            // Parse cookies
            const cookies = parseCookies(cookiesText);
            
            document.getElementById('step2').classList.add('hidden');
            document.getElementById('loading').classList.remove('hidden');
            
            try {
                const response = await fetch(`${apiBase}/v1/auth/browser-callback`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        auth_token: authToken,
                        govbr_cookies: cookies,
                        sigef_cookies: cookies,
                    })
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Erro ao enviar cookies');
                }
                
                // Sucesso!
                document.getElementById('loading').classList.add('hidden');
                document.getElementById('step3').classList.remove('hidden');
                document.getElementById('status').className = 'status success';
                document.getElementById('status').innerHTML = 
                    '<strong>✅ Sucesso!</strong> Autenticação concluída.';
                
            } catch (error) {
                showError(error.message);
            }
        }
        
        function skipCookies() {
            // Para teste - envia cookies vazios
            document.getElementById('cookiesInput').value = 'test=1';
            submitCookies();
        }
        
        function parseCookies(text) {
            // Converte string de cookies para array de objetos
            const cookies = [];
            
            // Tenta diferentes formatos
            if (text.includes('=')) {
                const pairs = text.split(';');
                for (const pair of pairs) {
                    const [name, ...valueParts] = pair.trim().split('=');
                    if (name) {
                        cookies.push({
                            name: name.trim(),
                            value: valueParts.join('=').trim(),
                            domain: '.sigef.incra.gov.br',
                        });
                    }
                }
            }
            
            return cookies;
        }
        
        function showError(message) {
            document.getElementById('loading').classList.add('hidden');
            document.getElementById('step1').classList.add('hidden');
            document.getElementById('step2').classList.add('hidden');
            document.getElementById('errorDiv').classList.remove('hidden');
            document.getElementById('errorMessage').textContent = message;
            document.getElementById('status').className = 'status error';
            document.getElementById('status').innerHTML = '<strong>Erro:</strong> ' + message;
        }
    </script>
</body>
</html>
"""
            background: #5568d3;
        }
        
        .btn-secondary {
            background: #e0e0e0;
            color: #333;
        }
        
        .btn-secondary:hover {
            background: #d0d0d0;
        }
        
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .timer {
            text-align: center;
            font-size: 12px;
            color: #999;
            margin-top: 20px;
        }
        
        code {
            background: #f5f5f5;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Autenticação Gov.br</h1>
        <p class="subtitle">API Gov-Auth - Autenticação Remota</p>
        
        <div id="status" class="status info" style="display: none;"></div>
        
        <div id="loading">
            <div class="spinner"></div>
            <p style="text-align: center; color: #666; margin-top: 15px;">
                Carregando página de autenticação...
            </p>
        </div>
        
        <div id="authenticated" style="display: none;">
            <div class="status success">
                <strong>✓ Autenticado com sucesso!</strong>
                <p style="margin-top: 10px;">Seus dados foram enviados para a API.</p>
            </div>
            <p style="text-align: center; color: #666; margin-top: 20px;">
                Você pode fechar esta janela.
            </p>
        </div>
        
        <div id="error" style="display: none;">
            <div class="status error">
                <strong>✗ Erro na Autenticação</strong>
                <p id="error-message" style="margin-top: 10px;"></p>
            </div>
            <div class="button-group">
                <button class="btn-secondary" onclick="location.reload()">Tentar Novamente</button>
                <button class="btn-secondary" onclick="window.close()">Fechar</button>
            </div>
        </div>
        
        <div class="timer">
            <p id="timer">Timeout: <span id="timeout-count">10</span>s</p>
        </div>
    </div>
    
    <script>
        const urlParams = new URLSearchParams(window.location.search);
        const authToken = urlParams.get('token');
        const apiBase = window.location.origin;
        
        if (!authToken) {
            showError('Token de autenticação não fornecido');
        } else {
            initializeAuth();
        }
        
        function showStatus(message, type = 'info') {
            const elem = document.getElementById('status');
            elem.textContent = message;
            elem.className = `status ${type}`;
            elem.style.display = 'block';
        }
        
        function showError(message) {
            document.getElementById('loading').style.display = 'none';
            document.getElementById('error').style.display = 'block';
            document.getElementById('error-message').textContent = message;
        }
        
        function showSuccess() {
            document.getElementById('loading').style.display = 'none';
            document.getElementById('authenticated').style.display = 'block';
        }
        
        async function initializeAuth() {
            showStatus('Estabelecendo conexão com Gov.br...', 'info');
            
            try {
                // Aguarda um pouco para que a página de login do Gov.br carregue
                // Em produção, isso seria feito via iframe ou popup
                await new Promise(resolve => setTimeout(resolve, 2000));
                
                showStatus('Redirecionando para Gov.br...', 'info');
                
                // Redireciona para Gov.br
                // Em uma implementação real, isso seria feito via OAuth2 flow
                window.location.href = 'https://sso.acesso.gov.br/';
                
            } catch (error) {
                showError(`Erro: ${error.message}`);
            }
        }
        
        // Contador de timeout
        let timeout = 600; // 10 minutos em segundos
        setInterval(() => {
            timeout--;
            document.getElementById('timeout-count').textContent = Math.max(0, Math.floor(timeout / 60));
            
            if (timeout <= 0) {
                showError('Sessão expirada. Tente fazer login novamente.');
            }
        }, 1000);
    </script>
</body>
</html>
"""
