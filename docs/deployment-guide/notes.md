# Deployment Notes

## Ollama Setup

```bash
ollama --version
ollama pull qwen2.5:3b
ollama run qwen2.5:3b
```

## Ollama API Test

Local API endpoint:

```text
http://localhost:11434/api/generate
```

n8n container access endpoint:

```text
http://host.docker.internal:11434/api/generate
```


## Embedding Model Setup

```bash
ollama pull embeddinggemma
```

Embedding API endpoint:

```text
http://localhost:11434/api/embed
```

PostgreSQL table:

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    document_id TEXT NOT NULL,
    title TEXT NOT NULL,
    category TEXT,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(<embedding_dimension>),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```