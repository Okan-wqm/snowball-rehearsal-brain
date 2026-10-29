# Aşama 1 §1.12 — Teslim listesi

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 1 çalışırken
Çapa: beklemede: aşama 1 çıkış raporu

---

**Beyin reposunda:** `adapters/lint/`, taban çıkarıcı, `fixers/` (`fixer.range`; `fixer.llm`:
şablon, düzenleme şeması, deterministik uygulayıcı), `candidate.publish` aday paketi biçimi,
`docs/` üreticisi (bulgu ve organ sayfaları, iki format, sabit şablon, dizin). `referee/` altında
P1, P2 ve çıkış partisinin MF'leri ve testleri (§1.13).

**Hakem reposunda, aktarımla:** P1, P2 ve çıkış partisinin `referee/` ağaçları; her biri bir
`setup/imports.jsonl` satırı. Kilit açılışında `setup/stage.json` `stage: 2`.

**Hedefte (`brain/state`):** `profile.json`, `cases/`, `ledger.jsonl` (`events`, `cost`, `freeze`,
`rival`, `accept`, `security` bölümleri), `findings.jsonl`, `unresolved.jsonl`, `chain/root.jsonl`, `runs/`
(koşu sonuçları ve `run_meta`, hash'le adreslenmiş), `security/`, `status.md`, `docs/`.

**`asama-1/` altında:** tarihli çıkış raporu: PASS satırının kopyası, hash'i satırla eşleşir.

**Bilerek bu aşamada olmayanlar ve açılış tetikleri** (Y4: dosya, okuyucusunun karar
değiştirebildiği aşamada açılır):

| Parça | Açılış tetiği |
|---|---|
| Repo haritası, `map.build` | `impact_miss` sinyali eşiği ya da K2 silmeleri (`tohum/17`) |
| `contracts/` | Bulgu şemasından başka ikinci ortak arayüz |
| İtibar görünümü | Bir sınıfta ≥ 2 aday organ |
| Ders görünümü, enjeksiyonu ve provası (`harness.drill`) | Aşama 2 partisi; ham `cause` satırları bu aşamadan yazılır |
| Organ yaşam döngüsü, `genesis-queue` | Bir sınıfta ≥ 2 aday organ |
| Bisect | Sıralı olmayan merge'ler |
| `main` senkronu | Aşama 2; eskimiş bulgu oranı sinyali ve kendi güvenlik kararı |
| `chain.asof` | İlk zamansal sorgu okuyucusu |
| Kapsayıcılık özetleri, sandbox kanaryası | Çalışma zamanında araç kullanan ilk ajan: P2'nin güvenlik avcısı ya da en geç Aşama 4 |
| `profile.propose` | İkinci birim ya da ikinci hedef |
| `services[]` ile birim | Servis isteyen ilk birim |
| Taban avcı, `harness.baseline` | Aşama 4 partisi, ilk LLM avcısından önce |
| Test-yazıcı koltuğu | İlk çağıranı, Aşama 4 |
| Held-out havuzu, bakış bütçesi, mühürlü depo | Aşama 4 |
