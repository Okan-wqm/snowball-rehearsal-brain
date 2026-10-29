# Şemalar, Devam: Bilgi, Organ, Profil, Politika

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 inşasında ve her şema değişikliğinde
Çapa: beklemede: aşama 0 — hakem reposundaki schemas/

---

`26`'nın devamıdır; aynı kurallar geçerlidir. Bir şemanın varlığı dosyasının açık olduğu anlamına
gelmez: dosya, okuyucusunun karar değiştirebildiği aşamada açılır (`27`).

**lesson**: `lesson_id`, `claim`, `cause`, `scope` `{class_level, property, path_glob,
conditions[]}`, `evidence_refs`, `origin_event`, `origin`, `hit`, `miss`, `withheld_hit`,
`withheld_miss`, `superseded_at?`, `derived_from?`.

**knowledge** (bağlama bağlı bilgi): `knowledge_id`, `claim`, `conditions[]` (kod-yerel,
yürütmeyle sınanabilir yüklemler; önceden kaydedilir), `contexts` `{context_fingerprint: {held,
failed}}` (sayıları hakem kanıtlı defterlerden hesaplar), `domain_bound` (doğruysa repodan
çıkmaz), `status` (`hypothesis`|`verified`|`refuted`|`contradicted_unexplained`), `derivation`,
`trust`, `origin`, `open_questions[]`. Repolar arası yalnız tipli alanlar taşınır; `claim` serbest
metni taşınmaz.

**proposal** (tasarım önerisi): `proposal_id`, `origin` (`repo_pattern`|`llm_prior`|`synthesis`|
`own_outcome`), `source_context?`, `alternatives` `[{origin, refs[]}]` (karşı koltuğun en az bir
referanslı alternatifi), `applicability_conditions[]`, `measured_benefit?` `{metric, delta,
run_ids[]}`, `state`. Hayatta kalma `origin` ve koşul başına ölçülür.

**map edge**: `edge_id`, `layer` (a|b|c|d), `from`, `to`, `kind`, `evidence_refs`, `derivation`,
`trust`, `snapshot_id`, `stale`. **coverage** bir görünümdür, dosya değildir: `path`, `fate`
(`seen`|`unseen`|`coarse`|`excluded`), `by_rungs[]`, `snapshot_id`.

**organ registry**: `organ_id`, `kind`, `state` (`DRAFT`|`SHADOW`|`ACTIVE`|`DEGRADED`|`RETIRED`),
`born_from` `{signal, measurement}`, `definition_sha256`, `prompt_sha256?`, `model`, `tools[]`,
`derived_from?`, `transition_evidence`. **accept** satırı (`part: accept`): `{organ_id,
definition_sha256, brain_sha, evidence_run_ids[]}`; kapının izin listesi bu satırlardan kurulur.

**reputation** (görünüm): `organ_id`, `window`, `class_level`, `rung`, `survived`, `failed`,
`beta_lower_bound`, `mean_net_value`, `rank_score` (= alt sınır × karar başına ortalama net
değer), `usd`.

**harness report**: `run_id`, `snapshot_id`, `spec_version`, `match_rule_version`, `hunter_id`,
`prompt_sha256`, `rung`, `n`, `n_groups`, `x_eff`, `recall`, `recall_lb`, `precision`,
`precision_lb`, `census` `{rules_total, rules_covered, misses}`, `clean_findings`, `unresolved`,
`cost_usd`, `value_per_usd`, `verdict`.

**profile.json**: `mode` (`write`|`training`), `languages{}`, `toolchains{lang: {lint[],
typecheck[], test[], format[], build[], coverage[]}}`, `affected_test_cmd`, `graph_cmd`,
`graph_granularity`, `test_path_rules[]`, `doc_paths[]`, `banned_constructs{lang: []}`,
`rule_property_map{tool: {rule_id: property}}`, `finding_id_patterns[]`, `security_paths[]`,
`excluded_dirs[]`, `registry_egress[]`, `install_scripts_required[]`, `ci_system`, `runner`,
`state_root`, `domain_lexicon[]`, `context_fingerprint`, `units[]` (doğrulanmış birim tarifleri, `26c`).
Okuyucu listesi profilde değil, `27`'dedir.

**policy.json**: `constitutional{monthly_cap_usd, monthly_cap_ci_minutes, session_cap_usd, shares,
class_floors{K0, K1, K2, K4: {kind: census, misses: 0}, K3, K5..K8: {recall_lb, precision_lb}},
required_exit_rows{capability: [row]}, regression_freeze, cycle_caps, daily_caps,
security_keywords[], banned_phrases[], stage_order, look_budget, confidence_level,
noninferiority_margin, n_min_paired, mcnemar_min_discordant, survival_windows{}, gate_rules{},
stage_params{}, stage_budgets{}, license_allowlist[], license_exceptions{pin: {expression, evidence}}}`,
`operating{key: {value, band}}` (kaynak sınırları; bandı operatör yazar, değer bant içinde iki yöne, `26c`),
`performance{rules{name: expr}, windows{}, lambda, beta_prior, shadow_discount, shadow_min_runs,
shadow_max_windows, ablation_margin, severity_map{}, op_allow{}, cheapest_model, effort{},
signal_thresholds{}}`. Eylemi kapılayan her şey anayasal bölümdedir ve yalnız sıkılaşır.
Başlangıç değerleri `18a` (anayasal) ve `18b`'de (performans).

**test-writer output**: `{status: test|not_derivable, expected_assertion_message, test_file,
must_cover_lines[]}`. Kırmızı koşu ancak başarısız assertion mesajı
`expected_assertion_message` ile eşleşirse kırmızıdır.

**looks** satırı (`part: looks`): `{pool_id, lineage, look_index, alpha_k, verdict}`. Bütçe
havuz başınadır; tüm soylar paylaşır.

**heldout.seal.json**: `seal_id`, `hmac_sha256`, `case_count`, `created_at`, `rotation_due`,
`cutoff_ts`, `sealed_prompt_sha256`; vaka listesi mühürlü depodadır.

**snowball-tests.json**, **exit-request.json**, aşama tablosu (`stage0.json`), tarif, aday, bildirim ve
operatör dosyaları (`control.json`, `setup/*`) `26c`'dedir.

**contract**: `contract_id`, `producer`, `consumer`, `schema_ref`, `state` (`proposed`|`frozen`),
`tests[]`. Bulgu biçimi sözleşme değil bu şemadır; ilk sözleşme ikinci ortak arayüzle doğar.
