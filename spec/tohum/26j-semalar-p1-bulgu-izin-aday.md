# Şemalar, Devam: P1'in Bulgu Yazıcısı, İzin Listesi ve Aday Yolu

Tarih: 2026-11-21 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: P1'in MF8–MF12'si yazılırken ve bir aday paketi, bulgu ya da `accept` satırı okunurken
Çapa: beklemede: P1 aktarımı — `findings.jsonl`, `unresolved.jsonl`, `accept` satırları, `candidates/<id>/package.json`

---

`26h`'nin devamı. Arayüz olgularıdır; kodun nasıl yazılacağı Kurucu'nundur. `referee/` yalnız partilerle değişir ve P1
ile Aşama 1'in MF1, MF5, MF6'sı arasında parti yoktur: o ilk okuyucuların hakemden istediği her şey P1'dedir.

**Bulgu yazıcısı, MF8** (bağımsız inceleme ekibi kararı (2026-11-21), seed-086).
- **Kök.** `13`'ün kökü aynı kalır; `tips`'e satırı olan her zincirli durum dosyası için bir anahtar eklenir: anahtar
  dosyanın adıdır (`findings.jsonl`, `unresolved.jsonl`), değeri son satırının saklı `row_hash`'idir. Olmayan ya da
  satırsız dosya anahtar eklemez: `29j`'nin vektörleri ve bugünkü her kök değişmez. Vektörü MF8'in `root_files`
  grubudur (`29zb`).
- **Kurulduğu gibi benimsenenler.** `unresolved.jsonl` satırı `{finding_id, fingerprint, cause, reasons, snapshot_id}`
  ve zincir alanları; `normalize` her Unicode boşluk dizisini tek boşluk yapar ve uçları kırpar, büyük-küçük harf ve
  noktalama kalır; `finding_id` `f-` ve parmak izidir; sembolsüz parmak izi her zaman dosyayı kullanır; üç `reopened`
  bulgunun bütün ömrü üzerinden sayılır; Aşama 1'de `blocked` son durumdur.
- **Kararlar.** `unresolved` satırının `snapshot_id`'si kararın verildiği tabandır. Son satırı `unresolved` olan bulgu
  başka bir tabanda gözlenince bir `open` satırıyla yeniden açılır (`reopened` sayılmaz); aynı tabanda hiçbir şey
  yazılmaz. Bir dosyanın eşit iki satırı aynı kuralı çiğniyorsa tek bulgudur. Bilinmeyen bir bulguyu adlandıran
  karar o adayın reddidir, devrin değil. Durumların yazıcıları `26k`'dedir (seed-088).
- **Kap.** Önerinin kabı organın çıktı listesidir: koşu sonuçlarında (`results`) tutulur, `yaz` onu hash'iyle okur (`26p`).
  `proposed_by` hakemin o çağrıya dair kendi kaydındaki organ kimliğidir, listenin bir alanı değildir.
- **Bitti.** MF8, `yaz`'a bağlandığında ve her canlı devirde boş girdiyle koştuğunda biter; ilk gerçek girdi Aşama 1
  MF1'dir.

**İzin listesi, MF9** (bağımsız inceleme ekibi kararı (2026-11-21), seed-087).
- **Paket.** Çalışma-zamanı adayı `koş`un çıktı ağacında `candidates/<id>/package.json`'dur, `26a`'nın dört anahtarıyla
  (`finding`, `diff`, `organ_ids`, `definition_sha256`). Kapı yalnız `organ_ids`'i okur.
- **Hazır adaylar.** Aşama 0'ın hazır adayları P1'in aktarımıyla biter: organ adlandırmayan aday `no_organ` ile
  reddedilir. Etkinleştirme (genesis) devri Aşama 0'ın kuralını korur.
- **Giriş.** P1'de hiçbir organ girmez. Giriş tetiği hakem kodu değil veridir: önyükleme hakeminin kabul ettiği beyin
  SHA'sında commit'lenmiş bir organ beyanı, giriş isteği `{organ_ids}`; ilk kullanımı Aşama 1 MF6'dır.
- **Satır.** `evidence_run_ids`, `yaz`'ın dayandığı imzalı sonucun önyükleme koşusunun kimliğidir, tek elemanlı liste.
  Liste `(organ_id, definition_sha256)` çiftiyle anahtarlanır. Aşama 1'de listeden çıkaran satır yoktur (gevşetme L1,
  seed-087). `accept` satır türü P1'den defter şemasındadır.
- **Bitti.** MF9, kuralları ve bağlantısı kanıtlandığında ve ret canlı koştuğunda biter; ilk gerçek `accept` satırı
  Aşama 1 MF5/MF6'dadır. seed-087'nin kalanları sayfanın sonundadır.

**Kapalı kapının reddi** (seed-085 j; sahip kararı (2026-11-21), gevşetme L-j). Bütün nedenleri duran nedenlerden olan
ret (`frozen:<trigger>`, `merge_paused`, `sentinel_pending`, `no_organ`, `organ_unknown:<id>`, `organ_not_listed:<id>`)
`cause` taşımaz, `unresolved` satırı yazmaz ve bulgusunu olduğu durumda bırakır. Başka bir nedeni olan ret `cause`'unu
o nedenlerden alır.

**P1'in üç yeni satırı** (operatörün tablo düzeltmesi, sahip onayı (2026-11-21): seed-086 ve seed-087'yi yanıtlayan iki
inceleyicinin bulduğu eksiktir, Kurucu'nun bir raporundan gelmez). Çalışma-zamanı aday yolunun hakem tarafı P1'in
çıkışından öncedir: Aşama 1 MF1, MF5 ve MF6 hakem değişikliği olmadan canlı koşar. MF1–MF9'un numaraları değişmez.
- **MF10, organ çıktısının tutulması** (modül `runner/organ_output.py`; test 56). `koş` bir organın çıktısını koşu
  sonuçlarında tutar. Test 56: organın çıktısı sonuçlarda hash'iyle durur ve `yaz` onu o hash'le okur; bir baytı
  değişmiş çıktı okunmaz. Çıktının biçimi ve tutma kuralı `26p`'dedir (seed-098).
- **MF11, çalışma-zamanı adayının yeniden koşusu** (modül `runner/candidate_rerun.py`; test 57). `koş` bir
  çalışma-zamanı adayını kapıdan önce yeniden koşar (`26a`: hakem hiçbir adaya yeniden koşturmadan güvenmez). Test 57:
  aday hazır aday gibi koşar (üç lint koşusu, test koşusu, kırmızı kontrol); yeniden koşusu olmayan aday kapıya ulaşmaz. Ayrıntısı `26p`'dedir.
- **MF12, `yaz`'ın aday okuması** (modül `loop/candidates.py`; test 58). `yaz` `candidates/<id>/`'yi sonuçlardan
  hash'iyle okur. Test 58: `organ_ids` kapıya, `finding` bulgu yazıcısına gider; biçimsiz paket yalnız o adayı reddeder.
  MF12'nin sözleşmeleri T1 ve T2 `26k`'dedir (seed-088).
Testler §0.9'un numaralarının devamıdır (`26e`). `26e`'nin tablosu ve `stages/stage1-P1.json` bu üç satırı taşır.

**Modül adı** (`26e`'nin kuralı). Modülün ilk adı (paketi ya da `.py`'siz dosyası) Python'un standart kütüphanesinde bir
modülün adı olamaz (`sys.stdlib_module_names`; `profile/` varken `import cProfile` düşer): böyle satırı olan tablo
yüklenmez. Hakem komutu `referee/`'yi `sys.path`'te önde koşar; Aşama 0'ın donmuş `profile`'ı o tablo yeniden açılana
kadar kalır ve hakemin hiçbir komutu `cProfile`'ı çağırmaz (`26e`).

**İzin listesi, MF9: seed-087'nin kalanları** (rapor masası uzlaşısı (2026-11-22), operatör kararı, sahibin yetkisiyle).
- **(i) Giriş isteği** beyin kökünde `accept.json`'dur (yalnız bir organ girerken): tam olarak `{organ_ids: [farklı, boş
  olmayan dizgiler]}` taşıyan düz bir dosya; başka biçim `accept_invalid`, o SHA'da tanımı olmayan kimlik
  `accept_unknown:<id>` ile reddedilir. Onu Kurucu commit'ler; kayıt da istek dosyası da değildir, onu değiştiren push kod
  isteğidir (`29b`). Yalnız kabul edilmiş SHA'dan etki eder; girmiş `(organ_id, definition_sha256)` çifti için bir şey
  yazmaz. Önyükleme hakeminin kabul ettiği hiçbir SHA döngünün reddedeceği bir `accept.json` taşımaz.
- **(ii) Koşu kimliği.** Önyükleme hakeminin imzalı sonucu `run: {id, attempt}` taşır, ikisi de ondalık rakam dizgisi
  (Actions koşusu ve denemesi); `evidence_run_ids` `[run.id]`'dir. `run.id`'si olmayan, boş ya da yalnız rakam olmayan
  (`local`) sonuç `accept` satırına dayanak olamaz: giriş isteği bir organ adlandırıyorsa devir kullanılamaz.
- **(iii)** P1'de merge, nöbetçi, geri alma, tatbikat ve PASS yolları canlı olarak yalnız genesis merge'ünden koşar. Merge
  mekaniğinin testleri gerçek bir `accept` satırı ve gerçek bir tanımla kurulan açık kapının arkasında durabilir; bu yer
  tutucu yalnız testlerdedir, canlı yoldan ulaşılamaz. **(g)** Listelenmiş çift sonraki SHA'larda listede kalır (L1). **(h)** Kapının tanımları kabul edilmiş SHA'daki organlardır (`26a`).
- **(iv)** `accept.json` için aşama koruması yoktur: P1 çıkış dönemine ertelendi, seed-073'ün (a), (c), (d)'siyle (organ
  dosya düzeni, `pulled`'a taşınma, organın imajı); o zamana kadar Kurucu'nun okuması geçerlidir.
