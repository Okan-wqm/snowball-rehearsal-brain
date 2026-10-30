# Mimari İlkeler III: Sınırlar ve Yapı

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: modül, servis ya da organ sınırı çizilirken; yeni bir ekosistem (pnpm, poetry, cargo, Go modülleri) desteklenirken; dış ya da eski bir modele bağlanırken
Çapa: profildeki graf aracı ve sınır kuralları (`14`); genellik kendi-testi (`21`); kaynaklar `catalog.md` bölüm C

---

Katalog danışmadır (`31`). Sınır kuralları `23`'ün ilk katmanıdır: doğru sınır yanlış bağımlılığı
derleme ya da lint zamanında imkânsız kılar. Dağıtım biçimini (monolit ya da servis) değiştirmek sistemin
işi değildir; sistem kanıt bildirir, sahibi karar verir.

| Kimlik · kanıt | İlke | Ne zaman | Bedel, yanlış uygulama | Bulma | Doğrulama |
|---|---|---|---|---|---|
| `bounded-context` · practice | Bir modelin ve terimlerinin tek ve tutarlı anlam taşıdığı sınır; bağlam haritası ilişkileri açık eder (Evans'ın dokuz deseni: ortaklık, paylaşılan çekirdek, müşteri/tedarikçi, uyumlu, ACL, açık ev sahibi servis, yayımlanmış dil, ayrı yollar, büyük çamur topu) | Aynı terim farklı yerlerde farklı anlamda (cihaz "durumu" alımda ve faturada); büyük model; birden çok ekip; servis sınırı çizimi | Küçük alanlar; erken çizilen sınırı taşımak pahalıdır, servisler arasında daha da pahalı; varlık başına bir servis (CRUD servisleri) | Alana göre adlandırılmış Nx uygulama ve kütüphaneleri; GraphQL alt grafikleri; ayrı şemalar; kenarda çeviri kodu; iki uygulamada aynı adla farklı alanlı tip (bağlamlar farklıysa meşru) | Bağlam haritası sınır kuralı olarak yazılır (Nx etiketleri, dependency-cruiser, import-linter): ihlal sıfır; bağlamlar arası çağrı yalnız yayımlanmış arayüzden |
| `acl` · practice | Yabancı ya da eski bir modelin kendi modeline sızmasını önleyen çeviri katmanı | Üçüncü taraf API, eski sistem, üreticiye özgü cihaz yükü, sahibi olunmayan üst servis, boğan incir göçü | Ayrı dağıtılırsa ek atlama ve gecikme; ek kod; üst servis iyi bir yayımlanmış dil sunuyorsa gereksiz | Alan imzalarının derininde dış DTO ya da SDK tipleri (sızıntı); kenarda eşleyiciler | Lint kuralı: dış tipler yalnız adaptör modüllerinde import edilir; kayıtlı yüklerle çeviri testleri |
| `ports-adapters` · practice | Uygulama çekirdeği dışarıyla yalnız kendi tanımladığı portlardan konuşur; adaptörler portu teknoloji başına uygular (HTTP, GraphQL, DB, NATS, MQTT, test dublörü); çekirdek cihaz ve veritabanı olmadan koşar | Birden çok sürücü ya da sürülen teknoloji; hızlı mantık testleri; değiştirilebilir altyapı | Düz CRUD için kalıp kod; sonsuza dek tek uygulamalı port (spekülatif genellik) | Alan modüllerinde ORM dekoratörleri ya da çerçeve paketleri; `ports` dizinleri; DI belirteçleri | Bağımlılık lint'i: çekirdek altyapı import etmez; çekirdek testleri bellek içi adaptörlerle koşar |
| `dependency-rule` · practice | Kaynak bağımlılıkları yalnız içe, politikaya (varlık, kullanım durumu) doğru gösterir; çerçeveye, DB'ye, arayüze değil. Paket grafiği döngüsüzdür | Uzun ömürlü iş mantığı, çerçeve değişkenliği, test edilebilirlik | Geçiş katmanları ve eşleme töreni; küçük serviste katman patlaması | Import döngüleri (Nx grafiği, madge, cargo crate grafiği); alanın denetleyiciyi import etmesi | Döngü sayısı sıfır; dependency-cruiser, ArchUnit, import-linter ya da Nx etiketleriyle katman kuralları |
| `deploy-shape` · contested | Modüler monolit: sınırları sıkı uygulanan tek dağıtım birimi. Mikroservis: verisinin sahibi, bağımsız dağıtılan servisler | Mikroservis: bağımsız ölçek ve yayın temposu, ekip özerkliği, çok dil (Rust, Python), hata yalıtımı ve ön koşullar (hızlı sağlama, izleme, hızlı dağıtım). Monolit: tek ekip, belirsiz sınırlar, güçlü tutarlılık | "Mikroservis primi": dağıtık sistem karmaşıklığı, nihai tutarlılık, işletim. Dağıtık monolit (paylaşılan DB, birlikte yayın, sohbetli eşzamanlı çağrılar) iki bedeli birden öder; sınırı uygulanmayan monolit çamur topuna döner | Veritabanı ya da alan kütüphanesi paylaşan servisler; birden çok servisi birlikte yayımlamayı zorlayan commit'ler; uzun eşzamanlı çağrı zincirleri | Birlikte yayın oranı; paylaşılan DB tespiti (`31a` `single-writer`); monolitte sınır ihlali sıfır (Shopify'ın Packwerk'i gibi) |
| `registry` · consensus (desen) | Çekirdek bir arayüz tanımlar ve uygulamaları bir kayıttan bulur; yeni yetenek eklemek çekirdeği değil, eklentiyi ve tanımlayıcısını eklemektir. Tanımlayıcı veridir | Aynı yeteneğin büyüyecek N çeşidi: ekosistemler (npm, pnpm, yarn, poetry, pip, uv, cargo, Go modülleri, Maven), CI sistemleri, lint araçları; birçok dosyaya dağılmış `switch (ecosystem)`; M dil × N araç sorununu ortak protokolle M+N'ye indirmek (LSP'nin gerekçesi) | Bir iki çeşit için dolaylılık (YAGNI); eklenti API'si bir sözleşmedir ve kullanıcısı çoğaldıkça gözlenebilir her davranışına bağlanılır (Hyrum yasası); bulunamayan eklenti sessizce geçemez, kapalıya düşer | Çekirdekte `if (pm === 'pnpm')` dalları (shotgun surgery: tek değişiklik için birçok dosyaya dokunmak); çekirdek kodda repo ya da araç adı (repoya özel yama); eklenti kaydı ya da manifesti (Renovate yöneticileri, Nx eklentileri) | Genellik testi: çekirdekte ekosistem ve hedef adı geçmez, adlar yalnız tanımlayıcılarda; kayıtlı her eklentiye aynı vektörlerle tek uyum takımı; eklenti eklemek yalnız kendi dizinine ve kayda dokunur (diff yolu denetimi); bilinmeyen ekosistem açık bir kapsama boşluğu yazar |
| `ownership` · practice | Sistemler onları kuran örgütün iletişim yapısını yansıtır (Conway); sahiplik dosyaları "bu kodun ve verinin sahibi kim" sorusunu açık eder | Sınır çizimi; sahipsiz kod; bir bulguyu sahibine yönlendirmek (Y3 durumları) | Sahiplik dosyaları bayatlar; Conway bir gözlemdir, tasarım kuralı değil | CODEOWNERS, Nx proje etiketleri, sahibi olmayan yollar | Yolların sahip kapsaması; bağlam sınırlarının sahiplerle örtüşmesi |

**Yeni ekosistem kuralı.** Yeni bir ekosistem (pnpm, poetry, cargo, Go modülleri) repoya özgü yama olarak
değil, bir tanımlayıcı (veri: manifest ve kilit dosyası desenleri, komutlar) ve bir adaptör olarak gelir,
mevcutların geçtiği uyum vektörlerini geçer ve çekirdek dosyaya dokunmaz. Bu, `14`'ün "profil bir veri
dosyasıdır" kuralının ve `21`'in genellik testinin aynısıdır. İkinci gerçek çeşit gelene kadar küçük açık
bir dal daha sadedir (`31e` `yagni`); ama çekirdekte hedef ya da repo adı hiçbir zaman geçmez.

**İlişkiler.** Kayıt, port ve adaptörlere keşif eklenmiş hâlidir; temiz mimari altıgen mimarinin
çeşididir; bağlam sınırları kazara tekrarı meşrulaştırır (`31b`); çok karmaşık bir saga yanlış sınırın
işareti olabilir (`31d`).

**Kaynaklar** (`catalog.md`): `bounded-context` [FOWLER-BC] [DDD-REF] [DDD-CREW]; `acl` [AZ-ACL] [DDD-REF];
`ports-adapters` [COCKBURN]; `dependency-rule` [CLEAN-ARCH] [DEPCRUISER] [ARCHUNIT] [IMPORT-LINTER]
[NX-BOUNDARIES]; `deploy-shape` [FOWLER-MONOFIRST] [TILKOV] [FOWLER-PREMIUM] [FOWLER-PREREQ] [SHOPIFY]
[SHOPIFY-PACKWERK]; `registry` [POEAA-PLUGIN] [POEAA-SEPIF] [LSP] [VSCODE-LSP] [RENOVATE] [NX-PLUGINS]
[HYRUM]; `ownership` [FOWLER-CONWAY].
