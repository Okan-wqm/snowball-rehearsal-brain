# Değişiklik Günlüğü — Tohum, 2.2'nin On Altıncı Kayıtları

Tarih: 2026-11-23 · Sürüm: 2.2
Okunma: bir sayfanın geçmişi aranırken
Çapa: git geçmişi ve zincirdeki spec hash satırları

- 2.2 (2026-11-23, E730–E732; tohum dönemi AH; rapor masası uzlaşısı, sahibin yetkisiyle operatör kararı). **İlk iş**
  (`25` 10b). Teslimden itibaren önyükleme hakeminin hiçbir denetimi kırmızı olmaz: bu dönem ne bir tablo, ne bir vektör,
  ne bir zorunlu politika yolu, ne hakemin kodu değiştirir; yalnız sayfalar değişir. Kurucu'nun bugünkü işi sürer,
  sırası `CHANGELOG-14`'ünkidir. Bu dönemin yanıtları iki yerde ondan öncedir: P1'in çıkış isteğinden önce kurulmuş
  `harness.score` seed-101'in yanıtına uyar (`26q:46-80`, `26m:58-67`; bugün canlı bir dev raporu bütünüyle kaçırma
  olurdu), ve yine çıkış isteğinden önce MF12'nin kurulmuş satırları `26q:13-44`'e uyar (seed-100; modül sayfayı izler).
  Raporların teyidi `26l`'nin kuralı olarak kalır, bu listenin bir maddesi değildir. Yeni `26q` (`26j`, `26k` ve `26m`
  ona işaret eder). `26m` "Puanlama" düzeltildi: puanlayıcının dosyası koşunun gözlem listesidir, `findings.jsonl` değil
  (kuralı durur: puanlanan parmak izini yalnız hakem kodu yapar); `26m:67`'nin `rules_total`'ı `29za:9-22`'yi gösterir.
  `26e:72-73` yerinde düzeltildi: `rules_total` hedefin `census` vektörünün kural kümesidir (eski "aracın kataloğunda
  vaka üretilebilen kurallar" sözü kalktı, ikinci kaynak yok). `26n:58-59` ve `26q:55` L-AH1'i ayırır.
  **Gevşetme L-AH1** (kapsamlı; sahibe bildirilir; `26q:64-70`): iki dosyalı vektör komutu (`29a:73-74`) parmak izlerini
  verildiği gibi alır; yalnız o komut; canlı puanlama hakemin yaptığı parmak izini tutar. Başka gevşetme yok.
  Sıkılaştırmalar: paketin bulgusunda kimlik, durum ya da fazla anahtar `package_invalid` (100 (1)); paket tam olarak
  dört anahtardır, fazla üst anahtar ve 64 küçük onaltılık olmayan `definition_sha256` `package_invalid` (100 (4));
  bulgunun satırı `file`'daki birincil başvurudur (100); T1 devrin başladığı kaydı okur (100 (3)); kayıt ya da bir penceresi koşu
  değildir (101 (1)); ekilmiş koşu kayda yazmaz (101 (2)); koşusuz devirde puan yok, uydurulmuş kaçırma yok (101);
  aynı parmak izli ekilmiş satır reddedilir (101 (b)). Modülden farklar: satır `file`'daki ilk başvurudan birincil
  başvuruya (`26q:20-24`); payda kütüphaneden vektörün kümesine (`26q:74-80`); listede başka snapshot'ın satırı
  sessizce atlanmaz, listeyi kullanılamaz kılar (`26q:51-52`; masanın kararı: Kurucu'nun süzgeci bir ret olarak okunur,
  satırı sayıp atlamaz). AF boşluğunun nedeni: AF'nin `26m`'si "bir koşuda"
  puanladı ama koşuyu tanımlamadı; o dönemin iki paneli de bu boşluğu paylaştı; Kurucu sayfayı harfiyen ve doğru okudu.
  Yanıtlanan raporlar; her madde raporun yazıldığı hâliyle, kendi etiketiyle bir satırdır:
  `seed-100-the-form-of-a-package-s-finding-and-its-way-into-the-registry-are-unstated` → `26q:13-44`:
  - (1) paketin bulgusunun biçimi (parmak izi, kapının `{rule_id, path, line}`'ı, `26`'nın alanları ya da `finding_id`):
    yanıtlandı (`26q:14-17`, önerilen biçim; kapının üçlüsünü hakem türetir, `26q:20-24`);
  - (2) D5'in kayda sorduğu parmak izini kim hesaplar: yanıtlandı (`26q:18-19`, hakemin tek fonksiyonu; paketinki okunmaz);
  - (3) T1 hangi kaydı okur (devrin başındaki mi, önerileri uygulanmış mı): yanıtlandı (`26q:25-27`, başındaki);
  - (3, devamı) "`26j:25` öneriyi organın çıktı listesinde tutar, hiçbir sayfa o listenin dosyasını adlandırmaz":
    yanıtlandı, sayfada zaten vardır (`26p:28-30`, rapordan sonra AG'yle geldi; `26q:28`); satır biçimi ertelendi: Aşama
    1 MF1'i getiren döneme (ilk yazıcısı; P1 öneri okumaz);
  - (3, devamı) "hiçbir iş `yaz`'a öneri vermez, canlı devir bulgu açamaz": yanıtlandı (`26q:28-30`, tasarımdır;
    öneriyi okumak Aşama 1 MF1'le gelir);
  - (4) biçimsiz paketin nedeni: yanıtlandı (`26q:32-36`, `package_invalid`: tam dört anahtar ve biçimleri;
    `package_unusable` ayrıdır);
  - (4) bir bulgunun iki adayından sonrakinin nedeni: yanıtlandı (`26q:36-37`, `finding_decided`, kod noktası sırası);
  - (4) ağaçta parmak izi olmayan bulgunun nedeni: yanıtlandı (`26q:37`, `no_line`);
  - (4) hem hazır hem çalışma-zamanı adayının taşıdığı kimliğin nedeni: yanıtlandı (`26q:37-39`, `candidate_id_twice`);
  - (5) kapalı kapının reddi T2'nin iki kararının ilki mi: yanıtlandı (`26q:41-42`, değil; `26j:43-46`);
  - (6) genesis devri çalışma-zamanı adaylarını okur mu: yanıtlandı (`26q:43-44`, okumaz; `26j:33-34`);
  - vektör notu (hiçbir vaka çalışma-zamanı paketi taşımaz): yanıtlandı, sayfada zaten vardır (`26p:67`, `26q:44`);
  - Kurucu'nun okuması: yanıtlandı, kurulduğu gibi benimsendi (`26q:13-44`), `registry_unusable` dahil (`26q:39-40`);
    farkı satırın başvurusudur (`26q:20-24`);
  - sonuç (öneri `yaz`'a ulaşana kadar her canlı aday `finding_unknown`): yanıtlandı (`26q:28-30`, etrafından dolaşılmaz);
  - soru (biçim, hesaplayan, T1'in kaydı, nedenler, önerilerin dosyası için birer cümle): yanıtlandı (`26q:14-40`);
  - "bir sayfanın farklı olduğu yerde modül onu izler": yanıtlandı (`26q:11`; farklar yukarıda).
  `seed-101-the-run-in-the-writer-s-findings-file-and-the-findings-form-of-the-two-file-command-are-unstated` →
  `26q:46-80`, `26m:58-67`:
  - (1) bir koşunun o dosyada nerede başlayıp bittiği: yanıtlandı (`26q:47-55`: hiçbir yerde, `findings.jsonl` koşunun
    kaydı değildir; koşu bir avcı koşusudur, puanlayıcı hakem kodunun onun için yazdığı listeyi okur; `26m:61-65`);
  - (1, devamı) o listenin yeri, adı ve satır biçimi: ertelendi: Aşama 1 MF1'i (`lint.discover`) getiren döneme
    (`26q:56`; yazıcısı olmayan dosya yerleştirilemez; o zamana kadar puan yoktur, `26q:60-61`);
  - (2) ekilmiş ağaçtaki koşunun bulgularını tutan dosya: yanıtlandı (`26q:57-59`, koşunun kendi listesi; kayda yazılmaz);
  - (3) iki dosyalı komutun bulgu biçimi: yanıtlandı (`26q:64-70`, kurulduğu gibi; gevşetme L-AH1, yalnız o komut);
  - (3, devamı) "`/vec/cases.json`'un hiçbir vakası `harness.score`'u koşmaz, hiçbir şey kırmızı değil": yanıtlandı
    (`26q:71-73`, `match` vektörleri MF4'ündür, `29a:67`, `29a:73`; orada kırmızı olabilir);
  - (4) `rules_total` vakaların aracı başına mı bütün kütüphane üstünden mi: yanıtlandı (`26q:74-76`, ikisi de değil:
    `census` vektörünün kümesi, `29za:9-22`; `26m:67` oraya işaret eder);
  - (4, devamı) kataloğun dışındaki kuralın vakası ne ekler: yanıtlandı (`26q:77-80`, paydaya hiçbir şey; vaka sayılır);
  - Kurucu'nun okuması: yanıtlandı (iki dosyalı biçim kurulduğu gibi benimsendi, `26q:64-70`; "dosya koşudur", "karar
    satırı yeniden gözlemdir" ve kütüphane paydası reddedildi, `26q:49-55`, `26q:74-80`);
  - sonuç (`yaz` `report`'a satırsız dosya verir, vakalar hep kaçırma): yanıtlandı (`26q:60-61`, puan yok, `FAIL` yok);
  - güncelleme (a) aynı snapshot'taki iki koşu ayrılamaz: yanıtlandı (`26q:47-48`, `run_meta.run_id`; iki koşu iki liste);
  - güncelleme (b) önceki snapshot'tan açık kalan bulgunun gözlemi: yanıtlandı (`26q:49-52`, her gözlem listededir);
  - güncelleme (b) aynı dosyada bulunmuş bir satıra eşit ekilmiş satır: yanıtlandı (`26q:62-63`, vaka reddedilir);
  - güncelleme, Kurucu'nun okuması (koşu raporun snapshot'ının satırları, başkası `other_runs`): yanıtlandı
    (`26q:51-55`, pencere koşu değildir; başka snapshot'ın satırı listeyi kullanılamaz kılar);
  - soru (güncelleme: bir koşunun gözlemleri nerede kaydedilir): yanıtlandı (`26q:49-52`; yeri ertelendi, yukarıda);
  - soru (koşunun sınırları ya da ekilmiş koşunun dosyası, iki dosyalı biçim, paydanın aracı için birer cümle):
    yanıtlandı (`26q:47-59`, `26q:64-70`, `26q:74-76`).
