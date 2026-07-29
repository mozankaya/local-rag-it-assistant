# Vpn Remote Access

<!--
source_file_name: vpn-remote-access.md
source_file_type: md
content_hash: 42f2b1250f7ae99144d0e31940ecce8600fc5869607691e1fb53d4c2553b4d7c
processed_at: 2026-07-29T16:54:55
-->

# VPN ve Uzaktan Erişim

Bu doküman kurumsal VPN bağlantısı, iç kaynaklara erişim, MFA doğrulaması ve uzak masaüstü sorunları için temel adımları açıklar.

## VPN bağlantısı kurulamıyor

Bilgisayarın internet bağlantısı kontrol edilmelidir. VPN istemcisinde doğru bağlantı profili seçilmeli ve kullanıcı adı ile güncel şifre kullanılmalıdır.

Şifre yakın zamanda değiştirildiyse VPN istemcisinde kayıtlı eski bilgiler temizlenmeli ve yeni şifreyle tekrar giriş yapılmalıdır.

Hata kodu görülüyorsa ekran görüntüsü alınmalı ve hata koduyla birlikte IT destek kaydı oluşturulmalıdır.

## VPN bağlanıyor ancak iç sistemler açılmıyor

VPN bağlantısının aktif göründüğü doğrulanmalıdır. İç sistem adresi yeniden açılmalı ve tarayıcı kapatılıp tekrar denenmelidir.

Kurum içi dosya paylaşımı veya uygulama yalnızca belirli ağ yetkileriyle çalışıyorsa kullanıcının erişim yetkisi kontrol edilmelidir.

Sorun yalnızca tek bir sistemde yaşanıyorsa sistem adı ve erişim adresi belirtilerek destek kaydı oluşturulmalıdır.

## VPN sırasında MFA bildirimi gelmiyor

Telefonun internet bağlantısı kontrol edilmelidir. Doğrulama uygulaması açılarak bekleyen istek veya manuel doğrulama kodu kontrol edilmelidir.

Telefon değiştirildiyse veya doğrulama uygulaması yeniden kurulduysa MFA kaydının güncellenmesi gerekebilir.

Bildirim gelmiyorsa kullanıcı adı, telefon değişikliği bilgisi ve deneme saatiyle IT destek kaydı oluşturulmalıdır.

## VPN bağlantısı sık sık kopuyor

Kablosuz ağ sinyalinin kararlı olduğu kontrol edilmelidir. Mümkünse kablolu bağlantı veya farklı bir güvenilir ağ üzerinden test yapılmalıdır.

Bilgisayarın uyku moduna geçmesi VPN bağlantısını kesebilir. Uzun işlem sırasında güç ve uyku ayarları kontrol edilmelidir.

Kopma tekrar ediyorsa yaklaşık saat, kullanılan ağ türü ve varsa hata mesajı destek kaydına eklenmelidir.

## Uzak masaüstü bağlantısı açılamıyor

Önce VPN bağlantısının aktif olduğu doğrulanmalıdır. Uzak bilgisayar adı veya bağlantı adresi doğru girilmelidir.

Hedef bilgisayar kapalıysa veya ağdan ayrılmışsa bağlantı kurulamaz. Hedef cihazın açık olduğu ilgili kişi tarafından doğrulanmalıdır.

Erişim reddediliyorsa kullanıcı yetkisi ve hedef bilgisayar adıyla IT destek kaydı oluşturulmalıdır.

## VPN istemcisi açılmıyor

VPN istemcisi tamamen kapatılıp yeniden açılmalıdır. Bilgisayar yeniden başlatılarak tekrar denenmelidir.

Uygulama güncellemesi veya yeniden kurulumu gerekiyorsa kullanıcı kendi başına yönetici yetkisiyle kurulum yapmamalı, IT destek kaydı oluşturmalıdır.
