# Sistema de Importação em Massa de Veículos - Backend

Sistema backend para importação assíncrona de planilhas contendo cadastro de veículos, utilizando FastAPI, PostgreSQL, AWS SQS e processamento em background.

## 📋 Características

- **Processamento Assíncrono**: Upload de arquivos e processamento via fila (AWS SQS)
- **Escalável**: Worker independente que pode ser escalado horizontalmente
- **Rastreável**: Logs estruturados e controle de status de cada importação
- **Performance**: Processamento em batches (1000 registros por vez)
- **Validações**: Validação completa de dados (placa Mercosul, ano, valor FIPE)
- **API REST**: Endpoints documentados com Swagger/ReDoc
- **Testes**: Cobertura de testes unitários e de integração

## 🏗 Arquitetura

O sistema segue Clean Architecture com separação clara de responsabilidades:

```
app/
├── api/              # Camada de apresentação (FastAPI routes)
├── core/             # Configurações e dependências
├── domain/           # Entidades e regras de negócio
├── infrastructure/   # Implementações concretas (DB, SQS, storage)
├── services/         # Casos de uso e lógica de negócio
└── workers/          # Workers para processamento assíncrono
```

## 🚀 Tecnologias

- **Python 3.11**
- **FastAPI** - Framework web moderno e rápido
- **SQLAlchemy** - ORM para PostgreSQL
- **Alembic** - Migrações de banco de dados
- **boto3** - SDK AWS para SQS
- **pandas** - Processamento de planilhas
- **pytest** - Framework de testes
- **structlog** - Logs estruturados JSON

## 📦 Instalação

### Pré-requisitos

- Python 3.11+
- Docker e Docker Compose
- PostgreSQL (ou usar Docker Compose)

### Setup Local

1. Clone o repositório:
```bash
cd backend
```

2. Crie um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
```bash
cp .env.example .env
# Edite o .env com suas configurações
```

5. Inicie os serviços com Docker Compose:
```bash
docker-compose up -d
```

6. Execute as migrações:
```bash
alembic upgrade head
```

7. Crie a fila SQS (se usar LocalStack):
```bash
# Opção 1: Usando o script
./scripts/init_localstack.sh

# Opção 2: Manualmente
aws --endpoint-url=http://localhost:4566 sqs create-queue --queue-name vehicle-import-queue
```

**Nota**: Se estiver usando Docker Compose, o worker criará a fila automaticamente na inicialização.

## 🏃 Executando

### API

```bash
uvicorn app.main:app --reload
```

A API estará disponível em `http://localhost:8000`

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Worker

```bash
python -m app.workers
```

O worker irá consumir mensagens da fila SQS e processar os jobs de importação.

## 📡 API Endpoints

### Import Jobs

- `POST /api/v1/imports` - Upload de arquivo e criação de job
- `GET /api/v1/imports` - Lista jobs com paginação
- `GET /api/v1/imports/{id}` - Detalhes de um job (inclui logs)

### Veículos

- `GET /api/v1/vehicles` - Lista veículos com filtros e paginação
- `GET /api/v1/vehicles/{id}` - Detalhes de um veículo
- `PUT /api/v1/vehicles/{id}` - Atualiza veículo (apenas modelo e valor_fipe)
- `DELETE /api/v1/vehicles/{id}` - Deleta veículo

## 📊 Modelo de Dados

### import_jobs
Rastreia cada importação com status, progresso e timestamps.

### imported_vehicles
Cadastro de veículos importados com validações:
- Placa única (padrão Mercosul)
- Ano entre 1900 e ano atual + 1
- Valor FIPE positivo

### job_logs
Logs estruturados de cada job (info, warning, error).

## 🔄 Fluxo de Processamento

1. **Upload**: Cliente envia arquivo via API
2. **Validação**: Backend valida arquivo e cria job (status: pending)
3. **Fila**: Job é enviado para AWS SQS
4. **Worker**: Worker consome mensagem e processa em batches
5. **Progresso**: Status e progresso são atualizados em tempo real
6. **Conclusão**: Arquivo é removido e status atualizado (completed/failed)

## ✅ Validações

- **Placa**: Padrão Mercosul (`ABC1D23`)
- **Ano**: Entre 1900 e ano atual + 1
- **Valor FIPE**: Deve ser positivo
- **Modelo**: Não pode ser vazio

## 🧪 Testes

Execute os testes:

```bash
# Todos os testes
pytest

# Apenas testes unitários
pytest tests/unit

# Apenas testes de integração
pytest tests/integration

# Com cobertura
pytest --cov=app --cov-report=html
```

## 📝 Logs

Os logs são estruturados em formato JSON e incluem:
- Nível (info, warning, error)
- Contexto (job_id, request_id, etc)
- Timestamp ISO 8601
- Mensagem descritiva

## 🐳 Docker

### Build

```bash
docker-compose build
```

### Executar

```bash
docker-compose up
```

### Serviços

- **backend**: API FastAPI (porta 8000)
- **postgres**: Banco de dados PostgreSQL (porta 5432)
- **localstack**: AWS LocalStack para SQS local (porta 4566)
- **worker**: Worker de processamento

## 🔧 Configuração

Variáveis de ambiente principais:

```env
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
SQS_QUEUE_URL=http://localhost:4566/000000000000/vehicle-import-queue
AWS_ENDPOINT_URL=http://localhost:4566  # Para LocalStack
UPLOAD_DIR=./uploads
BATCH_SIZE=1000
```

## 📈 Performance

- Processa mínimo 100k registros
- Timeout máximo de 5s para upload (apenas validação inicial)
- Processamento em batches de 1000 registros
- Bulk insert para otimização
- Worker escalável (múltiplas instâncias)

## 🔒 Segurança

- Validação de tipos de arquivo
- Limite de tamanho de arquivo
- Sanitização de inputs
- Prepared statements (SQLAlchemy)
- Variáveis de ambiente para secrets

## 📚 Estrutura de Arquivos

```
backend/
├── app/
│   ├── api/              # Rotas e schemas
│   ├── core/             # Config, database, logging
│   ├── domain/           # Modelos de domínio
│   ├── infrastructure/   # SQS, file storage, repositories
│   ├── services/         # Lógica de negócio
│   └── workers/          # Processamento assíncrono
├── alembic/              # Migrações
├── tests/                # Testes
├── docker-compose.yml    # Orquestração
├── Dockerfile            # Container
└── requirements.txt      # Dependências
```

## 🤝 Contribuindo

1. Crie uma branch para sua feature
2. Faça commit das mudanças
3. Execute os testes
4. Abra um Pull Request

## 📄 Licença

Este projeto é privado e proprietário.
