# Şemalar, Devam: Aşama 1'in Parti Tabloları

Tarih: 2026-11-01 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 1'de her parti yazılırken ve parti çıkış isteğinden önce; kilidin açılışından önce
Çapa: `seed/bootstrap/stages/stage1-P1.json`, `stage1-P2.json`; `seed/bootstrap/snowball_bootstrap/stages.py`

---

`26c` "Aşama tablosu"nun Aşama 1'deki hâli. Kilit açılınca (`asama-0/10a`) önyükleme hakeminin tablosu açık partinin
tablosudur: `asama-1/13`'ün satırlarının makine kopyası, tohumda `seed/bootstrap/stages/stage1-<parti>.json`, `{stage: 1,
batch, mfs: [{mf, tests[], groups[], module, calls[]}]}`. Açık parti, sayacın (`setup/imports.jsonl`) kilitten sonra
aktarmadığı ilk partidir; Aşama 0 ve aktarılmış partiler bitmiştir (grupları her push'ta koşar, testleri bildirimde kalır).
`done_mf` açık partinin MF'lerinin 1'den kesintisiz önekidir, testleri `snowball-tests.json`'da `stage: 1`'dir. Partiler
numarasızdır (`asama-1/06`): her tablo kendi MF'lerini 1'den numaralar; Aşama 1'in kendi MF'leri tabloda değildir.

| Parti (`batch`) | MF | Test | Vektör grubu | Modül (`referee/` altında) | `calls` |
|---|---|---|---|---|---|
| `P1` | 1 | 51 | — | `runner/organs.py` | — |
| `P1` | 2 | 8 | — | `snapshot/make.py` | — |
| `P1` | 3 | 2, 4 | — | `cases/build.py` | — |
| `P1` | 4 | 1, 6, 7, 28 | `match`, `cp_lower`, `mcnemar` | `harness/score.py` | — |
| `P1` | 5 | 9, 11 | — | `harness/offline.py` | — |
| `P1` | 6 | 24 | — | `drift/check.py` | — |
| `P1` | 7 | 41 | — | `gozcu/evaluate.py` | — |
| `P1` | 8 | 12 | `root_files` | `findings/write.py` | — |
| `P1` | 9 | 55 | — | `gate/allowlist.py` | — |
| `P1` | 10 | 56 | — | `runner/organ_output.py` | — |
| `P1` | 11 | 57 | — | `runner/candidate_rerun.py` | — |
| `P1` | 12 | 58 | — | `loop/candidates.py` | — |
| `P2` | 1 | 53 | — | `security/derive.py` | — |

Test numaraları §0.9'undur (`asama-0/09`); 53 ve 55 onun numaralarının devamıdır: 53 `asama-1/13`'ün P2 MF1 için andığı
"`30d`'nin profil testleri", tanımı `30d` "Profil testi"ndedir, 55'inki `26h`'dedir. 56–58 de devamdır, tanımları `26j`'de.
Öbür testler ve gruplar `asama-1/13`'ündür. Modül yolu `26a`'nın araç adındandır (`snapshot.make` → `snapshot/make.py`),
aracı olmayan mekanizmada mekanizmanın adından; iki araçlı MF'nin modülü ilk aracınkidir (`asama-0/14` MF1, MF13). Modülsüz
kırmızı bu yolu siler (`asama-0/14`). Modülün ilk adı standart kütüphanede bir modülün adı olamaz (`sys.stdlib_module_names`;
ayrıntısı `26j`'de): böyle satırlı tablo yüklenmez. Parti çıkış isteği `{stage: 1, sha, spec_sha256, batch}`'tir (`26c`);
`batch` bu tablonun ilk sütunudur ve açık partininki olmalıdır, değilse `exit_request_wrong_batch`. P1'in MF8'i ve MF9'u ve
ilk dilimin sırası `26h`'dedir (sahip kararı (2026-11-20)); MF10–MF12 operatörün tablo düzeltmesidir (`26j`).

**Çıkış partisi.** `asama-1/13`'ün "Aşama 1 çıkışı" satırları (`exit.sample` 27, `spec.lint` 33, `exit.adversarial`
54; `29za`) bu tohumda tablo değildir: o parti Aşama 1'in kendi çıkışının (A)'sıyla gelir (`asama-1/08`) ve bu tohum
Aşama 1'in çıkış isteğini yargılamaz (`batch`'siz istek `exit_request_wrong_stage`'dir). Tablosu o yargıyla, bir tohum
döneminde gelir. P1 ve P2 aktarılınca açık tablo boştur, `done_mf` `[]`'dir. Ertelenen P3'ün tablosu da öyle gelir (`26h`).

**Önyükleme hakemi Aşama 1'de.** Rakip freni açık aşamanın `constitutional.stage_budgets.asama_<k>.rival_usd`'sidir: `k`
kilidin `stage`'idir, kilit yokken 0; Aşama 1'inki `asama-1/10`'un tablosundadır (`18a`). Aşamanın harcaması kilidin
açılışından sayılır: kilitten sonra yargılanan ilk push onu sıfırdan başlatır, imzalı durum aşamayı `spend_stage` olarak
tutar (Aşama 0'ın durumunda alan yoktur). Kilit açıkken anahtar `policy.json`'da yoksa koşu durur (`26c`: operatör
dosyası kapalıya düşer); `stage-open` anahtarsız politikayla kilidi açmaz. Kod isteğinde rakip, tohum sayfalarının
yanında açık tablonun kopyaladığı aşama sayfalarını görür: Aşama 0'da `asama-0/09` ve `asama-0/14`; Aşama 1'de
`asama-0/09`, `asama-1/06` ve `asama-1/13`.

**P2'nin tek MF'si** `30d`'nin profilidir (bağımsız inceleme ekibi kararı, 2026-11-20, seed-072): `agent.dispatch` ve
dispatch kanaryası (test 22) çalışma zamanında araç kullanan ilk ajanla, en geç Aşama 4'te gelir (`30f`); §0.9'un
donmuş tablosunda 22'nin partisi `P2` yazılı kalır, bu sayfa ondan üstündür (`02`).

**P1'in arayüz olguları** (bağımsız inceleme ekibi kararı, 2026-11-20; Kurucu raporları seed-073–077). Aşama
sayfalarının (`asama-1/13a`, `13c`, `13e`, `asama-0/09`) bıraktığı arayüz olgularıdır; kodun nasıl yazılacağı
Kurucu'nundur. Kalanları (seed-089–092, seed-094; rapor masası uzlaşısı, 2026-11-22) `26m` ve `26n`'dedir.
- **Organ tanımının hash'i** (`26b` `definition_sha256`; seed-073): organın okuyabildiği her beyin dosyasını kapsar;
  hakemde tek bir hash fonksiyonu vardır ve her organ onu kullanır; LLM organı ayrıca prompt'unu, modelini ve
  araçlarını hash'e katar (`11`: tanım hash'i prompt hash'i, model ve araç yüzeyidir).
- **Snapshot** (`snapshot.make`; seed-074): yer tutucu snapshot'ın türünü (temiz ya da ekilmiş) ele vermez. Vaka
  listesi `26`'nın `case` şemasıdır. Boş `finding_id_patterns` geçerlidir. "Yorum satırı"nın tanımı ertelenmiştir: bu
  tohum onu henüz tanımlamaz.
- **Dev vaka seti** (`cases.build`; seed-075): `<state_root>/cases/`'e bir kez yazılır ve yalnız sonuna eklenir. Bir
  vakanın modül grubu (`group`) değiştirilen dosyaya en yakın, paket manifesti taşıyan dizindir; öyle bir dizin yoksa
  birimin köküdür (bu bir sıkılaştırmadır). Vakanın ihlal kuralı operatörün hedeflediği kuraldır. Döngü başına
  önerilen vaka sayısı Kurucu'nun seçimidir; inceleyicilerden biri sabit bir sayı istedi, muhalefet kayıtlıdır.
- **Puanlama** (`harness.score`; seed-076): test 6, bulgunun bir `evidence_refs` yolu snapshot manifestinde yoksa ya
  da o yolun baytlarının hash'i manifesttekine uymuyorsa bulgunun reddedilip raporda adlandırılmasıdır. `rules_total`
  hedefin `census` vektörünün kural kümesidir (`29za:9-22`, `26q`), yalnız puanlanan vakalardakiler değil. Vektör
  karşılaştırması tablonun basamağına yarım yukarı yuvarlar (`29a`). İmza `26a`'dadır. `confidence_level` ve
  `stage_params`'ın `census_min_groups`, `planted_max_cases`, `evidence_ref_max_lines`, `match_window_lines`
  anahtarları Y'nin tesliminden okunması zorunlu yollardır: beynin politika okuması onları adlandırana kadar
  üzerlerindeki `policy_reads_required_absent` kırmızıdır (`29v`); biçimleri `26h`'dedir.
- **Test 9** (`asama-0/09`; seed-077): harness, `referee/harness/` paketi ve onun import kapanışıdır; model istemcisi
  `dispatcher/llm_call`'dur; ağı `koş` kapatır. Test 11'in sözü (`01a`'nın boş oyuncak reposu, sıfırdan büyüyen
  `<state_root>`) gevşetilmez.
