# Şemalar, Devam: Gözcü'nün Satırları ve Görünümleri

Tarih: 2026-11-21 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Gözcü (P1 MF7) yazılırken, bir `freeze` satırı okunurken ve kapı bir dondurmayı okurken
Çapa: beklemede: P1 aktarımı (Gözcü) — `<state_root>/ledger.jsonl`'un `part: freeze` satırları

---

`26`'nın devamı (bağımsız inceleme ekibi kararı (2026-11-21), seed-084, seed-085). Arayüz olgularıdır; kodun nasıl
yazılacağı Kurucu'nundur. Kuralların kendisi `28` ve `28a`'dadır. `freeze` ve `lift` satırının biçimi Kurucu'nun P1
MF7'de kurduğu biçimdir (seed-085 a); tohum onu benimser.

**`freeze` satırları.** Sunulan hedefin `<state_root>/ledger.jsonl`'unda `part: freeze`'dir (`26`); onları hakem,
`yaz`'ın devir sonu çağrısıyla, devrin tek `brain/state` commit'inde yazar (`26a` `gozcu.evaluate`). Alanları her
defter satırınınkidir (`26`). Üç tür:
- `kind: freeze`, `payload {trigger, scope, measurement, start}`. `trigger` ∈ {`regression`, `containment`,
  `budget_usd`, `budget_ci_minutes`}. `scope` boş olmayan, sıralı ve tekrarsız bir ad listesidir; ad bir sınıf
  kimliği (`K0`–`K8`) ya da `loop`'tur. `measurement` sayımların (JSON tamsayıları) nesnesidir; kayan nokta yoktur
  (`26` "Sayılar"). `start` dondurmanın başlangıcıdır (`28` "Kayıt": tetik, kapsam, ölçüm, başlangıç), bir `ts`.
- `kind: lift`, `payload {trigger, scope, start}`: kaldırdığı dondurmanın bu üç alanı; kalkışın zamanı satırın
  `ts`'sidir. Üçü bir dondurmayı tek başına adlandırır (bir tetik bir devirde en çok bir dondurma başlatır). Kalkış o
  dondurmanın bütün kapsamını bitirir; hiçbir `lift` satırının adlandırmadığı dondurma yürürlüktedir. Önünde
  yürürlükte bir dondurma adlandırmayan `lift` satırı kırık bir durumdur.
- `kind: hard_stop`, `payload {trigger, evidence}` (seed-085 h). `trigger` ∈ {`soft_freeze_limit`, `drift`,
  `chain_break`, `rekor`, `attestation`, `activation`, `ref_change`, `kill_switch`}; `evidence` boş olmayan bir dizgi
  listesidir. Sert duruşun kalkışı döngü dışı bir operatör işidir (`28`): döngü bir sert duruş için `lift` satırı yazmaz.

`01c`'nin ve `13`'ün durma satırı `hard_stop`'tur: `drift.check` yalnız okur ve hiçbir şey yazmaz, duruşu Gözcü yazar.
Etkinlik API'sinin aykırı girdileri için `trigger` `ref_change`'tir ve kanıt o girdileri adlandırır; `drift.check`'in
öbür nedenleri için `drift`'tir.

**Kapsamın okunuşu** (`27a` "Merge kapanır"). Yürürlükteki bir dondurmanın kapsamında bir sınıf varsa kapı o sınıfın
adayını merge etmez. Kapsamda `loop` varsa hiçbir merge yapılmaz; hakemin okuma işleri sürer (`28`). Regresyon
dondurmasının kapsamı sayılan geri almaların sınıflarıdır, bütçe dondurmasınınki `loop`'tur. Aşama 1'de tek sınıf
K0'dır.

**Görünümler.** Gözcü'nün okuduğu her görünüm sunulan hedefin defter satırlarından kurulur (`26`):
- merge'ler `events`/`merge` satırlarıdır, geri almalar `events`/`revert` satırlarıdır. Yalnız sıradan bir
  `events`/`merge` satırının geri alınması sayılır: `drill`/`plant` satırı ve bir `plant` satırının adlandırdığı
  merge'ün geri alınması provanındır (`29m`) ve hiçbir görünümde sayılmaz (seed-085 i).
- harcama, bu hedefin defterinde `ts`'si `now`'ın UTC takvim ayında olan `cost` satırlarının `usd_micros`
  toplamıdır; birden çok hedefte ayın harcamasının nerede toplandığı yanıtsızdır (seed-085 c).
- dondurmalar `freeze` bölümünün kendi satırlarıdır.
- sert duruş olguları defter satırı değildir: döngünün kendi çağrılarının bu devirde bulduklarıdır.
- Actions dakikası, kapsayıcılık ihlali, eşik değişikliği, koltuk benzerliği ve genesis taslağı Aşama 1'de ölçülmez:
  hiçbir bölümün satırı onları kaydetmez ve üreticileri sonraki aşamalardadır (`08`, `18`, `09a`, `12`, `28a` L2).
  Görünümleri boştur, kuralları yine yargılanır ve devrin çıktısı onları ölçülmemiş olarak adlandırır (seed-085 d, e).
