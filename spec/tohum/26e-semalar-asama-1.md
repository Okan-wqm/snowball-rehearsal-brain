# Şemalar, Devam: Aşama 1'in Parti Tabloları

Tarih: 2026-11-01 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 1'de her parti yazılırken ve parti çıkış isteğinden önce; kilidin açılışından önce
Çapa: `seed/bootstrap/stages/stage1-P1.json`, `stage1-P2.json`; `seed/bootstrap/snowball_bootstrap/stages.py`

---

`26c` "Aşama tablosu"nun Aşama 1'deki hâli. Kilit açılınca (`asama-0/10a`) önyükleme hakeminin tablosu açık partinin
tablosudur: `asama-1/13`'ün satırlarının makine kopyası, tohumda `seed/bootstrap/stages/stage1-<parti>.json`, `{stage: 1,
batch, mfs: [{mf, tests[], groups[], module, calls[]}]}`. Açık parti, sayacın (`setup/imports.jsonl`) kilitten sonra
aktarmadığı ilk partidir; Aşama 0 ve aktarılmış partiler bitmiştir (grupları her push'ta koşar, testleri bildirimde
kalır). `done_mf` açık partinin MF'lerinin 1'den kesintisiz önekidir, testleri `snowball-tests.json`'da `stage: 1`'dir.
Partiler numarasızdır (`asama-1/06`): her tablo kendi MF'lerini 1'den numaralar; Aşama 1'in kendi MF'leri tabloda
değildir.

| Parti (`batch`) | MF | Test | Vektör grubu | Modül (`referee/` altında) | `calls` |
|---|---|---|---|---|---|
| `P1` | 1 | 51 | — | `runner/organs.py` | — |
| `P1` | 2 | 8 | — | `snapshot/make.py` | — |
| `P1` | 3 | 2, 4 | — | `cases/build.py` | — |
| `P1` | 4 | 1, 6, 7, 12, 28 | `match`, `cp_lower`, `mcnemar` | `harness/score.py` | — |
| `P1` | 5 | 9, 11 | — | `harness/offline.py` | — |
| `P1` | 6 | 24 | — | `drift/check.py` | — |
| `P1` | 7 | 41 | — | `gozcu/evaluate.py` | — |
| `P1` | 8 | 52 | — | `policy/operating.py` | — |
| `P2` | 1 | 53 | — | `security/derive.py` | — |
| `P2` | 2 | 22 | — | `agent/dispatch.py` | — |

Test numaraları §0.9'undur (`asama-0/09`); 53 onun numaralarının devamıdır: `asama-1/13`'ün P2 MF1 için andığı
"`30d`'nin profil testleri", tanımı `30d` "Profil testi"ndedir. Öbür testler ve gruplar `asama-1/13`'ündür. Modül yolu `26a`'nın
araç adındandır (`snapshot.make` → `snapshot/make.py`), aracı olmayan mekanizmada mekanizmanın adından; iki araçlı MF'nin
modülü ilk aracınkidir (`asama-0/14` MF1 ve MF13 gibi). Modülsüz kırmızı bu yolu siler (`asama-0/14`). Parti çıkış isteği
`{stage: 1, sha, spec_sha256, batch}`'tir (`26c`); `batch` bu tablonun ilk sütunudur ve açık partininki olmalıdır,
değilse `exit_request_wrong_batch`.

**Çıkış partisi.** `asama-1/13`'ün "Aşama 1 çıkışı" satırları (`exit.sample` 27 ve 16, `spec.lint` 33) bu tohumda tablo
değildir: o parti Aşama 1'in kendi çıkışının (A)'sıyla gelir (`asama-1/08`) ve bu tohum Aşama 1'in çıkış isteğini
yargılamaz (`batch`'siz istek `exit_request_wrong_stage`'dir). Tablosu o yargıyla, bir tohum döneminde gelir. P1 ve P2
aktarılınca açık tablo boştur, `done_mf` `[]`'dir.

**Önyükleme hakemi Aşama 1'de.** Rakip freni açık aşamanın `stage_budgets.asama_<k>.rival_usd`'sidir: `k` kilidin
`stage`'idir, kilit yokken 0; Aşama 1'inki `asama-1/10`'un 15 USD'si (`18a`). Aşamanın harcaması kilidin açılışından
sayılır: kilitten sonra yargılanan ilk push onu sıfırdan başlatır, imzalı durum aşamayı `spend_stage` olarak tutar (Aşama 0'ın
durumunda alan yoktur). Kilit açıkken anahtar `policy.json`'da yoksa koşu durur (`26c`: operatör dosyası kapalıya düşer);
`stage-open` anahtarsız politikayla kilidi açmaz. Kod isteğinde rakip, tohum sayfalarının yanında açık tablonun
kopyaladığı aşama sayfalarını görür: Aşama 0'da `asama-0/09` ve `asama-0/14`; Aşama 1'de `asama-0/09`, `asama-1/06` ve
`asama-1/13`.
