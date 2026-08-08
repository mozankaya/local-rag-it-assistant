# RAG Evaluation

Bu klasör yalnızca güncel test vakalarını ve seçilmiş model sonuçlarını tutar.

## Klasör Yapısı

```text
docs/evaluation/
├── README.md
├── cases/
│   ├── evaluation-cases.json
│   ├── rag-regression-cases-mock-data.json
│   ├── rag-security-cases.json
│   └── retrieval-normalization-cases.json
└── results/
    ├── <model-etiketi>/
    └── qwen3-4b-instruct-2507-prompt-fallback/
        ├── results.csv
        └── summary.csv
```

Her test, `--model` parametresinde verilen etikete göre `results/` altında
ayrı bir klasör oluşturur.

Aynı model etiketiyle test tekrar çalıştırıldığında ilgili klasördeki
`results.csv` ve `summary.csv` dosyaları güncellenir. Böylece tarih damgalı
çok sayıda CSV dosyası birikmez.

Eski sonuçlara gerektiğinde Git geçmişinden veya oluşturulan tag'lerden
erişilebilir.

## Ortam Değişkenleri

PowerShell:

```powershell
$env:RAG_API_BASE_URL="http://127.0.0.1:8000"
$env:RAG_LOGIN_EMAIL="admin@izeltas.local"
$env:RAG_LOGIN_PASSWORD="<TEST_PASSWORD>"
```

## Final RAG Regresyon Testi

```powershell
python scripts/run_rag_evaluation.py `
  --model qwen3-4b-instruct-2507-prompt-fallback `
  --cases docs/evaluation/cases/rag-regression-cases-mock-data.json `
  --repeat 1
```

Güncel final regresyon seti 50 vaka içerir. Repository'de kayıtlı son çalıştırma 50/50 başarılıdır; kaynak, bölüm, anahtar kelime, yanıt türü ve yanıt biçimi kontrollerinin her biri 50/50 geçmiştir ve istek hatası yoktur. Bu sonuçların kaynağı `results/qwen3-4b-instruct-2507-prompt-fallback/summary.csv` dosyasıdır.

`results/qwen3-4b-instruct-2507-prompt-fallback/` dışındaki model sonuç dizinleri karşılaştırma için korunan tarihsel/baseline çalışmalardır. Önceki mock veri düzenini veya eski İngilizce `document_id` değerlerini yansıtabilirler ve güncel final sistem sonucu olarak değerlendirilmemelidir.

## Normalizasyon Testi

```powershell
python scripts/run_rag_evaluation.py `
  --model qwen3-4b-instruct-2507-normalization `
  --cases docs/evaluation/cases/retrieval-normalization-cases.json `
  --repeat 1
```

## Tarihsel Model Karşılaştırması

Önceki model veya veri düzeniyle karşılaştırma gerektiğinde tarihsel
`evaluation-cases.json` seti farklı bir sonuç etiketiyle çalıştırılabilir:

```powershell
python scripts/run_rag_evaluation.py `
  --model qwen3-4b-instruct-2507-prompt-fallback `
  --cases docs/evaluation/cases/evaluation-cases.json `
  --repeat 1
```

`--model` parametresi yalnızca sonuç klasörünü ve CSV içindeki model etiketini
belirler. n8n veya Ollama üzerindeki gerçek modeli otomatik olarak değiştirmez.

## Manuel Değerlendirme

`results.csv` içinde şu alanlar manuel olarak doldurulabilir:

- `manual_quality_score`: 1–5
- `manual_notes`: Kaynak sadakati, çelişki veya kaynak dışı bilgi notu

Otomatik metrikler retrieval ve cevap biçimi kontrollerini yapar. Kaynağın
anlamını tersine çevirme veya kaynakta olmayan bilgi ekleme gibi sorunlar
manuel olarak değerlendirilmelidir.
