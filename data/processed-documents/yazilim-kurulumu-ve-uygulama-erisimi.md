# Yazılım Kurulumu Ve Uygulama Erişimi

<!--
source_file_name: yazılım-kurulumu-ve-uygulama-erişimi.md
source_file_type: md
content_hash: 24010e63d5b680631739c741d4a71a79e41a986e856a31ab11791ce307600408
processed_at: 2026-08-08T11:41:16
-->

# Yazılım Kurulumu ve Uygulama Erişimi

<!-- Bu doküman staj projesi için hazırlanmış sentetik/mock IT prosedürüdür; gerçek şirket prosedürü değildir. -->

Bu doküman yeni yazılım kurulumu, uygulama açılmaması, lisans, güncelleme, yönetici yetkisi ve örnek kurumsal portal erişimi için izlenecek mock süreci açıklar.

## Yeni yazılım kurulumu talebi

Talepte yazılımın adı, sürümü, kullanım amacı, kullanılacağı bilgisayarın etiketi ve talebi açan kullanıcının departmanı belirtilmelidir.

Yazılım lisans gerektiriyorsa lisans ihtiyacı ve gerekli yönetici/onay bilgisi eklenmelidir. Kullanıcı kurum onayı olmadan internetten yazılım indirip kurmamalıdır.

Yazılımın iş için neden gerekli olduğu açık değilse talep değerlendirmeye alınmadan önce ek bilgi istenebilir.

## Uygulama açılmıyor

Uygulama tamamen kapatılıp yeniden açılmalı ve bilgisayar yeniden başlatılarak tekrar denenmelidir.

Hata mesajı varsa ekran görüntüsü alınmalı; uygulama adı, sürüm, yapılan işlem ve cihaz etiketi destek kaydına eklenmelidir.

Uygulama dosyalarını silmek, registry değiştirmek veya yönetici yetkisiyle yeniden kurmak kullanıcı tarafından yapılmamalıdır.

## Uygulama lisans hatası veriyor

Bilgisayarın kurum ağına veya gerekiyorsa VPN'e bağlı olduğu doğrulanmalıdır. Kullanıcı hesabının ilgili lisans grubunda olup olmadığı IT tarafından kontrol edilmelidir.

Lisans süresi dolmuş veya eşzamanlı kullanım sınırı aşılmışsa uygulama adı, kullanıcı ve iş etkisiyle lisans destek kaydı oluşturulmalıdır.

## Uygulama güncelleme istiyor

Kurum tarafından yönetilen uygulamalarda kullanıcı kendi başına yönetici yetkisiyle güncelleme yapmamalıdır.

Uygulama adı, mevcut sürüm, istenen yeni sürüm ve görülen uyarı destek kaydına eklenmelidir.

Güncelleme kritik iş sırasında çıktıysa kullanıcı mevcut çalışmasını kaydedip IT ile uygun zaman planlamalıdır.

## Yönetici parolası isteniyor

Kurulum veya ayar değişikliği sırasında yönetici parolası isteniyorsa işlem durdurulmalıdır.

Kullanıcıya kalıcı yönetici parolası verilmez. Yazılım adı, işlem amacı ve bilgisayar etiketiyle IT destek talebi oluşturulmalıdır.

Parola veya yönetici hesabı bilgisi e-posta/mesaj üzerinden paylaşılmamalıdır.

## Uygulama yetki talebi

Talepte uygulama adı, istenen rol/yetki, kullanım gerekçesi, kullanıcı ve departman bilgileri belirtilmelidir.

Gerekli yönetici veya uygulama sahibi onayı eklenmelidir. Gereğinden geniş yetki talep edilmemelidir.

## Bakım Takip Portalı açılmıyor

Bu başlık demo için kullanılan sentetik bir kurumsal portal örneğidir.

Kurum ağına veya VPN'e bağlı olunduğu doğrulanmalı, portal adresi doğru girilmeli ve farklı tarayıcıda denenmelidir.

Giriş ekranı açılıyor ancak "yetkiniz yok" mesajı veriyorsa bağlantı sorunu yerine kullanıcı rolü/yetkisi için uygulama erişim talebi oluşturulmalıdır.

Portal tamamen erişilemiyorsa hata saati ve ekran görüntüsüyle destek kaydı açılmalıdır.

## Kurumsal Yazılım Merkezi üzerinden kurulum

Kurum tarafından onaylanmış bir yazılım self-service katalogda bulunuyorsa kullanıcı yalnız kendi yetkisi dahilindeki kurulumu başlatabilir.

Katalogda bulunmayan veya yönetici yetkisi isteyen yazılımlar için IT talebi açılmalıdır.
