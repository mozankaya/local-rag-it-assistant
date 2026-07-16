# RAG Test Questions

Bu dosya, RAG tabanlı IT destek asistanının ilk prototipini test etmek için kullanılan örnek soruları içerir.

## Test Kriterleri

Her soru için aşağıdaki noktalar kontrol edilir:

- Doğru doküman veya kategoriye ait chunk getiriliyor mu?
- Cevap kaynak metne uygun mu?
- Cevap Türkçe mi?
- Cevap kısa ve anlaşılır mı?
- Model kaynak dışı bilgi üretiyor mu?
- Cevap tekrar içeriyor mu?

## Test Soruları

| No | Soru | Beklenen Doküman | Beklenen Kategori | Durum | Not |
|---|---|---|---|---|---|
| 1 | VPN bağlantısı kuramıyorum, ne yapmalıyım? | vpn-remote-access | vpn | Başarılı | İlgili VPN adımları getirildi. |
| 2 | Şifremi unuttum, nasıl sıfırlayabilirim? | password-and-account | account | Başarılı | Şifre sıfırlama süreci ve IT destek yönlendirmesi döndü. |
| 3 | Yazıcıdan çıktı alamıyorum. | printer-support | printer | Test edilecek |  |
| 4 | Outlook e-posta göndermiyor, ne yapmalıyım? | email-outlook | email | Test edilecek |  |
| 5 | Bilgisayarım çok yavaş çalışıyor. | hardware-support | hardware | Test edilecek |  |
| 6 | İnternet bağlantım yok, ne yapmalıyım? | network-connection | network | Test edilecek |  |
| 7 | Yeni ekipman talebi nasıl oluşturulur? | equipment-request | request | Test edilecek |  |
| 8 | Hesabım kilitlendi, ne yapmalıyım? | password-and-account | account | Test edilecek |  |
| 9 | VPN sürekli kopuyor. | vpn-remote-access | vpn | Test edilecek |  |
| 10 | Yazılım yetkisi talep etmek istiyorum. | equipment-request | request | Test edilecek |  |

## Örnek Başarılı Çıktı

### Soru

```text
VPN bağlantısı kuramıyorum, ne yapmalıyım?
```

### Beklenen Cevap Tipi

```text
- İnternet bağlantınızı kontrol edin.
- VPN kullanıcı adı ve şifrenizin doğru olduğundan emin olun.
- Çok faktörlü doğrulama kullanılıyorsa onay bildirimini kontrol edin.
- Sorun devam ederse VPN uygulamasını kapatıp tekrar açın veya IT destek ekibine başvurun.
```

## Gözlemler

İlk testlerde küçük boyutlu lokal model kullanıldığı için bazı cevaplarda tekrar, dil bilgisi hatası veya kaynak dışı detay üretme eğilimi gözlemlenmiştir.

Bu nedenle prompt yapısı sadeleştirilmiş, modele daha az ve daha ilgili context verilmiş ve cevaplar kısa maddelerle sınırlandırılmıştır.

## Gelecek İyileştirmeler

- Cevap yanında kaynak doküman bilgisinin gösterilmesi
- Test sonuçlarının başarılı/başarısız olarak işaretlenmesi
- Her soru için beklenen cevap örneğinin eklenmesi
- Farklı lokal modellerle cevap kalitesinin karşılaştırılması
- Daha geniş test soru seti hazırlanması