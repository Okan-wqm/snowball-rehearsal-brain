# Değişiklik Günlüğü — Tohum, 2.2'nin On Dokuzuncu Kayıtları

Tarih: 2026-11-23 · Sürüm: 2.2
Okunma: bir sayfanın geçmişi aranırken
Çapa: git geçmişi ve zincirdeki spec hash satırları

- 2.2 (2026-11-23, E739–E743; tohum dönemi AK; sahibin dört ipucu ve seed-102'ye rapor masası uzlaşısı).
  **İlk iş** (`25` 10b). Teslimden itibaren önyükleme hakeminin hiçbir denetimi kırmızı olmaz: bu dönem ne bir tablo,
  ne bir vektör, ne bir zorunlu politika yolu, ne hakemin kodu değiştirir; sayfalar ve başlatıcının aynası değişir.
  Kurucu'nun bugünkü işi sürer, sırası `CHANGELOG-14`'ünkidir; E739–E742 görevdir, kırmızı bir görev değil, ve
  sayfaların zaten istediğinin ötesinde hiçbir yeniden yapım istemez. Raporların teyidi `26l`'nin kuralı olarak kalır,
  bu listenin bir maddesi değildir.
  Yeni `00g`'ye sahibin dört ipucu (görev, reçete değil; olguları `sayfa:satır` ya da beynin `94517ab`'sında
  `dosya:satır`): E739 aday onu üreten organla yargılanır (`12:15-18`, `01b:9-12`; test: listelenmiş bir organı
  adlandıran, listede olmayan bir organın ürettiği paket reddedilir); E740 organ `26m:23-24`'ün söz verdiği araca
  ulaşır (Aşama 1 MF1'in ilk canlı koşusundan önce sınanır); E741 dersler büyürken bulma ve yeniden sınama bütün
  kümeyle büyümez (5 oturumdan sonra yanlışlanabilir); E742 bağlam ölçülen bir kaynaktır (E676'nın devamı). Korkuluklar:
  hiçbir hakem ya da denetim gevşemez, tohumdan yeni hakem kuralı yok. `00f` sonunda `00g`'yi gösteren bir satır
  kazanır; satırlarından hiçbiri yer değiştirmez.
  Başlatıcının aynası (E742; `26o` "Bağlam ve sıkıştırma"): `mirror.json` yeni `context` bölümünü kazanır: en yeni 20
  oturumun her biri için transkriptin oturuma ait `compact_boundary` olaylarından `compactions`,
  `first_compaction_min` ve her sıkıştırmanın `minute`, `input_tokens_before` ve `tokens_from`'u; olmayan değer `null`
  ve nedeni `not_measured`'da. Yalnız olgudur; başlatıcının başka hiçbir şeyi değişmez.
  `seed-102-where-a-running-referee-finds-a-target-s-census-rule-set-is-unstated` → `29za` sonu (`26q` (10) 80
  satırdadır, cümleleri `29za`'dadır):
  - (1) koşan hakem hedefin `census` kümesini nerede bulur: yanıtlandı, kurulduğu gibi benimsendi (küme hakemin
    kendisinindir, ağacında hedefin `kind`'ıyla anahtarlı, `26c:30-31`, `29z:25`; koşuda tohumun vektör dosyalarından,
    politikadan, `state_root`'tan ya da hedeften okunmaz, `29za:9`, `29za:28-29`, `26q:74-80`);
  - (1, devamı) "dosyadan okunuyorsa dosyayı ve anahtarı adlandır": yanıtlandı (hiçbir dosya okunmaz; tohumun `census`
    vektörü kümenin dayanağı ve test girdisidir, koşu girdisi değildir);
  - (1, kopya) kopyanın kümesi: ertelendi: kopyanın `census` vektörünü commit'leyen döneme (operatörün açık işi,
    `29za:19-22`; Aşama 1 çıkışından önce, `29za:21`); o güne kadar kopyanın sayımı yoktur, asla `PASS` değildir;
  - (1, operatörün eki) puanlayıcının `--census` girdisi (`referee/harness/score.py:427`, `:460`): koşuda puanlama
    hakemin kendi kümesi üzerinden sayar, asla çağıranın verdiği bir küme üzerinden değil; `--census` yalnız iki
    dosyalı vektör komutunundur;
  - (2) araç başına payda mı tek `census` nesnesi mi: yanıtlandı, kurulduğu gibi benimsendi, kurulmuş bir sıkılaştırma
    (küme tek aracındır, `29za:24-25`; `26b:43`'ün tek nesnesi onun sayımıdır; iki araçlı, kuralsız ya da kuralı iki
    kez taşıyan küme `census_invalid`); iki aracın rapor biçimi ertelendi: ikinci bir aracın ilk `census` vektörüne
    (K4'ün sayımı Aşama 3'tedir, `26m:72`);
  - (3) `29za:11-12`'nin kural başı raporu neyi okur: yanıtlandı, kurulduğu gibi benimsendi ("etkin" sabitlenmiş
    commit'teki vektörün kümesidir, oyuncakta `de5b57c`, kopyada `base_sha`; "üretilebilir" `cases.build produce`'un
    cevabıdır; çıkışta `uncased_rules` ve `missed_rules` `29za:15-17`'nin koşulunu taşır);
  - soru (her madde için bir cümle): yanıtlandı (her madde için bir cümle, `29za` sonu);
  - not (hiçbir şey kırmızı değil, 14 `census.*` vakası `produce` ile yanıtlanır): teyit edildi, not edildi
    (`cases/build.py` `produce` `{"producible": bool}` yazar, `29za:24-25`).
  Gevşetme yok.
