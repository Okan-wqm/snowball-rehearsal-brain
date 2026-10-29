# Şemalar ve Kanonik Biçimler: Defter, Bulgu, Vaka, Koşu

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 inşasında ve her şema değişikliğinde
Çapa: beklemede: aşama 0 — hakem reposundaki schemas/

---

Alanların tek kaynağı bu sayfa ve `26b`'dir; başka sayfa alan adı tanımlamaz, buraya atıf yapar.
Hepsi JSON Schema olarak hakem reposunda `schemas/` altındadır; harness her artefaktı şemaya
karşı doğrular. Alan adları İngilizce. Araç imzaları `26a`'da. Şema hakem kodudur: yeni alan ya
da yeni kategori önerisini genesis değil şerit yazarı yapar (`09a`).

**Bölüm → dosya.** Her durum dosyası yalnız sonuna eklenen, zincirli JSONL'dir; kök hash hepsini kapsar.

| Bölüm (`part`) | Dosya | Yazar | Açılış |
|---|---|---|---|
| `founder` | beyin reposunda `founder-ledger.jsonl` | Kurucu | Aşama 0 |
| `events`, `cost`, `freeze`, `rival`, `accept` | `<state_root>/ledger.jsonl` | Hakem işleri | Etkinleştirme |
| `looks` | `<state_root>/ledger.jsonl` | Hakem exit işi | İlk held-out havuzu |
| `drill` | `<state_root>/ledger.jsonl` | Hakem `exit.drill` işi | İlk prova (`18`, `22a`, `12a`) |
| — (bulgu satırları) | `<state_root>/findings.jsonl` | Hakem, adapter önerisinden | Etkinleştirme |
| — (unresolved satırları) | `<state_root>/unresolved.jsonl` | Hakem kapısı | Aşama 1 |
| — (kökler) | `<state_root>/chain/root.jsonl` | Hakem `yaz` işi | Etkinleştirme |

**ledger row** (tüm bölümler): `row_id`, `ts`, `part`, `kind`, `payload`, `derivation`, `trust`,
`snapshot_id`, `evidence_refs`, `cause?`, `miss_reason?`, `derived_from?`, `proposed_by?`,
`prev_hash`, `row_hash`. Satırı her zaman hakem yazar; oyuncunun önerdiği içerik `proposed_by`
ile işaretlenir ve `trust: inferred` saklanır. Kanonik biçim RFC 8785; `row_hash =
sha256(canonical(row − row_hash) ‖ prev_hash)`, küçük harf onaltılık; ilk satırın `prev_hash`'i
64 sıfır. Vektörler `29a`'da. **Sayılar:** hash'lenen hiçbir artefaktta kayan nokta yoktur;
tamsayı (para `*_micros`, süre `*_ms`) ya da en çok altı ondalıklı sabit ondalık dizgi
(`"0.962400"`) kullanılır. **`founder` satırı:** `kind` ∈ {`session_start`, `decision`, `build`,
`blocked`, `seed_issue`, `cost`, `session_end`}, `payload` `{summary, refs[]}`, `snapshot_id` beyin
reposunun o anki SHA'sı. `findings.jsonl` ve `unresolved.jsonl` satırları da `prev_hash`,
`row_hash` taşır.

**derivation** (kapalı küme): `tool`, `static_analysis`, `test_verified`, `llm_inference`,
`name_similarity`, `imported`. **trust**: `verified`, `observed`, `inferred`. Merge kararına
giren kanıt yalnız ilk üç derivation'dan olabilir.

**cause** (kapalı küme, başarısız ya da geri alınan olayda zorunlu): `test_regression`,
`contract_counterpart`, `build_break`, `lint_regression`, `flaky_dependency`, `conflict_with_main`,
`scope_violation`, `imported_assumption`, `impact_miss`, `unknown`. `impact_miss`: merge sonrası
kırmızının nedeni beyan edilen etki kümesinin dışındadır.

**miss_reason** (kapalı küme, harness kaçırması): `map_edge_missing`, `unseen_file`,
`wrong_property`, `ref_mismatch`, `not_reported`, `unknown`.

**finding**: `finding_id`, `fingerprint`, `state` (`open`|`fixed`|`verified`|`reopened`|
`withdrawn`|`blocked`|`unresolved`), `class_level` (K0–K8), `property`, `file`, `symbol?`,
`tool?`, `rule_id?`, `claim`, `evidence_refs` `[{path, line_start, line_end}]`, `required_change`
`[{file, symbol?, op}]` (`op`: `lint_fix`, `add_guard`, `remove`, `rename`, `change_type`, `move`,
`add_test`, `doc_fix`, `other`; sınıf başına izinli küme `policy.json`'da; `doc_fix` yalnız K8),
`severity_hint`, `confidence`, `derivation`, `trust`, `snapshot_id`. Şiddet avcıdan gelmez,
`severity_hint` yalnız ipucudur. `confidence`'in okuyucusu panelin faz sıralamasıdır.

**case**: `case_id`, `class_level`, `property`, `provenance` (`human_fix`|`mutation`|
`system_tp`|`system_regression`), `base_sha`, `fix_sha?`, `mutation_id?`, `touched_paths`
`[{path, hunks:[{start,end}], symbol?}]`, `tool?`, `rule_id?` (K0–K2'de ikisi zorunlu), `validity_evidence` `{kind, ref,
output_sha256}`, `split` (`dev`|`exit`|`heldout`), `group`.

**run_meta**: `run_id`, `subject_run_id?`, `organ_id`, `role`, `model_requested`,
`model_served`, `effort`, `prompt_sha256`, `rung`, `snapshot_id`, `tokens_in`, `tokens_out`,
`cost_usd`, `wall_clock_s`, `files_read`, `lessons_injected`, `imported_used`,
`previous_run_ref` (boş), `containment` `{paths_written[], commands[], network_attempts[],
declared_exits[]}`. Model, token ve maliyet alanlarını `çağır` işi ya da sağlayıcı geçidi
ölçer; `files_read` ve `containment`'ın ilk üç alanını `run.contained` ölçer; `lessons_injected`
ve `imported_used`'ı dispatcher yazar. Ajanın yazdığı tek alan `declared_exits`'tir.

**rival payload** (`part: rival`): `{subject_sha, verdict: refuted|not_refuted|unresolved,
attempts:[{claim, evidence_refs, reproducer?}], reproduced}`. `reproduced` hakemin yeniden
üreticiyi `koş`ta koşturmasının sonucudur; yalnız `reproduced: true` çürütmedir.

**drill payload** (`part: drill`): `{drill: lesson|revert|context|genesis, question, family,
instance_id, arm?: with|without, commitment_sha256, revealed_sha256?, outcome, verdict}`.
Taahhüt koşudan önce, açılım koşudan sonra yazılır; eşleşmezse prova `FAIL`'dır. Prova dosyası `29c`'de.

Diğer şemalar (ders, bilgi, öneri, harita, organ, itibar, rapor, profil, politika, test-yazıcı,
bakış, mühür, sözleşme) `26b`'dedir.
