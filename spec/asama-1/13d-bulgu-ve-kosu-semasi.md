# Aşama 1 §1.13d — P1: Bulgu ve koşu şeması

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: P1 partisi yazılırken ve Aşama 1 çalışırken
Çapa: beklemede: aşama 1 çıkış raporu

---

Bu sayfa Aşama 0 2.2'nin §0.7'sidir; `findings.jsonl` ilk okuyucusu Aşama 1 MF1'in keşfiyle gelir (§1.13).

İki format, tek kaynak: ajan için `findings.jsonl` satırı, insan için üretilmiş sayfa
(`tohum/15`). Alanların tek tanımı `tohum/26`'dadır; bu sayfa onları tanımlamaz, Aşama 1'deki
anlamlarını söyler.

| Alan | Aşama 1'deki anlamı |
|---|---|
| `finding_id`, `fingerprint` | Parmak izi `property + file + symbol + normalize(claim)`; satır girmez (`tohum/07`) |
| `state` | `open`, `fixed`, `verified`, `reopened`, `withdrawn`, `blocked`, `unresolved` |
| `class_level`, `property` | §1.13b |
| `tool`, `rule_id` | K0–K2 için zorunlu; K0 isabeti kural + eşlenmiş satırdır (`asama-0/08`) |
| `claim` | Ürün hakkında tek cümle |
| `evidence_refs` | `[{path, line_start, line_end}]`; manifestte var olmalı; tek birincil ref ≤ `stage_params.evidence_ref_max_lines` (30) satır |
| `required_change` | Dizi: `[{file, symbol?, op}]`; boşsa gözlemdir, puanlanmaz |
| `severity_hint` | Yalnız ipucu; şiddeti property ve sınıftan politika haritası türetir |
| `confidence`, `derivation`, `trust`, `snapshot_id` | `tohum/26` |

Gerekçe: gerçek hata, birinin değiştirmesi gereken şeydir; bir kuralın tetiklenmesi hata değildir.

**Satırı hakem yazar.** Adapter'ın ürettiği bulgu bir öneridir; `findings.jsonl`'a hakem yazar,
oyuncunun önerdiği içerik `proposed_by` ile işaretlenir.

**`run_meta`.** Alanlar `tohum/26`'dadır. Model, token ve maliyet alanlarını `çağır` işi,
`files_read` ve kapsayıcılık alanlarını `run.contained` ölçer; ajan yalnız `declared_exits`'i yazar.
`previous_run_ref` her zaman boştur. Aşama 0 ve 1'de `lessons_injected` ve `imported_used` boştur.
