# Gov.br Auth Frontend

Interface web para testar a API de autenticação Gov.br e integração com SIGEF.

## 🚀 Stack

- **React 18** - Framework UI
- **TypeScript** - Tipagem estática
- **Vite** - Build tool
- **Tailwind CSS** - Estilos
- **React Router** - Navegação
- **Axios** - HTTP Client
- **Lucide React** - Ícones

## 📦 Instalação

```bash
# Na pasta frontend/
npm install
```

## 🏃 Executar

```bash
# Desenvolvimento
npm run dev

# Acesse: http://localhost:3000
```

## ⚙️ Configuração

O frontend usa proxy para o backend:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000 (proxy automático)

As chamadas `/api/*` são automaticamente redirecionadas para o backend.

## 📁 Estrutura

```
src/
├── components/     # Componentes reutilizáveis
│   ├── Layout.tsx
│   ├── AuthStatus.tsx
│   ├── ParcelaDownload.tsx
│   └── BatchDownload.tsx
├── pages/          # Páginas da aplicação
│   ├── DashboardPage.tsx
│   ├── AuthPage.tsx
│   ├── DownloadPage.tsx
│   └── BatchPage.tsx
├── services/       # Serviços de API
│   ├── api.ts
│   ├── authService.ts
│   └── sigefService.ts
├── types/          # TypeScript types
│   └── api.ts
├── App.tsx         # Componente principal
├── main.tsx        # Entry point
└── index.css       # Estilos globais
```

## 🎨 Telas

- **Dashboard** - Visão geral do sistema
- **Autenticação** - Login/logout Gov.br
- **Download** - Busca e download de parcela individual (CSVs + Memorial PDF)
- **Lote** - Download em batch de múltiplas parcelas

## 🎯 Funcionalidades

### Download Individual
- Busca por código da parcela
- Visualização de informações da parcela
- Download de CSVs (Parcela, Vértice, Limite)
- **Download de Memorial Descritivo (PDF)** ✨ *Novo*
- Download no servidor ou direto no navegador

### Download em Lote
- Múltiplas parcelas simultaneamente
- Seleção de tipos de arquivo
- Acompanhamento de progresso
- Relatório de sucessos/falhas

## 🔧 Build

```bash
npm run build
```

Os arquivos serão gerados em `dist/`.
