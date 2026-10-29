# Aşama 0 §0.4 — Hata seti (P1'e taşındı)

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken
Çapa: beklemede: aşama 0 çıkış raporu

---

Vaka seti, mutasyon kataloğu, `cases.build` ve K0 çıkış örneklemi P1 partisine taşındı; metin
`asama-1/13a`'dadır. İlk okuyucuları Aşama 1 MF1'in dev ölçümü ve Aşama 1 çıkışının kural sayımıdır.

Aşama 0'da vaka yoktur. Döngünün adayları Kurucu'nun hazır adaylarıdır (`candidates/<hedef>/<cid>/`:
`finding.json`, `diff.patch`, `expect.json`); hedef bulgu hakemin kendi araç koşusunun yayımladığı
`(rule_id, path, line)` ve `fix` aralığıdır (§0.8).

Aşama 0'da kalan kural: aracı koşturan her adım `koş`ta, sırsız ve ağsız koşar; seçim ve karar hakem
kodudur (`tohum/08` 1).
