# Aşama 0 §0.14 — Sıralı mikro özellikler

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken
Çapa: beklemede: aşama 0 çıkış raporu

---

Her satır tek mekanizmadır, tek oturumda biter, kendi gerçek testiyle gelir ve önyükleme hakeminin
koşusu yeşilken kapanır; sonraki satır öncekinin koşusu yeşilken başlar. Her MF ilk canlı döngünün bir
adımında okunur (§0.1). Test numaraları §0.9'dandır. Üç ek kural:

- **Tohum vektörü.** Her MF bir tohum vektör grubuna bağlıdır; grup, MF `done_mf`'e girdiği push'tan sonra
  her push'ta koşar. Grup veridir (`{cmd, stdin?, fixture, expect, changed: {…, expect_not}}`);
  önyükleme hakemi tek bir genel koşucuyla uygular. Komut `referee/`'den koşar, çıktı tek satır JSON'dur
  (`tohum/29a`, `29d`); beklenen değerler tohum yazılırken iki bağımsız hesapla doğrulanır.
- **Modülsüz kırmızı.** Bir push MF k'yı `done_mf`'e eklediğinde önyükleme hakemi k'nın testlerini
  "Modül" sütunundaki yol silinmiş ağaçta yeniden koşar; yeşil kalırsa ret (`module_less_green:MFk`).
  Çıkışta 18'inin hepsi için (§0.10 #modulsuz).
- **Sıra.** Çağrılan MF çağırandan önce gelir (`calls`, tablonun altında); önyükleme hakemi tabloyu
  yüklerken bunu denetler.

"Kum" sütunu testin önyükleme hakeminin kumunda (python imajı; git, docker, node yok) neyle koştuğunu ve
gerçeğinin §0.10a'nın hangi satırında doğrulandığını söyler.

| MF | Mekanizma | Test | Vektör grubu | Modül (`referee/` altında) | Adım | Kum |
|---|---|---|---|---|---|---|
| 1 | Zincir: `ledger.chain hash`, `verify [--previous]` | 13 | `chain` | `ledger/chain.py` | D1, D6 | gerçek |
| 2 | `secrets.scan`: diff, defter satırı, prompt; eşleşme koşuyu geçersiz kılar, prompt gitmez | 38 | `secrets` | `gate/secrets.py` | D4–D6 | gerçek |
| 3 | `run.contained`: iç içe ağsız konteyner, koşu başına taze host dizini, sonuç hash'i dışarıda, kırmızı kontroller, birim imajı ve sınırları | 20, 21 | `contained` (üretilen `docker run` argv'si zorunlu bayrakları taşır, yasaklıları taşımaz) | `runner/contained.py` | D3 | taklit koşucu; gerçeği #kirmizi #kanarya |
| 4 | `profile.derive` (statik): diller, birim adayları, `security_paths`, hariç yollar, test yolu kuralları; önerinin bunları daraltması ret | 19, 47 | `profile` (fikstür ağaçlar) | `profile/derive.py` | D1 | gerçek |
| 5 | `deps.fetch` (npm): kilitteki `resolved` ve `integrity`, kayıt defteri izin listesi, içerik adresli artefakt, lisans raporu | 34 | `npmlock` (bir baytı değişmiş tarball reddedilir) | `runner/deps_npm.py` | D2 | yerel fikstür tarball'lar; gerçeği #getir |
| 6 | `unit.verify`: tarif (imaj `@sha256`, `inputs`, komutlar, sınırlar) HEAD'de 3/3 yeşil, ağsız; `inputs` kapanışı yeterli | 48 | `recipe` (statik tarif denetimi) | `profile/unit_verify.py` | D3 | taklit koşucu; gerçeği #birim |
| 7 | `gate.diffguard` (§0.8 madde 1) | 23 | `diffguard` | `gate/diffguard.py` | D5 | gerçek |
| 8 | `gate.check`, saf karar: §0.8 madde 3–8 ve eşlenmiş satır | 35 | `k0map` | `gate/check.py` | D5 | gerçek (fikstür `koş` çıktıları) |
| 9 | `target.write`: hedefe yazımın tek yolu GitHub REST ve Git Data API; yalnız `refs/heads/brain/**`; dal, PR, check, merge; geri alma commit'inin ağacı merge'ün ilk ebeveyninin ağacı | 49 | `refs` | `target/write.py` | D6 | süreç içi taklit API; gerçeği #merge |
| 10 | `ledger.append`: devir başına tek `brain/state` commit'i; yazımdan önce `verify --previous`; satırlar 2'den geçer | 39 | `chain`, `append` | `ledger/append.py` | D6 | gerçek, taklit yazarla |
| 11 | `rekor.anchor`: kök = bölüm uçlarının kanonik hash'i; Sigstore imzası (tohumun pinleri); sonraki D1 doğrular; imzalanamazsa sert duruş | 40 | `root` | `ledger/anchor.py` | D1, D6 | taklit imzalayıcı; gerçeği #kok |
| 12 | `sentinel.run`: merge sonrası etkilenen testler, kırmızıda 3/3 (`tohum/07`) | 36 | `flaky` | `gate/sentinel.py` | D7 | gerçek karar mantığı; gerçeği #nobetci |
| 13 | `gate.revert` ve mekanik `cause` (`test_regression`, `build_break`, `lint_regression`, `impact_miss`, `unknown`) | 25 | `cause` | `gate/revert.py` | D7 | taklit API; gerçeği #geri-alma |
| 14 | Geri alma provası (`exit.drill`, yalnız `revert`): seçim `HMAC(prova_tohumu, cycle_id)` önceki devrin `yaz`'ında, taahhüt zincirde; tohum fikstürlerinden ekilmiş kötü merge; açılım; karar | 50 | `revert_drill` (`tampered_key` dahil) | `harness/revert_drill.py` | D8 | taklit; gerçeği #geri-alma |
| 15 | `llm.call`: tipli girdi, şablon, 2, pinli `claude -p` (araç, ayar kaynağı, oturum kaydı yok; `--max-budget-usd`), sunulan model, `cost` satırı, aşama freni, 429 kesintidir | 37 | `prompt` (tipli girdi → prompt sha256; tip dışı alan girmez) | `dispatcher/llm_call.py` | D4 | taklit `claude` (PATH'te Python betiği); gerçeği #model |
| 16 | `status.block`, en küçük: defterden üretilir; elle düzenleme sonraki devirde yeniden üretilip `events`'e yazılır | 42 | `status` | `status/block.py` | D6 | gerçek |
| 17 | Döngü iş akışı `loop.yml` | 46 | tohumun `wiring` denetimi (vektör değil; her push'ta ve (A)'da) | `.github/workflows/loop.yml` | D0–D8 | statik; gerçeği (B) |
| 18 | Etkinleştirme: genesis satırı, `brain/integration` kesimi, mandal tabanı, hazır adaylar | 45, 14 | `genesis` | `activate.py` | (B) | taklit API; gerçeği #genesis |

`calls` (çağrılan → çağıranlar): 2 → 8, 10, 15; 3 → 6, 12; 4 → 5, 7; 5 → 6; 9 → 10, 13; 10 → 11, 14, 15, 16;
12 → 13 → 14; 17 ve 18 hepsini çağırır.

**Makine kopyası.** Tablonun her satırı (MF, testler, vektör grubu, modül yolu, `calls`) tohumda
`seed/bootstrap/stages/stage0.json`'dur. Önyükleme hakemi `done_mf`'in anlamını, test bildirimi
denetimini, modülsüz kırmızıyı, sırayı ve çıkıştaki MF sayısını oradan okur. Tohumun testi dosyayı bu
sayfa ve §0.9 ile birebir tutar; biri değişirse öbürleri aynı tohum döneminde değişir.

**Tohum denetimleri, Kurucu'nun MF'si değil:** `wiring` (MF17'nin kuralları), Kurucu defteri, genellik
ve spec denetimi önyükleme hakeminin kodudur (`tohum/29b`). Aşama 0 2.2'nin 30 MF'sinden taşınanlar ve
tohuma gidenler `asama-1/13`'tedir. Sonra çıkış isteği (§0.10).
