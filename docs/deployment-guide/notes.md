# Deployment Guide

Bu doküman, Local LLM & RAG Based IT Assistant projesinin lokal geliştirme ortamında çalıştırılması için gerekli adımları açıklar.

## 1. Gereksinimler

Aşağıdaki araçların kurulu olması gerekir:

- Docker
- Docker Compose
- Node.js
- npm
- Ollama
- n8n
- DBeaver veya PostgreSQL istemcisi
- Postman

## 2. Docker Servislerini Başlatma

Proje içinde `docker` klasörüne gidilir:

```bash
cd docker
```

`.env.example` dosyasından `.env` dosyası oluşturulur:

```bash
cp .env.example .env
```

Docker servisleri başlatılır:

```bash
docker compose up -d
```

Çalışan container’ları kontrol etmek için:

```bash
docker ps
```

Aşağıdaki servislerin çalışıyor olması beklenir:

```text
rag_postgres
rag_n8n
```

## 3. PostgreSQL ve pgvector Kontrolü

PostgreSQL container içine bağlanmak için:

```bash
docker exec -it rag_postgres psql -U rag_user -d rag_db
```

Tablo ve extension kurulumu için `database/schema.sql` dosyası kullanılabilir.

Beklenen tablo:

```text
document_chunks
```

Tablodaki kayıtları kontrol etmek için:

```sql
SELECT document_id, COUNT(*) AS chunk_count
FROM document_chunks
GROUP BY document_id
ORDER BY document_id;
```

Embedding alanının dolu olup olmadığını kontrol etmek için:

```sql
SELECT 
  document_id,
  chunk_index,
  embedding IS NOT NULL AS has_embedding
FROM document_chunks
ORDER BY document_id, chunk_index;
```

## 4. Ollama Model Kurulumu

Cevap üretimi için Qwen modeli kullanılır:

```bash
ollama pull qwen2.5:3b
```

Embedding üretimi için embedding modeli kullanılır:

```bash
ollama pull embeddinggemma
```

Ollama servisinin çalıştığını kontrol etmek için:

```bash
ollama list
```

Host bilgisayardan Ollama API test edilebilir:

```bash
curl http://localhost:11434/api/tags
```

n8n Docker container içinden Ollama’ya erişirken aşağıdaki adres kullanılır:

```text
http://host.docker.internal:11434
```

## 5. n8n Workflow Import

n8n arayüzüne gidilir:

```text
http://localhost:5678
```

Aşağıdaki workflow JSON dosyaları import edilir:

```text
workflows/embedding-ingestion-workflow.json
workflows/rag-query-workflow.json
workflows/rag-query-webhook-workflow.json
```

## 6. Embedding Ingestion Workflow Çalıştırma

Önce `Embedding Ingestion Workflow` çalıştırılır.

Bu workflow:

```text
Mock dokümanları okur
↓
Chunk’lara böler
↓
Embedding üretir
↓
PostgreSQL + pgvector veritabanına kaydeder
```

Workflow çalıştıktan sonra veritabanında kayıtlar kontrol edilir:

```sql
SELECT document_id, COUNT(*) AS chunk_count
FROM document_chunks
GROUP BY document_id
ORDER BY document_id;
```

Beklenen doküman kayıtları:

```text
email-outlook
equipment-request
hardware-support
network-connection
password-and-account
printer-support
vpn-remote-access
```

## 7. RAG Query Workflow Testi

Manuel test için `RAG Query Workflow` kullanılabilir.

Bu workflow içinde test sorusu Code node üzerinden verilir.

Örnek soru:

```text
VPN bağlantısı kuramıyorum, ne yapmalıyım?
```

Workflow çıktısında aşağıdaki alanlar beklenir:

```json
{
  "question": "...",
  "answer": "..."
}
```

## 8. Webhook Workflow Testi

Webhook tabanlı kullanım için `RAG Query Webhook Workflow` kullanılır.

Webhook node ayarlarında:

```text
HTTP Method: POST
Path: rag-query
Response Mode: Using Respond to Webhook node
```

Test URL örneği:

```text
http://localhost:5678/webhook-test/rag-query
```

Production URL örneği:

```text
http://localhost:5678/webhook/rag-query
```

Test URL kullanılacaksa n8n üzerinde workflow test modunda çalıştırılmalıdır.

Production URL kullanılacaksa workflow aktif hale getirilmelidir.

Postman ile örnek istek:

```json
{
  "question": "VPN bağlantısı kuramıyorum, ne yapmalıyım?"
}
```

Beklenen cevap:

```json
{
  "question": "VPN bağlantısı kuramıyorum, ne yapmalıyım?",
  "answer": "- İnternet bağlantınızı kontrol edin..."
}
```

## 9. Frontend Çalıştırma

Frontend klasörüne gidilir:

```bash
cd frontend
```

Paketler yüklenir:

```bash
npm install
```

`.env.example` dosyasından `.env` dosyası oluşturulur:

```bash
cp .env.example .env
```

Windows PowerShell kullanılıyorsa:

```powershell
Copy-Item .env.example .env
```

`.env` içindeki webhook URL’i düzenlenir:

```env
VITE_RAG_API_URL=http://localhost:5678/webhook-test/rag-query
```

Geliştirme sunucusu başlatılır:

```bash
npm run dev
```

Frontend varsayılan olarak şu adreste çalışır:

```text
http://localhost:5173
```

## 10. Webhook Test ve Production URL Farkı

### Test URL

```text
/webhook-test/rag-query
```

Bu URL sadece n8n üzerinde workflow test modunda çalışırken kullanılabilir.

### Production URL

```text
/webhook/rag-query
```

Bu URL için workflow aktif hale getirilmelidir.

Frontend sürekli kullanılacaksa `.env` içinde production webhook URL kullanılması önerilir.

## 11. Olası Hatalar

### Frontend: Failed to fetch

Olası nedenler:

- n8n workflow test modunda çalışmıyor olabilir.
- `.env` içindeki webhook URL yanlış olabilir.
- Production URL kullanılıyorsa workflow aktif olmayabilir.
- CORS veya ağ bağlantısı sorunu olabilir.

### n8n: Question embedding not found

Olası nedenler:

- Ollama çalışmıyor olabilir.
- Embedding modeli indirilmemiş olabilir.
- HTTP Request node URL’i yanlış olabilir.

### PostgreSQL bağlantı hatası

n8n container içinden PostgreSQL bağlantısı için host değeri:

```text
postgres
```

DBeaver veya host bilgisayardan bağlantı için host değeri:

```text
localhost
```

## 12. Mevcut Sürüm Notu

Bu deployment adımları ilk çalışan prototip için hazırlanmıştır. Sistem lokal geliştirme ortamında çalışacak şekilde yapılandırılmıştır.