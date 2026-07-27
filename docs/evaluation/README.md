# RAG Evaluation

Bu klasör yalnızca güncel test vakalarını ve seçilmiş model sonuçlarını tutar.

## Klasör Yapısı

```text
docs/evaluation/
├── README.md
├── cases/
│   ├── evaluation-cases.json
│   └── retrieval-normalization-cases.json
└── results/
    └── <model-etiketi>/
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

## Tam Test

```powershell
python scripts/evaluate_rag.py `
  --model qwen2.5-3b `
  --cases docs/evaluation/cases/evaluation-cases.json `
  --repeat 1
```

## Normalizasyon Testi

```powershell
python scripts/evaluate_rag.py `
  --model qwen2.5-3b-normalization `
  --cases docs/evaluation/cases/retrieval-normalization-cases.json `
  --repeat 1
```

## Model Karşılaştırması

n8n içindeki cevap üretme modeli değiştirildikten sonra aynı test farklı bir
model etiketiyle çalıştırılır:

```powershell
python scripts/evaluate_rag.py `
  --model qwen3-4b-instruct-2507-q4-k-m `
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