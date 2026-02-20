# 📥 Importador de Planilhas Configurável (Blueprint Técnico)

## 🎯 Objetivo

Criar um **motor de importação genérico e configurável via UI** para
importar dados de planilhas (Excel/CSV) para o banco de dados, com:

-   Pré-processamento da planilha
-   Mapeamento visual de colunas → campos do banco
-   Definição de tipos
-   Definição de chaves estrangeiras
-   Criação dinâmica de tabelas
-   Processamento assíncrono (fila + worker)
-   Reutilizável para múltiplos contextos de negócio

------------------------------------------------------------------------

## 🧠 Visão de Arquitetura

\[ Frontend (UI de Mapeamento) \]\
→ API\
→ Fila\
→ Worker\
→ Banco de Dados

------------------------------------------------------------------------

## 🔄 Fluxo do Usuário

### 1️⃣ Upload da Planilha

Usuário envia Excel ou CSV.

### 2️⃣ Pré-processamento

Sistema retorna: - colunas - sugestão de tipos - preview de linhas

### 3️⃣ Mapeamento via UI

Usuário define: - colunas válidas - tipos - chaves estrangeiras - tabela
destino

------------------------------------------------------------------------

## 🧩 Configuração de Importação (Exemplo)

``` json
{
  "target_table": "tb_user",
  "create_table": true,
  "columns": [
    { "sheet_column": "Nome", "db_column": "fullname", "type": "string" },
    { "sheet_column": "Idade", "db_column": "age", "type": "int" },
    {
      "sheet_column": "Empresa",
      "db_column": "company_id",
      "type": "fk",
      "fk": { "table": "tb_company", "lookup_column": "name", "on_missing": "create" }
    }
  ]
}
```

------------------------------------------------------------------------

## ⚙️ Pipeline do Worker

1.  Baixar arquivo
2.  Ler linhas
3.  Validar tipos
4.  Resolver FKs
5.  Inserir no banco
6.  Logar erros

------------------------------------------------------------------------

## 🛡️ Regras de Segurança

-   Whitelist de tipos
-   Whitelist de schemas
-   Validação de nomes
-   Limitar criação de tabelas

------------------------------------------------------------------------

## 📦 Estrutura de Dados

### import_templates

-   id
-   name
-   mapping_json

### import_jobs

-   id
-   status
-   total_rows
-   success_rows
-   failed_rows

### import_job_errors

-   job_id
-   row_number
-   error_message
