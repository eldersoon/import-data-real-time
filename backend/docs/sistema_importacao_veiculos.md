# 📦 Sistema de Importação em Massa de Veículos

## 📌 Visão Geral

Sistema fullstack para importação assíncrona de planilhas contendo
cadastro de veículos.

A importação deve ocorrer em background via fila (AWS SQS), garantindo:

-   Escalabilidade
-   Rastreabilidade
-   Logs estruturados
-   Controle de status
-   Performance
-   Experiência visual em tempo real

O arquivo NÃO deve ser armazenado permanentemente. Após processamento,
deve ser removido.

------------------------------------------------------------------------

# 🧱 Stack Tecnológica

## Backend

-   Python
-   FastAPI
-   SQLAlchemy (ORM)
-   PostgreSQL
-   AWS SQS
-   Docker

## Frontend

-   Next.js
-   React
-   TanStack Query (ou equivalente)
-   Docker

## Infra

-   Docker para frontend
-   Docker para backend
-   PostgreSQL containerizado (dev)
-   Integração com AWS SQS

------------------------------------------------------------------------

# 🏗 Arquitetura Geral

## Fluxo Simplificado

1.  Upload da planilha via frontend
2.  Backend:
    -   Valida
    -   Cria registro em `import_jobs`
    -   Envia mensagem para AWS SQS
3.  Worker:
    -   Consome fila
    -   Processa em batches
    -   Atualiza progresso
    -   Registra logs
4.  Frontend:
    -   Lista jobs
    -   Exibe progresso em tempo real (polling)
    -   Permite visualizar dados importados

------------------------------------------------------------------------

# 📊 Modelo de Dados

## 1️⃣ Tabela: import_jobs

Responsável por rastrear cada importação.

    id UUID PK
    filename VARCHAR NOT NULL
    status VARCHAR CHECK (pending, processing, completed, failed) NOT NULL
    total_rows INTEGER
    processed_rows INTEGER DEFAULT 0
    error_rows INTEGER DEFAULT 0
    started_at TIMESTAMP NULL
    finished_at TIMESTAMP NULL
    created_at TIMESTAMP DEFAULT now()

Regras: - Status inicial: pending - Ao iniciar processamento:
processing - Ao concluir com sucesso: completed - Se falhar: failed -
processed_rows deve ser atualizado progressivamente

------------------------------------------------------------------------

## 2️⃣ Tabela: imported_vehicles

Cadastro normalizado de veículos.

    id UUID PK
    job_id UUID FK -> import_jobs(id)
    modelo VARCHAR NOT NULL
    placa VARCHAR(7) NOT NULL UNIQUE
    ano INTEGER NOT NULL
    valor_fipe NUMERIC(12,2) NOT NULL
    created_at TIMESTAMP DEFAULT now()
    updated_at TIMESTAMP DEFAULT now()

Regras: - Placa deve ser única - Ano entre 1900 e ano atual + 1 - Valor
FIPE deve ser positivo - Registro só pode ser criado via importação -
CRUD completo exceto CREATE manual

------------------------------------------------------------------------

## 3️⃣ Tabela: job_logs

    id UUID PK
    job_id UUID FK
    level VARCHAR CHECK (info, warning, error)
    message TEXT NOT NULL
    created_at TIMESTAMP DEFAULT now()

------------------------------------------------------------------------

# 📥 Requisitos de Importação

## Estrutura da Planilha

Colunas obrigatórias:

-   modelo
-   placa
-   ano
-   valor_fipe

Validações: - modelo: string não vazia - placa: padrão Mercosul válido -
ano: inteiro válido - valor_fipe: número decimal positivo

------------------------------------------------------------------------

# ⚙️ Regras de Processamento

-   Processamento assíncrono via AWS SQS
-   Worker independente
-   Leitura em batches (ex: 1000 linhas)
-   Inserção via bulk insert (SQLAlchemy)
-   Commit por lote
-   Atualização progressiva de processed_rows
-   Erros por linha não interrompem processamento total
-   Incrementar error_rows em caso de falha
-   Arquivo deve ser deletado após conclusão

------------------------------------------------------------------------

# 🔁 API - Backend

## Upload

POST /imports

Retorno:

    {
      "job_id": "uuid",
      "status": "pending"
    }

## Listar Jobs

GET /imports

## Detalhar Job

GET /imports/{id}

------------------------------------------------------------------------

# 🚗 API - Veículos

## Listagem

GET /vehicles

Query params: - page - page_size - placa - modelo - ano_min - ano_max

Retorno:

    {
      "data": [...],
      "total": 1000,
      "page": 1,
      "page_size": 10
    }

## Atualizar

PUT /vehicles/{id}

Permitido: - modelo - valor_fipe

Não permitido: - placa - job_id

## Deletar

DELETE /vehicles/{id}

## Criar

Não permitido manualmente.

------------------------------------------------------------------------

# 🖥 Frontend

## Tela Upload

-   Input arquivo
-   Botão enviar
-   Feedback visual
-   Redirecionamento para jobs

## Tela Jobs

Tabela com: - Arquivo - Status - Progresso - Ações

Atualização via polling (3s)

## Tela Veículos

Tabela paginada com: - Modelo - Placa - Ano - Valor FIPE - Editar /
Deletar

Filtros: - Placa - Modelo - Range de ano

------------------------------------------------------------------------

# ⚡ Requisitos Não Funcionais

-   Processar mínimo 100k registros
-   Não bloquear HTTP
-   Timeout máximo 5s
-   Logs estruturados JSON
-   Dockerizado
-   Arquitetura escalável

------------------------------------------------------------------------

# 🎯 Objetivo Arquitetural

Demonstrar: - Processamento distribuído - Arquitetura orientada a
eventos - Escalabilidade - Observabilidade - Clean Architecture
