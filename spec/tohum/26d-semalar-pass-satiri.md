# Şemalar, Devam: Aşama 0'ın PASS Satırı ve Kilidin Açılışı

Tarih: 2026-11-01 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0'ın (B) devirlerini ve genesis, merge, PASS ve kök satırlarını yazan kod yazılırken; kilidin açılışından önce
Çapa: beklemede: aşama 0 — oyuncağın `brain/state`'indeki PASS satırı; `setup/stage.json`

---

`26`, `26b` ve `26c`'nin devamıdır; aynı kurallar geçerlidir. PASS satırını döngü hakemi yazar (`asama-0/10a` #pass,
`asama-0/08` devir 9); operatörün `stage-open` komutu onu okur ve `setup/stage.json`'u yalnız aşağıdaki kural tutarsa
yazar (`25a` 9, `02` 5). Bu sayfa `asama-0/10a`'nın PASS satırını alan alan söyler; aşama sayfası tohumla çelişirse
tohum geçerlidir (`02` 1).

**Yer.** `<state_root>` `01a`'nın adlandırdığı dizindir: hedefin `brain/state` commit'inin kökündeki `.brain/` (E58'in tek
klasörü). `stage-open` `.brain/ledger.jsonl`'u, `.brain/chain/root.jsonl`'u ve son kökün Sigstore paketi
`.brain/chain/<kök>.sigstore.json`'u (`<kök>` son kök satırının `root`'u) aynı commit'te, düzenli dosya olarak okur. Paketi
döngü yazar ve kök satırının yanında tutar; operatör paket vermez. `26b` profilinin `state_root`'u bugün yalnız `.brain/`
olabilir: commit'te başka bir dizin adlandıran profil `stage-open`'ı adıyla durdurur; başka bir dizin tohum dönemi ister.
Her `profile.json` tek düz JSON nesnesi olan düzenli dosyadır (BOM, çift anahtar yok); okunamayan profil de durdurur.

**Zincirli dosya** (`ledger.jsonl`, `chain/root.jsonl`, `setup/imports.jsonl`). Her satır, sonuncusu da, LF ile biter;
CR yoktur; satır tek bir JSON nesnesidir, hiçbir anahtar iki kez geçmez, `NaN` ve `Infinity` yoktur; `row_hash` `26`'nın
kuralıyla, `prev_hash` önceki satırın `row_hash`'i (ilk satırda 64 sıfır). Bir satırın hash'i LF'siz baytlarınınkidir.

**Öneri ve hakemin kendi satırı.** `proposed_by`'ı boş olmayan bir dizgi olan satır oyuncunun önerisidir (`26`) ve hiçbir
sayıma girmez. Hakemin kendi satırı `proposed_by` taşımaz (`proposed_by: null` taşıyan satır öneri değildir, sayılır ve
hakemin kendi satırı olmadığı için durdurur); `trust` `verified` ya da `observed`'dır (`inferred` oyuncunun önerisinin
saklandığı değerdir, `26`); `derivation` `tool`, `static_analysis` ya da `test_verified`'dır (`26`: merge kararına giren
kanıtın üçü). Genesis, merge ve PASS satırları hakemin kendi satırlarıdır, `part: events`:
- **Genesis satırı**: `kind: genesis` (`29n`'nin okuduğu tür); `payload`'ı `29o`'nun yüküdür (`target`, `base_sha`, …).
  Defterin ilk satırı o hedefin genesis'idir (`25a` 7). `25a` 3 `brain/state`'i silinmez ve yeniden yazılamaz kılar: (B)
  kırmızı olunca operatör aktarımı geri alıp düzeltilmiş SHA'yı aktarırsa (`asama-0/10a` "Başarısızlık") ve dal
  silinmezse ilk genesis yerinde kalır, (B) iki hedefte yeni aktarım satırını adlandıran yeni bir genesis satırıyla
  yeniden koşar. (B)'nin koştuğu genesis defterin son genesis satırıdır; aşağıdaki kural yalnız ondan sonrakileri sayar.
- **Merge satırı**: `kind: merge`; `payload`'ı serbesttir.
- **PASS satırı**: oyuncak defterinde; `kind` serbesttir. `payload` bir nesnedir ve şu alanları taşır (başka alan da
  taşıyabilir):
  - `stage`: tamsayı `0` (mantıksal değer değil); `verdict`: dizgi `"PASS"` (`19`).
  - `import_line_sha256`: 64 küçük onaltılık; PASS yazıldığında `setup/imports.jsonl`'un son aktarım satırının
    (`referee_tree_sha256` taşıyan son satır, `29n`) LF'siz baytlarının sha256'sı; genesis yükündeki aynı adlı alanın
    kuralı (`29o`). Güven kökünün operatör aktarımıdır (`10a` #pass).
  - `copy_genesis_row_hash`: 64 küçük onaltılık; kopya defterinin son genesis satırının `row_hash`'i.
  - `copy_merge_row_hashes`: dizgi dizisi, en az bir eleman, her biri bir kez; her eleman kopya defterinde son
    genesis'ten sonra gelen bir merge satırının `row_hash`'i.
  - `owner_exception`: (A) sonucunun `exit.owner_exception` nesnesi aynen, `{anchor, stage, carry_to, reason,
    carry_commitment, measured}` (`02` "Sahip istisnası"; `anchor` `#`'siz yazılır: `durustluk`). (A) sonucunda yoksa
    PASS satırında da yoktur.

**Kök.** Kök satırının Rekor kaydı (`13`, `29j`) bir Rekor v1 `hashedrekord`'dur: gövdesi `apiVersion` `0.0.1`,
`spec.data.hash`'i `{algorithm: sha256, value: <kök>}`; verinin hash'i kökün kendisidir, zincirin verdiği sha256 (uçların
RFC 8785 baytlarınınki), onun bir özeti değil. Tohumun sabitlediği `sigstore==4.5.0`'ın `sign`'ı `--rekor-version`
verilmezse TUF imza yapılandırmasının listelediği en yüksek sürümü seçer (v2: `hashedrekord` `0.0.2`); v2 gövdesi bu değildir.

**`stage-open`'ın kuralı.** Komut iki hedefin `brain/state` başını operatörün yerel klonunda okur, iki defterin ve iki
kök zincirinin her satırını tohumun koduyla doğrular ve şunları denetler; biri tutmazsa nedeni adlandırıp durur (çıkış
2) ve hiçbir şey yazmaz:
1. Sayaç, `setup/summary.json` ve hakem ağacı `--referee` klonunun commit'inden okunur, çalışma ağacından değil. Sayacın
   son aktarım satırı Aşama 0'ındır; `--result` o satırın `result_sha256`'sının adlandırdığı imzalı (A) sonucudur;
   `--referee` klonunun commit'indeki hakem ağacı (korunanlar hariç, git'ten `26c`'nin hash'i) o satırınkidir.
2. Her hedef defterinin ilk satırı o hedefin genesis satırıdır; son genesis satırının `payload.target`'ı
   `setup/summary.json` `targets[]`'taki o hedefin `id`'si (bir oyuncak, bir kopya), kopyada `payload.base_sha` o
   satırın `base_sha`'sı (kopyanın bir tabanı vardır), ikisinde de `payload.import_line_sha256`,
   `payload.referee_tree_sha256` ve `payload.result_sha256` sayacın son aktarım satırınınkidir (`29o`).
3. Öneriler ayrıldıktan sonra oyuncak defterinde son genesis'ten sonra `payload.stage` 0 ve `payload.verdict` `"PASS"`
   olan tam bir `events` satırı vardır; oyuncunun önerdiği bir kopyası sayılmaz.
4. O satır hakemin kendi satırıdır ve oyuncak defterinde son genesis ile onun arasında en az bir merge satırı vardır
   (`asama-0/08`: merge devir 2, PASS devir 9).
5. PASS satırının `import_line_sha256`'sı sayacın son aktarım satırınınkidir. Sonra yazılmış, ya da geri alınıp yerine
   başkası gelmiş bir aktarım bu satırı değiştirir; PASS satırı başka bir aktarımı adlandırıyorsa kilit açılmaz.
   Yeniden aktarımdan sonra kilidi, iki hedefin yeni genesis satırlarından sonra yazılan PASS satırı açar.
6. `copy_genesis_row_hash` verilen kopya klonunun son genesis'inin, `copy_merge_row_hashes` o defterde ondan sonraki
   merge satırlarınındır.
7. `owner_exception` (A) sonucununkiyle RFC 8785 baytlarıyla aynıdır ya da ikisinde de yoktur.
8. Her hedefte son kök satırının `root`'u defterin uçlarının köküdür ve aynı commit'teki paket `--identity` ile
   `sha256:<kök>` özetini doğrular; paketin tek saydamlık kaydının (gövdesi katı base64) yaprak hash'i satırın
   `rekor_uuid`'idir (önünde 16 karakterlik ağaç kimliği olabilir, ardında hiçbir şey olamaz) ve gövdesi yukarıdaki v1
   `hashedrekord`'dur; başka bir tür ya da gövde biçimi (v2 dahil) kilidi açmaz.

Hepsi tutarsa `setup/stage.json` `26c`'deki beş alanla yazılır: `pass_row_sha256` PASS satırının LF'siz baytlarının
sha256'sı, `toy_state_head` ve `copy_state_head` okunan başlar, `import_line_sha256` sayacın son aktarım satırınınki.
