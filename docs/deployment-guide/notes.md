# Deployment Guide Notes

Bu doküman, **Local LLM & RAG Based IT Assistant** projesinin lokal geliştirme ortamında çalıştırılması için gerekli temel teknik adımları açıklar.

Bu dosya geliştirme sürecinde kullanılan kısa kurulum, çalıştırma, test ve bakım notlarını içerir.

> Not: Proje hâlen geliştirme aşamasındadır. Bu doküman final deployment dokümanı değil, lokal geliştirme ortamında sistemi ayağa kaldırmak ve test etmek için hazırlanan güncel teknik notlardır.

---

## 1. Gereksinimler

Aşağıdaki araçların kurulu olması gerekir:

- Docker
- Docker Compose
- Python
- Node.js
- npm
- Ollama
- n8n
- DBeaver veya başka bir PostgreSQL istemcisi
- Postman veya benzeri bir API test aracı

Projede kullanılan temel bileşenler:

- PostgreSQL + pgvector
- n8n
- Ollama
- FastAPI backend
- React + TypeScript frontend
- Local LLM
- RAG tabanlı soru-cevap akışı
- JWT tabanlı giriş sistemi

---

## 2. Docker Servislerini Başlatma

Proje içinde `docker` klasörüne gidilir:

```powershell
cd docker
```

`.env.example` dosyasından `.env` dosyası oluşturulur:

```powershell
cp .env.example .env
```

Windows PowerShell için:

```powershell
Copy-Item .env.example .env
```

Docker servisleri başlatılır:

```powershell
docker compose up -d
```

Çalışan container’ları kontrol etmek için:

```powershell
docker ps
```

Beklenen servisler:

```text
rag_postgres
rag_n8n
```

Not: Container’ları tek tek Docker Desktop üzerinden başlatmak yerine `docker compose up -d` komutu kullanılmalıdır. Aksi durumda n8n, PostgreSQL servisini doğru çözemeyebilir.

---

## 3. PostgreSQL ve pgvector

PostgreSQL container içine bağlanmak için:

```powershell
docker exec -it rag_postgres psql -U rag_user -d rag_db
```

Tablo ve extension kurulumu için şu dosya kullanılabilir:

```text
database/schema.sql
```

Beklenen temel tablolar:

```text
langchain_document_chunks
chat_logs
feedback_logs
users
```

LangChain PGVector doküman kayıtlarını kontrol etmek için:

```sql
SELECT 
  id,
  collection_id,
  LEFT(document, 120) AS preview,
  cmetadata
FROM langchain_document_chunks
ORDER BY id DESC
LIMIT 10;
```

Doküman kategorilerini kontrol etmek için:

```sql
SELECT 
  cmetadata ->> 'category' AS category,
  COUNT(*) AS chunk_count
FROM langchain_document_chunks
GROUP BY cmetadata ->> 'category'
ORDER BY category;
```

Kaynak dosya bazlı chunk sayılarını kontrol etmek için:

```sql
SELECT 
  cmetadata ->> 'document_id' AS document_id,
  cmetadata ->> 'source_file_name' AS source_file_name,
  COUNT(*) AS chunk_count
FROM langchain_document_chunks
GROUP BY 
  cmetadata ->> 'document_id',
  cmetadata ->> 'source_file_name'
ORDER BY document_id;
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

---

## 4. Ollama Model Kurulumu

Cevap üretimi için Qwen modeli kullanılır:

```powershell
ollama pull qwen2.5:3b
```

Embedding üretimi için embedding modeli kullanılır:

```powershell
ollama pull embeddinggemma
```

Ollama servisinin çalıştığını kontrol etmek için:

```powershell
ollama list
```

Host bilgisayardan Ollama API test edilebilir:

```powershell
curl http://localhost:11434/api/tags
```

n8n Docker container içinden Ollama’ya erişirken şu adres kullanılır:

```text
http://host.docker.internal:11434
```

Host bilgisayardan Ollama adresi:

```text
http://localhost:11434
```

---

## 5. Doküman Hazırlama Yapısı

Projedeki dokümanlar aşağıdaki yapı üzerinden yönetilir:

```text
data/
├─ source-documents/
├─ processed-documents/
└─ documents.json
```

`source-documents` klasörü orijinal kaynak dosyaları içerir.

Örnek kaynak dokümanlar:

```text
data/source-documents/account/password-and-account.md
data/source-documents/email/email-outlook.md
data/source-documents/general/test-kurumsal-it-dokumani.pdf
data/source-documents/hardware/hardware-support.md
data/source-documents/network/network-connection.md
data/source-documents/printer/printer-support.md
data/source-documents/request/equipment-request.md
data/source-documents/vpn/vpn-remote-access.md
```

`processed-documents` klasörü, preprocessing script’i tarafından üretilen temizlenmiş Markdown dosyalarını içerir.

`documents.json` dosyası, n8n ingestion workflow tarafından okunan manifest dosyasıdır.

Doküman preprocessing için gerekli Python paketleri:

```text
pymupdf
python-docx
```

Kurulum için:

```powershell
pip install -r requirements-doc-processing.txt
```

Dokümanları hazırlamak için:

```powershell
python scripts/prepare_documents.py
```

Bu işlemden sonra `processed-documents` klasörü ve `documents.json` dosyası güncellenir.

---

## 6. n8n Workflow Import

n8n arayüzü:

```text
http://localhost:5678
```

Aşağıdaki workflow JSON dosyaları import edilir:

```text
n8n-workflows/langchain-document-ingestion-workflow.json
n8n-workflows/rag-query-webhook-workflow.json
n8n-workflows/feedback-webhook-workflow.json
```

Kullanılan ana workflow’lar:

```text
LangChain Document Ingestion Workflow
RAG Query Webhook Workflow
Feedback Webhook Workflow
```

Manuel çalıştırılması gereken workflow:

```text
LangChain Document Ingestion Workflow
```

Sürekli kullanım için yayınlanması gereken workflow’lar:

```text
RAG Query Webhook Workflow
Feedback Webhook Workflow
```

n8n sürümüne göre eski “Active” butonu yerine “Publish Workflow” kullanımı olabilir. Bu durumda webhook workflow’ları publish edilmelidir.

---

## 7. LangChain Document Ingestion Workflow

`LangChain Document Ingestion Workflow`, dokümanları vektör veritabanına hazırlayan akıştır.

Bu workflow:

- `data/documents.json` dosyasındaki doküman listesini okur.
- `data/processed-documents` klasöründeki hazırlanmış dokümanları işler.
- Dokümanları chunk yapılarına böler.
- Ollama üzerinden embedding üretir.
- Sonuçları PostgreSQL + pgvector üzerindeki `langchain_document_chunks` tablosuna kaydeder.

Bu workflow her kullanıcı sorusunda çalışmaz. Sadece dokümanlar değiştiğinde manuel olarak çalıştırılır.

Workflow akışı:

```text
Manual Trigger
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
Insert Documents to PGVector
```

Bu workflow mevcut geliştirme aşamasında tam yeniden indexleme mantığıyla çalışır. Yani yeni ingestion çalıştırıldığında mevcut chunk kayıtları temizlenir ve dokümanlar yeniden eklenir.

Workflow çalıştıktan sonra kontrol için:

```sql
SELECT 
  cmetadata ->> 'document_id' AS document_id,
  cmetadata ->> 'section_title' AS section_title,
  LEFT(document, 120) AS preview
FROM langchain_document_chunks
ORDER BY document_id, id;
```

Beklenen dokümanlar:

```text
email-outlook
equipment-request
hardware-support
network-connection
password-and-account
printer-support
vpn-remote-access
test-kurumsal-it-dokumani
```

Not: Mevcut geliştirme aşamasında ingestion işlemi tam yeniden indexleme mantığıyla çalışır. Büyük veri setleri için ileride document-level reindexing ve hash tabanlı incremental indexing eklenmesi planlanabilir.

---

## 8. RAG Query Webhook Workflow

Frontend ile kullanılan ana soru-cevap workflow’udur.

Webhook ayarları:

```text
HTTP Method: POST
Path: rag-query
Response Mode: Using Respond to Webhook node
```

Test URL:

```text
http://localhost:5678/webhook-test/rag-query
```

Production URL:

```text
http://localhost:5678/webhook/rag-query
```

Test URL yalnızca n8n üzerinde workflow test modunda çalışırken kullanılabilir.

Production URL’nin çalışması için workflow publish edilmelidir.

Postman ile n8n webhook doğrudan test edilecekse örnek istek:

```json
{
  "question": "VPN bağlantısı kuramıyorum, ne yapmalıyım?"
}
```

Beklenen cevap yapısı:

```json
{
  "question": "VPN bağlantısı kuramıyorum, ne yapmalıyım?",
  "answer": "- Bilgisayarınızın internete bağlı olduğunu kontrol edin.\n- VPN kullanıcı adı ve şifrenizi doğru girdiğinizden emin olun.",
  "sources": [
    {
      "document_id": "vpn-remote-access",
      "title": "VPN ve Uzaktan Erişim Sorunları",
      "category": "vpn",
      "section_title": "VPN bağlantısı kurulamıyor",
      "chunk_index": 1,
      "source_file_name": "vpn-remote-access.md",
      "file_type": "md"
    }
  ]
}
```

Bu workflow ayrıca soru-cevap kayıtlarını `chat_logs` tablosuna kaydeder.

Kayıt tipleri için kullanılan örnek `response_type` değerleri:

```text
rag_answer
no_relevant_source
out_of_scope
llm_error
```

---

## 9. Feedback Webhook Workflow

Kullanıcıların chatbot cevaplarını **Faydalı / Faydasız** olarak değerlendirmesi için kullanılır.

Webhook ayarları:

```text
HTTP Method: POST
Path: feedback
Response Mode: Using Respond to Webhook node
```

Test URL:

```text
http://localhost:5678/webhook-test/feedback
```

Production URL:

```text
http://localhost:5678/webhook/feedback
```

Production URL’nin çalışması için workflow publish edilmelidir.

Postman ile n8n webhook doğrudan test edilecekse örnek istek:

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
      "section_title": "VPN bağlantısı kurulamıyor",
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

Feedback kayıtları `feedback_logs` tablosunda tutulur.

---

## 10. Backend Ortam Ayarları

Backend klasörüne gidilir:

```powershell
cd backend
```

`.env.example` dosyasından `.env` dosyası oluşturulur:

```powershell
cp .env.example .env
```

Windows PowerShell için:

```powershell
Copy-Item .env.example .env
```

Backend `.env` örnek yapılandırması:

```env
N8N_RAG_WEBHOOK_URL=http://localhost:5678/webhook/rag-query
N8N_FEEDBACK_WEBHOOK_URL=http://localhost:5678/webhook/feedback

REQUEST_TIMEOUT_SECONDS=60
MAX_QUESTION_LENGTH=1000

DATABASE_URL=postgresql+psycopg2://rag_user:rag_password_123@127.0.0.1:5432/rag_db

JWT_SECRET_KEY=local-development-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

Not: `.env` dosyası GitHub’a gönderilmemelidir. Bunun yerine `.env.example` dosyası örnek yapılandırma olarak tutulur.

Production webhook URL’leri:

```env
N8N_RAG_WEBHOOK_URL=http://localhost:5678/webhook/rag-query
N8N_FEEDBACK_WEBHOOK_URL=http://localhost:5678/webhook/feedback
```

Test webhook URL’leri:

```env
N8N_RAG_WEBHOOK_URL=http://localhost:5678/webhook-test/rag-query
N8N_FEEDBACK_WEBHOOK_URL=http://localhost:5678/webhook-test/feedback
```

Güncel geliştirme akışında backend’in production webhook URL’lerini kullanması önerilir. Böylece n8n üzerinde her istek için `Execute Workflow` modunu açık tutmak gerekmez.

---

## 11. Backend Kurulumu ve Çalıştırma

Backend klasörüne gidilir:

```powershell
cd backend
```

Sanal ortam oluşturulur:

```powershell
python -m venv .venv
```

Sanal ortam aktif edilir:

```powershell
.\.venv\Scripts\Activate.ps1
```

Gerekli paketler kurulur:

```powershell
pip install -r requirements.txt
```

Test kullanıcılarını oluşturmak için:

```powershell
python -m app.scripts.create_test_users
```

Backend çalıştırılır:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend sağlık kontrolü:

```text
http://127.0.0.1:8000/health
```

API dokümantasyonu:

```text
http://127.0.0.1:8000/docs
```

---

## 12. Kimlik Doğrulama ve JWT

Projede FastAPI backend üzerinde JWT tabanlı giriş sistemi kullanılmaktadır.

Giriş endpoint’i:

```text
POST /auth/login
```

Oturum kontrol endpoint’i:

```text
GET /auth/me
```

JWT doğrulaması gerektiren endpointler:

```text
GET /auth/me
POST /chat
POST /feedback
```

Herkese açık endpointler:

```text
GET /health
POST /auth/login
```

Başarılı girişten sonra backend JWT access token döndürür. Frontend bu token’ı `localStorage` içinde saklar.

Chat ve feedback isteklerinde token şu header ile gönderilir:

```text
Authorization: Bearer <access_token>
```

Geliştirme ortamında test kullanıcıları oluşturmak için:

```powershell
python -m app.scripts.create_test_users
```

Varsayılan demo kullanıcıları:

```text
Admin Kullanıcı:
admin@izeltas.local / Admin123!

Standart Kullanıcı:
user@izeltas.local / User123!
```

Bu kullanıcılar yalnızca lokal geliştirme ve demo testleri içindir.

---

## 13. Backend API Testleri

Önce login isteği yapılır:

```powershell
$login = Invoke-RestMethod `
  -Method POST `
  -Uri "http://127.0.0.1:8000/auth/login" `
  -ContentType "application/json" `
  -Body '{"email":"admin@izeltas.local","password":"Admin123!"}'

$token = $login.access_token
```

Token ile chat endpoint’i test edilir:

```powershell
Invoke-RestMethod `
  -Method POST `
  -Uri "http://127.0.0.1:8000/chat" `
  -Headers @{ Authorization = "Bearer $token" } `
  -ContentType "application/json" `
  -Body '{"question":"VPN bağlantısı kuramıyorum, ne yapmalıyım?"}'
```

Token ile feedback endpoint’i test edilir:

```powershell
Invoke-RestMethod `
  -Method POST `
  -Uri "http://127.0.0.1:8000/feedback" `
  -Headers @{ Authorization = "Bearer $token" } `
  -ContentType "application/json" `
  -Body '{
    "question": "VPN bağlantısı kuramıyorum, ne yapmalıyım?",
    "answer": "- İnternet bağlantınızı kontrol edin.",
    "feedback": "useful",
    "sources": []
  }'
```

---

## 14. Frontend Ortam Ayarları

Frontend klasörüne gidilir:

```powershell
cd frontend
```

`.env.example` dosyasından `.env` dosyası oluşturulur:

```powershell
cp .env.example .env
```

Windows PowerShell için:

```powershell
Copy-Item .env.example .env
```

Frontend `.env` örnek yapılandırması:

```env
VITE_AUTH_API_URL=http://127.0.0.1:8000/auth
VITE_RAG_API_URL=http://127.0.0.1:8000/chat
VITE_FEEDBACK_API_URL=http://127.0.0.1:8000/feedback
```

Not: Frontend artık doğrudan n8n webhook URL’lerine istek atmaz. Frontend istekleri önce FastAPI backend’e gönderilir. Backend gerekli doğrulamayı yaptıktan sonra n8n workflow’larına istek iletir.

`.env` değiştirildikten sonra Vite geliştirme sunucusu yeniden başlatılmalıdır.

---

## 15. Frontend Çalıştırma

Frontend klasörüne gidilir:

```powershell
cd frontend
```

Paketler yüklenir:

```powershell
npm install
```

Geliştirme sunucusu başlatılır:

```powershell
npm run dev
```

Frontend varsayılan olarak şu adreste çalışır:

```text
http://localhost:5173
```

Frontend üzerinde beklenen akış:

```text
1. Login ekranı açılır.
2. Kullanıcı e-posta ve şifre ile giriş yapar.
3. Başarılı giriş sonrası chat ekranı açılır.
4. Kullanıcı IT destek sorusu sorar.
5. Cevap ve kaynak bilgisi görüntülenir.
6. Kaynak bilgisi hover tooltip ile gösterilir.
7. Kullanıcı cevabı faydalı veya faydasız olarak işaretleyebilir.
8. Çıkış butonu ile oturum sonlandırılır.
```

---

## 16. Webhook Test ve Production URL Farkı

Test URL formatı:

```text
/webhook-test/...
```

Bu URL sadece n8n üzerinde workflow test modunda çalışırken kullanılabilir. Bu kullanımda genellikle n8n üzerinde `Execute Workflow` açık olmalıdır.

Production URL formatı:

```text
/webhook/...
```

Bu URL için ilgili workflow publish edilmelidir. Workflow publish edildikten sonra `Execute Workflow` açık olmasa bile production webhook URL üzerinden istek alınabilir.

Geliştirme ortamında sürekli test için production webhook URL kullanımı daha pratiktir.

Backend `.env` içinde önerilen kullanım:

```env
N8N_RAG_WEBHOOK_URL=http://localhost:5678/webhook/rag-query
N8N_FEEDBACK_WEBHOOK_URL=http://localhost:5678/webhook/feedback
```

---

## 17. Uçtan Uca Test Akışı

Sistem çalıştırıldıktan sonra aşağıdaki testler yapılmalıdır:

```text
1. Docker servisleri başlatılır.
2. Ollama servisinin çalıştığı kontrol edilir.
3. n8n workflow’larının import edildiği kontrol edilir.
4. RAG Query Webhook Workflow publish edilir.
5. Feedback Webhook Workflow publish edilir.
6. LangChain Document Ingestion Workflow manuel olarak çalıştırılır.
7. Backend çalıştırılır.
8. Frontend çalıştırılır.
9. Kullanıcı login ekranından giriş yapar.
10. VPN, şifre, Outlook veya yazıcı gibi IT konularında soru sorulur.
11. Backend soruyu n8n RAG workflow’una gönderir.
12. n8n ilgili dokümanları PostgreSQL + pgvector üzerinden arar.
13. Ollama ile cevap üretilir.
14. Cevap frontend üzerinde gösterilir.
15. Kaynak bilgisi hover tooltip ile görüntülenir.
16. Kullanıcı cevaba faydalı/faydasız geri bildirimi verir.
17. Feedback kaydı veritabanına eklenir.
18. Çıkış yapıldığında kullanıcı tekrar login ekranına yönlendirilir.
```

---

## 18. Chat Log Temizliği

Chatbot soru-cevap kayıtları, test sürecini izlemek ve ileride admin dashboard üzerinde istatistik göstermek için `chat_logs` tablosunda tutulur.

Prototip aşamasında log temizliği otomatik olarak çalıştırılmaz. Gerekirse eski kayıtlar manuel olarak temizlenebilir.

Temizlik sorgusu şu dosyada bulunur:

```text
database/maintenance.sql
```

Bu sorgu, 180 günden eski chat log kayıtlarını silmek için hazırlanmıştır.

Gerçek kullanım senaryosunda bu işlem n8n, backend cron job veya veritabanı zamanlayıcısı ile periyodik hale getirilebilir.

---

## 19. Olası Hatalar

### Frontend: Failed to fetch

Olası nedenler:

- FastAPI backend çalışmıyor olabilir.
- Frontend `.env` içinde backend URL’i yanlış olabilir.
- `.env` değiştirildikten sonra Vite yeniden başlatılmamış olabilir.
- CORS ayarları eksik veya hatalı olabilir.

### Frontend: 401 Unauthorized

Olası nedenler:

- Kullanıcı login olmamıştır.
- JWT token localStorage içinde yoktur.
- Token süresi dolmuştur.
- Backend JWT ayarları değişmiş olabilir.
- Geçersiz veya eski token kullanılıyor olabilir.

Çözüm olarak frontend üzerinden çıkış yapılıp tekrar login olunabilir. Gerekirse tarayıcı localStorage temizlenebilir.

### Backend: Chatbot servisine ulaşılamıyor

Olası nedenler:

- n8n çalışmıyor olabilir.
- RAG Query Webhook Workflow publish edilmemiş olabilir.
- Backend `.env` içinde yanlış webhook URL kullanılıyor olabilir.
- `/webhook-test/...` URL kullanılıyorsa n8n üzerinde Execute Workflow açık olmayabilir.
- Ollama çalışmıyor olabilir.
- RAG workflow içinde node hatası oluşmuş olabilir.

### Backend: Feedback servisine ulaşılamıyor

Olası nedenler:

- Feedback Webhook Workflow publish edilmemiş olabilir.
- Backend `.env` içinde feedback webhook URL yanlış olabilir.
- `feedback_logs` tablosu oluşturulmamış olabilir.
- Workflow içinde Postgres credentials yanlış olabilir.

### n8n: Question embedding not found

Olası nedenler:

- Ollama çalışmıyor olabilir.
- Embedding modeli indirilmemiş olabilir.
- Ollama URL’i yanlış olabilir.
- Embedding node çıktısı beklenen formatta gelmiyor olabilir.

### n8n: No relevant source response dönüyor

Olası nedenler:

- Soru mevcut doküman kapsamı dışında olabilir.
- İlgili doküman henüz ingestion workflow ile vektör veritabanına eklenmemiş olabilir.
- Relevance threshold değeri fazla sıkı olabilir.
- Chunk içeriği soruyla yeterince benzer bulunmamış olabilir.

### PostgreSQL bağlantı hatası

n8n container içinden PostgreSQL host değeri:

```text
postgres
```

DBeaver veya host bilgisayardan bağlantı host değeri:

```text
localhost
```

Backend `.env` içinde örnek bağlantı:

```env
DATABASE_URL=postgresql+psycopg2://rag_user:rag_password_123@127.0.0.1:5432/rag_db
```

### Ollama bağlantı hatası

Host bilgisayardan Ollama adresi:

```text
http://localhost:11434
```

n8n Docker container içinden Ollama adresi:

```text
http://host.docker.internal:11434
```

---

## 20. Mevcut Geliştirme Durumu

Bu deployment adımları lokal geliştirme ortamında çalışan prototip için hazırlanmıştır.

Mevcut geliştirme aşamasında aşağıdaki özellikler bulunmaktadır:

- Docker tabanlı PostgreSQL + pgvector kurulumu
- Docker tabanlı n8n kurulumu
- Host bilgisayarda çalışan Ollama servisi
- Qwen2.5 tabanlı lokal cevap üretimi
- Embeddinggemma tabanlı lokal embedding üretimi
- Mock IT dokümanlarının manifest üzerinden okunması
- Doküman preprocessing akışı
- LangChain tabanlı doküman ingestion workflow’u
- PGVector üzerinde doküman chunk kayıtlarının saklanması
- RAG tabanlı soru-cevap workflow’u
- Kapsam dışı soru kontrolü
- İlgili kaynak bulunamadığında fallback cevap üretimi
- LLM hata durumunda fallback cevap üretimi
- FastAPI backend gateway
- JWT tabanlı login sistemi
- Chat ve feedback endpointlerinin JWT ile korunması
- React + TypeScript frontend
- İZELTAŞ temasına uygun koyu renkli chat arayüzü
- Hızlı konu butonları
- Yeni sohbet butonu
- Kaynakların hover tooltip ile gösterilmesi
- Faydalı / Faydasız kullanıcı geri bildirimi
- Chat log ve feedback kayıtlarının PostgreSQL üzerinde saklanması

---

## 21. Planlanan Geliştirmeler

Proje geliştirme süreci devam etmektedir. İlerleyen aşamalarda aşağıdaki geliştirmeler yapılabilir:

- Backend ve frontend servislerinin Docker Compose içine eklenmesi
- Frontend tarafında rol bazlı ekranların geliştirilmesi
- Admin dashboard ekranı eklenmesi
- Chat log ve feedback istatistiklerinin görüntülenmesi
- Sık sorulan soruların analiz edilmesi
- `no_relevant_source` kayıtlarından eksik doküman ihtiyaçlarının çıkarılması
- Doküman bazlı incremental indexing geliştirilmesi
- Doküman ekleme/güncelleme sürecinin daha dinamik hale getirilmesi
- Daha gelişmiş hata loglama yapısı
- Kullanıcı yönetimi ekranı
- Kurumsal ağ veya sunucu ortamı için deployment düzenlemeleri
- Test raporunun genişletilmesi
- Kullanım kılavuzu ve bakım dokümanlarının tamamlanması