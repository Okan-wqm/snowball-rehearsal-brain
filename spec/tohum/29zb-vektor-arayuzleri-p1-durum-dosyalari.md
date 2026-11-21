# Vektör Arayüzleri: P1'in Durum Dosyalı Kökü

Tarih: 2026-11-21 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: P1 MF8'in kökü yazılırken ve `root_files` grubu okunurken
Çapa: `seed/bootstrap/vectors/vectors.json` (`root_files`); `ledger/anchor.py`

---

`29a`'nın ve `29d`'nin kuralları geçerlidir (bağımsız inceleme ekibi kararı (2026-11-21), seed-086; kural `26j`).

## `root_files` (P1 MF8, `ledger/anchor.py`)

`python -m ledger.anchor root <defter.jsonl> <durum_dosyası.jsonl>...`: `29j`'nin `root`'u, defterin ardından durum
dosyalarıyla. Satırı olan her dosya `tips`'e adıyla (`findings.jsonl`, `unresolved.jsonl`) ve son satırının saklı
`row_hash`'iyle girer; satırsız dosya anahtar eklemez; `root` yine `tips`'in RFC 8785 baytlarının sha256'sıdır
(`13`). Grup P1 MF8'indir ve MF8 bitince koşar. Vakalar: `state_files_keyed` iki dosya iki anahtar ekler, bölümlerin
uçları değişmez; `empty_file_adds_nothing` satırsız dosya kökü değiştirmez.
