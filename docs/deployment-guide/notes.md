# Deployment Guide Notes

Bu doküman, **Local LLM & RAG Based IT Assistant** projesinin lokal geliştirme ortamında çalıştırılması için gerekli temel teknik adımları açıklar.

Bu dosya geliştirme sürecinde kullanılan kısa kurulum ve bakım notlarını içerir.

---

## 1. Gereksinimler

Aşağıdaki araçların kurulu olması gerekir:

- Docker
- Docker Compose
- Node.js
- npm
- Ollama
- n8n
- DBeaver veya başka bir PostgreSQL istemcisi
- Postman

---

## 2. Docker Servislerini Başlatma

Proje içinde `docker` klasörüne gidilir:

    cd docker

`.env.example` dosyasından `.env` dosyası oluşturulur:

    cp .env.example .env

Windows PowerShell için:

    Copy-Item .env.example .env

Docker servisleri başlatılır:

    docker compose up -d

Çalışan container’ları kontrol etmek için:

    docker ps

Beklenen servisler:

    rag_postgres
    rag_n8n

Not: Container’ları tek tek Docker Desktop üzerinden başlatmak yerine `docker compose up -d` komutu kullanılmalıdır. Aksi durumda n8n, PostgreSQL servisini doğru çözemeyebilir.

---

## 3. PostgreSQL ve pgvector

PostgreSQL container içine bağlanmak için:

    docker exec -it rag_postgres psql -U rag_user -d rag_db

Tablo ve extension kurulumu için şu dosya kullanılabilir:

    database/schema.sql

Beklenen temel tablolar:

    document_chunks
    feedback_logs
    chat_logs

Doküman chunk kayıtlarını kontrol etmek için:

    SELECT document_id, COUNT(*) AS chunk_count
    FROM document_chunks
    GROUP BY document_id
    ORDER BY document_id;

Embedding alanını kontrol etmek için:

    SELECT 
      document_id,
      chunk_index,
      embedding IS NOT NULL AS has_embedding
    FROM document_chunks
    ORDER BY document_id, chunk_index;

Feedback kayıtlarını kontrol etmek için:

    SELECT id, question, feedback, created_at
    FROM feedback_logs
    ORDER BY created_at DESC;

Chat log kayıtlarını kontrol etmek için:

    SELECT id, question, category, section_title, response_type, created_at
    FROM chat_logs
    ORDER BY created_at DESC;

---

## 4. Ollama Model Kurulumu

Cevap üretimi için Qwen modeli kullanılır:

    ollama pull qwen2.5:3b

Embedding üretimi için embedding modeli kullanılır:

    ollama pull embeddinggemma

Ollama servisinin çalıştığını kontrol etmek için:

    ollama list

Host bilgisayardan Ollama API test edilebilir:

    curl http://localhost:11434/api/tags

n8n Docker container içinden Ollama’ya erişirken şu adres kullanılır:

    http://host.docker.internal:11434

---

## 5. n8n Workflow Import

n8n arayüzü:

    http://localhost:5678

Aşağıdaki workflow JSON dosyaları import edilir:

    workflows/embedding-ingestion-workflow.json
    workflows/rag-query-workflow.json
    workflows/rag-query-webhook-workflow.json
    workflows/feedback-webhook-workflow.json

Sürekli kullanım için aktif olması gereken workflow’lar:

    RAG Query Webhook Workflow
    Feedback Webhook Workflow

Manuel çalıştırılması yeterli olan workflow:

    Embedding Ingestion Workflow

Manuel test için kullanılan workflow:

    RAG Query Workflow

---

## 6. Embedding Ingestion Workflow

`Embedding Ingestion Workflow`, dokümanları vektör veritabanına hazırlayan akıştır.

Bu workflow:

- `data/documents.json` dosyasındaki doküman listesini okur.
- `data/mock-data` klasöründeki mock IT dokümanlarını işler.
- Dokümanları section ve chunk yapılarına böler.
- Ollama üzerinden embedding üretir.
- Sonuçları PostgreSQL + pgvector üzerindeki `document_chunks` tablosuna kaydeder.

Bu workflow her kullanıcı sorusunda çalışmaz. Sadece dokümanlar değiştiğinde manuel olarak çalıştırılır.

Workflow çalıştıktan sonra kontrol için:

    SELECT document_id, section_title, chunk_index, LEFT(content, 120) AS preview
    FROM document_chunks
    ORDER BY document_id, chunk_index;

Beklenen dokümanlar:

    email-outlook
    equipment-request
    hardware-support
    network-connection
    password-and-account
    printer-support
    vpn-remote-access

Not: Mevcut prototipte ingestion işlemi tam yeniden indexleme mantığıyla çalışır. Büyük veri setleri için ileride document-level reindexing ve hash tabanlı incremental indexing eklenmesi planlanabilir.

---

## 7. RAG Query Webhook Workflow

Frontend ile kullanılan ana soru-cevap workflow’udur.

Webhook ayarları:

    HTTP Method: POST
    Path: rag-query
    Response Mode: Using Respond to Webhook node

Test URL:

    http://localhost:5678/webhook-test/rag-query

Production URL:

    http://localhost:5678/webhook/rag-query

Postman ile örnek istek:

    {
      "question": "VPN bağlantısı kuramıyorum, ne yapmalıyım?"
    }

Beklenen cevap yapısı:

    {
      "question": "...",
      "answer": "...",
      "sources": [
        {
          "document_id": "vpn-remote-access",
          "title": "VPN ve Uzaktan Erişim Sorunları",
          "category": "vpn",
          "section_title": "VPN bağlantısı kurulamıyor",
          "chunk_index": 1
        }
      ]
    }

Bu workflow ayrıca soru-cevap kayıtlarını `chat_logs` tablosuna kaydeder.

---

## 8. Feedback Webhook Workflow

Kullanıcıların chatbot cevaplarını **Faydalı / Faydasız** olarak değerlendirmesi için kullanılır.

Webhook ayarları:

    HTTP Method: POST
    Path: feedback
    Response Mode: Using Respond to Webhook node

Test URL:

    http://localhost:5678/webhook-test/feedback

Production URL:

    http://localhost:5678/webhook/feedback

Postman ile örnek istek:

    {
      "question": "VPN bağlantısı kuramıyorum, ne yapmalıyım?",
      "answer": "- İnternet bağlantınızı kontrol edin.",
      "feedback": "useful",
      "sources": [
        {
          "document_id": "vpn-remote-access",
          "title": "VPN ve Uzaktan Erişim Sorunları",
          "category": "vpn",
          "section_title": "VPN bağlantısı kurulamıyor",
          "chunk_index": 1
        }
      ]
    }

Beklenen cevap:

    {
      "status": "success",
      "message": "Feedback saved successfully.",
      "feedback": "useful"
    }

Feedback kayıtları `feedback_logs` tablosunda tutulur.

---

## 9. Frontend Çalıştırma

Frontend klasörüne gidilir:

    cd frontend

Paketler yüklenir:

    npm install

`.env.example` dosyasından `.env` dosyası oluşturulur:

    cp .env.example .env

Windows PowerShell için:

    Copy-Item .env.example .env

Test URL ile kullanım:

    VITE_RAG_API_URL=http://localhost:5678/webhook-test/rag-query
    VITE_FEEDBACK_API_URL=http://localhost:5678/webhook-test/feedback

Production URL ile kullanım:

    VITE_RAG_API_URL=http://localhost:5678/webhook/rag-query
    VITE_FEEDBACK_API_URL=http://localhost:5678/webhook/feedback

Geliştirme sunucusu başlatılır:

    npm run dev

Frontend varsayılan olarak şu adreste çalışır:

    http://localhost:5173

Not: `.env` değiştirildikten sonra Vite geliştirme sunucusu yeniden başlatılmalıdır.

---

## 10. Webhook Test ve Production URL Farkı

Test URL formatı:

    /webhook-test/...

Bu URL sadece n8n üzerinde workflow test modunda çalışırken kullanılabilir.

Production URL formatı:

    /webhook/...

Bu URL için ilgili workflow aktif hale getirilmelidir.

Frontend sürekli kullanılacaksa `.env` içinde production webhook URL kullanılması önerilir.

---

## 11. Chat Log Temizliği

Chatbot soru-cevap kayıtları, test sürecini izlemek ve ileride admin dashboard üzerinde istatistik göstermek için `chat_logs` tablosunda tutulur.

Prototip aşamasında log temizliği otomatik olarak çalıştırılmaz. Gerekirse eski kayıtlar manuel olarak temizlenebilir.

Temizlik sorgusu şu dosyada bulunur:

    database/maintenance.sql

Bu sorgu, 180 günden eski chat log kayıtlarını silmek için hazırlanmıştır.

Gerçek kullanım senaryosunda bu işlem n8n, backend cron job veya veritabanı zamanlayıcısı ile periyodik hale getirilebilir.

---

## 12. Olası Hatalar

### Frontend: Failed to fetch

Olası nedenler:

- n8n workflow test modunda çalışmıyor olabilir.
- `.env` içindeki webhook URL yanlış olabilir.
- Production URL kullanılıyorsa workflow aktif olmayabilir.
- `.env` değiştirildikten sonra Vite yeniden başlatılmamış olabilir.

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
- Workflow aktif olmayabilir.

### PostgreSQL bağlantı hatası

n8n container içinden PostgreSQL host değeri:

    postgres

DBeaver veya host bilgisayardan bağlantı host değeri:

    localhost

### Ollama bağlantı hatası

Host bilgisayardan Ollama adresi:

    http://localhost:11434

n8n Docker container içinden Ollama adresi:

    http://host.docker.internal:11434

---

## 13. Mevcut Prototip Notu

Bu deployment adımları lokal geliştirme ortamında çalışan prototip için hazırlanmıştır.

Mevcut prototipte aşağıdaki özellikler bulunmaktadır:

- Docker tabanlı PostgreSQL + pgvector kurulumu
- Docker tabanlı n8n kurulumu
- Host bilgisayarda çalışan Ollama servisi
- Mock IT dokümanlarının manifest üzerinden okunması
- Dokümanların embedding’e çevrilmesi
- RAG tabanlı soru-cevap workflow’u
- Webhook üzerinden frontend entegrasyonu
- React + TypeScript frontend
- Cevaplarda kaynak doküman ve bölüm bilgisinin gösterilmesi
- Faydalı / Faydasız kullanıcı geri bildirimi
- Chat log ve feedback kayıtlarının PostgreSQL üzerinde saklanması