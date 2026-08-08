# Ortak Klasör ve Dosya Erişimi

<!-- Bu doküman staj projesi için hazırlanmış sentetik/mock IT prosedürüdür; gerçek şirket prosedürü değildir. -->

Bu doküman ortak klasör görünürlüğü, erişim reddi, dosya kilidi, salt okunur açılma ve ağ yolu sorunlarında izlenecek kontrollü adımları açıklar.

## Ortak klasör görünmüyor

Kullanıcının ağ veya VPN bağlantısının aktif olduğu kontrol edilmelidir. Ortak klasörün bilinen ağ yolu doğru yazılmalıdır.

Aynı klasör başka yetkili kullanıcıda görünüyorsa sorun kullanıcının yetkisi veya eşleştirmesiyle ilişkili olabilir.

Klasör yolu, kullanıcı adı ve ihtiyaç duyulan erişim türüyle destek kaydı oluşturulmalıdır.

## Ortak klasöre erişim reddedildi

Kullanıcının ilgili klasör için okuma/yazma yetkisi bulunup bulunmadığı kontrol edilmelidir.

Yetki talebinde kullanıcı adı, departman, tam klasör yolu, istenen erişim türü ve iş gerekçesi belirtilmelidir. Gerekli yönetici/veri sahibi onayı talebe eklenmelidir.

Kullanıcı başka bir kullanıcının hesabını kullanarak veya klasör izinlerini kendisi değiştirerek erişim sağlamaya çalışmamalıdır.

## Dosya başka kullanıcı tarafından kullanılıyor

Dosyanın gerçekten başka kullanıcı tarafından açık olup olmadığı ekip içinde kontrol edilmelidir.

Dosyayı kullanan kişi işlemini tamamladıktan sonra kapatmalı ve dosya tekrar denenmelidir. Kullanıcı kilit dosyalarını veya geçici dosyaları manuel silmemelidir.

Kilit uzun süre kalkmıyorsa dosya yolu ve yaklaşık saat bilgisiyle destek kaydı açılmalıdır.

## Dosya salt okunur açılıyor

Kullanıcının klasörde yazma yetkisi olup olmadığı ve dosyanın başka kullanıcı tarafından düzenlenip düzenlenmediği kontrol edilmelidir.

Dosya yalnızca belirli kullanıcıda salt okunur açılıyorsa kullanıcı yetkisi; herkes için aynıysa dosyanın/klasörün genel durumu incelenmelidir.

## Ağ yolu bulunamadı

Bilgisayarın kurumsal ağa veya gerekiyorsa VPN'e bağlı olduğu doğrulanmalıdır. Ağ yolu yazım hatası olmadan tekrar denenmelidir.

Aynı yol başka kullanıcıda da açılmıyorsa ortak servis veya ağ sorunu olabilir. Kullanıcı DNS, host dosyası veya ağ güvenliği ayarlarını değiştirmemelidir.

## Yeni klasör yetkisi talebi

Talepte kullanıcı adı, departman, klasör yolu, okuma/yazma ihtiyacı, iş gerekçesi ve gerekiyorsa süre bilgisi verilmelidir.

"Geniş erişim" yerine yalnız iş için gerekli en dar yetki talep edilmelidir.

## Dosya erişim sorunu için destek kaydına eklenecek bilgiler

Tam klasör/dosya yolu, kullanıcı adı, bağlantı durumu (ofis/VPN), hata mesajı ve erişimin daha önce çalışıp çalışmadığı belirtilmelidir.
