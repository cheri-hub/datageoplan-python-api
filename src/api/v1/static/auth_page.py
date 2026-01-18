"""
Página HTML de autenticação que roda no navegador do cliente.

Este arquivo é servido para que o usuário faça login via Gov.br
enquanto a API roda em Docker ou servidor remoto.

Usa um bookmarklet para capturar cookies automaticamente do SIGEF.
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
            max-width: 700px;
            width: 100%;
            padding: 40px;
        }
        h1 { color: #333; margin-bottom: 10px; text-align: center; }
        .subtitle { color: #666; margin-bottom: 30px; text-align: center; }
        .status {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .status.info { background: #e3f2fd; color: #1976d2; border-left: 4px solid #1976d2; }
        .status.success { background: #e8f5e9; color: #388e3c; border-left: 4px solid #388e3c; }
        .status.error { background: #ffebee; color: #d32f2f; border-left: 4px solid #d32f2f; }
        .status.waiting { background: #fff3e0; color: #f57c00; border-left: 4px solid #f57c00; }
        .step {
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            margin: 15px 0;
            border: 1px solid #e9ecef;
        }
        .step-number {
            display: inline-block;
            width: 28px;
            height: 28px;
            background: #667eea;
            color: white;
            border-radius: 50%;
            text-align: center;
            line-height: 28px;
            font-weight: bold;
            margin-right: 10px;
        }
        .step h3 { color: #333; margin-bottom: 12px; display: flex; align-items: center; }
        .step p { color: #666; font-size: 14px; margin-left: 38px; }
        button {
            padding: 14px 28px;
            border: none;
            border-radius: 8px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            margin: 8px 4px;
            transition: all 0.2s;
        }
        .btn-primary { background: #667eea; color: white; }
        .btn-primary:hover { background: #5568d3; transform: translateY(-1px); }
        .btn-success { background: #28a745; color: white; }
        .btn-success:hover { background: #218838; }
        .btn-secondary { background: #6c757d; color: white; }
        .bookmarklet {
            display: inline-block;
            padding: 12px 24px;
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 14px;
            cursor: move;
            box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
            transition: all 0.2s;
        }
        .bookmarklet:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(40, 167, 69, 0.4);
        }
        .hidden { display: none; }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 30px auto;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .instruction-box {
            background: #1e1e1e;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
            margin-left: 38px;
        }
        .instruction-box code {
            color: #4ec9b0;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 13px;
        }
        .drag-hint {
            font-size: 12px;
            color: #999;
            margin-top: 8px;
            margin-left: 38px;
        }
        .success-icon {
            font-size: 60px;
            text-align: center;
            margin: 20px 0;
        }
        .poll-status {
            text-align: center;
            color: #666;
            font-size: 14px;
            margin-top: 15px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 Autenticação Gov.br</h1>
        <p class="subtitle">Sistema SIGEF - Captura automática de sessão</p>
        
        <div id="status" class="status info">
            <strong>📋 Instruções:</strong> Siga os 3 passos abaixo para autenticar automaticamente.
        </div>

        <!-- STEPS CONTAINER -->
        <div id="stepsContainer">
            <!-- Step 1: Drag bookmarklet -->
            <div class="step">
                <h3><span class="step-number">1</span> Arraste para a barra de favoritos</h3>
                <p>Arraste o botão verde abaixo para sua barra de favoritos:</p>
                <div style="text-align: center; margin: 20px 0;">
                    <a id="bookmarklet" class="bookmarklet" href="#">
                        📤 Enviar Cookies SIGEF
                    </a>
                </div>
                <p class="drag-hint">💡 Arraste e solte na barra de favoritos do navegador (não clique aqui)</p>
            </div>
            
            <!-- Step 2: Login SIGEF -->
            <div class="step">
                <h3><span class="step-number">2</span> Faça login no SIGEF</h3>
                <p>Clique no botão abaixo para abrir o SIGEF. Faça login com seu certificado Gov.br.</p>
                <div style="text-align: center; margin: 20px 0;">
                    <button class="btn-primary" onclick="openSigef()">🌐 Abrir SIGEF</button>
                </div>
            </div>
            
            <!-- Step 3: Click bookmarklet -->
            <div class="step">
                <h3><span class="step-number">3</span> Clique no favorito</h3>
                <p>Após fazer login no SIGEF, clique no favorito <strong>"📤 Enviar Cookies SIGEF"</strong> que você salvou.</p>
                <p style="margin-top: 10px;">Os cookies serão enviados automaticamente e esta página será atualizada.</p>
            </div>
        </div>
        
        <!-- Loading / Waiting -->
        <div id="waitingDiv" class="hidden">
            <div class="spinner"></div>
            <p class="poll-status">⏳ Aguardando autenticação no SIGEF...</p>
            <p class="poll-status" id="pollCounter">Verificando a cada 2 segundos...</p>
        </div>
        
        <!-- Success -->
        <div id="successDiv" class="hidden">
            <div class="success-icon">✅</div>
            <div class="status success">
                <strong>Autenticação concluída com sucesso!</strong>
                <p style="margin-top: 8px;">Seus cookies do SIGEF foram capturados.</p>
            </div>
            <p style="text-align: center; color: #666; margin-top: 20px;">
                Você pode fechar esta janela e voltar para o aplicativo.
            </p>
        </div>
        
        <!-- Error -->
        <div id="errorDiv" class="hidden">
            <div class="status error">
                <strong>❌ Erro</strong>
                <p id="errorMessage" style="margin-top: 8px;"></p>
            </div>
            <div style="text-align: center; margin-top: 20px;">
                <button class="btn-secondary" onclick="location.reload()">Tentar Novamente</button>
            </div>
        </div>
    </div>
    
    <script>
        const urlParams = new URLSearchParams(window.location.search);
        const authToken = urlParams.get('token');
        const apiBase = window.location.origin + '/api';
        let pollInterval = null;
        
        // Verifica se tem token
        if (!authToken) {
            showError('Token de autenticação não fornecido na URL.');
        } else {
            // Cria o bookmarklet dinamicamente com o token e apiBase corretos
            createBookmarklet();
            // Inicia polling para detectar quando a autenticação for concluída
            startPolling();
        }
        
        function createBookmarklet() {
            // JavaScript que será executado quando o usuário clicar no favorito
            const bookmarkletCode = `
                (function() {
                    var cookies = document.cookie;
                    if (!cookies || cookies.length < 10) {
                        alert('Nenhum cookie encontrado. Faça login primeiro!');
                        return;
                    }
                    
                    var cookieList = [];
                    cookies.split(';').forEach(function(c) {
                        var parts = c.trim().split('=');
                        if (parts[0]) {
                            cookieList.push({
                                name: parts[0],
                                value: parts.slice(1).join('='),
                                domain: '.sigef.incra.gov.br'
                            });
                        }
                    });
                    
                    fetch('${apiBase}/v1/auth/browser-callback', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        mode: 'cors',
                        body: JSON.stringify({
                            auth_token: '${authToken}',
                            govbr_cookies: cookieList,
                            sigef_cookies: cookieList
                        })
                    })
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (data.error) {
                            alert('Erro: ' + data.error);
                        } else {
                            alert('✅ Cookies enviados com sucesso! Volte para a página de autenticação.');
                        }
                    })
                    .catch(function(e) {
                        alert('Erro ao enviar: ' + e.message);
                    });
                })();
            `.replace(/\\s+/g, ' ').trim();
            
            document.getElementById('bookmarklet').href = 'javascript:' + encodeURIComponent(bookmarkletCode);
        }
        
        function openSigef() {
            // Abre SIGEF em nova aba
            window.open('https://sigef.incra.gov.br/', '_blank');
            
            // Mostra estado de espera
            document.getElementById('status').className = 'status waiting';
            document.getElementById('status').innerHTML = 
                '<strong>⏳ Aguardando:</strong> Faça login no SIGEF e clique no favorito "Enviar Cookies SIGEF".';
        }
        
        function startPolling() {
            // Verifica periodicamente se a autenticação foi concluída
            let checks = 0;
            pollInterval = setInterval(async () => {
                checks++;
                document.getElementById('pollCounter').textContent = 
                    `Verificação #${checks} - a cada 3 segundos...`;
                
                try {
                    const response = await fetch(`${apiBase}/v1/auth/status?token=${authToken}`);
                    const data = await response.json();
                    
                    if (data.authenticated) {
                        // Sucesso!
                        clearInterval(pollInterval);
                        showSuccess();
                    }
                } catch (e) {
                    // Ignora erros de rede durante polling
                    console.log('Polling error:', e);
                }
                
                // Timeout após 10 minutos
                if (checks > 200) {
                    clearInterval(pollInterval);
                    showError('Timeout: autenticação não foi concluída em 10 minutos.');
                }
            }, 3000);
        }
        
        function showSuccess() {
            document.getElementById('stepsContainer').classList.add('hidden');
            document.getElementById('waitingDiv').classList.add('hidden');
            document.getElementById('successDiv').classList.remove('hidden');
            document.getElementById('status').className = 'status success';
            document.getElementById('status').innerHTML = 
                '<strong>✅ Sucesso!</strong> Autenticação concluída com sucesso.';
        }
        
        function showError(message) {
            if (pollInterval) clearInterval(pollInterval);
            document.getElementById('stepsContainer').classList.add('hidden');
            document.getElementById('waitingDiv').classList.add('hidden');
            document.getElementById('errorDiv').classList.remove('hidden');
            document.getElementById('errorMessage').textContent = message;
            document.getElementById('status').className = 'status error';
            document.getElementById('status').innerHTML = '<strong>❌ Erro:</strong> ' + message;
        }
    </script>
</body>
</html>
"""
