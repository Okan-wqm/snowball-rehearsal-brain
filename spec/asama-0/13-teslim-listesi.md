# Aşama 0 §0.13 — Teslim listesi

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken
Çapa: beklemede: aşama 0 çıkış raporu

---

**Beyin reposunda, `referee/` altında (aktarılacak döngü hakemi):** §0.14'ün 18 modülü
(`ledger/chain.py`, `gate/secrets.py`, `runner/contained.py`, `profile/derive.py`, `runner/deps_npm.py`,
`profile/unit_verify.py`, `gate/diffguard.py`, `gate/check.py`, `target/write.py`, `ledger/append.py`,
`ledger/anchor.py`, `gate/sentinel.py`, `gate/revert.py`, `harness/revert_drill.py`,
`dispatcher/llm_call.py`, `status/block.py`, `activate.py`), döngü iş akışı `.github/workflows/loop.yml`,
`schemas/` ve kendi testleri (`tests/`).

**Beyin reposunda, `referee/` dışında:** `targets/<hedef>/units.json` (tarif önerisi, veri);
`candidates/<hedef>/<cid>/` (`finding.json`, `diff.patch`, `expect.json`; oyuncakta bir iyi ve dört kötü,
kopyada bir iyi ve bir kötü aday); `tests/fixtures/toy-repo/` (oyuncak hedefin içeriği: tohumlanmış
düzeltilebilir lint borcu, ajan yapılandırması yok); `founder-ledger.jsonl` (tohumun aracıyla zincirli);
`reports/*.json` (tipli bildirimler); `snowball-tests.json`; çıkışta `exit-request.json` (`tohum/26c`).

**Hakem reposunda, aktarımla:** pinli SHA'nın `referee/` ağacı kökte ve `.github/workflows/loop.yml`;
önyükleme hakemi (`bootstrap/`, `bootstrap.yml`) yerinde kalır; `setup/imports.jsonl` satırı. Kilit
açılışında `setup/stage.json` (§0.10a).

**Hedeflerde (oyuncak ve kopya), `brain/state`:** genesis satırı; `profile.json` (`units[]` ve
doğrulanmış tarif); `ledger.jsonl` (`events`, `cost` ve `drill` satırları); `chain/root.jsonl`;
`status.md` bloğu. `brain/integration`'da merge ve geri alma commit'leri; oyuncakta PASS satırı.

**Rekor'da:** (A) sonucu (kurulum özeti, vektör, koltuk ve politika hash'leriyle, `tohum/25`) ve her
devrin kökü.

**`asama-0/` altında:** tarihli çıkış raporu: PASS satırının kopyası, güven kökü, insan dokunuşu sayısı,
kopyada ilk canlı merge'e kadar oturum ve USD.

**Bu aşamada olmayanlar:** `snowball init`, `mcp/`, `docs.index`, `profile.propose`, snapshot ve vaka
seti, `harness.score`, taban avcı, `exit.sample`, `drift.check`, Gözcü, `agent.dispatch`, `spec.lint`,
`lock.check`, `brain.accept`. Yerleri ve açılış tetikleri `asama-1/13`'tedir; kilit ve push kabulü
önyükleme hakemindedir (`tohum/29b`).
