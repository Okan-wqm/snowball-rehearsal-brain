# Aşama 1 §1.12 — Teslim listesi

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 1 çalışırken
Çapa: beklemede: aşama 1 çıkış raporu

---

**Beyin reposunda:** `adapters/lint/`, taban çıkarıcı, `fixers/` (`fixer.range`; `fixer.llm`:
şablon, düzenleme şeması, deterministik uygulayıcı), `candidate.publish` aday paketi biçimi,
`docs/` üreticisi (bulgu ve organ sayfaları, iki format, sabit şablon).

**Hakem reposunda:** değişiklik yok.

**Hedefte (`brain/state`):** `profile.json`, `cases/`, `ledger.jsonl` (`events`, `cost`, `freeze`,
`rival`, `accept` bölümleri), `findings.jsonl`, `unresolved.jsonl`, `chain/root.jsonl`, `runs/`
(koşu sonuçları ve `run_meta`, hash'le adreslenmiş), `status.md`, `docs/`.

**`asama-1/` altında:** tarihli çıkış raporu: PASS satırının kopyası, hash'i satırla eşleşir.

**Bilerek bu aşamada olmayanlar ve açılış tetikleri** (Y4: dosya, okuyucusunun karar
değiştirebildiği aşamada açılır):

| Parça | Açılış tetiği |
|---|---|
| Repo haritası, `map.build` | `impact_miss` sinyali eşiği ya da K2 silmeleri (`tohum/17`) |
| `contracts/` | Bulgu şemasından başka ikinci ortak arayüz |
| İtibar görünümü | Bir sınıfta ≥ 2 aday organ |
| Ders görünümü ve enjeksiyonu | Aşama 2 planlayıcısı; ham `cause` satırları bu aşamadan yazılır |
| Organ yaşam döngüsü, `genesis-queue` | Bir sınıfta ≥ 2 aday organ |
| Bisect | Sıralı olmayan merge'ler |
| `main` senkronu | Aşama 2; eskimiş bulgu oranı sinyali ve kendi güvenlik kararı |
| `chain.asof` | İlk zamansal sorgu okuyucusu |
| Kapsayıcılık özetleri, sandbox kanaryası | Çalışma zamanında araç kullanan ilk ajan; en geç Aşama 4 |
| Test-yazıcı koltuğu | İlk çağıranı, Aşama 4 |
| Held-out havuzu, bakış bütçesi, mühürlü depo | Aşama 4 |
