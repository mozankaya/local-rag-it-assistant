# RAG Değerlendirmesi

Bu dizin değerlendirme vaka dosyalarını ve kaydedilmiş final, destekleyici ve tarihsel sonuçları içerir.

## Klasör yapısı

```text
docs/evaluation/
├── cases/
│   ├── evaluation-cases.json
│   ├── rag-regression-cases-mock-data.json
│   ├── rag-security-cases.json
│   └── retrieval-normalization-cases.json
└── results/
    ├── qwen3-4b-instruct-2507/                  Final 50 vakalı regresyon
    ├── qwen3-4b-instruct-2507-normalization/    Normalizasyon sonuçları
    ├── qwen3-4b-instruct-2507-stability/        Kararlılık sonuçları
    ├── security/
    │   └── qwen3-4b-instruct-2507-security/     Güvenlik ve sağlamlık sonuçları
    ├── qwen2.5-3b/                              Tarihsel model karşılaştırması
    ├── phi4-mini-3.8b/                          Tarihsel model karşılaştırması
    ├── qwen3-4b-historical-comparison/          Tarihsel model karşılaştırması
    ├── qwen2.5-3b-normalization/                 Tarihsel normalizasyon sonucu
    └── phi4-mini-3.8b-normalization/             Tarihsel normalizasyon sonucu
```

Her çalışma sonuç dizininde ayrıntılı vaka kayıtlarını içeren `results.csv` ve toplu metrikleri içeren `summary.csv` bulunur.

## Ortam değişkenleri

PowerShell:

```powershell
$env:RAG_API_BASE_URL="http://127.0.0.1:8000"
$env:RAG_LOGIN_EMAIL="admin@izeltas.local"
$env:RAG_LOGIN_PASSWORD="<TEST_PASSWORD>"
```

## Final RAG regresyonu

Final değerlendirme, Ollama üzerinde çalışan `qwen3:4b-instruct-2507-q4_K_M` cevap modelini temsil eder. Değerlendiricideki `--model` argümanı çalışma etiketi, CSV `model` alanı ve sonuç dizini adı için kullanılır; n8n veya Ollama modelini seçmez ya da değiştirmez.

Backend, n8n, PostgreSQL, Ollama ve gerekli workflow'lar çalışırken repo kökünden:

```powershell
python scripts/run_rag_evaluation.py `
  --model qwen3-4b-instruct-2507 `
  --cases docs/evaluation/cases/rag-regression-cases-mock-data.json `
  --repeat 1
```

Bu komut sonuçları `results/qwen3-4b-instruct-2507/` dizinine yazar. Kayıtlı final sonuçlarını korumak için mevcut CSV dosyalarının üzerine yazmadan önce ayrı bir kopya alınmalıdır.

## Sonuç dosyaları

[`results.csv`](results/qwen3-4b-instruct-2507/results.csv), her vaka için soru ve cevapla birlikte beklenen ve gerçekleşen cevap türünü, doküman ve bölüm eşleşmelerini, kaynak skorlarını, anahtar kelime ve cevap biçimi kontrollerini, genel vaka sonucunu, cevap süresini, istek hatasını ve isteğe bağlı manuel değerlendirme alanlarını içerir.

[`summary.csv`](results/qwen3-4b-instruct-2507/summary.csv), toplam çalışma ve başarılı vaka sayılarını; kaynak, bölüm, anahtar kelime, cevap türü ve cevap biçimi eşleşme sayılarını; istek hatası sayısını ve ortalama, minimum ve maksimum cevap sürelerini özetler.

## Güncel sonuç özeti

| Test | Sonuç |
|---|---|
| Final regresyon | 50/50 |
| İstek hataları | 0 |
| Ortalama cevap süresi | 3.223 s |
| Normalizasyon | 12/12 |
| Kararlılık | 147/147 |
| Güvenlik ve sağlamlık | 18/18 |

`50/50`, hazırlanmış mock/sentetik final regresyon setindeki bütün vakaların geçtiğini ifade eder; evrensel bir doğruluk oranı değildir.

Normalizasyon testi repo kökünden şu komutla çalıştırılabilir:

```powershell
python scripts/run_rag_evaluation.py `
  --model qwen3-4b-instruct-2507-normalization `
  --cases docs/evaluation/cases/retrieval-normalization-cases.json `
  --repeat 1
```

## Tarihsel model karşılaştırması

Bu sonuçlar ayrı bir 49 vakalı tarihsel karşılaştırmaya aittir ve final 50 vakalı regresyonla birleştirilmemelidir.

| Model | Sonuç |
|---|---|
| Qwen2.5 3B | 45/49 |
| Phi4-mini 3.8B | 44/49 |
| Qwen3 4B | 49/49 |

Bu karşılaştırma sonucunda Qwen3 4B final cevap modeli olarak seçilmiştir. `--model` gerçek runtime modelini değiştirmediği için karşılaştırma öncesinde hedef model n8n/Ollama yapılandırmasında ayrıca doğrulanmalıdır.

Tarihsel Qwen3 çalıştırması, final sonuçlarını ezmemesi için ayrı bir etiket kullanır:

```powershell
python scripts/run_rag_evaluation.py `
  --model qwen3-4b-historical-comparison `
  --cases docs/evaluation/cases/evaluation-cases.json `
  --repeat 1
```

## Manuel değerlendirme

`results.csv` içindeki `manual_quality_score` ve `manual_notes` alanları kaynak sadakati, çelişki veya kaynak dışı bilgi gibi otomatik kontrollerin kapsamadığı noktalar için kullanılabilir.
