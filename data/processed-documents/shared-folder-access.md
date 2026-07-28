# Shared Folder Access

<!--
source_file_name: shared-folder-access.md
source_file_type: md
content_hash: 4258accdc026b345c7cef41f8daab45d4b0c622901058bbc0c7a81535b415050
processed_at: 2026-07-27T16:48:21
-->

# Ortak Klasör ve Dosya Erişimi

Bu doküman ortak klasör erişimi, izin hataları, salt okunur dosyalar, kilitli belgeler ve ağ yolu sorunlarını açıklar.

## Ortak klasör görünmüyor

Kullanıcının kurum ağına veya VPN'e bağlı olduğu doğrulanmalıdır. Ağ sürücüsü bağlantısı yeniden açılmalı ve oturum kapatılıp tekrar giriş yapılmalıdır.

Klasör yeni oluşturulduysa veya yetki yeni verildiyse erişimin yansıması için kısa süre beklenebilir.

Sorun devam ederse klasör yolu, kullanıcı adı ve erişim amacıyla destek kaydı oluşturulmalıdır.

## Ortak klasöre erişim reddedildi

Doğru klasör yolunun kullanıldığı kontrol edilmelidir. Kullanıcının ilgili klasör için yetkili olup olmadığı doğrulanmalıdır.

Yetki talebinde kullanıcı adı, departman, klasör yolu, istenen erişim türü ve iş gerekçesi belirtilmelidir.

Yazma yetkisi gerekmiyorsa yalnızca okuma erişimi talep edilmelidir.

## Dosya salt okunur açılıyor

Kullanıcının klasörde yazma yetkisi olup olmadığı kontrol edilmelidir. Dosyanın başka bir kullanıcı tarafından kilitlenmiş olabileceği değerlendirilmelidir.

Dosya yerel bilgisayara kopyalanıp düzenlenmemeli; kurum içi sürüm ve yetki süreci korunmalıdır.

## Dosya başka kullanıcı tarafından kullanılıyor

Dosyayı açık tutan kullanıcı bilgisi görünüyorsa ilgili kişiden dosyayı kapatması istenmelidir.

Kullanıcı dosyayı kapattığı hâlde kilit devam ediyorsa dosya yolu ve saat bilgisiyle destek kaydı oluşturulmalıdır.

## Ağ yolu bulunamadı

Kurum ağı veya VPN bağlantısı kontrol edilmelidir. Ağ yolu doğru yazılmalı ve eski kısayol yerine güncel klasör yolu kullanılmalıdır.

Aynı klasöre başka kullanıcılar da erişemiyorsa sorun klasör sunucusu veya ağ bağlantısıyla ilgili olabilir.

## Ortak klasör yetki talebi

Talepte kullanıcı adı, sicil numarası, departman, tam klasör yolu ve erişim gerekçesi belirtilmelidir.

Okuma, yazma veya düzenleme yetkisinden hangisinin gerekli olduğu açıkça yazılmalıdır. Gerekli yönetici veya veri sahibi onayı talebe eklenmelidir.
