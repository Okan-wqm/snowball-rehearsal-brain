# Değişiklik Günlüğü — Tohum

Tarih: 2026-10-29 · Sürüm: 2.2
Okunma: bir sayfanın geçmişi aranırken
Çapa: git geçmişi ve zincirdeki spec hash satırları

- 2.2 (2026-11-06, E561–E566; sahibin kararı): `02` "Sahip istisnası": #spec de istisna edilir (E286), Aşama 1'in
  (A)'sına taşınır; `26c`: `spec_exception` ve yanında tohumun taşıma kaydının (`stages/carry-spec.json`) hash'i
  `spec_commitment`. Arayüz olgusu (E563): `exit.owner_exception` ve PASS satırının `owner_exception`'ı `anchor`'a göre
  sıralı bir dizidir (`26d:45-47`, denetim 7); çıkış isteği olmayan push'un sonucu değişmez.
- 2.2 (2026-11-06, E560; üç uzmanlı iki turlu çıkış panelinin kararı): `seed/founder/prompt.md` "Çıkış sırası": bir
  aşamanın ya da partinin mikro özellikleri bitince sıradaki iş çıkış isteğidir, koşulların tutup tutmadığını isteğe
  verilen hakem kararı söyler; istekten önce ancak `referee/` kodunun yanlış karar verdiği gerçek bir girdiyi (girdi,
  beklenen, gözlenen) gösteren iş gelir, ölçülmemiş ya da sınanmamış olmak bu kanıt değildir. Kural tek yerdedir,
  tohum sayfaları onu yinelemez. Önceden yanıtlanmış: `seed-046-pass-row-unnamed`'in sonraki düzenlemesi bir ilerleme
  notudur; `26d:36-47`, `10a:44` ve `seed-048-copy-gate-record-and-a-result-bytes`'ın yanıtı (`26d:47`) onu karşılar.
  80 satır sınırı için 2026-11-01 E478–E485 kaydı `CHANGELOG-5.md`'ye taşındı.
- 2.2 (2026-11-05, E550, E551, E553; Kurucu raporları, sahibin kararı): yeni `29e` "Bütçe durması": rakibin bir koşudaki
  payı ayın tavanından ve aşamanın freninden kalanla koşu başı tavanın en küçüğüdür; payı biten ya da çağrısı frene
  takılan baş yargılanmaz (`last_evaluated_sha`, seriler ve rakip hata serisi değişmez), sonuç `budget_stop` ile freni
  ve payı adlandırır, yoklama aynı başı pay büyüyene dek uyarıyla geçer; `29e:26`'nın bütçe istisnası kalktı, `29b`
  oraya bakar. `18a`: rakip freni 2026-11-05'ten Aşama 0'da da Aşama 1'de de 1000 USD'dir (rakip `claude` CLI
  aboneliğiyle koşar, fren yalnız kaçak frenidir; `asama-1/10`), `26e` sayıyı yinelemez. Yanıtlanan raporlar:
  `referee-049-rival-budget-consumes-commit` → `29e:42-53` (bütçe durması; çağrı başı tavan da fren, `per_run`),
  `29e:26` (bütçe rakip tarafı hata değildir), `29b:76-77` (baş tüketilmez), `18a:59` (politika: 1000 USD),
  `29e:53` (bu kuraldan önce yargılanmış sayılan baş yeniden açılmaz); declined (11-03 güncellemesi):
  `seed-044-revert-facts-producers`: ret geçerli (2026-11-01 kaydındaki `declined: seed-044-revert-facts-producers`
  satırı; `29j:53-60`); `asama-0/10a:26` `#geri-alma` Aşama 0'da değişmedi. 80 satır sınırı için 2026-11-02 E506 ve
  E507 kayıtları `CHANGELOG-5.md`'ye taşındı.
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
- 2.2 (2026-11-02, E506, E507): kapsülde defterin salt-okur dizini ve standart kütüphaneyi gizleyen modül adı:
  `CHANGELOG-5.md`.
- 2.2 (2026-11-01, E411–E417, E470–E475, E478–E485): `26d`'nin olguları (son kökün paketi, zincirli satır, Rekor v1,
  genesis satırı), içe aktarmanın git nesneleriyle anlatımı ve `stage-open`'ın bağları: `CHANGELOG-5.md`.
- 2.2 (2026-10-31 – 2026-11-01, E93, E333, E342, E390–E400, E404, E405, E421–E436, E450): önyükleme hakeminin
  çıkıştan sonraki kuralı, imzalı durumun arayüzü, Kurucu raporlarının yanıtları, npm workspaces kilidi, PASS
  satırı, `stage-open`, fiziksel güvenlik ve kapsülün ajan/skill tanımları: `CHANGELOG-4.md`.
- 2.2 (2026-10-30 – 2026-10-31, E64, E65, E249, E280–E301, E308, E317–E324, E338, E339, E341, E344): ders provasının
  aileleri ve sınav tarafı, sistem haritası, Aşama 0 çıkışının karar verilemeyen koşulları, `control`'ün döngü arayüzü,
  sınıf merdiveninin varsayılanlığı, yük altında performans ve `main`'in salt okunur okunuşu: `CHANGELOG-3.md`.
- 2.2 (2026-10-28 – 2026-10-30, E246–E247 ve öncesi): üçüncü inceleme, önyükleme hakeminin yazılışı ve sonraki kararlar: `CHANGELOG-2.md`.
- 2.1 ve öncesi (2026-10-28): `CHANGELOG-1.md`.
