# Şemalar, Devam: Paketin Bulgusu, Avcı Koşusu ve Puanlamanın Paydası

Tarih: 2026-11-23 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: P1 MF12 ve MF4 (`loop/candidates.py`, `loop/decide.py`, `harness/score.py`) ve `cases.build` yazılırken ya da değiştirilirken, bir paketin `finding`'i ya da bir koşunun puanı okunurken ve P1'in çıkış isteğinden önce
Çapa: beklemede: P1 aktarımı — `candidates/<id>/package.json`'un `finding`'i, avcı koşusunun gözlem listesi, harness raporu

---

`26j` MF12'nin, `26k` T1–T2'nin ve `26m` "Puanlama"nın devamı (rapor masası uzlaşısı (2026-11-23), seed-100 ve
seed-101; operatör kararı, sahibin yetkisiyle). Arayüz olgularıdır; kodun nasıl yazılacağı Kurucu'nundur. "Kurulduğu
gibi benimsendi" Kurucu'nun yapımını arayüz yapar (`26j:17`'nin emsali); sayfanın ayrıldığı yerde modül sayfayı izler.

**Paketin bulgusu ve kayda yolu** (seed-100, E730; Kurucu'nun okuması kurulduğu gibi benimsendi; sıkılaştırmalar, (3)'te fark).
- (1) Paketin `finding`'i düzeltmenin ait olduğu bulgudur, önerilen biçimde: `findings.write`'ın 5. kuralının nesnesi,
  yani `26`'nın bulgu alanları, `finding_id`, `fingerprint`, `state`, `trust` ve `proposed_by` olmadan (`symbol`, `tool`
  ve `rule_id` isteğe bağlı). Sıkılaştırma: bu beş alandan birini ya da başka bir anahtarı taşıyan `finding` paketi
  `package_invalid` yapar; aday bir bulgunun kimliğini ya da durumunu hiçbir zaman kendisi söyleyemez.
- (2) D5'in kayda sorduğu parmak izini hakem yapar: `findings.write`'ın tek fonksiyonu (`26m:59-61`), devrin ağacında,
  adayın yeniden koşusunun karşılaştırıldığı ağaçta (`26p:64-66`). Paketin parmak izi üstüne söylediği hiçbir şey okunmaz.
- (3) Bir sayfanın bir bulgunun satırını okuduğu her yerde o satır birincil başvurununkidir (`evidence_refs[0]`,
  `26h:59`) ve o başvuru bulgunun `file`'ındadır: parmak izinin `content`'i (biçim 2), kapının `{rule_id, path, line}`'ı
  (`asama-0/08`: bulgunun `rule_id`'si, `file`'ı ve birincil başvurunun `line_start`'ı) ve K0–K2 isabeti (`26m:51-54`)
  aynı başvuruyu okur. Birincil başvurusu başka bir yolda olan bulgunun satırı yoktur (`no_line`); kapının bir değeri
  yoksa kapı adayı reddeder (`candidate_unusable`). Sıkılaştırma; fark: kurulan, `file`'daki ilk başvuruyu okur.
- (4) T1 (`26k:34-35`) devrin başladığı kaydı okur: `yaz`'ın `brain/state`'ten çektiği `findings.jsonl`'u, bu devrin
  önerileri uygulanmış hâlini değil. Aynı devirde önerilen bulgunun o devirdeki adayı `finding_unknown`'dır; bulgu
  sonraki devirden itibaren karara bağlanabilir. Sıkılaştırma: hiçbir aday kendi devrinde önerilen bir bulguyu düzeltemez.
- (5) Organın önerilerinin dosyası `26p:28-30`'dadır (`findings.json`; satır biçimi Aşama 1 MF1'i getiren dönemde). P1
  hiçbir öneri okumaz (`26j:27-28`): bir öneri `yaz`'a ulaşana kadar her canlı çalışma-zamanı adayı `finding_unknown`'dır.
  Bu tasarımdır, etrafından dolaşılmaz: ilk öneri Aşama 1 MF1'de, ilk çalışma-zamanı adayı MF5'te gelir (`26h:12-15`).
- (6) Nedenler, kurulduğu gibi. Her biri yalnız o adayın reddidir (`26k` T2); hiçbiri duran neden değildir
  (`26j:43-46`), `cause`'u `unknown`'dır (`26:41-44`) ve `unresolved` satırı yazmaz. `package_invalid`: `yaz`'ın,
  yeniden koşunun verdiği paketin biçim denetimi: paket tam olarak `26a:66`'nın dört anahtarıdır, fazla bir üst anahtar
  (ör. `fingerprint`) da `package_invalid`'dir; `organ_ids` `gate.allowlist`'in okuduğu biçimdedir, `definition_sha256`
  64 küçük onaltılık dizgilerdir, `finding` (1)'in biçimidir. `koş`'un `package_unusable`'ından (`26p:47-48`) ayrı
  aşamadır, iki ad da durur. `finding_decided`: bir bulgunun sonraki adayı; sıra aday kimliklerinin kod noktası
  sırasıdır. `no_line`: bulgunun devrin ağacında parmak izi yok. `candidate_id_twice`: hem bir hazır hem bir
  çalışma-zamanı adayının taşıdığı kimlik; bir kimlik bir karar satırıdır (`c:<id>`): ikisi de reddedilir, hiçbiri
  yargılanmaz (genesis'ten sonra hazır aday zaten `no_organ` alır). `registry_unusable`: `findings.jsonl` geçerli bir
  zincir değil; o dosya D6'yı da durdurur, bu ad hiçbir devri yazdırmaz.
- (7) Kapalı kapının reddi (`26j:43-46`) bulgu üstüne bir karar değildir, T2'nin iki kararının ilki sayılmaz: aynı
  bulgunun sonraki adayı kendi nedenleriyle yargılanır. Duran bir nedenin yanında başka bir nedeni olan ret karardır.
- (8) Genesis devri çalışma-zamanı adayı okumaz (`26j:33-34`, `26a:66-68`): orada bulunan paket yargılanmaz, karar
  satırı almaz. Vektör: MF10–MF12'nin grubu yoktur (`26p:67`); test 58 bağlar.

**Avcı koşusu ve gözlem listesi** (seed-101, E731; `26m` "Puanlama"nın dosyası düzeltildi, kuralı durur).
- (1) Koşu, bir avcı organının bir snapshot üzerindeki bir koşusudur. Raporun `run_id`'si o koşunun `run_meta.run_id`'si
  (`26:62`), `snapshot_id`'si koşununkidir; aynı snapshot'taki iki koşu iki ayrı listedir.
- (2) Koşunun gözlem listesini hakem kodu o koşu için yazar: koşunun her gözlemi, organın sırasıyla, yeniden gözlemler
  ve hedefin kaydında zaten olan bulgular dahil (`asama-1/13e:24`); her parmak izini `findings.write`'ın tek fonksiyonu
  o snapshot'ın ağacında yapar. Liste durum ve karar satırı taşımaz. Snapshot'ı koşununki olmayan bir satır taşıyan
  liste kullanılamaz; satır sessizce atlanmaz. `26m` (2)'nin "ilk gözlem"i bu listede okunur.
- (3) `findings.jsonl` hedefin kaydıdır: durumları tutar, yeniden gözlem için satır yazmaz (`26k:16-17`). Ne kendisi ne
  bir penceresi (bütün dosya ya da bir snapshot'ın satırları) bir koşudur; puanlayıcının girdisi değildir.
  Sıkılaştırma. Gevşetme değildir: puanlanan her parmak izini hâlâ yalnız hakem kodu yapar (L-AH1 dışında, (8)).
- (4) Listenin yeri, adı ve satır biçimi ertelendi: Aşama 1 MF1'i (`lint.discover`, ilk avcı) getiren döneme (`26p:28-30`).
- (5) Ekilmiş ağaçtaki (dev ya da çıkış snapshot'ı) koşunun yalnız kendi listesi vardır: gözlemlerinin hiçbiri
  `findings.jsonl`'a ya da `unresolved.jsonl`'a yazılmaz (`asama-1/13c:14`, `13c:21`). Sıkılaştırma. Kayda yalnız
  hedefin kendi ağacındaki bir koşunun gözlemleri, yazıcıdan geçerek girer.
- (6) Vakanın snapshot'ında avcı koşusu olmayan devirde hiçbir harness raporu puanlanmaz: hedefin satırı bunu adlandırır
  (neden adı Kurucu'nundur), hüküm ne `FAIL` ne `PASS`'tir (Aşama 1 MF1'e kadar). Sıkılaştırma: uydurulmuş kaçırma yoktur.
- (7) `cases.build`, ekilmiş ihlali vakanın ağacında aynı dosyadaki başka bir ihlalle aynı parmak izini taşıyan vakayı
  reddeder: puanlayıcı onun bulgusunu ayıramaz (`26j:23`, `26m:61-62`; neden adı Kurucu'nundur). Sıkılaştırma (`asama-1/13a`).
- (8) İki dosyalı komut (`29a:73-74`), kurulduğu gibi: girdisi fikstürlerin verdiği biçimde bir JSON bulgu dizisidir
  (`26`'nın bulgu nesneleri, `vectors/match/findings_*.json` gibi); çıktısı `{"hits": n}`'dir (ret varsa `refused`);
  rapor ve hüküm yoktur, hiçbir şey yazmaz. Onu hiçbir iş koşmaz; hiçbir defter satırı, kapı ya da hüküm onu okumaz.
  **Gevşetme L-AH1** (kapsamlı; sahibe bildirilir): bu komut parmak izlerini verildiği gibi alır, `29a:73`'ün kendi
  vektörlerinin istediği gibi (`fp-f1` hash değildir; boş olmayan bir "aynı bulgu" etiketidir). `26m:59-63`'ün "yalnız hakem
  kodunun yaptığı parmak izi" kuralının istisnası yalnız bu vektör komutudur; canlı puanlama (dört dosyalı biçim, rapor
  ve hüküm) hakemin yaptığı parmak izini tutar.
- (9) Önyükleme hakemi iki dosyalı komutu, sahibi MF4 olan `match` vektörlerine (`26e:21`, `29d:52-53`) uygular ve
  `hits`'i kendi tuttuğu değerlere karşı yargılar (`29a:67`); `/vec/cases.json` yalnız veri vektörlerinin girdileridir,
  onun bir grep'i hakemin kendi yargısını göstermez. Orada kırmızı olabilir.
- (10) Payda: `rules_total` hedefin `census` vektörünün kural kümesidir (`29za:9-22`; oyuncakta `eslint`'in yedi
  kuralı), ne kütüphanenin kuralları ne koşunun vakaları; vektör aracını adlandırır, payda araç başınadır. `26e:72-73` aynı
  kümeyi söyler. Kütüphanenin üretemediği vektör kuralı paydada kalır, kırmızı nedendir (`29za:12-13`).
  Kümenin dışındaki bir kuralın vakası `rules_total`'a ve `rules_covered`'a bir şey eklemez, yine de vakadır: `n`'de,
  `recall`'da ve kaçırmalarda sayılır, kaçırması `FAIL`'dır; puanlayıcı böyle kuralları raporun yanında adlandırır
  (`26b` raporu alanlarını korur; bugün oyuncakta `eqeqeq`). Vektörü olmayan hedefin (bugün kopya, `29za:19-22`) sayımı
  yoktur, hükmü asla `PASS` değildir. Fark: kurulan payda kütüphanenin kurallarıdır; modül sayfayı izler.
