# Şifre Ve Hesap Erişimi

<!--
source_file_name: şifre-ve-hesap-erişimi.md
source_file_type: md
content_hash: fc27c89d088c83bd4eb8c4e35419c284272d7d5718ca470a296280e3d88f7e17
processed_at: 2026-08-08T11:41:16
-->

# Şifre ve Hesap Erişimi

<!-- Bu doküman staj projesi için hazırlanmış sentetik/mock IT prosedürüdür; gerçek şirket prosedürü değildir. -->

Bu doküman parola sıfırlama, hesap kilidi, oturum açma, pasif hesap ve eski kimlik bilgilerinin temizlenmesi gibi kullanıcı hesabı sorunlarında izlenecek kontrollü adımları açıklar.

## Şifre unutuldu

Kullanıcı önce kurum tarafından sağlanan parola sıfırlama ekranını kullanmalıdır. Yeni parola oluşturulurken kurumun parola kurallarına uygun, önceki paroladan farklı ve yalnız kullanıcı tarafından bilinen bir parola seçilmelidir.

Şifre sıfırlama bağlantısı açılmıyorsa adres farklı bir tarayıcıda veya gizli pencerede denenebilir. İşlem tamamlandıktan sonra Outlook, VPN ve diğer kurumsal uygulamalarda yeni parolayla yeniden oturum açılmalıdır.

Sıfırlama ekranı kullanıcıyı tanımıyorsa, bağlantı hata veriyorsa veya işlem tamamlanamıyorsa kullanıcı adı, görülen hata mesajı ve deneme saatiyle IT destek kaydı açılmalıdır.

## Hesap kilitlendi

Art arda hatalı parola girilmesi hesabın geçici olarak kilitlenmesine neden olabilir. Kullanıcı tekrar tekrar parola denemek yerine kısa bir süre beklemeli ve doğru parolayla yeniden giriş yapmalıdır.

Kilit açıldıktan sonra sorun tekrar ediyorsa telefonda, Outlook'ta, VPN istemcisinde veya başka bir cihazda kayıtlı eski parola hesabı yeniden kilitliyor olabilir. Eski oturumlar yeni parolayla güncellenmelidir.

Kilit devam ederse destek kaydında kullanıcı adı, kilidin görüldüğü uygulama ve yaklaşık olay saati belirtilmelidir.

## Hesaba giriş yapılamıyor

Kullanıcı adı ve parolanın doğru yazıldığı, Caps Lock durumunun uygun olduğu ve klavye dilinin değişmediği kontrol edilmelidir.

Sorun yalnızca tek bir uygulamada görülüyorsa kullanıcı aynı hesapla başka bir kurumsal uygulamada oturum açmayı deneyebilir. Başka uygulamalarda giriş yapılabiliyorsa sorun genel hesap erişiminden çok ilgili uygulamaya özgü olabilir.

Ekranda "yetkiniz yok", "hesap devre dışı" veya benzeri bir mesaj varsa parola tekrar tekrar denenmemeli; hata mesajı destek kaydına eklenmelidir.

## Şifre değişti ancak uygulama eski şifreyi istiyor

Outlook, VPN, mobil e-posta ve ağ sürücüsü bağlantıları eski kimlik bilgilerini saklayabilir. Parola değişikliğinden sonra bu uygulamalar kapatılıp yeniden açılmalı ve yeni parola girilmelidir.

Telefon veya başka bilgisayarda eski parola kayıtlıysa hesabın tekrar kilitlenmesine neden olabilir. Aynı hesabın kullanıldığı cihazlar gözden geçirilmelidir.

Windows veya uygulama tarafında kayıtlı kimlik bilgileri kullanıcı tarafından silinemiyorsa IT desteğine uygulama adı ve cihaz etiketiyle başvurulmalıdır.

## Outlook sürekli parola istiyor

Parola yakın zamanda değiştirildiyse Outlook tamamen kapatılıp yeniden açılmalı ve yeni parola girilmelidir. VPN üzerinden çalışılıyorsa VPN bağlantısının aktif olduğu doğrulanmalıdır.

Outlook web erişimi çalışıyor ancak masaüstü Outlook sürekli parola istiyorsa sorun profil veya kayıtlı kimlik bilgisi kaynaklı olabilir. Kullanıcı profil silme ya da kayıt defteri değişikliği yapmamalıdır.

Sorun devam ederse Outlook sürümü, cihaz etiketi ve ekrandaki uyarıyla destek kaydı açılmalıdır.

## Hesap pasif görünüyor

Kullanıcı doğru parolayı girmesine rağmen hesabın pasif, devre dışı veya erişime kapalı olduğu mesajını görüyorsa parola sıfırlamak tek başına sorunu çözmeyebilir.

Kullanıcı adı ve ilgili hata mesajı IT destek ekibine iletilmelidir. Hesabın yeniden etkinleştirilmesi yalnız yetkili kullanıcı yönetimi süreci üzerinden yapılmalıdır.

Kullanıcı kendi hesabının durumunu değiştirmeye veya başka bir hesap kullanarak yetki aşmaya çalışmamalıdır.

## Hesap sorunu için destek kaydına eklenecek bilgiler

Destek kaydına kullanıcı adı, cihaz etiketi, sorun yaşanan uygulama, hata mesajı ve yaklaşık olay saati eklenmelidir.

Parola, MFA doğrulama kodu, erişim anahtarı veya başka bir gizli bilgi hiçbir zaman destek kaydına yazılmamalıdır.
