# Aşama 0 §0.7 — Bulgu ve koşu şeması (P1'e taşındı)

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken
Çapa: beklemede: aşama 0 çıkış raporu

---

`findings.jsonl` alanlarının Aşama 1'deki anlamı ve `run_meta` P1 partisine taşındı; metin
`asama-1/13d`'dedir. Alanların tek tanımı yine `tohum/26`'dadır.

Aşama 0'da `findings.jsonl` yoktur. Döngü hedef bulguyu adayın `finding.json`'undan alır ve hakemin
kendi araç koşusuyla doğrular (§0.8). Her karar, nedeniyle birlikte bir `events` satırıdır; her
`llm.call` çağrısı bir `cost` satırı (model, sunulan model, CLI'nin bildirdiği maliyet) yazar. Satırları
yalnız hakem yazar; beyinden gelen içerik (aday, tarif önerisi) `proposed_by` ile işaretlenir.
