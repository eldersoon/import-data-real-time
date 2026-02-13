# Frontend - Sistema de Importação de Veículos

Frontend Next.js para o sistema de importação de veículos com atualizações em tempo real via Server-Sent Events (SSE).

## Tecnologias

- **Next.js 14** - Framework React
- **TypeScript** - Tipagem estática
- **Ant Design** - UI Kit
- **TanStack Query** - Gerenciamento de estado e cache
- **Axios** - Cliente HTTP
- **Server-Sent Events (SSE)** - Atualizações em tempo real

## Funcionalidades

- ✅ Upload múltiplo de arquivos (CSV, XLS, XLSX)
- ✅ Lista de jobs com atualizações em tempo real via SSE
- ✅ Detalhes do job com progresso em tempo real
- ✅ Lista de veículos importados com paginação
- ✅ Edição e exclusão de veículos
- ✅ Filtros avançados
- ✅ Limpeza de dados (admin)

## Instalação

```bash
npm install
```

## Desenvolvimento

```bash
npm run dev
```

A aplicação estará disponível em `http://localhost:3000`

## Build

```bash
npm run build
npm start
```

## Docker

```bash
docker-compose up
```

## Estrutura

```
src/
├── app/                    # Páginas Next.js (App Router)
│   ├── layout.tsx         # Layout principal
│   ├── page.tsx           # Página inicial
│   ├── upload/            # Página de upload
│   ├── jobs/              # Páginas de jobs
│   └── vehicles/          # Página de veículos
├── components/            # Componentes React
│   ├── StatusBadge/       # Badge de status
│   ├── JobCard/           # Card de job
│   ├── JobTable/          # Tabela de jobs
│   ├── UploadForm/        # Formulário de upload
│   ├── VehicleTable/      # Tabela de veículos
│   └── Navigation/        # Menu de navegação
├── hooks/                 # Custom hooks
│   ├── useJobSSE.ts       # Hook SSE para job individual
│   └── useJobsSSE.ts      # Hook SSE para lista de jobs
└── lib/                   # Utilitários
    ├── api/               # Cliente API e endpoints
    ├── types/             # TypeScript types
    └── utils/             # Funções utilitárias
```

## Variáveis de Ambiente

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## SSE (Server-Sent Events)

O frontend usa SSE para receber atualizações em tempo real dos jobs:

- **Endpoint**: `/api/v1/imports/stream?job_id={id}` (job específico)
- **Endpoint**: `/api/v1/imports/stream` (todos os jobs)
- **Eventos**: `job_status`, `job_progress`, `job_log`, `connected`

O `SSEClient` gerencia reconexão automática com backoff exponencial.
