# İZELTAŞ IT Danışma Asistanı — Yerel Kurulum Rehberi

## 1. Amaç ve kapsam

Bu rehber, İZELTAŞ IT Danışma Asistanı prototipinin yerel bir Windows bilgisayarda Docker Compose ve Ollama ile kurulmasını, çalıştırılmasını ve doğrulanmasını açıklar.

Hedef ortamlar yerel geliştirme, test ve staj demosudur. Sistem üretim kullanımı için TLS, kurumsal SSO, yüksek erişilebilirlik, otomatik yedekleme veya merkezi secret yönetimi sağlamaz.

Docker Compose, PostgreSQL + pgvector, n8n, FastAPI backend ve React frontend servislerini birlikte başlatır. Ollama, host işletim sisteminde ayrı çalışır. Normal yerel kurulumda backend veya frontend'i host üzerinde ayrıca başlatmak gerekmez.

## 2. Mimari özeti

```text
Tarayıcı
  → React + TypeScript / Nginx
  → FastAPI (Bearer JWT)
      ├─→ PostgreSQL
      └─→ n8n (X-Internal-Webhook-Key)
            ├─→ PostgreSQL + pgvector
            └─→ Ollama (host işletim sistemi)
```

- Frontend yalnızca FastAPI ile iletişim kurar; n8n webhook'larını doğrudan çağırmaz.
- PostgreSQL, n8n, backend ve frontend Docker Compose içinde çalışır.
- Ollama'ya container içinden `host.docker.internal` üzerinden erişilir.
- Varsayılan yayımlanan servis portları yalnızca `127.0.0.1` adresine bağlanır.
- Veri seti gerçek şirket verisi değil, zenginleştirilmiş ve Türkçeleştirilmiş 12 kategorize mock IT destek dokümanıdır.

## 3. Ön gereksinimler

Tam Docker kurulumu için:

- Windows 10 veya Windows 11
- Git
- Docker Desktop
- Docker Compose v2 (`docker compose`)
- Ollama

Host üzerinde doküman hazırlama, geliştirme veya test için ayrıca Python 3 gerekir. Frontend'i Docker dışında geliştirmek için Node.js ve npm gerekir. Docker imajları backend için Python 3.12, frontend build'i için Node.js 22 kullanır.

Çalışma dizini: herhangi bir dizin.

```powershell
git --version
docker --version
docker compose version
ollama --version
```

Docker komutlarından önce Docker Desktop'ın çalıştığını doğrulayın.

## 4. Repoyu edinme ve temel dizinler

Çalışma dizini: reponun oluşturulacağı üst dizin.

```powershell
git clone https://github.com/mozankaya/local-rag-it-assistant.git
```

Bundan sonraki "repo kökü" ifadeleri klonlanan `local-rag-it-assistant` dizinini belirtir.

```text
local-rag-it-assistant/
├─ backend/                         FastAPI, Alembic ve backend testleri
├─ data/
│  ├─ source-documents/           Kaynak dokümanlar
│  ├─ processed-documents/        İşlenmiş Markdown dosyaları
│  └─ documents.json              Ingestion manifesti
├─ database/                        Okunabilir şema ve bakım SQL referansları
├─ docker/                          Docker Compose ve ortam örneği
├─ docs/evaluation/                 Değerlendirme vakaları ve sonuçları
├─ frontend/                        React + TypeScript uygulaması
├─ n8n-workflows/                   Dört n8n workflow exportu
├─ scripts/                         Doküman ve değerlendirme scriptleri
└─ requirements-doc-processing.txt
```

## 5. Ollama modellerini kurma

Ollama host işletim sisteminde çalışmalıdır.

Çalışma dizini: herhangi bir dizin.

```powershell
ollama pull qwen3:4b-instruct-2507-q4_K_M
ollama pull qwen2.5:3b
ollama pull embeddinggemma:latest
ollama list
Invoke-RestMethod http://localhost:11434/api/tags
```

n8n yapılandırmasındaki model eşleşmeleri:

| Görev | Model etiketi |
|---|---|
| Ana cevap modeli | `qwen3:4b-instruct-2507-q4_K_M` |
| Scope classifier | `qwen2.5:3b` |
| Embedding modeli | `embeddinggemma:latest` |

n8n içindeki Ollama credential Base URL'si `http://host.docker.internal:11434` olmalıdır. Kısa `qwen3:4b` etiketi yerine tablodaki tam cevap modeli etiketi kullanılmalıdır.

## 6. Docker ortamını yapılandırma

Çalışma dizini: `docker/`.

```powershell
Copy-Item .env.example .env
```

`docker/.env` dosyasındaki gerçek secret değerlerini Git'e eklemeyin. En az aşağıdaki placeholder değerleri benzersiz ve güçlü değerlerle değiştirin:

- `POSTGRES_PASSWORD`
- `N8N_ENCRYPTION_KEY`
- `N8N_WEBHOOK_SECRET`
- `JWT_SECRET_KEY`

Compose tarafından kullanılan varsayılan, secret olmayan değerler:

```env
POSTGRES_USER=rag_user
POSTGRES_DB=rag_db
POSTGRES_PORT=5432

N8N_PORT=5678
GENERIC_TIMEZONE=Europe/Istanbul

BACKEND_PORT=8000
N8N_RAG_WEBHOOK_URL=http://n8n:5678/webhook/rag-query
N8N_FEEDBACK_WEBHOOK_URL=http://n8n:5678/webhook/feedback
N8N_REINDEX_WEBHOOK_URL=http://n8n:5678/webhook/admin-document-reindex

RAG_TOP_K=5
RAG_SCORE_THRESHOLD=0.54
RAG_MAX_SOURCES=3

JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

FRONTEND_PORT=5173
VITE_AUTH_API_URL=http://127.0.0.1:8000/auth
VITE_RAG_API_URL=http://127.0.0.1:8000/chat
VITE_FEEDBACK_API_URL=http://127.0.0.1:8000/feedback
```

Retrieval en fazla beş aday getirir, `0.54` veya daha düşük skor/distance değerlerini kabul eder ve yanıtta en fazla üç kaynak gösterir. Bu retrieval ölçümünde düşük değer daha iyi eşleşme anlamına gelir.

Compose; veritabanı URL'sini, webhook URL'lerini ve secret'ını, RAG ayarlarını, health URL'lerini ve JWT ayarlarını backend'e açıkça iletir. `REQUEST_TIMEOUT_SECONDS=60`, `REINDEX_TIMEOUT_SECONDS=300`, `SERVICE_STATUS_TIMEOUT_SECONDS=3` ve `MAX_QUESTION_LENGTH=1000` Docker Compose tarafından iletilmez; Docker kurulumunda backend kodundaki bu varsayılanlar kullanılır. Ayrı manuel backend kurulumu için mevcut `backend/.env.example`, desteklenen ortam değişkenlerini gösterir.

`N8N_WEBHOOK_SECRET`, FastAPI'nin n8n'e gönderdiği `X-Internal-Webhook-Key` değeridir ve n8n Header Auth credential değeriyle aynı olmalıdır.

Yayımlanan portlar `docker/.env` ile belirlenir; ancak portlar bağımsız biçimde serbestçe değiştirilemez:

- `FRONTEND_PORT` 5173 dışında bir değere alınırsa backend CORS izinlerine yeni frontend origin'i eklenmelidir.
- `BACKEND_PORT` değiştirilirse `VITE_*` API URL'leri aynı porta göre güncellenmeli ve frontend yeniden build edilmelidir.
- `VITE_ADMIN_API_URL` zorunlu değildir. Tanımlanmadığında frontend admin API taban adresini `VITE_AUTH_API_URL` içindeki `/auth` son ekini kaldırarak oluşturur.

## 7. Docker Compose yığını başlatma

Çalışma dizini: `docker/`.

```powershell
docker compose up -d --build
docker compose ps
```

Başlatılan container'lar:

```text
rag_postgres
rag_n8n
rag_backend
rag_frontend
```

Varsayılan yerel adresler:

| Servis | Adres |
|---|---|
| Frontend | `http://localhost:5173` |
| FastAPI health | `http://127.0.0.1:8000/health` |
| FastAPI Swagger | `http://127.0.0.1:8000/docs` |
| n8n | `http://localhost:5678` |
| Ollama API | `http://localhost:11434/api/tags` |
| PostgreSQL | `127.0.0.1:5432` |

Temel log kontrolü için, çalışma dizini `docker/`:

```powershell
docker compose logs --tail 100 postgres n8n backend frontend
```

## 8. Veritabanı migration'ları

Backend container başlarken otomatik olarak `alembic upgrade head` çalıştırır; ardından Uvicorn başlar. Canlı şema için esas kaynak Alembic migration zinciridir. `database/schema.sql` yalnızca okunabilir referanstır ve normal kurulumda elle import edilmemelidir.

Migration durumunu doğrulamak için, çalışma dizini `docker/`:

```powershell
docker compose exec backend alembic current
```

Migration'ı gerektiğinde yeniden uygulamak için, çalışma dizini `docker/`:

```powershell
docker compose exec backend alembic upgrade head
```

Varsayılan `POSTGRES_USER` ve `POSTGRES_DB` değerleri kullanılıyorsa temel tabloları ve aktif chunk sayılarını kontrol etmek için, çalışma dizini `docker/`:

```powershell
docker compose exec postgres psql -U rag_user -d rag_db -c "\dt"
docker compose exec postgres psql -U rag_user -d rag_db -c "SELECT metadata ->> 'document_id' AS document_id, COUNT(*) AS chunk_count FROM public.langchain_document_chunks GROUP BY metadata ->> 'document_id' ORDER BY document_id;"
```

Beklenen temel tablolar `alembic_version`, `n8n_vector_collections`, `langchain_document_chunks`, `langchain_document_chunks_staging`, `users`, `chat_logs` ve `feedback_logs` tablolarıdır.

## 9. n8n credential ve workflow kurulumu

n8n arayüzünü `http://localhost:5678` adresinde açın ve ilk açılışta owner hesabını oluşturun.

### Credential'lar

PostgreSQL credential:

```text
Host: postgres
Port: 5432
Database: docker/.env içindeki POSTGRES_DB
User: docker/.env içindeki POSTGRES_USER
Password: docker/.env içindeki POSTGRES_PASSWORD
SSL: kapalı
```

Ollama API credential:

```text
Base URL: http://host.docker.internal:11434
```

Header Auth credential:

```text
Header Name: X-Internal-Webhook-Key
Header Value: docker/.env içindeki N8N_WEBHOOK_SECRET
```

### Dört workflow exportu

Repo aşağıdaki dört exportu içerir:

| Dosya | Workflow | Trigger |
|---|---|---|
| `n8n-workflows/rag-query-webhook-workflow.json` | RAG Query Webhook Workflow | Authenticated POST webhook |
| `n8n-workflows/langchain-document-ingestion-workflow.json` | LangChain Document Ingestion Workflow | Manual Trigger ve authenticated POST webhook |
| `n8n-workflows/feedback-webhook-workflow.json` | Feedback Webhook Workflow | Authenticated POST webhook |
| `n8n-workflows/database-retention-cleanup-workflow.json` | Database Retention Cleanup | Günlük schedule |

JSON dosyalarını n8n arayüzünden import edin. Exportlar credential secret'larını taşımaz; importtan sonra credential eşleşmelerini yapın:

| Workflow | Gerekli credential'lar |
|---|---|
| RAG Query | PostgreSQL, Ollama API, Header Auth |
| Document Ingestion | PostgreSQL, Ollama API, Header Auth |
| Feedback | PostgreSQL, Header Auth |
| Database Retention Cleanup | PostgreSQL |

Webhook workflow'larında production `/webhook/...` URL'lerinin kullanılabilmesi için workflow'ları publish edin. Doğrulanacak POST yolları:

```text
/webhook/rag-query
/webhook/feedback
/webhook/admin-document-reindex
```

Cleanup workflow yerel bakım için isteğe bağlı olarak etkinleştirilebilir; her gün 03:00'te 30 günden eski chat ve feedback loglarını siler.

Bu log saklama politikası kullanıcı hesaplarından ayrıdır. Pasif bir kullanıcı, pasifleştirildikten 30 gün (720 saat) sonra backend kullanıcı yönetimi üzerinden kalıcı silinmeye uygun hale gelir; Database Retention Cleanup kullanıcı hesaplarını silmez.

## 10. Demo kullanıcılarını oluşturma

Backend container çalışırken, çalışma dizini `docker/`:

```powershell
docker compose exec backend python -m app.scripts.create_test_users
```

Script aşağıdaki yerel demo hesaplarını oluşturur veya günceller:

```text
Admin: admin@izeltas.local / Admin123!
User:  user@izeltas.local / User123!
```

Bu hesaplar yalnızca yerel demo içindir. Varsayılan parolaları paylaşılan veya üretim benzeri bir ortamda kullanmayın.

## 11. Doküman hazırlama ve ilk reindex

Desteklenen kaynak türleri MD, TXT, PDF ve DOCX; maksimum upload boyutu 10 MiB'dir. Kaynaklar `data/source-documents/`, işlenmiş dosyalar `data/processed-documents/`, manifest ise `data/documents.json` altındadır.

Host üzerinde doküman işleme bağımlılıklarını kurmak için, çalışma dizini repo kökü:

```powershell
python -m pip install -r requirements-doc-processing.txt
```

Manifesti ve processed dosyaları hazırlamak için, çalışma dizini repo kökü:

```powershell
python scripts/prepare_documents.py
```

Script çıktıları staging alanda hazırlar ve yalnızca tüm kaynaklar başarıyla işlendiğinde canlı processed dizini ile manifesti günceller. Hata durumunda mevcut çıktılar korunur.

Sonra admin hesabıyla frontend'e girin ve **Doküman Yönetimi → Yeniden İndeksle** işlemini çalıştırın.

Reindex davranışı:

- Chunk'lar önce `langchain_document_chunks_staging` tablosuna yazılır.
- Staging içeriği promotion öncesinde doğrulanır.
- Geçerli staging verisi transaction tabanlı işlemle aktif tabloya aktarılır.
- Hata durumunda önceki aktif indeks korunur.
- Session-level PostgreSQL advisory lock aynı anda tek reindex'e izin verir; ikinci istek HTTP 409 döner.
- Kaynak setinin bilinçli olarak boşaltılması desteklenir ve aktif indeks kilit altında güvenli biçimde temizlenir.

Admin panelinden upload veya update yapmak dosyayı otomatik ön işler, ancak reindex'i otomatik çalıştırmaz. Yeni içeriğin RAG indeksine geçmesi için **Yeniden İndeksle** ayrıca çalıştırılmalıdır.

## 12. Servis ve smoke-test doğrulaması

Container durumunu kontrol etmek için, çalışma dizini `docker/`:

```powershell
docker compose ps
```

PostgreSQL ve frontend için `healthy`, n8n ve backend için `running` durumu beklenir.

Backend health kontrolü için, çalışma dizini repo kökü:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Login ve chat smoke testi için, çalışma dizini repo kökü:

```powershell
$login = Invoke-RestMethod `
  -Method POST `
  -Uri "http://127.0.0.1:8000/auth/login" `
  -ContentType "application/json" `
  -Body '{"email":"admin@izeltas.local","password":"Admin123!"}'

$token = $login.access_token

Invoke-RestMethod `
  -Method POST `
  -Uri "http://127.0.0.1:8000/chat" `
  -Headers @{ Authorization = "Bearer $token" } `
  -ContentType "application/json" `
  -Body '{"question":"VPN bağlantısı kurulamıyor, ne yapmalıyım?"}'
```

Başarılı cevapta `answer`, `sources` ve `response_type` alanları bulunur. `response_type` değeri `rag_answer` olduğunda `answer` alanı beklenen 1–3 maddelik formatta döner.

Frontend'te login, bir chat sorusu, kaynak gösterimi ve feedback gönderimini doğrulayın. Admin hesabıyla **Sistem Durumu** ekranı backend, PostgreSQL, n8n ve Ollama erişimini gösterir.

## 13. İsteğe bağlı geliştirme ve test komutları

### Backend testleri

Uygulama bağımlılıkları kurulu bir Python ortamında test bağımlılıklarını kurmak için, çalışma dizini `backend/`:

```powershell
python -m pip install -r requirements-test.txt
```

Testleri çalıştırmak için, çalışma dizini `backend/`:

```powershell
pytest
```

Güncel test sonucu, çalışan ortamdaki `pytest` çıktısından doğrulanmalıdır.

### Frontend kontrolleri

Çalışma dizini: `frontend/`.

```powershell
npm install
npm run lint
npm run build
npm run dev
```

### İsteğe bağlı final RAG regresyonu

Backend, n8n, PostgreSQL, Ollama ve gerekli workflow'lar çalışırken, çalışma dizini repo kökü:

```powershell
python scripts/run_rag_evaluation.py `
  --model qwen3-4b-instruct-2507 `
  --cases docs/evaluation/cases/rag-regression-cases-mock-data.json `
  --repeat 1
```

Repository'de kayıtlı son final çalıştırma 50/50 başarılıdır. Sonuçlar `docs/evaluation/results/qwen3-4b-instruct-2507/results.csv`, özet metrikler ise aynı dizindeki `summary.csv` dosyasındadır.

`--model` yalnızca sonuç klasörü ve CSV etiketi olarak kullanılır; n8n veya Ollama modelini değiştirmez. Ayrıntılı vakalar ve sonuçlar için `docs/evaluation/` dizinine bakın.

## 14. Sorun giderme

### Docker servisleri başlamıyor

Çalışma dizini: `docker/`.

```powershell
docker compose ps
docker compose logs --tail 200 postgres n8n backend frontend
```

Docker Desktop'ın çalıştığını, `docker/.env` dosyasını, boş ortam değerlerini ve port çakışmalarını kontrol edin.

### Ollama kullanılamıyor

Çalışma dizini: herhangi bir dizin.

```powershell
ollama list
Invoke-RestMethod http://localhost:11434/api/tags
```

n8n Ollama credential Base URL'sinin `http://host.docker.internal:11434` ve model etiketlerinin bu rehberdeki tam etiketler olduğunu doğrulayın.

### PostgreSQL kullanılamıyor

Çalışma dizini: `docker/`.

```powershell
docker compose ps postgres
docker compose logs --tail 200 postgres
```

`POSTGRES_USER`, `POSTGRES_PASSWORD` ve `POSTGRES_DB` değerlerinin n8n PostgreSQL credential ile eşleştiğini kontrol edin.

### n8n workflow bulunamıyor veya yetkilendirme başarısız

- Dört workflow'un import edildiğini ve kullanılan webhook workflow'unun publish edildiğini doğrulayın.
- Production URL'lerinde `/webhook/...` yolunu kullanın.
- 401 veya webhook yetkilendirme hatasında Header Auth adının tam olarak `X-Internal-Webhook-Key` olduğunu kontrol edin.
- Header Auth değeri `docker/.env` içindeki `N8N_WEBHOOK_SECRET` ile aynı olmalıdır.

### Frontend API isteği başarısız

Backend health adresini ve `VITE_*` URL'lerini kontrol edin. URL veya backend portu değiştiyse frontend'i yeniden build edin. Frontend portu değiştiyse backend CORS origin'ini de güncelleyin.

### HTTP 401 veya 403

- 401, geçersiz ya da süresi dolmuş JWT nedeniyle oluşabilir; tekrar login olun.
- 403, pasif hesapla login denemesinde veya standart kullanıcının admin endpoint'ine erişmesinde oluşabilir; aktif hesap ve doğru rol kullandığınızı doğrulayın.

### Reindex 409, 502 veya 504 döndürüyor

- 409, başka bir reindex'in advisory lock'u tuttuğunu gösterir; devam eden işlemin bitmesini bekleyin.
- 502, backend'in n8n'e ulaşamadığını veya geçerli bir n8n cevabı alamadığını gösterir; workflow, credential ve n8n loglarını kontrol edin.
- 504, reindex isteğinin backend zaman aşımına ulaştığını gösterir; n8n execution ve Ollama durumunu kontrol edin.

### Doküman değişikliğinden sonra embedding yok

Upload veya update yalnızca ön işlemeyi otomatik yapar. Admin panelinden **Yeniden İndeksle** işlemini çalıştırın; sorun sürerse ingestion execution'ı, Ollama embedding credential'ını ve staging doğrulamasını kontrol edin.

### Migration başarısız

Çalışma dizini: `docker/`.

```powershell
docker compose logs --tail 200 backend
docker compose exec backend alembic current
docker compose exec backend alembic upgrade head
```

`database/schema.sql` dosyasını elle import ederek migration zincirini atlamayın.

### Frontend route refresh başarısız

Docker frontend'i Nginx ile sunar ve SPA fallback `frontend/nginx.conf` içinde `/index.html` olarak tanımlıdır. Container'ın güncel frontend imajıyla build edildiğini ve bu Nginx yapılandırmasını kullandığını doğrulayın.

## 15. Güvenlik ve yerel veri notları

- Gerçek `.env` dosyaları, parolalar, JWT secret, n8n encryption key, webhook secret ve access token'lar Git'e eklenmemelidir.
- `JWT_SECRET_KEY`, `N8N_ENCRYPTION_KEY`, `N8N_WEBHOOK_SECRET` ve veritabanı parolası yerel kurulumda değiştirilmelidir.
- FastAPI'den n8n'e giden webhook istekleri `X-Internal-Webhook-Key` ile korunur.
- Frontend doğrudan n8n'e bağlanmamalıdır.
- Varsayılan Compose port bağlamalarının `127.0.0.1` ile sınırlı kalması yerel demo sınırını korur.
- Ollama inference, doküman işleme ve veritabanı yerel ortamda çalışır.
- Repo yalnızca mock IT dokümanları içerir; gerçek şirket veya kişisel veri eklemeyin.
- Demo hesapları üretim hesabı değildir.

## 16. Durdurma, yeniden başlatma, rebuild ve sıfırlama

Servisleri durdurmak için, çalışma dizini `docker/`:

```powershell
docker compose down
```

Servisleri yeniden başlatmak için, çalışma dizini `docker/`:

```powershell
docker compose up -d
```

Kod veya build-time frontend ortamı değiştiğinde rebuild için, çalışma dizini `docker/`:

```powershell
docker compose up -d --build
```

Yalnızca tek servisi rebuild etmek için, çalışma dizini `docker/`:

```powershell
docker compose up -d --build backend
docker compose up -d --build frontend
```

PostgreSQL ve n8n kalıcı verileri dahil yerel Docker verilerini tamamen silerek sıfırlamak için, çalışma dizini `docker/`:

```powershell
docker compose down -v
docker compose up -d --build
```

`docker compose down -v` geri alınamaz biçimde PostgreSQL ve n8n volume'larını siler; yalnızca bilinçli temiz demo kurulumu için kullanın.
