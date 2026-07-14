# V1 RAG Evaluation Results

Bu dosya, ilk çalışan RAG prototipinin örnek IT destek soruları üzerindeki test sonuçlarını içerir.

## Test Ortamı

- LLM Runtime: Ollama
- LLM Model: qwen2.5:3b
- Embedding Model: embeddinggemma
- Vector Database: PostgreSQL + pgvector
- Workflow: RAG Query Webhook Workflow
- Frontend: React + TypeScript

## Değerlendirme Kriterleri

| Kriter | Açıklama |
|---|---|
| Doğru Kaynak | Sistem ilgili doküman/chunk bilgisini getirdi mi? |
| Kaynağa Uygunluk | Cevap kaynak metindeki bilgilerle uyumlu mu? |
| Dil Kalitesi | Cevap Türkçe, anlaşılır ve kısa mı? |
| Tekrar Durumu | Cevap gereksiz tekrar içeriyor mu? |
| Kaynak Dışı Bilgi | Model kaynakta olmayan bilgi uydurdu mu? |

## Test Sonuçları

| No | Soru | Beklenen Kaynak | Gelen Kaynak | Sonuç | Not |
|---|---|---|---|---|---|
| 1 | VPN bağlantısı kuramıyorum, ne yapmalıyım? | vpn-remote-access | vpn-remote-access | Başarılı | Doğru kaynak getirildi. Cevap ilgili VPN bağlantı adımlarını içerdi. |
| 2 | Şifremi unuttum, nasıl sıfırlayabilirim? | password-and-account | password-and-account | Kısmen başarılı | Doğru kaynak getirildi. Cevap genel olarak uygun olsa da bazı tekrarlar ve gereksiz ifadeler içerdi. |
| 3 | Yazıcıdan çıktı alamıyorum. | printer-support | printer-support | Başarılı | Doğru kaynak getirildi. Cevap kaynakla uyumlu ve uygulanabilir adımlar içerdi. |
| 4 | Outlook e-posta göndermiyor, ne yapmalıyım? | email-outlook | email-outlook | Kısmen başarılı | Doğru kaynak getirildi. Ancak cevapta e-posta gönderme bölümü dışında farklı alt bölümlerden de etkilenme görüldü. |
| 5 | Bilgisayarım çok yavaş çalışıyor. | hardware-support | hardware-support | Başarılı | Doğru kaynak getirildi. Cevap kısa, anlaşılır ve uygulanabilir bulundu. |
| 6 | İnternet bağlantım yok, ne yapmalıyım? | network-connection | network-connection | Başarılı | Doğru kaynak getirildi. Cevap kısa ve ilgili bağlantı kontrol adımlarını içerdi. |
| 7 | Yeni ekipman talebi nasıl oluşturulur? | equipment-request | equipment-request | Kısmen başarılı | Doğru kaynak getirildi. Cevap kaynakla uyumlu olsa da ifade dili daha doğal hale getirilebilir. |
| 8 | Hesabım kilitlendi, ne yapmalıyım? | password-and-account | password-and-account | Kısmen başarılı | Doğru kaynak getirildi. Ancak cevapta dil bilgisi hataları ve bazı tekrarlar gözlemlendi. |
| 9 | VPN sürekli kopuyor. | vpn-remote-access | vpn-remote-access | Başarısız / Kısmen başarılı | Doğru kaynak getirildi fakat cevapta anlamsız ifadeler ve dil karışıklığı oluştu. |
| 10 | Yazılım yetkisi talep etmek istiyorum. | equipment-request | equipment-request | Başarılı | Doğru kaynak getirildi. Cevap genel olarak kaynakla uyumlu ve anlaşılır bulundu. |

## Örnek Test Çıktıları

### 1. VPN bağlantısı kuramıyorum, ne yapmalıyım?

**Gelen kaynak:** `vpn-remote-access`

**Cevap özeti:**

```text
- İnternet bağlantısını kontrol edin.
- Kullanıcı adı ve şifrenizi doğrulayın.
- Çok faktörlü doğrulama durumunda telefonu kontrol edin.
- VPN uygulamasını kapatıp tekrar açın.
- Bilgisayarınızı yeniden başlatın.
```

**Değerlendirme:**  
Cevap doğru kaynak üzerinden üretilmiştir. Bazı ifadeler daha doğal hale getirilebilir, ancak genel olarak kullanıcıya uygulanabilir adımlar sunmaktadır.

### 2. Şifremi unuttum, nasıl sıfırlayabilirim?

**Gelen kaynak:** `password-and-account`

**Cevap özeti:**

```text
- Şifrenizi unutmuş olduğunuzda IT destek ekibine başvurmanız gerekebilir.
- Şifre sıfırlama bağlantısı çalışmıyorsa veya hesabınıza erişemiyorsanız IT destek ekibine başvurmanız önerilir.
- Kurumun belirttiği şifre sıfırlama süreci takip edilmelidir.
```

**Değerlendirme:**  
Kaynak doğru getirilmiştir. Cevap genel olarak uygun olsa da aynı yönlendirmeyi birden fazla kez tekrar ettiği için kısmen başarılı olarak değerlendirilmiştir.

### 3. Yazıcıdan çıktı alamıyorum.

**Gelen kaynak:** `printer-support`

**Cevap özeti:**

```text
- Bilgisayar ve yazıcının aynı ağda olduğundan emin olun.
- Kullanılan yazıcıyı kontrol edin ve varsayılan yazıcı olarak ayarlayın.
- Kağıt sıkışması veya toner bitmesi durumunu inceleyin.
```

**Değerlendirme:**  
Cevap kaynakla uyumlu, kısa ve uygulanabilir adımlar içerdiği için başarılı kabul edilmiştir.

### 4. Outlook e-posta göndermiyor, ne yapmalıyım?

**Gelen kaynak:** `email-outlook`

**Cevap özeti:**

```text
- E-posta alıcı adresi kontrol edilmelidir.
- Büyük dosya boyutu sınırı kontrol edilmelidir.
- Posta kutusu doluluğu ve senkronizasyon durumu incelenmelidir.
```

**Değerlendirme:**  
Doğru doküman getirilmiştir. Ancak cevapta e-posta gönderme konusu yanında e-posta alma/senkronizasyon bölümünden de etkilenme görülmüştür. Bu nedenle kısmen başarılı olarak değerlendirilmiştir.

### 9. VPN sürekli kopuyor.

**Gelen kaynak:** `vpn-remote-access`

**Cevap özeti:**

```text
- Kablo ağ sinyalini kontrol edin.
- ABD bağlantısı deneyin.
- Hata mesajını bilgisayardancreenshot alın.
```

**Değerlendirme:**  
Doğru kaynak getirilmesine rağmen cevapta anlamsız ifadeler, dil bozulması ve kaynak metnin hatalı yorumlanması görülmüştür. Bu test, küçük boyutlu lokal modelin cevap kalitesi açısından sınırlılıklarını göstermektedir.

## Genel Gözlemler

- Sistem, test edilen sorularda çoğunlukla doğru doküman veya kategoriye ait kaynakları getirmiştir.
- Cevapların altında kaynak doküman bilgisi gösterilebilmiştir.
- Retrieval yani ilgili dokümanı bulma tarafı genel olarak başarılıdır.
- Cevap üretim tarafında küçük lokal model nedeniyle bazı dil bilgisi hataları, tekrarlar ve anlamsız ifadeler görülebilmektedir.
- Prompt sadeleştirildiğinde cevaplar daha kısa ve kaynaklara daha bağlı hale gelmiştir.
- Bazı sorularda aynı doküman içindeki farklı alt bölümlerden bilgi karışması oluşabilmektedir.
- Kaynak gösterme özelliği, cevabın hangi dokümandan üretildiğini takip etmeyi kolaylaştırmıştır.

## V1 Sonucu

İlk çalışan prototip; doküman ingestion, vektör arama, lokal LLM cevap üretimi, webhook API, React frontend entegrasyonu ve kaynak gösterme özellikleri açısından başarıyla doğrulanmıştır.

Testlerde sistemin ilgili kaynakları büyük ölçüde doğru bulduğu görülmüştür. Bununla birlikte, kullanılan küçük boyutlu lokal model nedeniyle bazı cevaplarda dil kalitesi ve ifade tutarlılığı sınırlı kalmıştır.

Bu nedenle V1 sürümü, çalışan bir lokal RAG prototipi olarak başarılı kabul edilmiştir. Sonraki sürümlerde cevap kalitesinin artırılması, kaynak seçim stratejisinin geliştirilmesi ve kullanıcı geri bildirimi toplanması hedeflenmektedir.

## V1 Sonrası Planlanan Geliştirmeler

V1 testleri sonucunda sistemin doküman bulma tarafında genel olarak başarılı olduğu, ancak cevap üretimi ve kullanıcı deneyimi tarafında geliştirilebilecek noktalar bulunduğu görülmüştür. Bu nedenle sonraki aşamalarda aşağıdaki geliştirmelerin yapılması planlanmaktadır:

- Daha güçlü lokal modeller denenerek cevap kalitesi karşılaştırılacaktır.
- Prompt yapısı farklı soru türlerine göre iyileştirilecektir.
- Aynı doküman içindeki farklı alt bölümlerden bilgi karışmasını azaltmak için chunk seçim stratejisi geliştirilecektir.
- Cevap altında gösterilen kaynak doküman bilgisi daha kullanıcı dostu hale getirilecektir.
- Faydalı / Faydasız geri bildirim butonları eklenerek kullanıcı geri bildirimi toplanacaktır.
- Test sonuçları daha geniş bir soru setiyle tekrar değerlendirilecektir.
- Doküman listesinin manifest dosyası üzerinden yönetilmesi sağlanacaktır.
- Frontend tasarımı daha kurumsal ve kullanıcı dostu hale getirilecektir.
- İlerleyen sürümlerde admin panel üzerinden doküman ekleme özelliği değerlendirilecektir.