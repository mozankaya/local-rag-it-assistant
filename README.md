# Local LLM & RAG Based IT Assistant

Bu proje, yazılım mühendisliği stajı kapsamında geliştirilen lokal çalışan RAG tabanlı bir IT destek asistanı prototipidir.

Sistem; mock IT dokümanlarını işler, bu dokümanları embedding vektörlerine dönüştürür, PostgreSQL + pgvector üzerinde saklar ve kullanıcıdan gelen IT destek sorularına lokal LLM desteğiyle cevap üretir.

## Proje Amacı

Projenin amacı, kurum içi IT destek dokümanları üzerinden çalışan, dış bulut servislerine veri göndermeyen, lokal LLM ve RAG mimarisine dayalı bir soru-cevap asistanı geliştirmektir.

Bu ilk sürümde sistem aşağıdaki yetenekleri sağlamaktadır:

- Mock IT destek dokümanlarını okuma
- Dokümanları anlamlı parçalara ayırma
- Ollama üzerinden embedding üretme
- PostgreSQL + pgvector veritabanına kayıt
- Kullanıcı sorusunu embedding’e dönüştürme
- Benzer doküman parçalarını pgvector ile arama
- Bulunan kaynakları prompt içine ekleme
- Ollama üzerinde çalışan lokal LLM ile cevap üretme
- n8n Webhook üzerinden API benzeri kullanım
- React + TypeScript tabanlı basit chat arayüzü

## Kullanılan Teknolojiler

| Katman | Teknoloji |
|---|---|
| Frontend | React + TypeScript + Vite |
| Workflow / Orkestrasyon | n8n |
| LLM Runtime | Ollama |
| Cevap Üretimi | Qwen2.5 |
| Embedding Modeli | embeddinggemma |
| Veritabanı | PostgreSQL |
| Vektör Arama | pgvector |
| Container | Docker / Docker Compose |
| Test Aracı | Postman |

## Proje Yapısı

```text
.
├── data/
│   └── mock-data/
│       ├── password-and-account.md
│       ├── vpn-remote-access.md
│       ├── email-outlook.md
│       ├── printer-support.md
│       ├── hardware-support.md
│       ├── network-connection.md
│       └── equipment-request.md
│
├── database/
│   └── schema.sql
│
├── docker/
│   ├── docker-compose.yml
│   └── .env.example
│
├── docs/
│   └── deployment-guide.md
│
├── frontend/
│   ├── src/
│   ├── .env.example
│   ├── package.json
│   └── vite.config.ts
│
├── tests/
│   └── rag-test-questions.md
│
└── workflows/
    ├── embedding-ingestion-workflow.json
    ├── rag-query-workflow.json
    └── rag-query-webhook-workflow.json
```

## Workflow Açıklamaları

### 1. Embedding Ingestion Workflow

Bu workflow mock IT dokümanlarını işler.

Genel akış:

```text
Manual Trigger
↓
Clear Existing Chunks
↓
Create File List
↓
Read/Write Files from Disk
↓
Create Chunks
↓
HTTP Request - Embedding
↓
Prepare Embedding Record
↓
Postgres Insert
```

Bu workflow sonucunda doküman parçaları `document_chunks` tablosuna kaydedilir.

### 2. RAG Query Workflow

Bu workflow manuel test için hazırlanmıştır.

Genel akış:

```text
Manual Trigger
↓
Set Test Question
↓
Embed Question
↓
Prepare Search Query
↓
Search Similar Chunks
↓
Build Prompt
↓
Generate Answer
↓
Format Answer
```

### 3. RAG Query Webhook Workflow

Bu workflow frontend veya Postman üzerinden gelen soruları cevaplamak için kullanılır.

Genel akış:

```text
Webhook
↓
Get User Question
↓
Embed Question
↓
Prepare Search Query
↓
Search Similar Chunks
↓
Build Prompt
↓
Generate Answer
↓
Format Answer
↓
Respond to Webhook
```

Örnek istek:

```json
{
  "question": "VPN bağlantısı kuramıyorum, ne yapmalıyım?"
}
```

Örnek cevap:

```json
{
  "question": "VPN bağlantısı kuramıyorum, ne yapmalıyım?",
  "answer": "- İnternet bağlantınızı kontrol edin.\n- VPN kullanıcı adı ve şifrenizin doğru olduğundan emin olun."
}
```

## Frontend

Frontend, React + TypeScript ile geliştirilmiş basit bir chat arayüzüdür.

Çalıştırmak için:

```bash
cd frontend
npm install
npm run dev
```

Frontend `.env` dosyasında n8n webhook URL’i tanımlanmalıdır:

```env
VITE_RAG_API_URL=http://localhost:5678/webhook-test/rag-query
```

Test webhook URL’i kullanılacaksa n8n üzerinde workflow’un test modunda çalışıyor olması gerekir. Production webhook kullanılacaksa workflow aktif hale getirilmelidir.

## Mevcut Sınırlamalar

Bu sürüm ilk çalışan prototip olarak hazırlanmıştır. Aşağıdaki geliştirmeler ilerleyen sürümlerde ele alınabilir:

- Doküman listesinin n8n içinde elle tanımlanması yerine manifest dosyasından okunması
- Sadece değişen dokümanların yeniden embedding işlemine alınması
- Daha güçlü lokal LLM modellerinin test edilmesi
- Cevap yanında kaynak doküman bilgisinin gösterilmesi
- Frontend tasarımının kurumsal arayüze dönüştürülmesi
- Test soru seti ile ölçülebilir değerlendirme yapılması
- Hata yönetimi ve loading durumlarının iyileştirilmesi

## Not

Bu proje bir staj prototipi olarak geliştirilmiştir. Gerçek kurumsal veriler yerine mock IT destek dokümanları kullanılmıştır. Sistem lokal çalışacak şekilde tasarlanmıştır.