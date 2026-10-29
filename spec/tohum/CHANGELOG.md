# Değişiklik Günlüğü — Tohum

Tarih: 2026-10-28 · Sürüm: 2.2
Okunma: bir sayfanın geçmişi aranırken
Çapa: git geçmişi ve zincirdeki spec hash satırları

- 2.2 (2026-10-28): üçüncü inceleme (altı inceleyici, iki tur, birbirlerinin bulgularını kanıtla
  çapraz denetleyerek) sonrası. Çekme modeli: oyuncu yalnız kendi reposuna yazar ve aday yayımlar;
  hakem reposu özel ve yalnız operatörün yazdığı yerdir; hedefe yalnız yazar App'i yazar; GitHub
  Free'de özel repoda ruleset olmadığı için hakem kodu aşama çıkışında operatör aktarımıyla değişir
  ve bu insan dokunuşu sayılır. Beş iş deseni (çek, getir, koş, çağır, yaz); kod yürüten işin ağı
  ve sırrı yoktur; kırmızı kontrol; kök hash Rekor'a. Önyükleme hakemi ve tohum vektörleri tohumla
  gelir; Aşama 0 hakemin tamamını kurar, Aşama 1 yalnız oyuncu organlarını. Yazma ve eğitim modu.
  Ajan dispatch sözleşmesi ve kanarya testi. İstatistik: deterministik sınıflarda kural sayımı,
  gerçel etkin başarı, tam testler, havuz başına bakış bütçesi, ileriye dönük held-out, `human_fix`
  katman kapısı. Yeteneğe anahtarlı zorunlu çıkış satırları. Kullanıcı kararları K1–K9: bilgi
  bağlama bağlı, ithal bilgi hipotez, alan bilgisi yerel, okuyarak öğrenme ve diğer yetenekler
  organ değil sinyal, kopyalamak yerine sentez, öğrenmenin ölçüsü hata, doküman koda göre bayat
  olabilir, snowball hedef reponun dokümanını da yazar. Aşama 2 ve 3'ün neden yazılmadığı açıklandı.
  Ardından yalnız tohumla çalışan tek oturumluk bir Kurucu denemesinin bulduğu boşluklar kapatıldı:
  Kurucu defteri ilk oturumdan yazılır; spec isteği ile kod isteği ayrıldı; önyükleme hakeminin
  test bildirimi, ret artefaktı ve vektör arayüzü tanımlandı; aktarım operatör dosyalarını hariç
  tutar; hash'lenen artefaktta kayan nokta yoktur; aşama tasarım sabitleri politika anahtarı oldu.
  Önyükleme hakemi yazıldı (`seed/bootstrap/`): altı işli iş akışı, standart kütüphaneyle paket,
  hash'e sabitlenmiş model çağrısı ve Sigstore gereksinimleri, makine okunur vektörler, testler ve
  her kasıtlı bozmayı yakalayan bir mutasyon kontrolü. Spec koda göre güncellendi: üç tür
  push (spec, kod, çıkış isteği), imzalı durum artefaktı, rakip çağrısının yapısal yalıtımı,
  vakada `tool` alanı, kurulumdaki dosya adları.
  Sonra, operatörün dört isteğiyle: (1) yalnız açık ve ticari kullanıma uygun lisans: anayasal
  `license_allowlist` ve `license_exceptions` (`18a`), lisans tekerleğin kendisinden okunur ve
  lisansı söyleyen her yer izinli olmalıdır (`24`); örüntü önerisi kod kopyalamaz (`21a`);
  önyükleme hakemi kurucunun ve kendi tekerleklerini kurmadan önce denetler. (2–3) Öğrenmenin,
  öğrenileni kullanmanın ve kendini geliştirmenin testi: ders provası, geri alma ve bağlam
  provası (`22a`), genesis provası (`12a`); cevap anahtarı koşudan önce hash'le bağlanır; yeni
  zorunlu çıkış satırları (`18`); önyükleme hakeminin ret hafızası ve `not_learning`. (4) Yolda
  görülen eksikler: aşamalar getirdiği yetenekleri beyan etmiyordu, `spec.lint` zorunlu satırları
  mekanik denetleyemezdi; şimdi özet yetenekleri listeler, satırlar `#kimlik` taşır ve Aşama 1
  ile 4'ün eksik satırları eklendi. 15 dakikalık yoklama ayda ~2.900 Actions dakikası harcardı;
  yoklama saatliktir, boşta hiçbir şey kurmaz ve dakika hesabı `25`'tedir. Politika başlangıç
  değerleri `18a` (anayasal) ve `18b` (performans) olarak bölündü. Ardından provanın kendisi
  sınandı (`29c`, `seed/drill/`): referans yargıç, bir öğrenen ve 14 kusurlu simüle beyin; 500'er
  provada öğrenen hiç FAIL almadı (498 PASS), kusurluların hiçbiri PASS almadı; yargıçtaki 19 kasıtlı
  bozmanın hepsi yakalandı. Bu ölçüm üç hatayı düzeltti: plasebo %90'da on provada bir öğreneni
  haksız düşürüyordu (artık %99); k = 12 öğreneni %4 düşürüyordu (artık 20); ilgisiz bir kırılma
  çelişki sayılıyordu (artık örneğin kendi tuzak testi). Kredi yöntemi Newcombe'a sabitlendi.
- 2.1 (2026-10-28): ikinci beş incelemeden (istekler ve kararlar, bağlantı ve veri akışı, mantık,
  uçtan uca simülasyon, kırmızı takım) doğrulanan bulgular. Hakem reposu: oyuncu kendi hakemini
  yazamaz; kapı, kullanıcı hesabında da çalışan, yalnız hakem App'inin raporlayabildiği zorunlu
  durum kontrolüdür. Kurulum iki bölüm. Tohum koltukları, sözlük ve okuyucu tablosu, dondurma,
  araç imzaları sayfaları. Held-out hesaplanamaz havuzdan; bakış bütçesi rotasyonla sıfırlanmaz;
  Clopper–Pearson. Çıkış tabanları anayasal, prosedür yalnız sıkılaştırır. Keşif tüm ihlaller ve
  mandal; nöbetçi ve birinci ebeveyn bisect. Model kuralı iki modelle uygulanabilir hâle geldi.
  Oracle: property'den test, hunk kapsaması, kapı yeniden koşturur. Dersler: ilk okuyucu
  düzeltici, test-yazıcı okumaz, kredi rastgele saklamayla. Yasaklı ifade listesi tanımlandı.
- 2.0 (2026-10-28): beş bağımsız incelemeden (tutarlılık, istekler, uygulanabilirlik, kırmızı
  takım, ölçüm ekonomisi) sonra yeniden yazım. Yetki üç yere ayrıldı (beyin reposu, hedef repo,
  mühürlü depo) çünkü tek repoda dosya bazlı izin yok; held-out mühürlü depoya taşındı; cevap
  anahtarına `provenance` geldi; K0 oracle'ı "araç yeşil" yerine "base SHA'ya göre fark" oldu;
  SHADOW→ACTIVE kilidi çözüldü; istatistik sayfası ve UNMEASURABLE verdict'i; dinamik eşik
  prosedürü ve `policy.json`; oracle sertleştirme ve diff-guard; ikili ayrık model kuralı ve
  donmuş koltuklar; Gözcü deterministik; itibar Beta alt sınırı ve kök neden kredisi; ablasyon
  bileşik skor; zincir için CI attestation; çalışma modeli, kurulum günü ve şema sayfaları;
  hafıza modeli, kas sinyalleri, dersler, metrikler, çok repo, yama değil mimari çözüm sayfaları;
  tohumdan hedef repoya özgü adlar çıkarıldı; sistem çıktıları İngilizce ve bulgular iki formatta.
  Sonra rakip API anahtarsız çalışır oldu (iç kullanım; ticari kullanımda anahtara geçilir): `claude` CLI
  oturumuyla, hakemin kendi MCP sunucusuyla ve pinli npm kilidiyle; model SDK'sı ve fiyat tablosu kalktı,
  her koşu izolasyonunu CLI'nin `init` olayından kanıtlar (`29b`).
- 1.0 (2026-10-28): tek dosya özellik başına sayfalara bölündü.
- 0.1–0.11 (2026-10-28): tek dosya taslak dönemi; geçmişi zincirde ve git'te.
