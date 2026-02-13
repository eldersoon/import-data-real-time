# Exemplos de Uso da API

## Upload de Arquivo

```bash
curl -X POST "http://localhost:8000/api/v1/imports" \
  -F "file=@veiculos.csv"
```

Resposta:
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "pending"
}
```

## Listar Jobs

```bash
curl "http://localhost:8000/api/v1/imports?skip=0&limit=10"
```

## Detalhar Job

```bash
curl "http://localhost:8000/api/v1/imports/123e4567-e89b-12d3-a456-426614174000"
```

## Listar Veículos

```bash
# Todos os veículos
curl "http://localhost:8000/api/v1/vehicles?page=1&page_size=10"

# Com filtros
curl "http://localhost:8000/api/v1/vehicles?page=1&page_size=10&ano_min=2020&ano_max=2023&modelo=Gol"
```

## Atualizar Veículo

```bash
curl -X PUT "http://localhost:8000/api/v1/vehicles/123e4567-e89b-12d3-a456-426614174000" \
  -H "Content-Type: application/json" \
  -d '{
    "modelo": "Gol 1.6",
    "valor_fipe": 55000.00
  }'
```

## Deletar Veículo

```bash
curl -X DELETE "http://localhost:8000/api/v1/vehicles/123e4567-e89b-12d3-a456-426614174000"
```
