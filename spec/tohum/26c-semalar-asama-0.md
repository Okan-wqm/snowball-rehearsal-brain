# Şemalar, Devam: Aşama 0'ın Dosyaları

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 inşasında, kurulumda ve operatör dosyası yazılırken
Çapa: beklemede: aşama 0 — hakem reposundaki schemas/; `seed/bootstrap/stages/stage0.json`

---

`26` ve `26b`'nin devamıdır; aynı kurallar geçerlidir. Operatör dosyalarında **eksik ya da bilinmeyen
alan kapalıya düşer**: okuyucu en kısıtlayıcı değeri varsayar ve operatörü uyarır.

**snowball-tests.json** (beyin kökü): `{tests: [{id, cmd, stage}], done_mf: [], lockfiles: []}`; `id`
§0.9 test numarasıdır (`T13`); `cmd` repo kökünden koşar. `done_mf` geçerli aşamanın tablosuna göre
bitmiş MF'lerin 1'den kesintisiz önekidir. **exit-request.json** (kök): `{stage, sha, spec_sha256}`;
`sha` son kabul edilmiş commit, `spec_sha256` donmuş aşama dizininin hash'idir; yalnız bu dosyayı
değiştiren push çıkış isteğidir; reddedilmiş bir istekle bayt bayt aynı dosya sonraki kod push'larında yok
sayılır (`29b`, `asama-0/10`). Parti isteği aynı biçimdedir, `batch` alanıyla.

**Aşama tablosu** (tohumda `seed/bootstrap/stages/stage0.json`; `asama-0/14`'ün makine kopyası):
`{stage, mfs: [{mf, tests[], groups[], module, calls[]}]}`. `module` `referee/` altındaki yoldur
(modülsüz kırmızı onu siler); `calls` çağrılan MF'lerdir ve her biri çağırandan küçüktür. Önyükleme
hakemi `done_mf`'in anlamını, test bildirimini, vektör gruplarının ne zaman koştuğunu, modülsüz kırmızıyı
ve çıkıştaki MF sayısını buradan okur. Partilerin tabloları aynı dizindedir (`asama-1/13`).

**control.json** (hakem reposu): `{kill_switch, budget_state, oauth_token_expires, loop_schedule,
merge_paused, founder_resume?}`. Kapalıya düşüş: `kill_switch` eksikse açık; `budget_state` (`ok` ya da
frene takılan kalem) eksikse fren; `loop_schedule` eksikse `false` (zamanlanmış devir `paused` ile yeşil
biter); `merge_paused` eksikse `true` (gözlem sürer, merge yok); `founder_resume {after_run, note}`
yalnız adlandırdığı koşudan sonra bir kez geçerlidir (`24a`).

**setup/summary.json** (`25`'in alanlarına ek): `seed_epochs[]` `{commit, spec_tohum_sha256, seed_sha256,
bootstrap_sha256}`; `targets[]` `{id, repo, kind: toy|copy, base_sha, identifiers[], excluded_paths[],
unit_candidates[]}` (`identifiers` genellik denetiminin ad listesidir; `excluded_paths` operatör verisidir,
hakem kodu değildir; `unit_candidates` kopyanın aday birim yolları, sırayla); `honesty_commitment`
(`sha256(canonical(anahtar))`); ekim kaçırıldıysa sahibin `honesty_exception` `{stage: 0, carry_to: 1, reason}`'ı
(`02` "Sahip istisnası"; yanındaki taahhüt taşıma hedefinin ekimidir, o olmadan istisna koşulu kaldırmaz); ilk
koşu işareti.

**setup/imports.jsonl**: her aktarım bir satır `{ts, stage, batch?, brain_sha, referee_tree_sha256,
result_sha256, toy_tree_sha256?}`, zincirli (`26`); insan dokunuşu sayacı. **setup/stage.json**:
`{stage, pass_row_sha256, toy_state_head, copy_state_head, import_line_sha256}`; `stage-open` yazar,
operatör iter (`asama-0/10a`). **setup/honesty-key.json**: ekim kimlikleri, tespit yüklemleri, kardeş
girdi; çıkışta operatör ekler.

**reports/*.json** (beyin): `{id, kind: seed_issue|referee_weakness|spec_issue, ref, evidence_test?,
state}`. Önyükleme hakemi `pull`'da okur, rakipten gizler, imzalı sonuçta `reports[]` olur ve operatörü
uyarır; bir vektörü adlandıran `seed_issue` onu `disputed` yapar (en çok iki açık itiraz). Spec ve tohum
sorunlarını operatör tohum dönemiyle kapatır, Kurucu teyit eder.

**Hazır aday** (`candidates/<hedef>/<cid>/`, beyin): `finding.json` `{rule_id, path, line, fix_range,
tool_output_sha256}` (hakemin yayımladığı araç çıktısından); `diff.patch` (birleşik diff, yalnız düz
dosya); `expect.json` `{decision: merge|reject, reason?}` (kötü adayın beklenen ret nedeni, ör.
`scope_violation`). Hakem `expect.json`'a güvenmez; onu yalnız (B)'nin #ret satırında karşılaştırır.

**Birim tarifi** (beyin `targets/<hedef>/units.json` önerir; doğrulanmışı `profile.json` `units[]`):
`{unit_id, path, inputs[], toolchain, env_image (@sha256), lockfiles[], install_scripts_required[],
lint_cmd[], test_cmd[], affected_test_cmd[], services: [], limits{}}`. `inputs` birimin dizini, kullandığı
ortak kütüphaneler ve kök yapılandırmalardır; yeterliliğinin kanıtı yalnız bu girdilerle HEAD'in 3/3
yeşil koşmasıdır (`unit.verify`). Lint için yeşil: `lint_cmd` üç koşunun her birinde 0 ya da 1 ile biter ve
üç koşunun çıkış kodu ve stdout'u bayt bayt aynıdır (ESLint'te 1 bulunan ihlaldir; `asama-0/08` ölçüt 5 ihlal
ister, ölçüt 6 yeşil). `toolchain` `node@X.Y.Z`'dir: kesin sürüm (üç ondalık bileşen; aralık ya da `lts` gibi
takma ad değil), birimin en yakın sürüm dosyasındaki sürüm. İmaj resmi araç zinciri imajıdır, etiketindeki
sürüm de `X.Y.Z`'dir. `install_scripts_required[]`'in her elemanı kilitteki tam paket yolu (kök `""` dışında
bir `packages` anahtarı, ör. `node_modules/x`) ya da `ad@sürüm`'dür; `ad@sürüm` tarball'ının adı ve sürümü
eşleşen paketi işaretler, kilitte eşleşeni yoksa hiçbir şeyi. Başka bir eleman, ör. çıplak ad (her sürümü
işaretlerdi) ya da kilitte olmayan bir yol, işaret değildir ve isteği kullanılamaz yapar: `deps.fetch` onu
reddeder (çıkış 2, `29g`).
`services` Aşama 0'da boştur. Önerinin hariç yolları ya da güvenlik yollarını daraltması reddedilir.

**policy.json `operating{}`**: `{key: {value, band: [min, max]}}`; anahtarlar `unit_inputs_bytes`,
`deps_bytes`, `worktree_bytes`, `container_mem_bytes`, `kos_wall_s`, `test_total_s`, `output_bytes`.
Döngünün karşılaştırdığı her sınır buradadır, sabit yoktur; bandı operatör yazar (`18a`). Sınıra takılan
iş `limit_hit:<anahtar>`'dır, Kurucu'ya sayılmaz, `status.md`'de görünür. Aşama 0'da değer kendini
ayarlamaz; bant içinde ayar P1'le gelir.

**status-stage0.md** (önyükleme hakeminin her koşusunun yüklediği adım özeti): son kabul ve son
değerlendirilen SHA, park, seriler, frenlere karşı harcama, belirteç süresi, son kararlar, açık
bildirimler; Kurucu oturum sayısı ve USD (ölçüm, kapı değil).
