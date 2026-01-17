# 🚀 Deploy Gov-Auth API

## Arquitetura

```
                    ┌─────────────────────────────────────────────────────┐
                    │                   SERVIDOR                          │
                    │                                                     │
  Internet ──────►  │  Nginx (443)                                        │
                    │     │                                               │
                    │     ├── cherihub.cloud ──────► cherihub-home :3001  │
                    │     ├── sicar.cherihub.cloud                        │
                    │     │      ├── /api ─────────► sicar-api :8000      │
                    │     │      └── / ────────────► sicar-frontend :3000 │
                    │     └── govauth.cherihub.cloud ► gov-auth-api :8001 │
                    │                                                     │
                    └─────────────────────────────────────────────────────┘
```

## Setup Inicial (Uma vez)

### 1. No servidor

```bash
# Baixar e executar script de setup
curl -sSL https://raw.githubusercontent.com/SEU_USUARIO/gov-auth/main/scripts/setup-server.sh | bash

# Ou manualmente:
mkdir -p /opt/gov-auth/data/{sessions,downloads,logs}

# Gerar chaves
openssl rand -hex 32  # Para API_KEY
openssl rand -hex 32  # Para SECRET_KEY

# Criar .env
cat > /opt/gov-auth/.env << EOF
API_KEY=sua-api-key-gerada
SECRET_KEY=sua-secret-key-gerada
EOF
chmod 600 /opt/gov-auth/.env
```

### 2. Configurar DNS

Adicione um registro A ou CNAME:
- `govauth.cherihub.cloud` → IP do servidor

### 3. Configurar Nginx

Adicione ao `/etc/nginx/sites-enabled/default`:

```nginx
# GOV-AUTH - govauth.cherihub.cloud
server {
    listen 443 ssl;
    server_name govauth.cherihub.cloud;
    ssl_certificate /etc/letsencrypt/live/cherihub.cloud/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cherihub.cloud/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
```

Adicione também no redirect HTTP (bloco listen 80):
```nginx
server_name cherihub.cloud www.cherihub.cloud sicar.cherihub.cloud govauth.cherihub.cloud;
```

Teste e recarregue:
```bash
nginx -t && systemctl reload nginx
```

### 4. Certificado SSL (se necessário)

Se o certificado atual não cobrir `govauth.cherihub.cloud`:

```bash
certbot --nginx -d govauth.cherihub.cloud
```

### 5. Gerar chave SSH para GitHub Actions

```bash
# No servidor
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/github_actions -N ""
cat ~/.ssh/github_actions.pub >> ~/.ssh/authorized_keys

# Copiar a chave PRIVADA para usar no GitHub
cat ~/.ssh/github_actions
```

### 6. Configurar Secrets no GitHub

No repositório, vá em **Settings → Secrets and variables → Actions** e adicione:

| Secret | Valor |
|--------|-------|
| `SSH_PRIVATE_KEY` | Conteúdo de `~/.ssh/github_actions` |
| `SERVER_HOST` | IP ou hostname do servidor |
| `SERVER_USER` | `root` |

## CI/CD

O pipeline é acionado automaticamente em:
- Push na branch `main`
- Manualmente via "Actions" → "Run workflow"

### Fluxo

```
Push main → Tests → Build Docker → Deploy → Health Check
```

### Logs do deploy

```bash
# No servidor
docker logs -f gov-auth-api

# Logs do Nginx
tail -f /var/log/nginx/access.log
```

## Comandos Úteis

```bash
# Ver status
docker ps | grep gov-auth

# Logs
docker logs -f gov-auth-api

# Restart
cd /opt/gov-auth && docker compose restart

# Parar
cd /opt/gov-auth && docker compose down

# Atualizar manualmente
cd /opt/gov-auth
docker compose pull
docker compose up -d

# Health check
curl https://govauth.cherihub.cloud/health
```

## Endpoints

Após o deploy:

| Endpoint | URL |
|----------|-----|
| Health | https://govauth.cherihub.cloud/health |
| Docs | https://govauth.cherihub.cloud/docs |
| API | https://govauth.cherihub.cloud/api/v1/... |

## Troubleshooting

### Container não inicia

```bash
docker logs gov-auth-api
docker compose -f /opt/gov-auth/docker-compose.yml config
```

### Erro de permissão

```bash
chown -R 1000:1000 /opt/gov-auth/data
```

### Nginx 502 Bad Gateway

```bash
# Verificar se container está rodando
docker ps | grep gov-auth

# Verificar porta
curl http://localhost:8001/health
```

### Renovar certificado

```bash
certbot renew --dry-run
certbot renew
```
