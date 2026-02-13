# Configuração do SQS no LocalStack

## ⚠️ Importante

**A URL da fila SQS não deve ser acessada diretamente no navegador!**

A URL `http://localhost:4566/000000000000/vehicle-import-queue` é apenas uma referência para uso com a API AWS (boto3, AWS CLI, etc). Acessar diretamente no navegador resultará em erros como "NoSuchBucket".

## Como verificar se a fila está funcionando

### 1. Usando o script Python (dentro do container)

```bash
docker-compose exec worker python scripts/init_sqs_queue.py
```

### 2. Usando AWS CLI (se instalado localmente)

```bash
# Listar filas
aws --endpoint-url=http://localhost:4566 sqs list-queues

# Obter URL da fila
aws --endpoint-url=http://localhost:4566 sqs get-queue-url --queue-name vehicle-import-queue

# Enviar mensagem de teste
aws --endpoint-url=http://localhost:4566 sqs send-message \
  --queue-url http://localhost:4566/000000000000/vehicle-import-queue \
  --message-body '{"test": "message"}'

# Receber mensagens
aws --endpoint-url=http://localhost:4566 sqs receive-message \
  --queue-url http://localhost:4566/000000000000/vehicle-import-queue
```

### 3. Verificar logs do worker

O worker cria a fila automaticamente na inicialização. Verifique os logs:

```bash
docker-compose logs worker | grep -i queue
```

### 4. Verificar saúde do LocalStack

```bash
curl http://localhost:4566/_localstack/health | jq '.services.sqs'
```

Deve retornar: `"available"`

## Inicialização Automática

O worker automaticamente:
1. Aguarda o LocalStack estar pronto
2. Cria a fila SQS se não existir
3. Inicia o processamento de mensagens

Não é necessário criar a fila manualmente se o worker estiver rodando.
