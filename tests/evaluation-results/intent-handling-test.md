# Intent Handling Test

## Amaç

Bu test, chatbot'un karşılama, asistan kimliği, kapsam dışı sorular ve normal IT destek sorularını doğru yönlendirip yönlendirmediğini kontrol etmek için yapılmıştır.

## Test Sonuçları

| Soru | Beklenen Davranış | Sonuç |
|---|---|---|
| Merhaba | Karşılama cevabı | Başarılı |
| Sen kimsin? | Asistan kimliği cevabı | Başarılı |
| Ne yapabiliyorsun? | Desteklenen konuları açıklama | Başarılı |
| Teşekkürler | Teşekkür cevabı | Başarılı |
| Bana yemek tarifi verir misin? | Kapsam dışı cevabı | Başarılı |
| Python kodu yazar mısın? | Kapsam dışı cevabı | Başarılı |
| Bugün hava nasıl? | Kapsam dışı cevabı | Başarılı |
| VPN bağlantısı kuramıyorum | Normal RAG cevabı | Başarılı |
| Merhaba, VPN bağlantısı kuramıyorum | Normal RAG cevabı | Başarılı |
| Şifremi unuttum | Normal RAG cevabı | Başarılı |

## Genel Değerlendirme

Eklenen basit intent kontrolü sayesinde chatbot, genel karşılama ve asistan kimliği sorularına doğrudan cevap verebilmekte; kapsam dışı sorularda ise RAG/LLM akışına girmeden kullanıcıyı desteklenen IT konularına yönlendirmektedir.