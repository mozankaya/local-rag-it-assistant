# Deployment Guide Notes

Bu doküman, **Local LLM & RAG Based IT Assistant** projesinin lokal geliştirme ortamında çalıştırılması için gerekli teknik adımları açıklar.

Bu dosya geliştirme sürecinde kullanılan teknik kurulum notlarını içerir. Proje sonunda ayrı olarak kullanıcı kılavuzu ve bakım kılavuzu hazırlanacaktır.

---

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

---

## 2. Docker Servislerini Başlatma

Proje içinde `docker` klasörüne gidilir:

```bash
cd docker
```

`.env.example` dosyasından `.env` dosyası oluşturulur:

```bash
cp .env.example .env
```

Windows PowerShell kullanılıyorsa:

```powershell
Copy-Item .env.example .env
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

---

## 3. PostgreSQL ve pgvector Kontrolü

PostgreSQL container içine bağlanmak için:

```bash
docker exec -it rag_postgres psql -U rag_user -d rag_db
```

Tablo ve extension kurulumu için `database/schema.sql` dosyası kullanılabilir.

Beklenen temel tablolar:

```text
document_chunks
feedback_logs
```

Doküman chunk kayıtlarını kontrol etmek için:

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

Feedback kayıtlarını kontrol etmek için:

```sql
SELECT id, question, feedback, sources, created_at
FROM feedback_logs
ORDER BY created_at DESC;
```

---

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

---

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
workflows/feedback-webhook-workflow.json
```

---

## 6. Embedding Ingestion Workflow

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

Bu workflow manuel çalıştırılabilir. Çünkü dokümanlar her değiştiğinde tekrar ingestion yapılması gerekir, ancak her kullanıcı sorusunda çalışması gerekmez.

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

---

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
  "answer": "...",
  "sources": [...]
}
```

---

## 8. RAG Query Webhook Workflow

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
  "answer": "- İnternet bağlantınızı kontrol edin...",
  "sources": [
    {
      "document_id": "vpn-remote-access",
      "title": "VPN ve Uzaktan Erişim Sorunları",
      "category": "vpn",
      "chunk_index": 1
    }
  ]
}
```

---

## 9. Feedback Webhook Workflow

Kullanıcıların chatbot cevaplarını **Faydalı / Faydasız** olarak değerlendirebilmesi için `Feedback Webhook Workflow` kullanılır.

Webhook node ayarlarında:

```text
HTTP Method: POST
Path: feedback
Response Mode: Using Respond to Webhook node
```

Test URL örneği:

```text
http://localhost:5678/webhook-test/feedback
```

Production URL örneği:

```text
http://localhost:5678/webhook/feedback
```

Test URL kullanılacaksa n8n üzerinde workflow test modunda çalıştırılmalıdır.

Production URL kullanılacaksa workflow aktif hale getirilmelidir.

Postman ile örnek istek:

```json
{
  "question": "VPN bağlantısı kuramıyorum, ne yapmalıyım?",
  "answer": "- İnternet bağlantınızı kontrol edin.",
  "feedback": "useful",
  "sources": [
    {
      "document_id": "vpn-remote-access",
      "title": "VPN ve Uzaktan Erişim Sorunları",
      "category": "vpn",
      "chunk_index": 1
    }
  ]
}
```

Beklenen cevap:

```json
{
  "status": "success",
  "message": "Feedback saved successfully.",
  "feedback": "useful"
}
```

Feedback kayıtları PostgreSQL üzerinde `feedback_logs` tablosunda tutulur.

Kontrol için:

```sql
SELECT id, question, feedback, sources, created_at
FROM feedback_logs
ORDER BY created_at DESC;
```

---

## 10. Frontend Çalıştırma

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

`.env` içindeki webhook URL’leri düzenlenir.

Test URL ile kullanım:

```env
VITE_RAG_API_URL=http://localhost:5678/webhook-test/rag-query
VITE_FEEDBACK_API_URL=http://localhost:5678/webhook-test/feedback
```

Production URL ile kullanım:

```env
VITE_RAG_API_URL=http://localhost:5678/webhook/rag-query
VITE_FEEDBACK_API_URL=http://localhost:5678/webhook/feedback
```

Test URL kullanılıyorsa ilgili workflow n8n üzerinde test modunda çalıştırılmalıdır.

Production URL kullanılıyorsa ilgili workflow aktif hale getirilmelidir.

Geliştirme sunucusu başlatılır:

```bash
npm run dev
```

Frontend varsayılan olarak şu adreste çalışır:

```text
http://localhost:5173
```

---

## 11. Webhook Test ve Production URL Farkı

### Test URL

```text
/webhook-test/...
```

Bu URL sadece n8n üzerinde workflow test modunda çalışırken kullanılabilir.

Örnek:

```text
http://localhost:5678/webhook-test/rag-query
http://localhost:5678/webhook-test/feedback
```

### Production URL

```text
/webhook/...
```

Bu URL için workflow aktif hale getirilmelidir.

Örnek:

```text
http://localhost:5678/webhook/rag-query
http://localhost:5678/webhook/feedback
```

Frontend sürekli kullanılacaksa `.env` içinde production webhook URL kullanılması önerilir.

---

## 12. Aktif Olması Gereken Workflow'lar

Sürekli kullanım için aşağıdaki workflow’lar aktif hale getirilmelidir:

```text
RAG Query Webhook Workflow
Feedback Webhook Workflow
```

Manuel çalıştırılması yeterli olan workflow:

```text
Embedding Ingestion Workflow
```

Manuel test için kullanılan workflow:

```text
RAG Query Workflow
```

---

## 13. Olası Hatalar

### Frontend: Failed to fetch

Olası nedenler:

- n8n workflow test modunda çalışmıyor olabilir.
- `.env` içindeki webhook URL yanlış olabilir.
- Production URL kullanılıyorsa workflow aktif olmayabilir.
- Frontend çalışırken `.env` değiştirildiyse Vite yeniden başlatılmamış olabilir.
- CORS veya ağ bağlantısı sorunu olabilir.

### n8n: Question embedding not found

Olası nedenler:

- Ollama çalışmıyor olabilir.
- Embedding modeli indirilmemiş olabilir.
- HTTP Request node URL’i yanlış olabilir.

### n8n: Feedback kaydedilemiyor

Olası nedenler:

- `feedback_logs` tablosu oluşturulmamış olabilir.
- Feedback değeri `useful` veya `not_useful` dışında gönderilmiş olabilir.
- Postgres credentials yanlış olabilir.
- Workflow aktif olmayabilir veya test URL için Execute Workflow yapılmamış olabilir.

### PostgreSQL bağlantı hatası

n8n container içinden PostgreSQL bağlantısı için host değeri:

```text
postgres
```

DBeaver veya host bilgisayardan bağlantı için host değeri:

```text
localhost
```

### Ollama bağlantı hatası

Host bilgisayardan Ollama için:

```text
http://localhost:11434
```

n8n Docker container içinden Ollama için:

```text
http://host.docker.internal:11434
```

---

## 14. Mevcut Prototip Notu

Bu deployment adımları lokal geliştirme ortamında çalışan prototip için hazırlanmıştır.

Mevcut prototipte aşağıdaki özellikler bulunmaktadır:

- Docker tabanlı PostgreSQL + pgvector kurulumu
- Docker tabanlı n8n kurulumu
- Host bilgisayarda çalışan Ollama servisi
- Mock IT dokümanlarının embedding'e çevrilmesi
- RAG tabanlı soru-cevap workflow'u
- Webhook üzerinden frontend entegrasyonu
- React + TypeScript frontend
- Cevaplarda kaynak doküman bilgisinin gösterilmesi
- Faydalı / Faydasız kullanıcı geri bildirimi
- Feedback kayıtlarının PostgreSQL üzerinde saklanması

Bu dosya proje geliştirme sürecindeki teknik çalıştırma notlarını içerir.