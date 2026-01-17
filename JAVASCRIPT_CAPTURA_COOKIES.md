# JavaScript para Captura de Cookies na Autenticação Gov.br

## 📍 Onde Integrar

Arquivo: [src/api/v1/static/auth_page.py](src/api/v1/static/auth_page.py)

Na seção JavaScript (após linha que diz `// AQUI VAI O CÓDIGO DE REDIRECT`), adicione:

---

## 🔄 Fluxo de Captura

### 1️⃣ **Opção A: Usando Storage API + PostMessage (RECOMENDADO)**

```javascript
// Captura cookies após Gov.br redirecionar de volta
function captureGovBrCookies() {
    // 1. Lê todos os cookies da página
    const cookies = document.cookie.split(';').map(c => {
        const [name, value] = c.trim().split('=');
        return {
            name: name,
            value: decodeURIComponent(value),
            domain: window.location.hostname,
            path: '/',
            httpOnly: false,  // Não conseguimos detectar, assume false
            secure: window.location.protocol === 'https:',
            sameSite: 'Lax'
        };
    }).filter(c => c.name); // Remove cookies vazios
    
    // 2. Tenta extrair JWT do localStorage (se Gov.br colocou lá)
    const jwtPayload = extractJWTFromStorage();
    
    // 3. Envia para callback
    return {
        govbr_cookies: cookies,
        sigef_cookies: [],
        jwt_payload: jwtPayload || {}
    };
}

// Extrai dados do JWT armazenado
function extractJWTFromStorage() {
    // Gov.br pode armazenar em:
    // - localStorage['govbr_token']
    // - localStorage['id_token']
    // - sessionStorage
    
    try {
        const token = localStorage.getItem('id_token') || 
                     localStorage.getItem('govbr_token') ||
                     sessionStorage.getItem('id_token');
        
        if (!token) return null;
        
        // Decodifica JWT (sem validar assinatura)
        const payload = JSON.parse(
            atob(token.split('.')[1])
        );
        
        return {
            cpf: payload.cpf,
            nome: payload.name || payload.full_name,
            email: payload.email,
            access_token: localStorage.getItem('access_token'),
            id_token: token,
            cnpjs: payload.cnpjs || [],
            nivel_acesso: payload.nivel_acesso || 'bronze'
        };
    } catch (e) {
        console.error('Erro ao extrair JWT:', e);
        return null;
    }
}

// Função principal
async function handleAuthCallback() {
    try {
        // Aguarda um pouco para Gov.br processar
        await new Promise(r => setTimeout(r, 1000));
        
        // Captura cookies
        const authData = captureGovBrCookies();
        
        // Envia para API
        const response = await fetch('/api/auth/browser-callback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(authData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccessMessage('✓ Autenticação realizada!');
            // Redirecionar para página principal
            setTimeout(() => window.location.href = '/', 2000);
        } else {
            showErrorMessage('❌ Erro na autenticação: ' + result.detail);
        }
    } catch (error) {
        showErrorMessage('❌ Erro: ' + error.message);
    }
}

// Detecta quando voltamos do Gov.br e captura
if (window.location.hash.includes('code=') || 
    window.location.search.includes('code=') ||
    localStorage.getItem('id_token')) {
    handleAuthCallback();
}
```

---

### 2️⃣ **Opção B: Usando Fetch com Cookies Automáticos (MAIS SIMPLES)**

Se Gov.br colocar os cookies automaticamente:

```javascript
async function completarAutenticacao() {
    try {
        // Aguarda processamento do Gov.br
        await new Promise(r => setTimeout(r, 1500));
        
        // Extrai token JWT do localStorage
        const idToken = localStorage.getItem('id_token');
        const accessToken = localStorage.getItem('access_token');
        
        if (!idToken) {
            showErrorMessage('Não foi possível capturar autenticação.');
            return;
        }
        
        // Decodifica JWT
        const payload = JSON.parse(atob(idToken.split('.')[1]));
        
        // Envia para API (cookies são enviados automaticamente pelo browser)
        const response = await fetch('/api/auth/browser-callback', {
            method: 'POST',
            credentials: 'include',  // Inclui cookies automaticamente
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                auth_token: getAuthTokenFromURL(),
                govbr_cookies: [
                    {
                        name: 'id_token',
                        value: idToken,
                        domain: window.location.hostname,
                        path: '/',
                        secure: true,
                        sameSite: 'Lax'
                    }
                ],
                sigef_cookies: [],
                jwt_payload: {
                    cpf: payload.cpf,
                    nome: payload.name,
                    email: payload.email,
                    access_token: accessToken
                }
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccessMessage('✓ Login realizado com sucesso!');
            setTimeout(() => window.location.href = '/', 1500);
        }
    } catch (error) {
        showErrorMessage('❌ Erro: ' + error.message);
    }
}

// Chama quando volta do Gov.br
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', completarAutenticacao);
} else {
    completarAutenticacao();
}
```

---

### 3️⃣ **Opção C: Detectar Redirecionamento Gov.br**

Se você sabe qual será a URL de callback do Gov.br:

```javascript
// Config
const AUTH_TOKEN = getTokenFromURL('token');
const GOVBR_CALLBACK_URL = 'https://acesso.gov.br/...';  // URL do seu servidor

// 1. Redireciona para Gov.br
function irParaGovBr() {
    // Constrói URL de autenticação Gov.br
    const govbrURL = new URL('https://acesso.gov.br/oauth');
    govbrURL.searchParams.set('client_id', CLIENT_ID);
    govbrURL.searchParams.set('redirect_uri', GOVBR_CALLBACK_URL);
    govbrURL.searchParams.set('response_type', 'code');
    govbrURL.searchParams.set('scope', 'openid email cpf');
    
    // Salva token para saber de volta
    sessionStorage.setItem('auth_token', AUTH_TOKEN);
    
    // Redireciona
    window.location.href = govbrURL.toString();
}

// 2. Volta de Gov.br (nesta mesma página)
async function processarRetornoGovBr() {
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    const state = params.get('state');
    
    if (!code) return;  // Não veio de Gov.br
    
    const authToken = sessionStorage.getItem('auth_token');
    
    // Troca 'code' por token com Gov.br
    // (Isso normalmente é feito no backend)
    
    // Captura os cookies que Gov.br colocou
    const cookies = document.cookie
        .split(';')
        .map(c => {
            const [name, value] = c.trim().split('=');
            return { name, value };
        });
    
    // Envia para nossa API
    const response = await fetch('/api/auth/browser-callback', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            auth_token: authToken,
            govbr_cookies: cookies,
            sigef_cookies: [],
            jwt_payload: { /* extrair do cookie ou header */ }
        })
    });
    
    // Continua...
}
```

---

## 📝 Funções Auxiliares Necessárias

Adicione estas funções ao seu JavaScript:

```javascript
// Extrai parâmetro da URL
function getTokenFromURL(paramName) {
    const params = new URLSearchParams(window.location.search);
    return params.get(paramName);
}

// Extrai token da URL e remove dela
function getAuthTokenFromURL() {
    const token = getTokenFromURL('token');
    if (token) {
        // Remove token da URL por segurança
        window.history.replaceState({}, 
            document.title, 
            window.location.pathname
        );
    }
    return token;
}

// Mostra mensagem de sucesso
function showSuccessMessage(msg) {
    const el = document.getElementById('status-message');
    if (el) {
        el.textContent = msg;
        el.style.color = '#10b981';
    }
    console.log(msg);
}

// Mostra mensagem de erro
function showErrorMessage(msg) {
    const el = document.getElementById('status-message');
    if (el) {
        el.textContent = msg;
        el.style.color = '#ef4444';
    }
    console.error(msg);
}

// Verifica timeout
function startTimeoutCounter() {
    let remaining = 600;  // 10 minutos
    const counterEl = document.getElementById('timeout-counter');
    
    setInterval(() => {
        remaining--;
        const mins = Math.floor(remaining / 60);
        const secs = remaining % 60;
        
        if (counterEl) {
            counterEl.textContent = 
                `${mins}:${secs.toString().padStart(2, '0')}`;
        }
        
        if (remaining <= 0) {
            showErrorMessage('⏰ Sessão expirou. Faça login novamente.');
            setTimeout(() => window.location.reload(), 3000);
        }
    }, 1000);
}

// Detecta quando voltamos de Gov.br
document.addEventListener('DOMContentLoaded', () => {
    const authToken = getAuthTokenFromURL();
    
    if (authToken) {
        // Voltamos do Gov.br
        completarAutenticacao();
    } else {
        // Primeira carga - mostrar botão de login
        document.getElementById('login-button').style.display = 'block';
        startTimeoutCounter();
    }
});
```

---

## 🔗 Integração Completa (Resumo)

Arquivo `src/api/v1/static/auth_page.py` precisa ter:

```python
HTML_AUTH_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Autenticação - Gov.br</title>
    <style>
        /* CSS existente aqui */
    </style>
</head>
<body>
    <!-- HTML existente aqui -->
    
    <script>
        // UMA DAS 3 OPÇÕES ACIMA
    </script>
</body>
</html>
"""
```

---

## 🧪 Teste da Captura de Cookies

No console do navegador (`F12 → Console`):

```javascript
// Ver cookies
console.log(document.cookie);

// Ver localStorage
console.log(localStorage);

// Simular callback (para teste)
fetch('/api/auth/browser-callback', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        auth_token: 'seu-token-aqui',
        govbr_cookies: [
            { name: 'test', value: 'teste', domain: 'localhost', path: '/' }
        ],
        sigef_cookies: [],
        jwt_payload: { cpf: '12345678901', nome: 'Teste' }
    })
}).then(r => r.json()).then(console.log);
```

---

## ✅ Checklist de Implementação

- [ ] Escolhi uma das 3 opções (A, B ou C)
- [ ] Integrei o JavaScript em `auth_page.py`
- [ ] Testei em `http://localhost:8000/auth-browser?token=...`
- [ ] Cookies são capturados
- [ ] Mensagem de sucesso aparece
- [ ] Sessão é criada na API
- [ ] Redireciona para página inicial

---

**Nota:** Se tiver dúvidas sobre qual opção usar, **recomendo Opção B** (mais simples e funciona com a maioria dos navegadores modernos).
