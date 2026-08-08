# VPN ve Uzaktan Erişim

<!-- Bu doküman staj projesi için hazırlanmış sentetik/mock IT prosedürüdür; gerçek şirket prosedürü değildir. -->

Bu doküman uzaktan çalışma sırasında VPN istemcisi, MFA doğrulaması, iç sistem erişimi ve uzak masaüstü bağlantısı için uygulanabilecek temel ve koşullu kontrolleri açıklar.

## VPN bağlantısı kurulamıyor

Önce internet erişiminin çalıştığı doğrulanmalıdır. VPN istemcisinde tanımlı kurumsal profil seçilmeli ve kullanıcı güncel parolasıyla giriş yapmalıdır.

Parola yakın zamanda değiştirildiyse istemcide kayıtlı eski bilgiler yeni bağlantıyı engelleyebilir. Uygulama kapatılıp yeniden açılmalı ve güncel kimlik bilgileriyle tekrar denenmelidir.

Hata kodu görülüyorsa ekran görüntüsü, hata kodu, deneme saati ve bağlantı yapılan ağ türü destek kaydına eklenmelidir.

## VPN istemcisi açılmıyor

VPN uygulaması görev çubuğunda veya arka planda açık kalmış olabilir. Uygulama tamamen kapatılıp yeniden açılmalı, ardından bilgisayar yeniden başlatılarak tekrar denenmelidir.

Uygulama yine açılmıyorsa kullanıcı kendi başına yönetici yetkisiyle kurulum, kaldırma veya sürücü değişikliği yapmamalıdır.

Uygulama adı/sürümü, cihaz etiketi ve görülen hata mesajıyla IT destek kaydı oluşturulmalıdır.

## VPN bağlanıyor ancak iç sistemler açılmıyor

VPN bağlantısının gerçekten aktif olduğu doğrulanmalı ve iç sistem adresi yeni tarayıcı oturumunda tekrar açılmalıdır.

Sorun yalnız tek bir iç uygulamada görülüyorsa uygulama adı, erişim adresi ve kullanıcı rolü not edilmelidir. Birden fazla iç sistem aynı anda açılmıyorsa VPN oturumu kapatılıp yeniden kurulabilir.

Kullanıcının ilgili sisteme yetkisi yoksa VPN bağlantısını yeniden kurmak yetki sorununu çözmez; uygulama erişim talebi açılmalıdır.

## VPN sırasında MFA bildirimi gelmiyor

Telefonun internet bağlantısı ve doğrulama uygulamasının çalıştığı kontrol edilmelidir. Uygulama açıldığında bekleyen doğrulama isteği olup olmadığı incelenebilir.

Telefon değiştirildiyse veya doğrulama uygulaması yeniden kurulduysa MFA kaydının tekrar eşleştirilmesi gerekebilir.

Kullanıcı parolasını veya MFA kodunu destek personeli dahil hiç kimseyle paylaşmamalıdır. Bildirim gelmiyorsa kullanıcı adı, telefon değişikliği durumu ve deneme saatiyle destek kaydı açılmalıdır.

## VPN bağlantısı sık sık kopuyor

Kablosuz ağın kararlı olduğu kontrol edilmelidir. Mümkünse kablolu bağlantı veya başka güvenilir bir ağ üzerinden karşılaştırmalı test yapılmalıdır.

Bilgisayarın uyku moduna geçmesi VPN oturumunu kesebilir. Uzun çalışan işlemlerde güç ve uyku ayarları kontrol edilmelidir.

Kopmalar belirli saatlerde tekrar ediyorsa yaklaşık saat aralığı, kullanılan ağ türü ve varsa hata mesajı kayda eklenmelidir.

## Uzak masaüstü bağlantısı açılamıyor

Önce VPN bağlantısının aktif olduğu doğrulanmalıdır. Hedef bilgisayarın açık ve kurumsal ağa bağlı olduğu ilgili kullanıcı veya ekip tarafından kontrol edilmelidir.

Hedef bilgisayar adı doğru girilmelidir. Erişim reddediliyorsa kullanıcı uzak masaüstü yetkisinin bulunup bulunmadığını IT desteğiyle doğrulamalıdır.

Kullanıcı güvenlik duvarı veya uzak masaüstü servis ayarlarını kendi başına değiştirmemelidir.

## Uzaktan erişim destek kaydına eklenecek bilgiler

Kullanıcı adı, cihaz etiketi, VPN istemcisi sürümü, bağlantı yapılan ağ türü, hata kodu, yaklaşık olay saati ve etkilenilen iç sistem adı eklenmelidir.

Parola, MFA kodu ve diğer gizli bilgiler kayda yazılmamalıdır.
