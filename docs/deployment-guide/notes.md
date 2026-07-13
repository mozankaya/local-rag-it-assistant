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