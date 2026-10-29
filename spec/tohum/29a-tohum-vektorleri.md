# Tohum Vektörleri: Değişmeyen Beklenen Çıktılar

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: zincir, istatistik ve puanlama kodu yazarken
Çapa: hakem reposu `vectors/` dosyası; hash'i `setup/summary.json`'da

---

Bu değerler tohumla gelir; operatör kurulumda onları hakem reposunun `vectors/` dizinine kopyalar.
Kurucu değiştiremez; önyükleme hakemi Kurucu'nun koduna her push'ta onları koşturur (`29b`).
Değerler tohum yazılırken iki bağımsız hesapla doğrulanmıştır. **Vektörler tabandır, yeter
değildir:** vektöre özgü bir dal yazmak tohum rakibinin ilk baktığı şeydir (`29`).

## Zincir

Kanonik biçim RFC 8785; vektörlerde yalnız ASCII dizgi, tamsayı, nesne ve dizi vardır.
`row_hash = sha256(canonical(row − row_hash) ‖ prev_hash)`; `‖` bayt birleştirmedir, `prev_hash`
ASCII onaltılık dizgidir. Z = 64 sıfır.

- **V1.** Satır `{"row_id":"r1","ts":"2026-10-28T00:00:00Z","part":"events","kind":"genesis",
  "payload":{},"derivation":"tool","trust":"verified","snapshot_id":"s0","evidence_refs":[],
  "prev_hash":Z}` → `row_hash` =
  `3bae91580aca99362572e9f5f41b3e46c2bc0c29236f72e867faa5cd46ca603a`.
- **V2.** Satır `{"row_id":"r2","ts":"2026-10-28T00:00:01Z","part":"cost","kind":"run",
  "payload":{"usd_micros":0},"derivation":"tool","trust":"observed","snapshot_id":"s0",
  "evidence_refs":[],"prev_hash":<V1 row_hash>}` → `row_hash` =
  `3b10a5bb06351b0933c0e30f7dd55d3a57245743b97fb1faba348351a554a45c`.
- **V3.** V2'de `payload.usd_micros` 1 yapılıp `row_hash` değiştirilmezse `chain.verify` `r2`'yi
  kırık raporlar; V1 geçerli kalır.

## İstatistik

Tek yönlü Clopper–Pearson alt sınırı, α = 0,10 (`19`):

| (x, n) | Alt sınır |
|---|---|
| (60, 60) | 0,9624 |
| (45, 45) | 0,9501 |
| (44, 44) | 0,9490 |
| (25, 25) | 0,9120 |
| (10, 10) | 0,7943 |
| (8, 10) | 0,5504 |
| gerçel `x_eff` (7,5; 10) | 0,4982 |

Gerçel argümanlı Beta ile `x_eff` = 8,0 tamsayı sonucunu (0,5504) vermelidir.

Tam tek yönlü McNemar p-değeri (b: eskinin lehine, c: yeninin lehine uyuşmaz çift):

| (b, c) | p |
|---|---|
| (0, 3) | 0,1250 |
| (0, 4) | 0,0625 |
| (1, 7) | 0,0352 |
| (0, 8) | 0,0039 |
| (2, 8) | 0,0547 |

## Eşleme (match-rule v2)

- K0: bulgu ile vakanın `tool`, `rule_id` ve hunk üzerinden eşlenmiş satırı aynıysa isabet.
- K0: aynı kural, eşlenmiş satır farklı → isabet değil.
- Bir bulgu iki vakayı alamaz; bir vaka bir koşuda bir kez sayılır.

## Arayüz

Önyükleme hakemi vektörleri Kurucu'nun koduna şu komutlarla, `referee/` kökünden uygular; çıktı
stdout'ta tek satır JSON'dur:

- `python -m ledger.chain hash` (stdin: tek satır) → `{"row_hash": ...}`
- `python -m ledger.chain verify <dosya> [--previous <dosya>]` → `{"valid": bool, "broken_row": ...}`
- `python -m harness.stats cp_lower <x> <n> <alpha>` → `{"lb": "0.962400"}` (altı ondalık dizgi)
- `python -m harness.stats mcnemar <b> <c>` → `{"p": "0.062500"}`
- `python -m harness.score <bulgular> <vakalar>` (iki JSON dizisi) → `{"hits": int}`; eşleme fikstürleri önyükleme
  hakemiyle birlikte `seed/bootstrap/vectors/` altında gelir.
- `python -m harness.drill judge <prova dosyası>` → `{"drill": ..., "verdicts": {...}}`; kurallar ve vektörler `29c`'de.

Karşılaştırma tablodaki basamak sayısıyla yapılır.

Her vektörün testi hem doğru sonucu hem de bir bayt değiştirilmiş girdide yanlış sonucun
reddedildiğini gösterir; yalnız doğru girdide yeşil kalan vektör testi test değildir (`04`).
