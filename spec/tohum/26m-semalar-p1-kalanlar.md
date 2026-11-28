# Şemalar, Devam: P1'in Kurulmuş Satırlarının Kalanları

Tarih: 2026-11-22 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: P1 MF2–MF4 (`snapshot.make`, `cases.build`, `harness.score`) yazılırken ya da değiştirilirken ve P1'in çıkış isteğinden önce
Çapa: beklemede: P1 aktarımı — snapshot belgesi, `<state_root>/cases/dev.jsonl`, harness raporu

---

`26e` "P1'in arayüz olguları"nın devamı (rapor masası uzlaşısı (2026-11-22), seed-089–091; operatör kararı, sahibin
yetkisiyle). Arayüz olgularıdır; kodun nasıl yazılacağı Kurucu'nundur. "Kurulduğu gibi benimsendi" Kurucu'nun yapımını
arayüz yapar (`26j:17`'nin emsali): sonraki bir değişikliği yeni bir biçimdir, hiçbir zaman sessiz değil.

**Snapshot** (`snapshot.make`, P1 MF2; seed-089).
- (1) Bir kimlik (`asama-1/13c:16-17`) bir dosyanın yolunda, bir bağın yolunda ya da hedefinde geçiyorsa o vakanın
  snapshot'ı üretilmez ve vaka çıktıda adlandırılır; yol yeniden adlandırılmaz (adlandırma gerçek hiçbir ağaçta olmayan
  yollar doğurur, `touched_paths`'ten ve manifestten ayrılırdı). Sıkılaştırma; ret kurulduğu gibi benimsendi
  (`identifier_in_path`).
- (2) Manifest `asama-1/13c:30`'daki gibidir: yalnız düzenli dosyalar, yol → baytlarının sha256'sı; bir bağı gösteren
  bulgu manifestin dışındadır. `snapshot_id` 64 küçük onaltılıktır ve bütün snapshot'ı kapsar: bir dosya baytı, dosya
  yolu, bağ yolu, bağ hedefi ya da çalıştırma biti değişince değişir; bunlarda eşit iki snapshot'ın kimliği birdir. Onu
  hakem kodunda tek fonksiyon yapar ve denetler. Serileştirme kurulduğu gibi benimsendi (`{files, links, exec}`, sıralı
  JSON olarak hash'lenir). Sıkılaştırma: "içerik hash'i" bağları ve kipleri de kapsar.
- (3) Sayfada zaten vardır: `asama-1/13c:31`. Adapter birimin lint aracına snapshot'tan değil, birimin tarifinden Aşama
  0'ın `deps.fetch`'iyle (`asama-0/06`) `koş` koşusunda ulaşır; snapshot'ın hariç tutmaları (`13c:14-15`) değişmez.
- (4) Sayfada zaten vardır: `01b:36`, `27a:14`. `finding_id_patterns` `profile.json`'un alanıdır (`26b:49`);
  `profile.json`'u `profile.derive` yazar, oyuncunun önerisi türetmeyi yalnız genişletir. Aşama 1'de bu alanın türetme
  kuralı yoktur: liste boştur (geçerli, `26e:65`).
- Yer tutucu kuralı (`26e:64`) ve `26`'nın `case` şeması değişmez; yeniden yapım Kurucu'nundur. Hiçbir vaka alanı
  eklenmez: `make`'in değiştirdiği kimlikler vakanın kendi alanlarıdır (`case_id`, `fix_sha`, `mutation_id`; `26:57-60`);
  ekilen içerik `human_fix` için `base_sha`'nın ağacı, `mutation` için o ağaç artı `mutation_id`'nin adlandırdığı
  mutasyondur (`asama-1/13a:11-16`).

**Dev vaka seti** (`cases.build`, P1 MF3; seed-090).
- (1) `<state_root>/cases/dev.jsonl`: tek JSON-lines dosyası (`<state_root>` hedefin kendisinindir, `27a:9-10`), satır başına
  bir `26` `case`. `case_id` kimliktir: dosyadaki bir kimlik yeniden yazılmaz; aynı kimlikle başka içerik reddedilir,
  düzenleme değildir. Yalnız ekleme defterin önek kuralıyla yargılanır (önceki satırlar bayt düzeyinde aynı, `01b:33`).
  Başka bir `split` yazıcısı gelince kendi dosyasını alır.
- (2) Taşınma: `cases/dev.jsonl` bir `<state_root>` yoludur, hedefin `brain/state`'indedir. `yaz` onu devrin tek
  `brain/state` commit'inde (D6) yazar; sonraki devrin `çek`'i onu `brain/state` başından okur ve `pulled`'da taşır,
  başta yoksa yoktur. `yaz`'ın almadığı bir dosya tutulamaz (`01b:34`).
- (3) Vaka `base_sha`'sına sabittir (`asama-1/13a:15-16`): entegrasyon başının ilerlemesi onu ne geçersiz kılar ne
  yeniden tabanlar. Taban commit'i okunamayan vaka puanlanmaz, raporda adlandırılır, sessizce düşmez. Vaka yalnız bir
  geri çekme satırıyla kapanır (`01b:34`).
- (4) `cases/` önerisini (`26a:43`) Kurucu kabul etmez ve yazmaz: vaka satırını yalnız `yaz` (hakem kodu) yazar, yalnız
  `cases.build`'in yargısından (geçerli; `validity_evidence.output_sha256` `yaz`'ın okuduğu `koş` sonucunun hash'i);
  kapı `brain/state` commit'ini `01b:34`'ün yol kuralıyla (yalnız ekleme, `provenance` zorunlu) kabul eder. Kurucu
  `cases.build`'i dev için yalnız oyuncakta çağırır; o çağrı `brain/state`'e yazmaz.
- (5) Mutasyon bölgesinin dışında (başka bir satırda ya da dosyada) yeni bir (kural, satır) ihlali bırakan mutasyon
  reddedilir: vakanın ağacı tabanından tam olarak bir yeni ihlalle ayrılır. Sıkılaştırma (`asama-1/13a:18-21`); ret
  kurulduğu gibi benimsendi (`violation_outside_region`).
- (6) K0–K2 isabeti: bulgunun birincil başvurusu (`evidence_refs[0]`) vakanın aynı `path`'teki bir hunk'ının tamamen
  içindedir; `tool` ve `rule_id` aynıdır (`29a:60`). Bu `asama-0/08`'in eşlemesidir: hunk içindeki satır hunk'ın aday
  tarafındaki aralığına eşlenir. Hunk'tan geniş başvuru isabet değildir. Sıkılaştırma (kurulan: başvurulardan herhangi
  biri); K3 ve üstü "başvurulardan biri" kalır (`asama-1/13e:16`).
- Grup kuralı (`26e:68-69`) değişmez; `referee/cases/build.py`'nin yeniden yapımı Kurucu'nundur. (1)–(4) artık
  sayfadadır: dev vakaları `brain/state`'e yazılabilir.

**Puanlama** (`harness.score`, P1 MF4; seed-091).
- (1) Parmak izini yalnız hakem kodu yapar: `findings.jsonl`'un yazıcısının tek fonksiyonu (`findings/write.py`, MF8).
  Biçimi kurulduğu gibi benimsendi: RFC 8785 biçiminin sha256'sı, 64 küçük onaltılık, `["symbol", property, file,
  symbol, normalize(claim)]` ya da `["line", rule_id, file, normalize(content)]` (`normalize` `26j:17-19`). Puanlayıcı
  yalnız bu fonksiyonun yaptığı parmak izini puanlar ve onu koşunun gözlem listesinden (`26q`; `findings.jsonl`
  değil) yazıldığı gibi okur; bir ajanın dosyasındaki parmak izini hiçbir zaman almaz. Sıkılaştırma; istisnası L-AH1.
- (2) Bir koşuda (`26q`: bir avcı koşusu) birden çok görülen parmak izi tek bulgudur: listenin sırasındaki ilk gözlem
  puanlanır; sonrakiler raporda sayılan yeniden gözlemlerdir, ne isabet ne yanlış pozitif (`26k:16-18`'in kuralı).
- (3) Hüküm: vaka yoksa ya da sınıf sayımın (K0–K2) dışındaysa `UNMEASURABLE`; isabet almayan bir vaka varsa `FAIL`;
  yoksa `rules_total`'ın (`29za:9-22`: hedefin `census` vektörünün kural kümesi, `26q`) koşuda vakası olmayan bir kuralı
  varsa `UNMEASURABLE`; yoksa `PASS`. `PASS` her kuralın kapsanmasını ve sıfır kaçırmayı ister (`asama-1/13e:22`);
  `UNMEASURABLE` asla `PASS` gibi davranmaz (`19:12-13`). Dev raporunun grup tabanı yoktur (`26h:67-68`). `19:24`'ün
  `min(45, mevcut)`'u çıkış ölçüsünündür: `exit.sample` onu çekildiği sayıyla verir; verilmezse çıkış hükmü `PASS`
  olmaz. Sıkılaştırma: kendi vakalarıyla yetinen hiçbir koşu `PASS` almaz.
- (4) K4'ün sayımı Aşama 3'e ertelendi (K4 orada gelir, `03:63`); o zamana kadar bir K4 raporu `UNMEASURABLE`'dır.

Açıkça ertelenenler ve test 9, test 11, sürükleme etkinliği, Aşama 1'in bulgu başı frenleri `26n`'dedir. Koşunun
tanımı, gözlem listesi, payda ve iki dosyalı komutun gevşetmesi L-AH1 `26q`'dadır (seed-101).

**Vakanın grubu** (`26e:68-69`; seed-105; devamı `26n:73-78`). Paket manifesti temel adı `package.json` olan düzenli
dosyadır (`29k:51`'in `manifest`'i), başka hiçbir şey değildir: Nx'in `project.json`'ı da, `pyproject.toml`,
`Cargo.toml` ya da `go.mod` da grup işaretlemez. Arama değiştirilen dosyanın dizininden birimin köküne kadardır, kök
dahil, üstüne çıkmaz; yolda manifest yoksa grup birimin köküdür. Sıkılaştırma: grup birimin kökü ya da altındadır.
