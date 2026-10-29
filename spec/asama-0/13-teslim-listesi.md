# Aşama 0 §0.13 — Teslim listesi

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken
Çapa: beklemede: aşama 0 çıkış raporu

---

**Beyin reposunda, `referee/` altında (aktarılacak hakem):** `ledger/` (`ledger.append`,
`chain.verify`, `rekor.anchor`), kill switch ve bütçe okuyucu, `profile.derive`, `harness/`
(`snapshot.make`, `cases.build` ve mutasyon kataloğu, `exit.sample`, `exit.drill`, `harness.score`,
`harness.baseline` ve grep kümesi), `spec.lint`, `runner/` (`run.contained`, `deps.fetch`),
`gate/` (`gate.diffguard`, `gate.check`, `sentinel.run`, `gate.revert`, `lock.check`,
`brain.accept`), `drift.check`, `llm.call`, `secrets.scan`, `dispatcher/` (`agent.dispatch`),
`gozcu/` (`gozcu.evaluate`, `status.block`), `schemas/`, beş işin iş akışları (`çek`, `getir`,
`koş`, `çağır`, `yaz`), kendi testleri, aktarım ve etkinleştirme betikleri.

**Beyin reposunda, oyuncu:** `cli/` (`snowball init`), `profile.propose`, `mcp/` (bu aşamanın
beyin araçları, `tohum/26a`), `docs.index`, `founder-ledger.jsonl`, `tests/fixtures/toy-repo/`
(tohumlanmış lint borcu, gömülü dispatch kanaryaları), `candidates/` altında etkinleştirmenin hazır
iyi ve hazır kötü adayı.

**Hakem reposunda, aktarımla:** pinli SHA'nın `referee/` ağacı; önyükleme hakemi yerini ona bırakır.

**Hedeflerde, etkinleştirmeyle (`brain/state`):** `profile.json`, `cases/` (dev K0),
`ledger.jsonl` (`events`, `cost`, `rival`, `accept` bölümleri), `chain/root.jsonl`, `status.md`
(hakemin durum bloğu ve Aşama 0 şablonu). Oyuncak hedefte ayrıca canlı döngünün
`brain/integration` merge'ü.

**Rekor'da:** (A) sonuçları, kurulum özeti hash'i ve ilk kök hash.

**`asama-0/` altında:** tarihli çıkış raporu: PASS satırının kopyası, taban recall ve maliyeti,
güven kökü, insan dokunuşu sayacı.
