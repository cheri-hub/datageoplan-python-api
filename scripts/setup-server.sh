#!/bin/bash
# ============================================
# Setup inicial do Gov-Auth no servidor
# Execute como root no servidor
# ============================================

set -e

echo "🚀 Configurando Gov-Auth no servidor..."

# ============================================
# 1. Criar diretórios
# ============================================
echo "📁 Criando diretórios..."
mkdir -p /opt/gov-auth/data/{sessions,downloads,logs}
chmod -R 755 /opt/gov-auth

# ============================================
# 2. Criar arquivo .env
# ============================================
echo "🔐 Configurando variáveis de ambiente..."

# Gera chaves seguras
API_KEY=$(openssl rand -hex 32)
SECRET_KEY=$(openssl rand -hex 32)

cat > /opt/gov-auth/.env << EOF
# Gov-Auth API - Variáveis de Ambiente
# Gerado em: $(date)

API_KEY=${API_KEY}
SECRET_KEY=${SECRET_KEY}
EOF

chmod 600 /opt/gov-auth/.env

echo ""
echo "🔑 API_KEY gerada: ${API_KEY}"
echo "   (Guarde esta chave para usar na integração!)"
echo ""

# ============================================
# 3. Configurar Nginx
# ============================================
echo "🌐 Configurando Nginx..."

# Backup da config atual
cp /etc/nginx/sites-enabled/default /etc/nginx/sites-enabled/default.bak.$(date +%Y%m%d%H%M%S)

# Adiciona configuração do gov-auth
cat >> /etc/nginx/sites-enabled/default << 'NGINX_CONFIG'

# ============================================
# GOV-AUTH - govauth.cherihub.cloud
# ============================================
server {
    listen 443 ssl;
    server_name govauth.cherihub.cloud;
    ssl_certificate /etc/letsencrypt/live/cherihub.cloud/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cherihub.cloud/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # API Gov-Auth
    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts maiores para operações de autenticação
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
NGINX_CONFIG

# Adiciona redirect HTTP para o novo subdomínio
sed -i 's/server_name cherihub.cloud www.cherihub.cloud sicar.cherihub.cloud;/server_name cherihub.cloud www.cherihub.cloud sicar.cherihub.cloud govauth.cherihub.cloud;/' /etc/nginx/sites-enabled/default

# Testa configuração
echo "🔍 Testando configuração Nginx..."
nginx -t

# Recarrega Nginx
echo "♻️ Recarregando Nginx..."
systemctl reload nginx

# ============================================
# 4. Configurar certificado SSL
# ============================================
echo "🔒 Verificando certificado SSL..."
# O certificado wildcard ou SAN já deve cobrir govauth.cherihub.cloud
# Se não, execute: certbot --nginx -d govauth.cherihub.cloud

# ============================================
# 5. Criar docker-compose.yml inicial
# ============================================
cat > /opt/gov-auth/docker-compose.yml << 'COMPOSE'
# Gov.br Auth API - Docker Compose Produção
services:
  api:
    image: gov-auth-api:latest
    container_name: gov-auth-api
    ports:
      - "8001:8000"
    env_file:
      - .env
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
      - LOG_LEVEL=INFO
      - HOST=0.0.0.0
      - PORT=8000
      - CORS_ORIGINS=https://govauth.cherihub.cloud,https://cherihub.cloud
    volumes:
      - /opt/gov-auth/data/sessions:/app/data/sessions
      - /opt/gov-auth/data/downloads:/app/data/downloads
      - /opt/gov-auth/data/logs:/app/data/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 15s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
COMPOSE

# ============================================
# 6. Instruções finais
# ============================================
echo ""
echo "============================================"
echo "✅ Setup concluído!"
echo "============================================"
echo ""
echo "📋 Próximos passos:"
echo ""
echo "1. Adicione o DNS para govauth.cherihub.cloud apontando para este servidor"
echo ""
echo "2. Configure os secrets no GitHub:"
echo "   - SSH_PRIVATE_KEY: Chave SSH privada para acessar o servidor"
echo "   - SERVER_HOST: $(hostname -I | awk '{print $1}')"
echo "   - SERVER_USER: root"
echo ""
echo "3. Se precisar de certificado SSL separado:"
echo "   certbot --nginx -d govauth.cherihub.cloud"
echo ""
echo "4. Para testar manualmente:"
echo "   cd /opt/gov-auth"
echo "   docker compose up -d"
echo "   curl http://localhost:8001/health"
echo ""
echo "🔑 Sua API_KEY: ${API_KEY}"
echo ""
