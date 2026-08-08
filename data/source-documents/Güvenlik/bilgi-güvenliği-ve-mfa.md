# Bilgi Güvenliği ve MFA

<!-- Bu doküman staj projesi için hazırlanmış sentetik/mock IT prosedürüdür; gerçek şirket prosedürü değildir. -->

Bu doküman şüpheli e-posta, phishing, beklenmeyen MFA onayı, MFA bildirimi gelmemesi ve telefon değişikliği gibi güvenlik olaylarında izlenecek ilk adımları açıklar.

## Şüpheli e-posta alındı

Gönderen adresi, konu, bağlantılar ve ek dosyalar dikkatle kontrol edilmelidir. Beklenmeyen bağlantı veya ek açılmamalıdır.

E-posta silinmeden önce kurumun IT destek/bilgi güvenliği sürecine bildirilmelidir. Ekran görüntüsünde gereksiz kişisel bilgiler varsa paylaşılmadan önce gizlenmelidir.

Kullanıcı e-postadaki numarayı arayarak veya bağlantıyı tıklayarak doğrulama yapmamalıdır.

## Yanlışlıkla şüpheli bağlantıya tıklandı

Kullanıcı bağlantıyı kapatmalı ve sayfaya parola/MFA kodu gibi bilgi girdiyse bunu destek kaydında açıkça belirtmelidir.

Parola girildiyse kurumun parola değiştirme süreci uygulanmalı ve IT/bilgi güvenliği ekibi mümkün olan en kısa sürede bilgilendirilmelidir.

Olay saati, e-posta gönderen adresi ve tıklanan bağlantının metni kayda eklenmelidir.

## Beklenmeyen MFA onayı geliyor

Kullanıcı kendisinin başlatmadığı MFA isteğini onaylamamalıdır.

Beklenmeyen istek tekrar ediyorsa hesap parolası değiştirilmesi ve aktif oturumların kontrolü için IT desteğine başvurulmalıdır.

Parola, MFA doğrulama kodu veya başka bir gizli bilgi paylaşılmamalıdır.

## MFA bildirimi gelmiyor

Telefonun internet bağlantısı ve doğrulama uygulamasının çalıştığı kontrol edilmelidir. Uygulama içinde bekleyen onay isteği bulunup bulunmadığı incelenebilir.

Bildirim gelmemesi nedeniyle kullanıcı MFA'yı devre dışı bırakmaya veya başka kullanıcının cihazını kullanmaya çalışmamalıdır.

Kullanıcı adı, cihaz/telefon değişikliği durumu ve deneme saati destek kaydına eklenmelidir.

## Telefon değiştirildi ve MFA çalışmıyor

Yeni telefonda doğrulama uygulaması kurulmuş olsa bile önceki MFA kaydı otomatik taşınmamış olabilir.

MFA kaydı yetkili destek süreci üzerinden yeniden eşleştirilmelidir. Kullanıcı eski cihazına erişemiyorsa bu durum talepte belirtilmelidir.

MFA yedek kodları veya doğrulama kodları destek kaydına yazılmamalıdır.

## Parola veya doğrulama kodu isteyen kişiyle karşılaşıldı

IT destek personeli dahil hiç kimse kullanıcıdan parolasını veya anlık MFA kodunu paylaşmasını istememelidir.

Böyle bir talep e-posta, telefon veya mesaj yoluyla gelirse kullanıcı işlem yapmadan olayı güvenlik sürecine bildirmelidir.

## Güvenlik olayı için destek kaydına eklenecek bilgiler

Olay saati, gönderen adresi, kullanılan uygulama, ekran görüntüsü ve kullanıcının hangi işlemi yaptığı yazılmalıdır.

Parola, MFA kodu, erişim anahtarı ve API anahtarı gibi gizli bilgiler eklenmemelidir.
