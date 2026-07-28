# Deployment Guide Notes

Bu doküman, **İZELTAŞ IT Danışma Asistanı** projesinin lokal geliştirme ortamında kurulması, çalıştırılması, test edilmesi ve temel bakım işlemlerinin gerçekleştirilmesi için kullanılan güncel teknik notları içerir.

> Not: Bu belge final üretim deployment dokümanı değildir. Lokal geliştirme, demo ve staj projesi test ortamı için hazırlanmıştır.

---

## 1. Güncel Sistem Özeti

Projenin temel teknoloji yapısı:

- PostgreSQL + pgvector
- n8n
- Ollama
- FastAPI
- React + TypeScript
- Docker Compose
- JWT tabanlı kimlik doğrulama
- Rol bazlı kullanıcı ve admin ekranları
- Lokal LLM + RAG tabanlı soru-cevap sistemi

Güncel RAG ayarları:

```text
Cevap modeli:
qwen3:4b-instruct-2507-q4_K_M

Scope classifier modeli:
qwen2.5:3b

Embedding modeli:
embeddinggemma:latest

Retrieval topK:
5

Score threshold:
0.51

MAX_SOURCES:
3

Düşük score daha iyi:
true
```

Güncel değerlendirme sonuçları:

```text
Ana test:
49/49

Sorgu normalizasyon testi:
12/12

Kararlılık testi:
147/147

Kararlılık testi ortalama yanıt süresi:
3.099 saniye

Teknik istek hatası:
0
```

---

## 2. Gereksinimler

Aşağıdaki araçların kurulu olması gerekir:

- Docker Desktop
- Docker Compose
- Python
- Node.js
- npm
- Ollama
- Git
- DBeaver veya başka bir PostgreSQL istemcisi
- Postman veya benzeri bir API test aracı

n8n, proje içindeki Docker Compose yapısı üzerinden çalıştırılır.

---

## 3. Proje Dizin Yapısı

Temel klasörler:

```text
local-rag-it-assistant/
├─ backend/
├─ data/
│  ├─ source-documents/
│  ├─ processed-documents/
│  └─ documents.json
├─ database/
├─ docker/
├─ docs/
│  ├─ deployment-guide/
│  └─ evaluation/
├─ frontend/
├─ n8n-workflows/
└─ scripts/
```

Doküman yapısı:

```text
data/source-documents
```

Orijinal MD, TXT, PDF ve DOCX dosyalarını içerir.

```text
data/processed-documents
```

`prepare_documents.py` tarafından üretilen temizlenmiş Markdown dosyalarını içerir.

```text
data/documents.json
```

n8n ingestion workflow'unun okuduğu doküman manifestidir.

---

## 4. Docker Servislerini Başlatma

Proje içindeki `docker` klasörüne geçilir:

```powershell
cd docker
```

İlk kurulumda `.env.example` dosyasından `.env` oluşturulur:

```powershell
Copy-Item .env.example .env
```

Servisler başlatılır:

```powershell
docker compose up -d
```

Çalışan container'lar kontrol edilir:

```powershell
docker ps
```

Beklenen temel container'lar:

```text
rag_postgres
rag_n8n
```

Servisleri durdurmak için:

```powershell
docker compose down
```

Sadece n8n'i durdurmak veya yeniden başlatmak için:

```powershell
docker compose stop n8n
docker compose start n8n
```

> Container'ları Docker Desktop üzerinden tek tek başlatmak yerine `docker compose up -d` kullanılması önerilir.

---

## 5. PostgreSQL ve pgvector

PostgreSQL container'ına bağlanmak için:

```powershell
docker exec -it rag_postgres psql -U rag_user -d rag_db
```

Şema ve extension kurulumu için:

```text
database/schema.sql
```

Beklenen temel tablolar:

```text
langchain_document_chunks
chat_logs
feedback_logs
users
n8n_vector_collections
```

Doküman chunk sayılarını kontrol etmek için:

```sql
SELECT
    cmetadata ->> 'document_id' AS document_id,
    COUNT(*) AS chunk_count
FROM langchain_document_chunks
GROUP BY cmetadata ->> 'document_id'
ORDER BY document_id;
```

Doküman bölümlerini kontrol etmek için:

```sql
SELECT
    cmetadata ->> 'document_id' AS document_id,
    cmetadata ->> 'section_title' AS section_title,
    cmetadata ->> 'source_file_name' AS source_file_name,
    LEFT(document, 150) AS preview
FROM langchain_document_chunks
ORDER BY document_id, section_title;
```

Chat log kayıtlarını kontrol etmek için:

```sql
SELECT
    id,
    question,
    category,
    section_title,
    response_type,
    created_at
FROM chat_logs
ORDER BY created_at DESC;
```

Feedback kayıtlarını kontrol etmek için:

```sql
SELECT
    id,
    question,
    feedback,
    created_at
FROM feedback_logs
ORDER BY created_at DESC;
```

Kullanıcı kayıtlarını kontrol etmek için:

```sql
SELECT
    id,
    email,
    full_name,
    role,
    is_active,
    created_at
FROM users
ORDER BY id;
```

> `n8n_vector_collections` tablosu n8n LangChain yapısı tarafından yönetilir. Manuel olarak değiştirilmemelidir.

---

## 6. Ollama Model Kurulumu

Ana cevap modeli:

```powershell
ollama pull qwen3:4b-instruct-2507-q4_K_M
```

Scope classifier modeli:

```powershell
ollama pull qwen2.5:3b
```

Embedding modeli:

```powershell
ollama pull embeddinggemma:latest
```

Kurulu modelleri kontrol etmek için:

```powershell
ollama list
```

Ollama API kontrolü:

```powershell
curl http://localhost:11434/api/tags
```

Host bilgisayardan Ollama adresi:

```text
http://localhost:11434
```

n8n Docker container'ından Ollama adresi:

```text
http://host.docker.internal:11434
```

> RAG cevap modelinde kısa `qwen3:4b` etiketi yerine tam model etiketi kullanılmalıdır:

```text
qwen3:4b-instruct-2507-q4_K_M
```

Bu sürüm, yaklaşık 4 milyar parametreli instruct ve non-thinking modelin Q4_K_M quantize edilmiş varyantıdır.

---

## 7. Dokümanları Hazırlama

Doküman işleme bağımlılıkları kurulur:

```powershell
pip install -r requirements-doc-processing.txt
```

Kaynak dokümanlar hazırlandıktan veya değiştirildikten sonra proje kök dizininde:

```powershell
python scripts/prepare_documents.py
```

çalıştırılır.

Bu işlem:

- Kaynak dosyaları okur.
- Temizlenmiş Markdown çıktıları üretir.
- `data/processed-documents` klasörünü günceller.
- `data/documents.json` manifestini günceller.
- `content_hash` ve metadata alanlarını yeniler.

Kaynak dosya değiştiğinde yalnızca scripti çalıştırmak yeterli değildir. Yeni içeriklerin vektör veritabanına aktarılması için ayrıca **Full Reindex** çalıştırılmalıdır.

---

## 8. n8n Workflow Import ve Yayınlama

n8n arayüzü:

```text
http://localhost:5678
```

Import edilmesi gereken temel workflow dosyaları:

```text
n8n-workflows/langchain-document-ingestion-workflow.json
n8n-workflows/rag-query-webhook-workflow.json
n8n-workflows/feedback-webhook-workflow.json
```

Ana workflow'lar:

```text
LangChain Document Ingestion Workflow
RAG Query Webhook Workflow
Feedback Webhook Workflow
```

Yayınlanması gereken webhook workflow'ları:

```text
RAG Query Webhook Workflow
Feedback Webhook Workflow
LangChain Document Ingestion Workflow
```

Ingestion workflow, admin paneldeki yeniden indeksleme endpoint'i tarafından webhook üzerinden tetiklenebildiği için güncel sürümde publish edilmelidir.

n8n sürümüne bağlı olarak arayüzde:

```text
Active
```

yerine:

```text
Publish Workflow
```

ifadesi görülebilir.

Workflow değişikliği sonrasında:

1. Node ayarları kaydedilir.
2. Workflow publish edilir.
3. Güncel workflow JSON dosyası tekrar export edilir.
4. Export edilen JSON repo içindeki dosyanın yerine konur.

---

## 9. LangChain Document Ingestion Workflow

Bu workflow dokümanları pgvector veritabanına aktarır.

Temel akış:

```text
Manual/Webhook Trigger
↓
Clear Existing LangChain Chunks
↓
Read Manifest
↓
Create File List
↓
Read Files from Disk
↓
Prepare LangChain Documents
↓
Default Data Loader
↓
Recursive Character Text Splitter
↓
Embeddings Ollama
↓
Insert Documents to PGVector
```

Güncel splitter ayarları:

```text
Chunk size:
900

Chunk overlap:
100
```

Güncel embedding modeli:

```text
embeddinggemma:latest
```

Embedding'e gönderilen doküman metni, doküman başlığı, bölüm başlığı ve bölüm içeriğini birlikte taşır:

```text
title: <document_title> - <section_title> | text: <content>
```

Örnek:

```text
title: IT Destek Kaydı Oluşturma ve Takip Süreci -
Destek kaydında bulunması gereken bilgiler |
text: Kullanıcı adı, sicil numarası, departman...
```

Bu yapı sayesinde genel kullanıcı soruları ile ayrıntılı bölüm içerikleri arasındaki retrieval eşleşmesi güçlendirilmiştir.

Workflow şu anda **tam yeniden indeksleme** mantığıyla çalışır:

1. Eski chunk kayıtları temizlenir.
2. Manifestteki bütün dokümanlar yeniden okunur.
3. Embedding'ler yeniden üretilir.
4. Bütün kayıtlar pgvector'a eklenir.

Doküman sayısı arttığında ileride incremental reindex geliştirilebilir.

---

## 10. RAG Query Webhook Workflow

Ana soru-cevap workflow'udur.

Webhook ayarları:

```text
HTTP Method:
POST

Path:
rag-query

Response Mode:
Using Respond to Webhook node
```

Test URL:

```text
http://localhost:5678/webhook-test/rag-query
```

Production URL:

```text
http://localhost:5678/webhook/rag-query
```

Production URL'nin kullanılabilmesi için workflow publish edilmiş olmalıdır.

### 10.1. İşlem Sırası

```text
Webhook
↓
Detect Simple Intent
↓
Get Similar Documents
↓
Build Prompt
↓
IF No Relevant Source
↓
RAG Answer Model veya Scope Classifier
↓
Format Answer
↓
Save Chat Log
↓
Respond to Webhook
```

Static intentler:

- Selamlama
- Teşekkür
- Asistanın kimliği
- Asistanın yapabildikleri

Static olmayan sorular vektör aramasına gönderilir.

### 10.2. Sorgu Normalizasyonu

Sorgu embedding'inden önce:

- Unicode NFKC normalizasyonu
- Türkçe küçük harfe dönüştürme
- Sondaki gereksiz noktalama temizliği
- Fazla boşlukları tek boşluğa indirme

uygulanır.

Sorgu embedding formatı:

```text
task: search result | query: <normalized_question>
```

### 10.3. Retrieval Ayarları

```text
topK:
5

SCORE_THRESHOLD:
0.51

MAX_SOURCES:
3

LOWER_SCORE_IS_BETTER:
true
```

Kabul koşulu:

```text
score <= 0.51
```

İlk beş adaydan threshold'u geçen en iyi üç aday cevap modeline gönderilir.

Debug alanları:

```text
candidate_count
threshold_pass_count
selected_count
candidate_documents
```

Alanların anlamları:

```text
candidate_count
Vektör aramasından gelen toplam aday sayısıdır.

threshold_pass_count
Score threshold koşulunu sağlayan aday sayısıdır.

selected_count
MAX_SOURCES sınırından sonra prompta gönderilen aday sayısıdır.
```

### 10.4. Cevap Modeli

Ana cevap modeli:

```text
qwen3:4b-instruct-2507-q4_K_M
```

Modelden:

- Yalnızca kaynak pasajlara dayanması
- Türkçe cevap vermesi
- 1-3 madde üretmesi
- Kaynakta olmayan bilgi eklememesi
- Koşulları ve olumsuz ifadeleri koruması
- Gizli bilgilerin paylaşılmasını önermemesi

istenir.

### 10.5. Scope Classifier

Threshold'u geçen kaynak bulunamazsa ana cevap modeli çalıştırılmaz. Soru ayrı scope classifier'a gönderilir.

Scope classifier modeli:

```text
qwen2.5:3b
```

Beklenen etiketler:

```text
IT_RELATED
OUT_OF_SCOPE
```

Sonuç mantığı:

```text
IT_RELATED + kaynak yok
→ no_relevant_source

OUT_OF_SCOPE
→ out_of_scope
```

Scope classifier; bilgisayar, yazılım, dijital portal, kullanıcı hesabı, ağ, VPN, e-posta, yazıcı, donanım, siber güvenlik ve IT ekipman taleplerini IT kapsamında değerlendirir.

### 10.6. Kaynaklar Alanı

Response içindeki `sources` alanı, cevap modeline gönderilen ilgili aday bölümleri gösterir.

Bu nedenle frontend'de gösterilen her kaynak, cevabın her maddesinde mutlaka kullanılmış olmayabilir. Güncel prototipte bu alan cevap üretimine sunulan ilgili kaynakları temsil eder.

---

## 11. RAG Cevap Yapısı

Örnek istek:

```json
{
  "question": "IT destek kaydı nasıl oluştururum?"
}
```

Örnek cevap:

```json
{
  "question": "IT destek kaydı nasıl oluştururum?",
  "answer": "- Kullanıcı adı, sicil numarası, departman, cihaz etiketi ve iletişim bilgisi yazılmalıdır.\n- Sorun kısa ancak açık şekilde açıklanmalı ve hangi uygulama veya cihazda yaşandığı belirtilmelidir.\n- Hata mesajı, olay saati ve sorunu tekrar oluşturmak için uygulanan adımlar eklenmelidir.",
  "sources": [
    {
      "document_id": "it-support-ticket-process",
      "title": "It Support Ticket Process",
      "category": "support",
      "section_title": "Destek kaydında bulunması gereken bilgiler",
      "chunk_index": 2,
      "source_file_name": "it-support-ticket-process.md",
      "file_type": "md",
      "score": 0.4193
    }
  ],
  "response_type": "rag_answer"
}
```

Desteklenen `response_type` değerleri:

```text
rag_answer
no_relevant_source
out_of_scope
llm_error
static_response
```

---

## 12. Feedback Webhook Workflow

Feedback webhook'u, kullanıcıların cevapları faydalı veya faydasız olarak işaretlemesini sağlar.

Webhook ayarları:

```text
HTTP Method:
POST

Path:
feedback
```

Production URL:

```text
http://localhost:5678/webhook/feedback
```

Örnek istek:

```json
{
  "question": "VPN bağlantısı kurulamıyor.",
  "answer": "- Bilgisayarın internet bağlantısı kontrol edilmelidir.",
  "feedback": "useful",
  "sources": []
}
```

Desteklenen feedback değerleri:

```text
useful
not_useful
```

Kayıtlar `feedback_logs` tablosunda tutulur.

---

## 13. Backend Ortam Ayarları

Backend klasörüne geçilir:

```powershell
cd backend
```

İlk kurulumda:

```powershell
Copy-Item .env.example .env
```

Örnek backend `.env`:

```env
N8N_RAG_WEBHOOK_URL=http://localhost:5678/webhook/rag-query
N8N_FEEDBACK_WEBHOOK_URL=http://localhost:5678/webhook/feedback
N8N_REINDEX_WEBHOOK_URL=http://localhost:5678/webhook/reindex-documents

REQUEST_TIMEOUT_SECONDS=60
MAX_QUESTION_LENGTH=1000

DATABASE_URL=postgresql+psycopg2://rag_user:rag_password_123@127.0.0.1:5432/rag_db

JWT_SECRET_KEY=local-development-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

> Gerçek `.env` dosyası GitHub'a gönderilmemelidir. Repo içinde yalnızca `.env.example` tutulmalıdır.

n8n workflow path'i farklıysa `N8N_REINDEX_WEBHOOK_URL` mevcut workflow path'ine göre düzenlenmelidir.

---

## 14. Backend Kurulumu ve Çalıştırma

Backend klasöründe:

```powershell
python -m venv .venv
```

Sanal ortam etkinleştirilir:

```powershell
.\.venv\Scripts\Activate.ps1
```

Bağımlılıklar kurulur:

```powershell
pip install -r requirements.txt
```

Test kullanıcıları oluşturulur:

```powershell
python -m app.scripts.create_test_users
```

Backend, `backend` klasörü içindeyken başlatılır:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Başarılı başlangıçta:

```text
Application startup complete.
```

satırı görülmelidir.

Sağlık kontrolü:

```text
http://127.0.0.1:8000/health
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

> `uvicorn app.main:app` komutu proje kök dizininde çalıştırılırsa `ModuleNotFoundError: No module named 'app'` hatası oluşabilir. Önce `backend` klasörüne geçilmelidir.

Alternatif olarak proje kök dizininde:

```powershell
uvicorn app.main:app --reload --app-dir backend
```

kullanılabilir.

---

## 15. JWT Login ve Demo Kullanıcıları

Temel endpointler:

```text
POST /auth/login
GET /auth/me
POST /chat
POST /feedback
```

JWT gerektiren endpointler:

```text
GET /auth/me
POST /chat
POST /feedback
/admin/*
```

Varsayılan lokal demo kullanıcıları:

```text
Admin:
admin@izeltas.local
Admin123!

Standart kullanıcı:
user@izeltas.local
User123!
```

Bu hesaplar yalnızca lokal geliştirme ve demo ortamı içindir.

Başarılı login sonrasında token:

```text
Authorization: Bearer <access_token>
```

header'ı ile gönderilir.

---

## 16. Admin Endpointleri

Güncel admin özellikleri:

- Dashboard
- İnceleme kuyruğu
- Kullanıcı yönetimi
- Doküman yönetimi
- Doküman yükleme
- Doküman indirme
- Doküman silme
- Full Reindex

Temel admin endpointleri:

```text
GET /admin/dashboard/summary
GET /admin/dashboard/response-types
GET /admin/dashboard/categories
GET /admin/dashboard/feedback-summary
GET /admin/dashboard/recent-questions
GET /admin/dashboard/review-items

GET /admin/users
PATCH /admin/users/{user_id}/role
PATCH /admin/users/{user_id}/status

GET /admin/documents
GET /admin/documents/categories
GET /admin/documents/{document_id}/download
POST /admin/documents/upload
DELETE /admin/documents/{document_id}
POST /admin/documents/reindex
```

Doküman yükleme sonrasında:

1. Kaynak dosya `source-documents` altına kaydedilir.
2. `prepare_documents.py` çalıştırılır.
3. `processed-documents` ve `documents.json` güncellenir.
4. Yeni içerik henüz vektör veritabanına eklenmez.
5. Admin panelden **Yeniden İndeksle** çalıştırılır.

Doküman silme sırasında:

- Kaynak dosya silinir.
- Processed Markdown silinir.
- Manifest kaydı kaldırılır.
- İlgili vektör kayıtları temizlenir.

---

## 17. Backend API Testi

Login:

```powershell
$login = Invoke-RestMethod `
  -Method POST `
  -Uri "http://127.0.0.1:8000/auth/login" `
  -ContentType "application/json" `
  -Body '{"email":"admin@izeltas.local","password":"Admin123!"}'

$token = $login.access_token
```

Chat:

```powershell
Invoke-RestMethod `
  -Method POST `
  -Uri "http://127.0.0.1:8000/chat" `
  -Headers @{ Authorization = "Bearer $token" } `
  -ContentType "application/json" `
  -Body '{"question":"VPN bağlantısı kurulamıyor, ne yapmalıyım?"}'
```

Feedback:

```powershell
Invoke-RestMethod `
  -Method POST `
  -Uri "http://127.0.0.1:8000/feedback" `
  -Headers @{ Authorization = "Bearer $token" } `
  -ContentType "application/json" `
  -Body '{
    "question": "VPN bağlantısı kurulamıyor.",
    "answer": "- Bilgisayarın internet bağlantısı kontrol edilmelidir.",
    "feedback": "useful",
    "sources": []
  }'
```

---

## 18. Frontend Ortam Ayarları

Frontend klasörüne geçilir:

```powershell
cd frontend
```

İlk kurulumda:

```powershell
Copy-Item .env.example .env
```

Örnek frontend `.env`:

```env
VITE_AUTH_API_URL=http://127.0.0.1:8000/auth
VITE_RAG_API_URL=http://127.0.0.1:8000/chat
VITE_FEEDBACK_API_URL=http://127.0.0.1:8000/feedback
```

Frontend artık doğrudan n8n webhook'larına istek göndermez. İstekler önce FastAPI Gateway'e gider.

`.env` değiştirildikten sonra Vite yeniden başlatılmalıdır.

---

## 19. Frontend Çalıştırma

```powershell
cd frontend
npm install
npm run dev
```

Varsayılan adres:

```text
http://localhost:5173
```

Beklenen kullanıcı akışı:

1. Login ekranı açılır.
2. Kullanıcı giriş yapar.
3. Chat ekranında IT sorusu sorar.
4. Cevap ve ilgili kaynaklar gösterilir.
5. Kullanıcı faydalı/faydasız feedback verir.
6. Kullanıcı çıkış yapabilir.

Admin kullanıcılar ayrıca:

- Dashboard
- İnceleme kuyruğu
- Kullanıcı yönetimi
- Doküman yönetimi

ekranlarına erişebilir.

---

## 20. Sistemi Çalıştırma Sırası

Önerilen başlangıç sırası:

```text
1. Docker Desktop'ı aç.
2. docker klasöründe docker compose up -d çalıştır.
3. Ollama'nın çalıştığını ve modellerin kurulu olduğunu kontrol et.
4. n8n workflow'larının import ve publish durumunu kontrol et.
5. Gerekliyse dokümanları prepare_documents.py ile hazırla.
6. Dokümanlar değiştiyse Full Reindex çalıştır.
7. backend klasöründe FastAPI'yi başlat.
8. frontend klasöründe Vite'ı başlat.
9. Login ve chat akışını test et.
```

Hızlı kontrol adresleri:

```text
n8n:
http://localhost:5678

FastAPI:
http://127.0.0.1:8000/health

Swagger:
http://127.0.0.1:8000/docs

Frontend:
http://localhost:5173

Ollama:
http://localhost:11434/api/tags
```

---

## 21. Uçtan Uca Manuel Test

Normal kullanıcı testi:

- Login başarılı mı?
- Chat sorusu gönderilebiliyor mu?
- Cevap Türkçe ve 1-3 madde mi?
- İlgili kaynak bilgileri görünüyor mu?
- Feedback kaydediliyor mu?
- Admin route'larına erişim engelleniyor mu?

Admin testi:

- Dashboard verileri geliyor mu?
- İnceleme kuyruğu yükleniyor mu?
- Kullanıcı rolü değiştirilebiliyor mu?
- Kullanıcı aktif/pasif yapılabiliyor mu?
- Son admin koruması çalışıyor mu?
- Doküman yükleme, silme ve reindex çalışıyor mu?

Doküman yönetimi testi:

```text
Yeni test dokümanı yükle
→ processed dosya ve manifesti kontrol et
→ Full Reindex çalıştır
→ yeni bilgiyle soru sor
→ doğru kaynağın geldiğini kontrol et
→ test dokümanını sil
→ vektör kaydının silindiğini doğrula
```

---

## 22. Evaluation Testleri

Evaluation çalıştırılmadan önce:

- Docker servisleri açık olmalıdır.
- Ollama çalışmalıdır.
- n8n workflow'ları publish edilmiş olmalıdır.
- FastAPI açık olmalıdır.
- n8n cevap modelinde doğru model seçilmiş olmalıdır.

> `--model` parametresi n8n modelini değiştirmez. Yalnızca sonuç klasörü ve CSV model etiketi olarak kullanılır.

### 22.1. Ana Test

```powershell
python scripts/evaluate_rag.py `
  --model qwen3-4b-instruct-2507 `
  --cases docs/evaluation/cases/evaluation-cases.json `
  --repeat 1
```

Beklenen:

```text
49/49
```

### 22.2. Normalizasyon Testi

```powershell
python scripts/evaluate_rag.py `
  --model qwen3-4b-instruct-2507-normalization `
  --cases docs/evaluation/cases/retrieval-normalization-cases.json `
  --repeat 1
```

Beklenen:

```text
12/12
```

### 22.3. Kararlılık Testi

```powershell
python scripts/evaluate_rag.py `
  --model qwen3-4b-instruct-2507-stability `
  --cases docs/evaluation/cases/evaluation-cases.json `
  --repeat 3
```

Beklenen toplam çalışma:

```text
49 vaka × 3 tekrar = 147
```

Son ölçülen sonuç:

```text
147/147
Ortalama süre: 3.099 saniye
Teknik hata: 0
```

Sonuç dosyaları:

```text
docs/evaluation/results/qwen3-4b-instruct-2507/
docs/evaluation/results/qwen3-4b-instruct-2507-normalization/
docs/evaluation/results/qwen3-4b-instruct-2507-stability/
```

---

## 23. Chat Log Temizliği

Bakım sorguları:

```text
database/maintenance.sql
```

Mevcut bakım sorgusu 180 günden eski chat loglarının temizlenmesi için kullanılabilir.

Prototip aşamasında otomatik temizlik zorunlu değildir. Gerçek kullanımda:

- n8n schedule
- backend cron job
- PostgreSQL zamanlayıcı

kullanılabilir.

---

## 24. Olası Hatalar

### 24.1. `WinError 10061`

Örnek:

```text
Hedef makine etkin olarak reddettiğinden bağlantı kurulamadı
```

Evaluation scripti login aşamasında bu hatayı veriyorsa FastAPI çalışmıyor olabilir.

Çözüm:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

### 24.2. `ModuleNotFoundError: No module named 'app'`

`uvicorn app.main:app` proje kökünde çalıştırılmış olabilir.

Çözüm:

```powershell
cd backend
uvicorn app.main:app --reload
```

veya:

```powershell
uvicorn app.main:app --reload --app-dir backend
```

### 24.3. Frontend `Failed to fetch`

Kontrol edilmesi gerekenler:

- FastAPI çalışıyor mu?
- Frontend `.env` adresleri doğru mu?
- `.env` sonrası Vite yeniden başlatıldı mı?
- CORS ayarları doğru mu?

### 24.4. `401 Unauthorized`

- Kullanıcı login olmamış olabilir.
- Token süresi dolmuş olabilir.
- Eski token `localStorage` içinde kalmış olabilir.
- JWT secret değişmiş olabilir.

Çözüm olarak logout/login yapılabilir veya localStorage temizlenebilir.

### 24.5. `403 Forbidden`

Normal kullanıcı admin endpoint'ine erişmeye çalışıyor olabilir.

Bu durum rol korumasının beklenen davranışıdır.

### 24.6. Backend chatbot servisine ulaşamıyor

Kontrol edilmesi gerekenler:

- n8n çalışıyor mu?
- RAG workflow publish edilmiş mi?
- Backend `.env` webhook URL'si doğru mu?
- Ollama çalışıyor mu?
- n8n execution içinde node hatası var mı?

### 24.7. `No relevant source`

Kontrol edilmesi gerekenler:

- İlgili doküman manifestte var mı?
- Processed dosya oluşmuş mu?
- Full Reindex çalıştırılmış mı?
- Doğru bölüm ilk beş aday içinde mi?
- Score değeri `0.51` veya daha düşük mü?
- `candidate_documents` debug alanı ne gösteriyor?

### 24.8. PostgreSQL bağlantı hatası

n8n container içinden:

```text
postgres
```

Host bilgisayardan:

```text
localhost
```

Backend `.env` örneği:

```env
DATABASE_URL=postgresql+psycopg2://rag_user:rag_password_123@127.0.0.1:5432/rag_db
```

### 24.9. Ollama bağlantı hatası

Host:

```text
http://localhost:11434
```

n8n container:

```text
http://host.docker.internal:11434
```

### 24.10. Test süresi ilk istekte yüksek

Ollama modeli belleğe ilk kez yüklenirken ilk istek diğerlerinden daha yavaş olabilir.

Kararlılık veya performans ölçümünden önce manuel bir RAG sorusu gönderilerek model ısıtılabilir. Sonuç raporlanırken testlerin seçilerek değil, bütün ölçümlerin dürüst şekilde değerlendirilmesi gerekir.

---

## 25. Güvenlik ve Repo Notları

GitHub'a gönderilmemesi gerekenler:

```text
.env
gerçek kullanıcı parolaları
JWT secret
gerçek şirket verileri
kişisel veya hassas bilgiler
```

Repo içinde tutulabilecekler:

```text
.env.example
mock IT dokümanları
workflow JSON dosyaları
evaluation senaryoları
evaluation sonuçları
deployment ve bakım notları
```

Model cevaplarında:

- Parola
- MFA kodu
- API anahtarı
- Access token
- Yönetici parolası

gibi gizli bilgilerin paylaşılması önerilmemelidir.

---

## 26. Güncel Geliştirme Durumu

Çalışan ana özellikler:

- Lokal Qwen3 cevap modeli
- Lokal EmbeddingGemma
- PostgreSQL + pgvector retrieval
- Doküman ve sorgu embedding prefix yapısı
- Türkçe query normalization
- topK=5 retrieval
- score threshold=0.51
- en fazla üç aday kaynak
- LLM tabanlı scope classifier
- `rag_answer`
- `no_relevant_source`
- `out_of_scope`
- `llm_error`
- `static_response`
- FastAPI Gateway
- JWT login
- Rol bazlı yetkilendirme
- React + TypeScript frontend
- Admin dashboard
- İnceleme kuyruğu
- Kullanıcı yönetimi
- Doküman yükleme, indirme ve silme
- Admin panelden Full Reindex
- Chat logları
- Feedback sistemi
- 49 vakalık ana evaluation
- 12 vakalık normalization testi
- 147 çalışmalık kararlılık testi

---

## 27. Gelecekte Yapılabilecek Geliştirmeler

- FastAPI ve frontend'i Docker Compose içine ekleme
- Document-level incremental reindex
- Doküman önizleme
- Mevcut dokümanı güncelleme/değiştirme
- Daha ayrıntılı audit log
- Sistem durumu ekranı
- Chat ve feedback detay raporları
- Exact used-source citation sistemi
- Daha geniş manuel kalite değerlendirmesi
- LLM-as-a-judge denemesi
- Responsive ve mobil kullanım iyileştirmeleri
- Gerçek kullanım için AD/LDAP/SSO entegrasyonu
