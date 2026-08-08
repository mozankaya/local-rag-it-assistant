# Destek Kaydı Ve Takip Süreci

<!--
source_file_name: destek-kaydı-ve-takip-süreci.md
source_file_type: md
content_hash: 467727329a0f85aa758b5a8f4dcd364cdb285cd7e80b3cae194db2425b20debd
processed_at: 2026-08-08T11:41:16
-->

# IT Destek Kaydı Oluşturma ve Takip Süreci

<!-- Bu doküman staj projesi için hazırlanmış sentetik/mock IT prosedürüdür; gerçek şirket prosedürü değildir. -->

Bu doküman doğru destek kaydı açma, öncelik belirleme, ekran görüntüsü ekleme, mevcut kaydı güncelleme ve çözüm sonrası kontrol için örnek kurumsal çalışma biçimini açıklar.

## Destek kaydında bulunması gereken bilgiler

Kullanıcı adı, departman, cihaz etiketi, iletişim bilgisi ve mümkünse çalışma konumu yazılmalıdır.

Sorun kısa fakat açık biçimde açıklanmalı; hangi uygulama, cihaz veya hizmette yaşandığı belirtilmelidir.

Hata mesajı, olay saati, sorunu tekrar oluşturmak için uygulanan adımlar ve yapılan temel kontroller eklenmelidir.

Örnek mock kayıt numarası biçimi DEMO-IT-2026-#### şeklinde düşünülebilir; bu gerçek bir şirket kayıt numarası değildir.

## Ekran görüntüsü veya hata kaydı ekleme

Ekran görüntüsünde hata mesajı okunabilir olmalıdır. Gereksiz kişisel veya hassas bilgiler paylaşılmadan önce gizlenmelidir.

Dosya adı ve hata saati açıklamaya eklenmelidir. Çok büyük video/log dosyaları yüklemek yerine önce gerekli bölüm paylaşılmalıdır.

## Hassas bilgilerin paylaşılması

Parola, MFA doğrulama kodu, erişim anahtarı, API anahtarı veya kişisel gizli bilgi destek kaydına eklenmemelidir.

Bir destek çalışanı bu bilgileri isterse kullanıcı paylaşmamalı ve durumu güvenlik sürecine bildirmelidir.

Sorunun çözümü için gerekiyorsa IT ekibi güvenli ve yetkili yöntemle kullanıcı oturumunu yönlendirmelidir.

## Destek kaydı önceliği

Birden fazla kullanıcıyı etkileyen, üretim veya iş sürekliliğini durduran durumlar yüksek öncelikli olarak bildirilmelidir.

Tek kullanıcıyı etkileyen ve geçici çözümü bulunan sorunlar normal öncelikle kaydedilebilir.

"Acil" veya "kritik" ibaresi yalnız gerçek iş etkisi bulunduğunda kullanılmalıdır; yalnız daha hızlı yanıt almak için kullanılmamalıdır.

## Aynı sorun için tekrar kayıt açma

Aynı sorun için yeni kayıt oluşturmak yerine mevcut kayıt güncellenmelidir.

Yeni hata mesajı, test sonucu, ekran görüntüsü veya ek bilgi mevcut kayda eklenmelidir.

Tekrarlanan kayıtlar aynı olayın farklı kayıtlar arasında bölünmesine ve çözüm sürecinin zorlaşmasına neden olabilir.

## Destek kaydına ek bilgi ekleme

IT ekibinin istediği cihaz adı, hata saati, ekran görüntüsü veya test sonucu mevcut kayıt üzerinden paylaşılmalıdır.

Sorun farklı bir uygulamayı etkilemeye başladıysa veya kapsamı büyüdüyse bu değişiklik açıkça yazılmalıdır.

## Çözüm sonrası kontrol

IT ekibinin bildirdiği çözüm uygulandıktan sonra kullanıcı sorunu tekrar test etmelidir.

Sorun çözüldüyse kayıt kapatma/onay adımı tamamlanabilir. Sorun sürüyorsa "çözülmedi" bilgisiyle birlikte yeni test sonucu aynı kayda eklenmelidir.

## Destek kaydı açmadan önce hızlı kontrol

Kullanıcı yalnız güvenli temel kontrolleri uygulamalıdır: uygulamayı yeniden açma, bağlantıyı kontrol etme, doğru cihaz/uygulamayı seçme gibi.

Yönetici parolası, sürücü değişikliği, registry, güvenlik ayarı veya fiziksel cihaz içi müdahale gerektiren işlemler kullanıcı tarafından yapılmamalıdır.
