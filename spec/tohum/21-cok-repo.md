# Çok Repo: Bağlanma Modu, Ne Taşınır, Ne Taşınmaz

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: beyin yeni bir repoya bağlanırken
Çapa: genellik kendi-testi; her repo için ayrı `<state_root>`; profildeki `mode`

---

Beyin repo bilmez, repo öğrenir. Repo Rust ise kaslar Rust alanında, TypeScript ise TypeScript
alanında büyür. Aynı beyin farklı repolarda farklı organlar taşır. Bilginin bağlama nasıl bağlı
olduğu ve repolar arasında nasıl terfi ettiği `21a`'dadır.

## Repo tanıma, keşfin ilk adımıdır

Bağlanınca araç zinciri profile yazılır: diller ve oranları, derleyici, test koşucu, lint ve
biçimleyici, "etkilenenleri test et" komutu, CI sistemi, paket yöneticileri, güvenlik yolları.
**Beyin önerir, hakem türetir** (`14`): `brain/state`'e giren profil hakemin kendi türetmesidir.
Tohum sayfalarındaki her kural komut adı yerine profil alanına bakar; tohumda hedef repoya ait
hiçbir yol, araç ya da karar belgesi adı geçmez ve genellik testi bunu tohum için de denetler.

Derleme grafiğinin ya da test hedeflerinin dışında kalan her dizin bir kapsama boşluğudur. Beyin
bunu sessizce geçmez: kapsamaya "görülmüyor" yazar ve bu bir kas büyütme sinyalidir.

## Hata sınıfları alan bağımsız, adapter'lar alan bağımlı

Lint, tip, ölü kod, sözleşme paritesi, mantık, güvenlik ve doküman sınıfları her dilde vardır. Her
sınıfın adapter'ı o dilin aracını sarar; beyin aracı bilmez, profilden okur ve sarıcıyı o araç
için üretir. Alan uzmanı ajanlar da profilden doğar: tohumda belirli bir çerçevenin adını taşıyan
uzman yoktur, "profildeki baskın çerçeve için uzman" vardır ve o uzman genesis'ten geçer.

## Bağlanma modu

| Mod | Ne zaman | Ne yapılır | Durum nerede |
|---|---|---|---|
| `write` | Hedef `main`, yazar App'inin karşılayamayacağı bir kural taşıyorsa (açık repo ya da Pro): yazar App'i bypass değil, güncelleme onaylı inceleme ister ya da yalnız operatör rolüne açıktır; `drift.check` her döngü doğrular | Tam döngü: keşif, düzeltme, `brain/integration`'a merge | Hedefte `brain/state` |
| `training` | Diğer her hedef; üçüncü kişi repoları yalnız bu modda | PR ve merge yok: okuma, sandbox deneyi, geçmiş düzeltmelerden vaka çıkarma, koşul öğrenme | Operatörün özel eğitim deposunda, hedef başına bir dal; yazarı yazar App'i, bütünlüğü Rekor kökü |

Üçüncü kişi repoları kimliksiz klonla okunur; kodları yalnız `koş` işinin ağsız konteynerinde
koşar; vakaları yalnız yereldir ve hiçbir çıkış kapısına girmez. Eğitim deposu ilk eğitim hedefi
bağlanınca açılır. Kurulumun ikinci bölümü (`25a`) her yeni hedef için yeniden yapılır.

## Taşınma kuralı

| Taşınır | Taşınmaz |
|---|---|
| Beyin ve hakem kodu | Vakalar, held-out, mühür |
| Organ tanımları; yeni repoda DRAFT'tan başlar, kanıtını orada toplar | Profil ve alan sözlüğü |
| `cause` ve `miss_reason` kategorileri | İtibar ve `derived_from` zinciri: repo sınırında kesilir |
| Ders ve bilgi satırlarının **yalnız tipli alanları** (`cause`, `scope`, `conditions`, bağlam sayıları) | Serbest metin (`claim` dahil), harita, kapsama, defterler |

Taşıma yalnız aynı sahibin repoları arasında, hakemin kanıtlı defterlerden hesapladığı sayılarla
yapılır; oyuncunun beyan ettiği sayım taşınmaz. Taşınan her prompt, kaynak reponun yol, sembol ve
ad listesine ve `domain_lexicon`'una karşı taranır; eşleşme varsa taşınmaz. Serbest metin taşınmaz,
çünkü bir repodaki metin her düzelticinin promptuna giden bir enjeksiyon yolu olurdu. Bir repoda
doğan tarif öbür repoda ancak ablasyonla gerekliliğini kanıtlarsa kalır.

## Kullanıcının dosyaları kullanıcının sisteminde

Repoya özgü her şey kullanıcının reposunda, eğitim deposunda ya da mühürlü deposunda durur, kök
kayıtları dahil. Beynin tarafında kod ve `21a`'daki kurallarla terfi etmiş, tanımlayıcılardan
temizlenmiş tipli soyutlamalar vardır. Beyin kaldırıldığında repo bütün hafızasıyla kullanıcının
elinde kalır; başka bir beyin aynı dosyalardan devam edebilir.
