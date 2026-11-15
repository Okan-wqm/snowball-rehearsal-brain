# Politika Başlangıç Değerleri: Performans Bölümü

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: etkinleştirmede performans bölümü yazılırken ve bir eşiğin ilk değeri aranırken
Çapa: beklemede: aşama 0 — etkinleştirmede `policy.json` performans bölümü; şema `26b`

---

Performans bölümü eylemi değil dikkati ve sırayı yönetir; değerleri `18`'deki prosedürle iki
yönlü değişir ve her değişiklik zincire yazılır. Anayasal bölüm `18a`'dadır. Adlar `26b` şemasıyla
aynıdır.

## Performans (`performance`)
| Anahtar | Başlangıç | Okuyan |
|---|---|---|
| `performance.windows.measure` | Ölçüm penceresi 14 gün | `11`, `12`, `17`, `28` |
| `performance.windows.security_sweep` | Güvenlik avcısının bütün sistemi bütün katalogla süpürmesi 7 günde bir ve her katalog ya da profil sürümünde | `30f` |
| `performance.rules.recall_gate`, `performance.rules.precision_gate` | `18`'deki örnek kurallar | `12`, kapı |
| `performance.shadow_min_runs` | Pencere başına koşu sayısının yarısı, en az 3 | `12` |
| `performance.shadow_max_windows` | 4 pencere; sonunda SHADOW → RETIRED | `12` |
| `performance.ablation_margin` | Katkının %90 üst sınırı < 0,02 bileşik skor → emeklilik | `12` |
| `performance.lambda` | 0,5 değer birimi / USD | `11` |
| `performance.beta_prior` | Beta(1, 1) | `11` |
| `performance.rules.reputation_half_life` | 30 gün; yalnız yeni karar varken işler | `11` |
| `performance.shadow_discount` | 0,5 | `11`, `12` |
| `performance.severity_map` | CRIT 10, HIGH 5, MED 2, LOW 1, lint 0,05 | `11`, `17`, `20` |
| `performance.op_allow` | K0 `lint_fix`; K1 `lint_fix`, `change_type`; K2 `remove`; K5–K6 `doc_fix` dışı hepsi; K8 `doc_fix` | `04a` 8, `26` |
| `performance.cheapest_model` | `claude-haiku-5-5`; yalnız panel faz 1–2 | `06`, `09` |
| `performance.effort` | Kurucu `high`; rakip `medium`; güvenlik avcısı `high`; panel koltuğu `low`; düzeltici `low` | `24`, `10a`, `30f` |
| `performance.rules.max_turns` | Rakip 30 (CLI turu; `bootstrap.json` `rival.max_turns`), avcı ve güvenlik avcısı 60, panel koltuğu 12 | `24`, `30f` |
| `performance.rules.gap_rule` | gap ≥ 0,2 iki pencere üst üste ve havuz ≥ 20 vaka | `17` |
| `performance.signal_thresholds` | `17`'deki tablonun eşik sütunu | `17` |
| `performance.rules.drift_bound` | Bir eşiğin başlangıçtan net hareketi > %20 → Gözcü işareti | `18` |
| `performance.rules.probe_cycle` | Sonda döngüsü başına 5 düzeltme; üst üste 2 temiz → kalkış | `28` |
| `performance.rules.lesson_n_min` | Ders başına kol başına 250 koşu; altında UNMEASURABLE | `22` |
| `performance.rules.seat_similarity` | Karar ve referans benzerliği > 0,8 → Gözcü işareti | `09a` |
| `performance.rules.genesis_drafts` | Pencere başına ≤ 3 taslak; kuyruk derinliği ≤ 10 | `12`, `17` |
| `performance.rules.lease_ttl` | Görev kirası 2 saat | `16` |
| `performance.rules.bisect` | Adım ≤ 15 dk, en çok 12 adım; bisect açılınca okunur | `07` |
