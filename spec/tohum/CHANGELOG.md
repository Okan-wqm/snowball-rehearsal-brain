# Değişiklik Günlüğü — Tohum

Tarih: 2026-10-29 · Sürüm: 2.2
Okunma: bir sayfanın geçmişi aranırken
Çapa: git geçmişi ve zincirdeki spec hash satırları

- 2.2 (2026-10-29, daraltma): `docs/asama-0-daraltma.md` (K1–K5 onaylı; hedefin kendi ajan sistemi kapsam dışı; sistem %100 LLM'lerce kurulur ve işletilir) tohuma işlendi. Önyükleme hakemi Aşama 0'dan sonra da beyin reposunun itme yargıcıdır; hakem kodu aşama ya da parti çıkışında aktarılır, parti çıkışı (A) → aktarım → (B)'nin dar hâlidir (`01a`, `02`, `00`, `09a`). Kilit (A)'da (aşama, donmuş spec hash) çifti, açılışı `stage-open` ile `setup/stage.json`; `spec.lint` gelene kadar `02` listesini tohumun spec denetimi uygular (`02`, `18`). Kurucu defteri ilk oturumdan tohumun aracıyla zincirli; bildirim kanalı `reports/*.json` (`00a`). Gerçek test kuralına modülsüz kırmızı (`04`). `loop.yml` kuralları, koşu başına taze host dizini, birim imajı `@sha256`, servisler sonraki partide (`08`). `units[]`, ajan yapılandırması ve operatörün `excluded_paths`'ı, daraltma reddi (`14`). Beyin reposu yeni ve ayrı; Kurucu başlatıcısı ve yerleşim `24a`'da; hedefe yazım yalnız API ile `refs/heads/brain/**`'a; lisans kapısı yalnız ürüne giren bağımlılıklar için (`24`). Kurulum: üç repoda ruleset, kopya hedef ve aynalama, `targets[]` ve `unit_candidates`, tohum dönemi, dürüstlük ekimi, ilk koşu (`25`); aktarım önyükleme hakemine dokunmaz, `loop.yml`'u koyar, `stage-open` ve kopyanın adımları (`25a`). Araçlara "Gelir" sütunu, `unit.verify`, `target.write`, `activate` (`26a`); Aşama 0 dosyalarının şemaları `26c`'de, `operating{}` `26b`'de; okuyucular `27` ve `27a`'da; `operating{}` sınırları ve `stage_budgets.asama_0` (`18a`). Vektör grupları, veri biçimi ve genel koşucu `29d`'de; `drill` grubu ve ders provası yargıcı Aşama 2 partisinin, istatistik ve eşleme vektörleri P1'in (`29a`, `29c`, `22a`). Güvenlik gözlemi ve avcı koltuğu P2 ile Aşama 1'de (`03`, `26`, `30d`, `30f`). K5 (sahibin düzeltmesi): bütçe kaçak frenidir, kısıt değil; oturum sayısı ve USD ölçüdür, çıkış koşulu değildir ve Kurucu'yu durdurmaz; abonelik penceresine takılmak (429) operatör uyarısı ve kesintidir, ret değildir (`06`, `18`, `18a`, `24`, `25`, `28`). `29` ve `29b`'nin bekleyen düzenlemeleri `docs/asama-0-daraltma-29-29b.md`'dedir.
- 2.2 (2026-10-29): güvenlik birinci sınıf (kayıtta E56 ve E57, operatörün yönü ve onayı). Güvenlik kataloğu: 66 açık sınıfı, her biri için bulma yolu, yürüterek kanıtlayan kapanış testi, CWE ve OWASP karşılığı ve düzeltme yolu; OWASP Top 10:2025 ve 2021, API Security Top 10:2023 ve CWE Top 25:2025 maddelerinin her biri bir sınıfa düşer; çok kiracılık, GraphQL ve kaynak tüketimi ayrı sayfadadır (`30`–`30c`). Zamanlama: bulmak, kanıtlamak, bildirmek ve bekçi testi bağlamak Aşama 1'den; hedefe güvenlik düzeltmesi yalnız K6 canlı olunca; migration, manifest, sır, yapılandırma ve iş akışı hiçbir zaman sistemin işi değildir (`30`, `03`, `05`, `04a` 10, `asama-0/05`). Hedef güvenlik profili ve kural–test bağı (`30d`). Zincirli `security` defter bölümü: yaşam döngüsü, düzeltilmemiş açığın ayrıntısının açık yüzeye çıkmaması, her kapanışın bir dedektör, bir regresyon testi ve bir ders bırakması (`30e`, `13`, `16`, `22`, `21a`); hakemin kendi ilk sekiz satırı `seed/security-ledger.jsonl`'dadır. Bağımsız güvenlik avcısı koltuğu: salt okunur, Kurucu'dan ve rakipten ayrı bağlam, model ve bütçe; yalnız izinli lisanslı tarayıcılar ve katalogla sürülen LLM katmanı; ekilmiş açık provasıyla ölçülür (`30f`, `18`, `18a`, `18b`, `25a` 7, `26` `drill: security`, `26a` `security.*`, `27`, `00b`).
- 2.2 (2026-10-29): eksik kaydının (`docs/eksik-kaydi.md`) onaylanan kararları. İç kullanımda geçit ve API anahtarı yoktur: `llm.call` ve araç kullanan ajan tohum rakibi gibi `çağır`'da `claude` CLI'siyle koşar (`24`, `08`, `06`, `26a`). Rakip defteri görmez; yeniden üretici sözleşmesi, kontrol ağacı, kanıtlanmış kusur ve açık iddia hafızası (`29`); ret hafızası yalnız Kurucu'nun düzeltebildiğini sayar; kesinti ile `request_rejected` ayrıldı; durum yoksa durur, karşılaştır-ve-yaz; kill switch canlı, `stopped`; çıkışta yalnız sağ çıkan artefakt, `spec.lint` ve `gate.lock`; donmuş spec yeniden donmaz; bütçe bitince iş başlamaz (`29b`, `29a`, `28`). Kurulum hash'leri her sonuçta, kurtarma, uyarılar ve `oauth_token_expires` (`25`); açık hakem reposuna yalnız açık hedef.
- 2.2 (2026-10-29): iç kullanımda beyin ve hakem repoları açıktır (operatör kararı; satışta özel olur). Önyükleme
  hakeminde okuyucu App'i yoktur: açık beyin kimliksiz okunur, App yalnız özel hedef gelince kurulur. Standart
  koşucu dakikası açık repoda ücretsizdir; 60 gün etkinlik yoksa zamanlayıcı kapanır (`25`).
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
