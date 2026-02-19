# Arquitetura e Fluxo do Sistema de Importação de Veículos

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura em Camadas](#arquitetura-em-camadas)
3. [Fluxo Completo de Importação](#fluxo-completo-de-importação)
4. [Detalhamento das Camadas](#detalhamento-das-camadas)
5. [Comunicação Frontend-Backend](#comunicação-frontend-backend)
6. [Sistema de Eventos e SSE](#sistema-de-eventos-e-sse)
7. [Tratamento de Erros e Fallbacks](#tratamento-de-erros-e-fallbacks)
8. [Decisões Arquiteturais](#decisões-arquiteturais)

---

## 🎯 Visão Geral

Este sistema implementa uma arquitetura de **importação assíncrona de veículos** a partir de planilhas (CSV/Excel), utilizando processamento em background com filas SQS e comunicação em tempo real via Server-Sent Events (SSE).

### Componentes Principais

- **Frontend**: Next.js 14 com TypeScript, React Query e Ant Design
- **Backend**: FastAPI (Python) com arquitetura em camadas
- **Fila de Processamento**: AWS SQS (com suporte a LocalStack para desenvolvimento)
- **Banco de Dados**: PostgreSQL
- **Comunicação em Tempo Real**: Server-Sent Events (SSE)

---

## 🏗️ Arquitetura em Camadas

O sistema segue uma **arquitetura em camadas** (Layered Architecture) com separação clara de responsabilidades:

```
┌─────────────────────────────────────────────────────────────┐
│                    CAMADA DE APRESENTAÇÃO                   │
│                    (Frontend - Next.js)                     │
│  - Componentes React                                        │
│  - Hooks customizados (useJobSSE, useJobs)                 │
│  - API Client (Axios)                                       │
│  - SSE Client                                               │
└─────────────────────────────────────────────────────────────┘
                            ↕ HTTP/SSE
┌─────────────────────────────────────────────────────────────┐
│                    CAMADA DE API                             │
│                    (FastAPI Routes)                         │
│  - /api/v1/imports                                          │
│  - /api/v1/vehicles                                         │
│  - /api/v1/admin                                            │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                    CAMADA DE SERVIÇOS                        │
│                    (Business Logic)                         │
│  - ImportService                                            │
│  - SpreadsheetParser                                        │
│  - ValidationService                                        │
│  - VehicleService                                           │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                    CAMADA DE DOMÍNIO                         │
│                    (Domain Models)                          │
│  - ImportJob                                                │
│  - ImportedVehicle                                          │
│  - JobLog                                                   │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                    CAMADA DE INFRAESTRUTURA                 │
│                    (Data Access & External)                 │
│  - Repositories (ImportJobRepository, VehicleRepository)   │
│  - FileStorage                                              │
│  - SQS (Publisher/Consumer)                                 │
│  - Events (JobEventManager)                                 │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                    CAMADA DE WORKERS                         │
│                    (Background Processing)                  │
│  - ImportWorker (SQS Consumer)                              │
│  - JobProcessor                                             │
└─────────────────────────────────────────────────────────────┘
```

### Princípios da Arquitetura

1. **Separação de Responsabilidades**: Cada camada tem uma responsabilidade única
2. **Dependency Inversion**: Camadas superiores dependem de abstrações (interfaces)
3. **Single Responsibility**: Cada classe/módulo tem uma única responsabilidade
4. **Dependency Injection**: Dependências são injetadas via construtores

---

## 🔄 Fluxo Completo de Importação

### 1. Upload da Planilha (Frontend → Backend)

#### 1.1. Frontend: UploadForm Component

O usuário seleciona um arquivo CSV/Excel através do componente `UploadForm`:

```typescript
// frontend/src/components/UploadForm/index.tsx
const handleUpload = async () => {
  const result = await createJob.mutateAsync(file);
  // Redireciona para página de jobs
  router.push('/jobs');
};
```

**O que acontece:**
- Validação de tipo de arquivo (CSV, XLS, XLSX)
- Validação de tamanho (máximo 20MB)
- Upload via React Query mutation (`useCreateJob`)

#### 1.2. API Client: Envio da Requisição

```typescript
// frontend/src/lib/api/hooks/useJobs.ts
export const useCreateJob = () => {
  return useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      const response = await apiClient.post('/imports', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return response.data;
    },
  });
};
```

**O que acontece:**
- Criação de `FormData` com o arquivo
- Requisição POST para `/api/v1/imports`
- Retorno do `job_id` e `status: "pending"`

### 2. Criação do Job (Backend - API Layer)

#### 2.1. Rota de Importação

```python
# backend/app/api/routes/imports.py
@router.post("", response_model=ImportJobCreateResponse, status_code=201)
async def create_import_job(
    file: UploadFile = File(...),
    db: Session = Depends(get_database),
):
    service = ImportService(db)
    job_id = service.create_import_job(file)
    return ImportJobCreateResponse(job_id=str(job_id), status="pending")
```

**O que acontece:**
- Recebe o arquivo via FastAPI `UploadFile`
- Injeta dependência de sessão do banco (`get_database`)
- Delega criação do job para `ImportService`
- Retorna resposta com `job_id` e status inicial

**Por que essa estrutura:**
- A rota é apenas um ponto de entrada HTTP
- Toda lógica de negócio fica na camada de serviços
- Facilita testes e manutenção

### 3. Processamento do Upload (Service Layer)

#### 3.1. ImportService: Criação do Job

```python
# backend/app/services/import_service.py
class ImportService:
    def __init__(self, db: Session):
        self.db = db
        self.job_repository = ImportJobRepository(db)
        self.file_storage = FileStorage()
        self.sqs_publisher = SQSPublisher()
        self.parser = SpreadsheetParser()

    def create_import_job(self, file: UploadFile) -> uuid.UUID:
        # 1. Criar registro do job no banco
        job = self.job_repository.create(filename=file.filename or "unknown")
        
        # 2. Salvar arquivo temporariamente
        file_path = self.file_storage.save_file(file, job.id)
        
        # 3. Contar total de linhas
        total_rows = self.parser.count_rows(file_path)
        job.total_rows = total_rows
        self.db.commit()
        
        # 4. Publicar job na fila SQS
        self.sqs_publisher.publish_job(job.id)
        
        return job.id
```

**O que acontece (passo a passo):**

1. **Criação do Job no Banco**:
   - `ImportJobRepository.create()` cria registro com status `PENDING`
   - Gera UUID único para o job
   - Salva nome do arquivo e timestamps

2. **Armazenamento Temporário**:
   - `FileStorage.save_file()` salva arquivo em `./uploads/{job_id}.{ext}`
   - Arquivo fica disponível para processamento posterior

3. **Contagem de Linhas**:
   - `SpreadsheetParser.count_rows()` lê arquivo e conta linhas
   - Atualiza `total_rows` no job
   - **Motivo**: Permite mostrar progresso ao usuário

4. **Publicação na Fila SQS**:
   - `SQSPublisher.publish_job()` envia mensagem para fila
   - Mensagem contém apenas `{"job_id": "uuid"}`
   - **Motivo**: Desacopla recebimento do processamento

**Por que essa ordem:**
- Job deve existir antes de processar
- Arquivo deve estar salvo antes de contar linhas
- SQS é o último passo para não perder mensagem se algo falhar antes

### 4. Processamento Assíncrono (Worker Layer)

#### 4.1. ImportWorker: Consumidor SQS

```python
# backend/app/workers/import_worker.py
class ImportWorker:
    def __init__(self):
        self.consumer = SQSConsumer()
        self.processor = JobProcessor()
    
    def start(self):
        while self.running:
            # 1. Receber mensagem da fila
            messages = self.consumer.receive_messages(max_messages=1, wait_time_seconds=20)
            
            for message in messages:
                parsed = self.consumer.parse_message(message)
                job_id = uuid.UUID(parsed['job_id'])
                
                # 2. Processar job
                self.processor.process_job(job_id)
                
                # 3. Deletar mensagem após sucesso
                self.consumer.delete_message(parsed['receipt_handle'])
```

**O que acontece:**
- Worker roda em loop infinito
- Long polling (20s) para reduzir requisições vazias
- Processa uma mensagem por vez
- Deleta mensagem apenas após sucesso (garante reprocessamento em caso de erro)

**Por que long polling:**
- Reduz custo de requisições AWS
- Melhora latência (menos polling vazio)
- Mais eficiente que short polling

#### 4.2. JobProcessor: Processamento do Arquivo

```python
# backend/app/workers/processor.py
class JobProcessor:
    def process_job(self, job_id: uuid.UUID) -> None:
        # 1. Buscar job e validar arquivo
        job = job_repository.get_by_id(job_id)
        file_path = self.file_storage.get_file_path(job_id, file_ext)
        
        # 2. Atualizar status para PROCESSING
        job_repository.update_status(job_id, ImportJobStatus.PROCESSING, started_at=datetime.utcnow())
        self._publish_event_async(job_id, "status_update", {...})
        
        # 3. Processar arquivo em chunks
        total_processed = 0
        total_errors = 0
        
        for chunk_df in self.parser.read_file(file_path, chunk_size=batch_size):
            vehicles_to_insert = []
            batch_placas = []
            
            # 3.1. Coletar placas do chunk
            for _, row in chunk_df.iterrows():
                batch_placas.append(row['placa'].strip().upper())
            
            # 3.2. Verificar duplicatas no banco
            existing_placas = vehicle_repository.get_placas_in_batch(batch_placas)
            existing_placas_set = set(existing_placas)
            
            # 3.3. Processar cada linha
            for row_number, row in chunk_df.iterrows():
                row_dict = row.to_dict()
                
                # Validar dados
                is_valid, errors = self.validator.validate_vehicle(row_dict, row_number)
                
                # Verificar duplicatas
                placa = row_dict['placa'].strip().upper()
                if placa in existing_placas_set or placa in seen_in_batch:
                    total_errors += 1
                    log_repository.create(job_id, "warning", f"Placa '{placa}' duplicada")
                    continue
                
                if not is_valid:
                    total_errors += 1
                    log_repository.create(job_id, "error", f"Linha {row_number + 1}: {', '.join(errors)}")
                    continue
                
                # Preparar dados do veículo
                vehicle_data = {
                    'job_id': job_id,
                    'modelo': str(row_dict['modelo']).strip(),
                    'placa': placa,
                    'ano': int(row_dict['ano']),
                    'valor_fipe': Decimal(str(row_dict['valor_fipe'])),
                }
                vehicles_to_insert.append(vehicle_data)
            
            # 3.4. Inserção em lote (bulk insert)
            if vehicles_to_insert:
                vehicle_repository.create_bulk(vehicles_to_insert)
                total_processed += len(vehicles_to_insert)
            
            # 3.5. Atualizar progresso
            job_repository.update_progress(job_id, processed_rows=total_processed, error_rows=total_errors)
            
            # 3.6. Publicar evento de progresso (throttled)
            if (datetime.utcnow() - self._last_progress_update.get(str(job_id), datetime.min)).total_seconds() >= 1:
                self._publish_event_async(job_id, "progress_update", {...})
        
        # 4. Finalizar job
        job_repository.update_status(job_id, ImportJobStatus.COMPLETED, finished_at=datetime.utcnow())
        self._publish_event_async(job_id, "status_update", {...})
        
        # 5. Deletar arquivo processado
        self.file_storage.delete_file(job_id, file_ext)
```

**Detalhamento do Processamento:**

##### 3.1. Leitura em Chunks

```python
# backend/app/services/spreadsheet_parser.py
class SpreadsheetParser:
    @classmethod
    def read_file(cls, file_path: str, chunk_size: int = 1000) -> Iterator[pd.DataFrame]:
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.csv':
            # CSV: leitura em chunks nativa do pandas
            for chunk in pd.read_csv(file_path, chunksize=chunk_size):
                cls._validate_columns(chunk)
                yield chunk
        elif file_ext in ['.xlsx', '.xls']:
            # Excel: precisa ler tudo primeiro, depois chunk manual
            full_df = pd.read_excel(file_path)
            cls._validate_columns(full_df)
            for i in range(0, len(full_df), chunk_size):
                yield full_df.iloc[i:i + chunk_size]
```

**Por que chunks:**
- Arquivos grandes não cabem na memória
- Permite processamento progressivo
- Reduz uso de memória
- Permite atualização de progresso durante processamento

**Por que Excel precisa ler tudo primeiro:**
- Pandas não suporta leitura em chunks para Excel
- Alternativa seria usar bibliotecas específicas (openpyxl, xlrd)
- Trade-off: mais memória vs. simplicidade

##### 3.2. Validação de Dados

```python
# backend/app/services/validation_service.py
class ValidationService:
    @staticmethod
    def validate_vehicle(row: Dict[str, Any], row_number: int) -> Tuple[bool, List[str]]:
        errors = []
        
        # Campos obrigatórios
        required_fields = ['modelo', 'placa', 'ano', 'valor_fipe']
        for field in required_fields:
            if field not in row or row[field] is None:
                errors.append(f"Campo '{field}' é obrigatório")
        
        # Validação de placa (formato Mercosul)
        placa = str(row['placa']).strip()
        if not ValidationService.validate_placa(placa):
            errors.append(f"Placa '{placa}' inválida")
        
        # Validação de ano (1900 até ano atual + 1)
        ano = int(row['ano'])
        if not ValidationService.validate_ano(ano):
            errors.append(f"Ano '{ano}' inválido")
        
        # Validação de valor FIPE (deve ser positivo)
        valor_fipe = float(row['valor_fipe'])
        if not ValidationService.validate_valor_fipe(valor_fipe):
            errors.append(f"Valor FIPE '{valor_fipe}' inválido")
        
        return len(errors) == 0, errors
```

**Validações implementadas:**
- **Placa**: Formato Mercosul (ABC1D23) ou antigo (ABC1234)
- **Ano**: Entre 1900 e ano atual + 1
- **Valor FIPE**: Deve ser positivo
- **Campos obrigatórios**: modelo, placa, ano, valor_fipe

**Por que validação separada:**
- Reutilizável em outros contextos
- Fácil de testar isoladamente
- Regras de negócio centralizadas

##### 3.3. Verificação de Duplicatas

```python
# Verificação em batch para performance
batch_placas = [row['placa'].strip().upper() for row in chunk_df.iterrows()]
existing_placas = vehicle_repository.get_placas_in_batch(batch_placas)
existing_placas_set = set(existing_placas)

# Verificação dentro do próprio batch
seen_in_batch = set()
if placa in existing_placas_set or placa in seen_in_batch:
    # Duplicata encontrada
    total_errors += 1
```

**Por que verificação em batch:**
- Uma query SQL para todo o chunk vs. N queries (uma por linha)
- Reduz drasticamente round-trips ao banco
- Melhora performance em arquivos grandes

**Por que verificar dentro do batch também:**
- Arquivo pode ter duplicatas internas
- Evita inserir mesmo veículo duas vezes no mesmo job

##### 3.4. Inserção em Lote (Bulk Insert)

```python
# backend/app/infrastructure/repositories/vehicle_repository.py
def create_bulk(self, vehicles_data: List[Dict[str, Any]]) -> int:
    if not vehicles_data:
        return 0
    
    # Usa bulk_insert_mappings do SQLAlchemy
    self.db.bulk_insert_mappings(ImportedVehicle, vehicles_data)
    self.db.commit()
    return len(vehicles_data)
```

**Por que bulk insert:**
- Uma transação para múltiplos registros
- Muito mais rápido que inserts individuais
- Reduz overhead de transações

**Trade-off:**
- Não retorna objetos criados (apenas count)
- Não valida constraints individuais antes de inserir
- Aceitável para importação em massa

### 5. Atualização de Status em Tempo Real (SSE)

#### 5.1. Publicação de Eventos (Backend)

```python
# backend/app/workers/processor.py
def _publish_event_async(self, job_id: str, event_type: str, data: Dict[str, Any]) -> None:
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(self.event_manager.publish(job_id, event_type, data))
        else:
            loop.run_until_complete(self.event_manager.publish(job_id, event_type, data))
    except RuntimeError:
        asyncio.run(self.event_manager.publish(job_id, event_type, data))
```

**O que acontece:**
- Worker roda em thread síncrona
- Event manager precisa de event loop assíncrono
- Detecta se há loop rodando e usa ou cria um novo
- Publica evento de forma assíncrona (fire-and-forget)

**Por que assíncrono:**
- Não bloqueia processamento do job
- SSE é assíncrono por natureza
- Worker continua processando mesmo se evento falhar

#### 5.2. JobEventManager: Pub/Sub In-Memory

```python
# backend/app/infrastructure/events/job_events.py
class JobEventManager:
    def __init__(self):
        # Dicionário: job_id -> lista de filas (subscribers)
        self._subscribers: Dict[str, List[asyncio.Queue]] = {"__all__": []}
        self._lock = asyncio.Lock()
    
    async def subscribe(self, job_id: Optional[str]) -> asyncio.Queue:
        async with self._lock:
            queue = asyncio.Queue()
            key = job_id or "__all__"
            if key not in self._subscribers:
                self._subscribers[key] = []
            self._subscribers[key].append(queue)
            return queue
    
    async def publish(self, job_id: str, event_type: str, data: Dict[str, Any]) -> None:
        event = {
            "job_id": job_id,
            "event_type": event_type,
            "data": data,
        }
        
        async with self._lock:
            # Enviar para subscribers específicos do job
            if job_id in self._subscribers:
                for queue in self._subscribers[job_id]:
                    await queue.put(event)
            
            # Enviar para subscribers de todos os jobs
            if "__all__" in self._subscribers:
                for queue in self._subscribers["__all__"]:
                    await queue.put(event)
```

**Arquitetura Pub/Sub:**
- **Publisher**: `JobProcessor` publica eventos
- **Subscribers**: Conexões SSE que recebem eventos
- **Channels**: Por `job_id` ou `__all__` (todos os jobs)

**Por que in-memory:**
- Simplicidade para MVP
- Baixa latência
- Não precisa de infraestrutura adicional (Redis, RabbitMQ)

**Limitação:**
- Não funciona com múltiplos servidores (não escalável horizontalmente)
- Eventos perdidos se servidor reiniciar
- Para produção, usar Redis Pub/Sub ou similar

#### 5.3. Endpoint SSE (Backend)

```python
# backend/app/api/routes/imports.py
@router.get("/stream")
async def stream_job_events(
    job_id: Optional[str] = Query(None),
    db: Session = Depends(get_database)
):
    event_manager = get_event_manager()
    
    async def event_generator():
        # 1. Subscrever aos eventos
        queue = await event_manager.subscribe(job_id)
        
        # 2. Enviar estado inicial se job_id fornecido
        if job_id:
            job = job_repository.get_by_id(job_uuid)
            if job:
                logs = log_repository.get_by_job_id(job_uuid)
                initial_data = {...}  # Dados completos do job
                yield f"event: job_status\ndata: {json.dumps(initial_data)}\n\n"
        
        # 3. Stream eventos em tempo real
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                
                event_type = event.get("event_type")
                event_data = event.get("data", {})
                
                # Mapear tipos de evento para nomes SSE
                sse_event_type = event_type
                if event_type == "status_update":
                    sse_event_type = "job_status"
                elif event_type == "progress_update":
                    sse_event_type = "job_progress"
                
                message = f"event: {sse_event_type}\ndata: {json.dumps(event_data)}\n\n"
                yield message
                
            except asyncio.TimeoutError:
                # Heartbeat para manter conexão viva
                yield f": heartbeat\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Desabilita buffering no Nginx
        },
    )
```

**O que acontece:**
1. Cliente conecta via GET `/imports/stream?job_id=xxx`
2. Backend subscreve cliente na fila de eventos
3. Envia estado inicial do job (se `job_id` fornecido)
4. Loop infinito aguarda eventos na fila
5. Quando evento chega, formata como SSE e envia
6. Heartbeat a cada 30s para manter conexão viva

**Formato SSE:**
```
event: job_status
data: {"id": "uuid", "status": "processing", ...}

event: job_progress
data: {"processed_rows": 1000, "total_rows": 5000, ...}

: heartbeat
```

**Por que SSE vs. WebSocket:**
- SSE é mais simples (HTTP unidirecional)
- Suportado nativamente pelo browser
- Não precisa de biblioteca adicional
- Adequado para notificações server→client

#### 5.4. Cliente SSE (Frontend)

```typescript
// frontend/src/lib/api/sse.ts
export class SSEClient {
  private eventSource: EventSource | null = null;
  private eventHandlers: Map<string, Set<SSECallback>> = new Map();
  
  connect(): void {
    this.eventSource = new EventSource(this.url);
    
    // Registrar handlers para eventos customizados
    this.eventHandlers.forEach((callbacks, eventType) => {
      this.eventSource?.addEventListener(eventType, (event: MessageEvent) => {
        const data = JSON.parse(event.data);
        callbacks.forEach((callback) => callback(data));
      });
    });
    
    // Reconexão automática com backoff exponencial
    this.eventSource.onerror = (error) => {
      if (this.eventSource?.readyState === EventSource.CLOSED) {
        this.scheduleReconnect();
      }
    };
  }
  
  on(eventType: string, callback: SSECallback): void {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, new Set());
    }
    this.eventHandlers.get(eventType)!.add(callback);
  }
}
```

**Funcionalidades:**
- Reconexão automática com backoff exponencial
- Handlers por tipo de evento
- Tratamento de erros
- Heartbeat handling

#### 5.5. Hook useJobSSE (Frontend)

```typescript
// frontend/src/hooks/useJobSSE.ts
export const useJobSSE = (jobId: string) => {
  const [job, setJob] = useState<ImportJobDetail | null>(null);
  const sseClientRef = useRef<SSEClient | null>(null);
  
  useEffect(() => {
    // 1. Buscar estado inicial
    const fetchInitialJob = async () => {
      const response = await apiClient.get(`/imports/${jobId}`);
      setJob(response.data);
    };
    fetchInitialJob();
    
    // 2. Conectar SSE
    const client = new SSEClient(`${SSE_URL}?job_id=${jobId}`);
    sseClientRef.current = client;
    
    // 3. Handlers de eventos
    client.on('job_status', (data) => {
      setJob((prev) => ({
        ...prev,
        status: data.status,
        started_at: data.started_at,
        finished_at: data.finished_at,
      }));
    });
    
    client.on('job_progress', (data) => {
      setJob((prev) => ({
        ...prev,
        processed_rows: data.processed_rows,
        total_rows: data.total_rows,
        error_rows: data.error_rows,
      }));
    });
    
    client.on('job_log', (data) => {
      setJob((prev) => ({
        ...prev,
        logs: [...(prev.logs || []), newLog],
      }));
    });
    
    client.connect();
    
    // 4. Cleanup
    return () => {
      client.disconnect();
    };
  }, [jobId]);
  
  return { job, isLoading, error, refetch };
};
```

**O que acontece:**
1. Busca estado inicial via REST (fallback se SSE falhar)
2. Conecta SSE para atualizações em tempo real
3. Atualiza estado React conforme eventos chegam
4. Limpa conexão ao desmontar componente

**Por que buscar estado inicial:**
- SSE pode não ter histórico de eventos anteriores
- Garante UI sempre sincronizada
- Fallback se SSE não conectar

---

## 📚 Detalhamento das Camadas

### Camada de API (Routes)

**Responsabilidade**: Receber requisições HTTP e delegar para serviços

**Arquivos:**
- `backend/app/api/routes/imports.py`
- `backend/app/api/routes/vehicles.py`
- `backend/app/api/routes/admin.py`

**Padrões:**
- Dependency Injection via FastAPI `Depends()`
- Validação de entrada via Pydantic schemas
- Tratamento de exceções centralizado
- Respostas tipadas via `response_model`

**Exemplo:**
```python
@router.post("", response_model=ImportJobCreateResponse, status_code=201)
async def create_import_job(
    file: UploadFile = File(...),
    db: Session = Depends(get_database),
):
    service = ImportService(db)
    job_id = service.create_import_job(file)
    return ImportJobCreateResponse(job_id=str(job_id), status="pending")
```

### Camada de Serviços

**Responsabilidade**: Lógica de negócio e orquestração

**Arquivos:**
- `backend/app/services/import_service.py`
- `backend/app/services/spreadsheet_parser.py`
- `backend/app/services/validation_service.py`
- `backend/app/services/vehicle_service.py`

**Características:**
- Não conhece detalhes de HTTP ou banco de dados
- Usa repositórios para acesso a dados
- Usa serviços de infraestrutura (SQS, FileStorage)
- Retorna objetos de domínio ou primitivos

**Exemplo:**
```python
class ImportService:
    def __init__(self, db: Session):
        self.job_repository = ImportJobRepository(db)
        self.file_storage = FileStorage()
        self.sqs_publisher = SQSPublisher()
    
    def create_import_job(self, file: UploadFile) -> uuid.UUID:
        # Orquestra criação do job
        job = self.job_repository.create(filename=file.filename)
        file_path = self.file_storage.save_file(file, job.id)
        self.sqs_publisher.publish_job(job.id)
        return job.id
```

### Camada de Domínio

**Responsabilidade**: Modelos de negócio e regras de domínio

**Arquivos:**
- `backend/app/domain/models/import_job.py`
- `backend/app/domain/models/imported_vehicle.py`
- `backend/app/domain/models/job_log.py`

**Características:**
- Entidades de negócio (não DTOs)
- Enums para estados
- Constraints de banco definidas aqui
- Independente de framework (SQLAlchemy é detalhe de implementação)

**Exemplo:**
```python
class ImportJobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ImportJob(Base):
    __tablename__ = "import_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String, nullable=False)
    status = Column(String, nullable=False, default=ImportJobStatus.PENDING)
    total_rows = Column(Integer, nullable=True)
    processed_rows = Column(Integer, nullable=False, default=0)
    error_rows = Column(Integer, nullable=False, default=0)
```

### Camada de Infraestrutura

**Responsabilidade**: Acesso a dados e integração com serviços externos

**Arquivos:**
- `backend/app/infrastructure/repositories/*.py`
- `backend/app/infrastructure/file_storage.py`
- `backend/app/infrastructure/sqs/*.py`
- `backend/app/infrastructure/events/job_events.py`

**Repositórios:**
- Abstraem acesso ao banco de dados
- Métodos específicos de domínio (não CRUD genérico)
- Transações gerenciadas aqui

**Exemplo:**
```python
class ImportJobRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, filename: str) -> ImportJob:
        job = ImportJob(filename=filename)
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job
    
    def update_progress(self, job_id: uuid.UUID, processed_rows: int, error_rows: int) -> None:
        job = self.get_by_id(job_id)
        if job:
            job.processed_rows = processed_rows
            job.error_rows = error_rows
            self.db.commit()
```

**FileStorage:**
- Abstrai armazenamento de arquivos
- Pode ser trocado por S3, GCS, etc.

**SQS:**
- Abstrai fila de mensagens
- Suporta LocalStack para desenvolvimento local

### Camada de Workers

**Responsabilidade**: Processamento assíncrono em background

**Arquivos:**
- `backend/app/workers/import_worker.py`
- `backend/app/workers/processor.py`

**Características:**
- Roda em processo separado
- Consome mensagens da fila SQS
- Processa jobs de forma assíncrona
- Publica eventos para SSE

**Separação ImportWorker vs. JobProcessor:**
- **ImportWorker**: Responsável por consumir SQS e orquestrar
- **JobProcessor**: Responsável pela lógica de processamento

**Por que separar:**
- Facilita testes (testar processor isoladamente)
- Permite diferentes workers (SQS, RabbitMQ, etc.)
- Separação de responsabilidades

---

## 🔌 Comunicação Frontend-Backend

### REST API

**Endpoints principais:**
- `POST /api/v1/imports` - Criar job de importação
- `GET /api/v1/imports` - Listar jobs
- `GET /api/v1/imports/{job_id}` - Detalhes do job
- `GET /api/v1/imports/stream` - SSE stream de eventos
- `GET /api/v1/vehicles` - Listar veículos importados

**Cliente HTTP (Frontend):**
```typescript
// frontend/src/lib/api/client.ts
const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
});

// Interceptor para tratamento de erros global
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    // Exibe mensagem de erro via Ant Design
    message.error(error.response?.data?.detail || 'Erro ao processar requisição');
    return Promise.reject(error);
  }
);
```

**React Query Hooks:**
```typescript
// frontend/src/lib/api/hooks/useJobs.ts
export const useCreateJob = () => {
  return useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      const response = await apiClient.post('/imports', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return response.data;
    },
  });
};

export const useJobs = (skip = 0, limit = 100, status?: string) => {
  return useQuery({
    queryKey: ['jobs', skip, limit, status],
    queryFn: async () => {
      const response = await apiClient.get('/imports', {
        params: { skip, limit, status },
      });
      return response.data;
    },
  });
};
```

**Por que React Query:**
- Cache automático
- Refetch automático
- Estados de loading/error
- Otimistic updates
- Invalidação de cache

### Server-Sent Events (SSE)

**Fluxo:**
1. Frontend conecta: `GET /api/v1/imports/stream?job_id=xxx`
2. Backend mantém conexão aberta
3. Backend envia eventos conforme processamento
4. Frontend atualiza UI em tempo real

**Tipos de eventos:**
- `job_status`: Mudança de status (pending → processing → completed)
- `job_progress`: Atualização de progresso (processed_rows, error_rows)
- `job_log`: Novo log adicionado

**Throttling de eventos:**
- Progresso atualizado no máximo a cada 1 segundo
- Evita spam de eventos
- Reduz carga no servidor e cliente

---

## ⚠️ Tratamento de Erros e Fallbacks

### Backend

#### 1. Validação de Entrada

```python
# backend/app/services/validation_service.py
def validate_vehicle(row: Dict[str, Any], row_number: int) -> Tuple[bool, List[str]]:
    errors = []
    # Validações...
    return len(errors) == 0, errors
```

**O que acontece:**
- Linha inválida não interrompe processamento
- Erro registrado em `JobLog`
- Contador `error_rows` incrementado
- Processamento continua para próxima linha

#### 2. Tratamento de Exceções no Worker

```python
# backend/app/workers/processor.py
try:
    self.processor.process_job(job_id)
    self.consumer.delete_message(receipt_handle)
except Exception as e:
    logger.error("job_processing_error", job_id=job_id_str, error=str(e))
    # Não deleta mensagem - permite retry
```

**O que acontece:**
- Erro não deleta mensagem da fila
- Mensagem volta para fila após visibility timeout
- Permite retry automático
- Em produção, implementar Dead Letter Queue após N tentativas

#### 3. Atualização de Status em Caso de Erro

```python
# backend/app/workers/processor.py
except Exception as e:
    logger.error("job_processing_failed", job_id=str(job_id), error=str(e))
    
    # Atualizar status para FAILED
    job_repository.update_status(
        job_id,
        ImportJobStatus.FAILED,
        finished_at=datetime.utcnow()
    )
    
    # Registrar log de erro
    log_repository.create(
        job_id,
        "error",
        f"Processing failed: {str(e)}"
    )
    
    # Publicar evento de falha
    self._publish_event_async(job_id, "status_update", {
        "status": ImportJobStatus.FAILED,
        ...
    })
```

**O que acontece:**
- Job marcado como `FAILED`
- Erro registrado em logs
- Evento publicado para frontend atualizar UI
- Arquivo não deletado (permite investigação)

### Frontend

#### 1. Tratamento de Erros HTTP

```typescript
// frontend/src/lib/api/client.ts
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response) {
      const status = error.response.status;
      const data = error.response.data as { detail?: string };
      
      switch (status) {
        case 400:
          message.error(data.detail || 'Requisição inválida');
          break;
        case 404:
          message.error(data.detail || 'Recurso não encontrado');
          break;
        case 500:
          message.error(data.detail || 'Erro interno do servidor');
          break;
      }
    } else if (error.request) {
      message.error('Erro de conexão com o servidor');
    }
    
    return Promise.reject(error);
  }
);
```

**O que acontece:**
- Erros HTTP exibidos via Ant Design `message`
- Mensagens específicas por código de status
- Erro de rede tratado separadamente

#### 2. Fallback SSE → REST

```typescript
// frontend/src/hooks/useJobSSE.ts
useEffect(() => {
  // 1. Buscar estado inicial via REST
  const fetchInitialJob = async () => {
    const response = await apiClient.get(`/imports/${jobId}`);
    setJob(response.data);
  };
  fetchInitialJob();
  
  // 2. Conectar SSE para atualizações
  const client = new SSEClient(`${SSE_URL}?job_id=${jobId}`);
  client.connect();
  
  // 3. Se SSE falhar, refetch periódico pode ser implementado
}, [jobId]);
```

**Estratégias de fallback:**
1. **Estado inicial via REST**: Garante dados mesmo se SSE não conectar
2. **Reconexão automática**: SSE client reconecta automaticamente
3. **Polling periódico**: Pode ser adicionado como fallback final

#### 3. Reconexão SSE com Backoff Exponencial

```typescript
// frontend/src/lib/api/sse.ts
private scheduleReconnect(): void {
  const delay = Math.min(
    this.options.reconnectDelay * Math.pow(this.options.backoffMultiplier, this.reconnectAttempts),
    this.options.maxReconnectDelay
  );
  
  setTimeout(() => {
    this.reconnectAttempts++;
    this.connect();
  }, delay);
}
```

**O que acontece:**
- Primeira tentativa: 1s
- Segunda tentativa: 2s
- Terceira tentativa: 4s
- Máximo: 30s
- Evita sobrecarga no servidor

---

## 🎯 Decisões Arquiteturais

### 1. Por que Arquitetura em Camadas?

**Vantagens:**
- Separação clara de responsabilidades
- Facilita testes unitários
- Permite trocar implementações (ex: S3 em vez de FileStorage)
- Código mais organizado e manutenível

**Trade-offs:**
- Mais arquivos/classes
- Pode parecer "over-engineering" para projetos pequenos
- Necessário disciplina para não quebrar camadas

### 2. Por que SQS em vez de Processamento Síncrono?

**Vantagens:**
- Não bloqueia API durante processamento
- Escalável (múltiplos workers)
- Resiliência (retry automático)
- Desacoplamento (API não precisa conhecer detalhes de processamento)

**Trade-offs:**
- Complexidade adicional (fila, workers)
- Latência inicial (job criado mas não processado imediatamente)
- Necessário monitoramento da fila

### 3. Por que SSE em vez de Polling?

**Vantagens:**
- Atualizações em tempo real (baixa latência)
- Menos requisições HTTP (conexão persistente)
- Eficiente para notificações server→client

**Trade-offs:**
- Conexão persistente (mais recursos no servidor)
- Limitações de proxy/load balancer
- Não funciona com múltiplos servidores sem Redis

### 4. Por que Processamento em Chunks?

**Vantagens:**
- Arquivos grandes não estouram memória
- Permite atualização de progresso
- Pode processar arquivos maiores que RAM disponível

**Trade-offs:**
- Mais complexo que ler arquivo inteiro
- Excel precisa ler tudo primeiro (limitação do pandas)

### 5. Por que Bulk Insert?

**Vantagens:**
- Muito mais rápido que inserts individuais
- Reduz overhead de transações
- Essencial para importação em massa

**Trade-offs:**
- Não retorna objetos criados
- Erro em uma linha pode invalidar todo o batch (não implementado aqui)

### 6. Por que Event Manager In-Memory?

**Vantagens:**
- Simplicidade (sem infraestrutura adicional)
- Baixa latência
- Adequado para MVP

**Limitações:**
- Não escala horizontalmente
- Eventos perdidos se servidor reiniciar
- Para produção: usar Redis Pub/Sub ou similar

---

## 📊 Fluxograma Completo

```
┌─────────────┐
│   Usuário   │
│  (Frontend) │
└──────┬──────┘
       │ 1. Upload arquivo
       ▼
┌─────────────────────────────────────┐
│  POST /api/v1/imports               │
│  (FastAPI Route)                    │
└──────┬──────────────────────────────┘
       │ 2. Delega para ImportService
       ▼
┌─────────────────────────────────────┐
│  ImportService.create_import_job()  │
│  - Cria job no banco                │
│  - Salva arquivo temporariamente    │
│  - Conta linhas                     │
│  - Publica na fila SQS             │
└──────┬──────────────────────────────┘
       │ 3. Retorna job_id
       ▼
┌─────────────┐
│  Frontend   │
│  Recebe     │
│  job_id     │
└──────┬──────┘
       │ 4. Conecta SSE
       ▼
┌─────────────────────────────────────┐
│  GET /api/v1/imports/stream         │
│  (SSE Connection)                   │
└─────────────────────────────────────┘
       │
       │ (Paralelo)
       │
       ▼
┌─────────────────────────────────────┐
│  ImportWorker (SQS Consumer)        │
│  - Recebe mensagem da fila          │
│  - Extrai job_id                    │
└──────┬──────────────────────────────┘
       │ 5. Delega processamento
       ▼
┌─────────────────────────────────────┐
│  JobProcessor.process_job()         │
│  - Atualiza status: PROCESSING      │
│  - Lê arquivo em chunks             │
│  - Valida cada linha                │
│  - Verifica duplicatas              │
│  - Insere veículos em lote          │
│  - Atualiza progresso                │
│  - Publica eventos SSE              │
│  - Atualiza status: COMPLETED       │
│  - Deleta arquivo                   │
└──────┬──────────────────────────────┘
       │ 6. Eventos SSE
       ▼
┌─────────────┐
│  Frontend   │
│  Atualiza   │
│  UI em      │
│  tempo real │
└─────────────┘
```

---

## 🔍 Pontos de Atenção e Melhorias Futuras

### 1. Escalabilidade Horizontal

**Problema atual:**
- Event Manager in-memory não funciona com múltiplos servidores
- Cada servidor tem seu próprio Event Manager

**Solução:**
- Migrar para Redis Pub/Sub
- Todos os servidores publicam/consomem do mesmo Redis

### 2. Dead Letter Queue (DLQ)

**Problema atual:**
- Mensagens com erro ficam em loop infinito na fila

**Solução:**
- Após N tentativas, mover para DLQ
- Alertar time de operações
- Permitir reprocessamento manual

### 3. Processamento Distribuído

**Problema atual:**
- Um worker processa um job por vez

**Solução:**
- Múltiplos workers processando jobs diferentes
- Processamento paralelo de chunks (com cuidado com duplicatas)

### 4. Persistência de Arquivos

**Problema atual:**
- Arquivos salvos em disco local
- Perdidos se servidor reiniciar antes de processar

**Solução:**
- Migrar para S3/GCS
- Arquivo disponível mesmo se worker falhar

### 5. Monitoramento e Observabilidade

**Melhorias:**
- Métricas de processamento (tempo médio, taxa de erro)
- Alertas para jobs falhados
- Dashboard de monitoramento
- Tracing distribuído (OpenTelemetry)

---

## 📝 Conclusão

Este sistema implementa uma arquitetura robusta e escalável para importação de veículos, utilizando:

- **Arquitetura em camadas** para organização e manutenibilidade
- **Processamento assíncrono** via SQS para não bloquear API
- **Comunicação em tempo real** via SSE para melhor UX
- **Validação e tratamento de erros** robustos
- **Processamento em chunks** para arquivos grandes
- **Bulk operations** para performance

A arquitetura permite evolução gradual, com pontos claros para melhorias futuras conforme o sistema cresce.
