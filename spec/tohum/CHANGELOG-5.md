# Değişiklik Günlüğü — Tohum, 2.2'nin Dördüncü Kayıtları

Tarih: 2026-11-04 · Sürüm: 2.2
Okunma: bir sayfanın geçmişi aranırken
Çapa: git geçmişi ve zincirdeki spec hash satırları

- 2.2 (2026-11-04, E499, E540–E546; Kurucu raporları, dört uzmanlı iki turlu panelin kararı): `25a` "Başarısızlık":
  kırmızı bir (B)'den sonra operatör iki hedefin her `brain/` dalını aynı repoda `refs/tags/arsiv/<aktarım>/<dal>`
  etiketine arşivler (`<aktarım>` başarısız aktarım satırının `row_hash`'i), satır 3'ün iki ruleset'inin uygulamasını
  yalnız silme süresince kapatıp (bypass aktörü yok) dalları siler, aktarımı geri alıp düzeltilmiş SHA'yı aktarır; (B)
  yeni bir defterin ilk genesis'inden koşar (`26d`, `07`). Tohum güvenlik defteri hakem reposunda
  `setup/security-ledger.jsonl`'dur, tohum dönemi teslim eder (`25` 3, 10b; `26c`, `29o`, `29s`, `27`). Aktarım
  doğruladığı imzalı (A) sonucunu aynı commit'te `setup/results/<result_sha256>.json` olarak yazar, `yaz` ve
  `stage-open` oradan okur (`25a` 1, `26c`, `26d`, `29s`, `27`). `26f`: canlı prova fikstürleri ikinci prova sırrıdır
  (biçim, aktarım satırına bağ, dosya başına kural, üretici `drill-fixtures`); kopya kapısı satırı `events`/`copy_gate`.
  `25a` 5'in App beyanı Aşama 0'da yoktur, okuyucusuyla P1'de gelir (`29o`). Yanıtlanan raporlar:
  `seed-045-drill-live-inputs-unnamed` (tamamlandı) → `26f:34-38` (yer: ikinci sır, yalnız `yaz`'ın adımında),
  `26f:39-50` (biçim: `import_line_sha256`, opak `id`, `cause`, `patch`), `26f:52-58` (dosya başına kural, üretici);
  `seed-047-regenesis-and-genesis-inputs` → (a) `25a:25-40` (arşiv, silme, yeniden aktarım), `26d:31-34` (ilk genesis),
  `07:9-10` (ne senkron ne zorla itme); (b) `29o:15-17` ve `29s:71-74` (defter işin checkout'unda), `26c:45` (dosya);
  `seed-048-copy-gate-record-and-a-result-bytes` → (a) `26f:60-67` (Kurucu'nun taslağı; `stage` ile `verdict: "PASS"`
  birlikte yok), `29s:22-24` (kapı satırından okunur); (b) `26c:38` (dosya, ad, denetim), `25a:15` (aynı commit),
  `26d:47` (`owner_exception`'ın kaynağı), `26d:57-59` (`stage-open` onu commit'ten okur), `29s:71-74`. Sahibe
  açık: aktarımın geri alınması sayaç satırını da siler (E546). 80 satır sınırı için E470–E475 ve E411–E417
  kayıtları `CHANGELOG-5.md`'ye taşındı.
- 2.2 (2026-11-02, E507; Kurucu raporu): `26e`: bir modülün ilk adı Python'un standart kütüphanesinde bir modülün adı
  olamaz (`sys.stdlib_module_names`); hakem komutu `referee/` `sys.path`'te önde koşar ve o ad standart modülü gizler;
  böyle satırı olan tablo yüklenmez. Aşama 0'ın donmuş tablosundaki `profile` (MF4, MF6) kuraldan önce gelir, o tablo
  yeniden açılana kadar kalır. Yanıtlanan rapor: `spec-011-profile-shadows-stdlib` → `26e:33-37` (hakemin hiçbir
  komutu `cProfile`'ı çağırmaz; Aşama 0'ın yolu kalır). 80 satır sınırı için 2026-11-01 E421–E436 kaydı
  `CHANGELOG-4.md`'ye taşındı.
- 2.2 (2026-11-02, E506; sahibin kararı, boşluk D): `24a` "Kurucu": kapsülde defterin salt-okur dizini
  `/opt/founder/ledger_index.py` vardır (imajla gelir, beyne gelmez; tohumun ekleme aracı yine yoktur). 80 satır
  sınırı için 2026-11-01 E450 kaydı `CHANGELOG-4.md`'ye taşındı.
- 2.2 (2026-11-01, E490–E499; Kurucu raporu, E373'ün kalanları, act10 şüphecisinin bulgusu): `25a` 1: içe aktarma
  iki repodan yalnız `main`'i okur ve yalnız her itmenin göndereceğini git'in nesne denetiminden geçirir; 255 bayttan
  uzun tek ad ve boş repo adı durdurur. Yeni `29s` döngünün üç girdisini verir, hiçbiri
  operatör değişkeni değildir: beyin reposu `bootstrap.json` `brain_repo`'dur; bir koşu `targets[]`'ın her girdisine
  dizinin sırasıyla hizmet eder; Sigstore hakemin `bootstrap/requirements/sign.txt`'idir, onu koşturan işte kontrol
  adımının klonundan, lisans kapısından geçirilerek kurulur. Yeni `26e` Aşama 1'in parti tablolarıdır (P1 ve P2;
  modül yolları, parti adları; çıkış partisi Aşama 1 çıkışının yargısıyla gelir); P2 MF1'in testi `30d` "Profil
  testi", 53. `29b`: rakip freni açık aşamanınki, harcama kilitten sayılır; `18a`: `stage_budgets.asama_1.rival_usd`
  15 USD. `27`: `bootstrap.json`, özet ve `sign.txt`'in döngüdeki okuyucuları; `29p` `29s`'e bakar. Yanıtlanan rapor:
  `seed-041-loop-run-inputs-unnamed` → `29s:13-17` (beyin), `29s:19-24` (hedefler), `29s:26-47` (Sigstore);
  `seed-042-d4-canary-inputs-unnamed` → `29s:49-69` (CLI'nin pini kilittir, kurulum adımı, model `rival.model`);
  `seed-043-sentinel-end-row-unnamed` → `26f:12-22` (yeni `26f`: `events`/`sentinel`, geri alma, nöbetçinin bitişi);
  `seed-045-drill-live-inputs-unnamed` → `26f:24-36` (provanın satırları, iş ve sır; canlı fikstürler henüz yok, E499);
  declined: `seed-044-revert-facts-producers`: `29j:53-60` her olgunun ne olduğunu söyler (`build_ok` kodun kırmızı
  başta derlenip yüklenmesi, lint merge'ün ilk ebeveynindeki ve baştaki araç toplamı); üreticileri Kurucu'nun hakem
  kodudur (seed-023 ve seed-030 gibi).
  Dönem kesildikten sonra gelen rapor: `seed-046-pass-row-unnamed` → `26d:36-47` (PASS satırı, `part: events`, hakemin
  kendi satırı; ek alan serbest: `conditions`, `not_checked`), `26d:9` (yazarı döngü hakemi), `29s:19-24` (bir koşu her
  hedefe hizmet eder), `10a:44` (PASS koşulların makine denetimi: denetlenmeyen satır tutmuş sayılmaz), `26f:12-14` ve
  `10a:25` (`flaky` yeşil değildir), `10a:26` (her ekim), `26d:35` ve `10a:24` (`hunk_covered` merge yükünde, kapılamaz).
- 2.2 (2026-11-01, E478–E485; sekizinci şüphecinin bulgusu): `25a` 1–2: içe aktarma beyni git'in nesne
  denetimiyle getirir; `.git`, `.gitattributes` ve `.gitmodules`'ü her derinlikte, harf duyarsız ve HFS+ biçimiyle,
  Windows'un tutamadığı adı (`|?*"<>`, 260 karakterden uzun yol) her sistemde, oyuncakta `.github`'ı reddeder;
  hiçbir şey itilmeden git'in katı nesne denetimi koşar; iki itme okunan `main`'e kirayla (`--force-with-lease`)
  olur ve ret uzak `main`'i adlandırır; yerel yol çağıranın dizinindendir. `26d`: `stage-open` sayacı, özeti ve
  hakem ağacını klonun commit'inden okur, çalışma ağacından değil; profil düzenli dosyada tek JSON nesnesidir.
- 2.2 (2026-11-01, E470–E475; dördüncü şüphecinin bulgusu; sahibin yetkisiyle mimari karar): `25a` 1–2 içe aktarmayı
  git nesneleriyle anlatır: hakem reposu çıplak klonlanır, yeni `main` pinli `referee/` ağacı ile `main`'den tam adıyla
  alınan korunanlardan kurulur, her ad nesne yazılmadan denetlenir (`26c`, sonda nokta ya da boşluk, aygıt adı, `~` ve
  rakam, korunanın harf varyantı, harf duyarsız tek ad), sayaç satırı aynı commit'tedir, oyuncak ve hakem zorlamadan
  itilir; çalışma ağacı yoktur. `26d`: `stage-open` klonun commit'indeki hakem ağacını ve genesis'in ağaç ve sonuç
  hash'lerini aktarım satırına bağlar, kopyanın tabanı vardır, profil okunabilir olmalıdır, kaydın verisinin hash'i
  kökün kendisidir; `26a` `rekor.anchor` bunu söyler.
- 2.2 (2026-11-01, E411–E417; üçüncü şüphecinin bulgusu): `26d`'ye olgular: son kökün Sigstore paketi döngünündür ve
  kök satırının yanında, aynı `brain/state` commit'inde `<state_root>/chain/<kök>.sigstore.json`'dadır (`stage-open`
  oradan okur; `27a`); `<state_root>` `01a`'nın `.brain/`'idir, başka bir `state_root` tohum dönemi ister (E417, sahibin
  yetkisiyle operatör kararı); zincirli satırın kuralları (son satır da LF ile biter,
  CR yok, anahtar iki kez yok); kök Rekor v1 `hashedrekord`'dur (`sigstore` 4.5.0 `sign --rekor-version 1`; bayraksız en
  yüksek sürüm, v2). Genesis satırı `events`, `kind: genesis`, hakemin kendi satırı; (B)'nin koştuğu genesis defterin
  son genesis'idir ve kural yalnız ondan sonrakileri sayar: yeniden aktarım kilidi kapatmaz (`25a` "Başarısızlık").
  Öneri, `proposed_by`'ı boş olmayan dizgi olan satırdır. `00b`: `26c` ve `26d` üç görevde okunur. 80 satır sınırı için
  2026-10-31'in dört kaydı daha `CHANGELOG-3.md`'ye taşındı (`main`'le birleşince orada).
