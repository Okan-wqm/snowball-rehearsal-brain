# Hafıza Modeli: Sekiz Hafıza, Tek Defter

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: yeni hafıza türü önerirken ve her defter şeması değişikliğinde
Çapa: `chain/root.jsonl`; her defter satırındaki `derivation` ve `trust` alanları

---

Sekiz hafıza vardır ama sekiz veritabanı yoktur. Tek gerçek kaynak zincirli `ledger.jsonl`'dır;
bölümleri `part` alanıyla ayrılır ve tek kök hash'e bağlanır (`13`, `26`). İtibar, ders sayaçları,
kapsama, organ durumu, hipotezler ve ithal bilgi **görünümdür**: defterden yeniden kurulur ve
harness'in bir kendi-testi onları sıfırdan kurup mevcut hâlleriyle karşılaştırır. Güvenlik kayıtları da
ayrı bir veritabanı değil, aynı defterin `security` bölümüdür (`30e`).

| # | Hafıza | Cevapladığı soru | Tohumda | Büyüme yolu |
|---|---|---|---|---|
| 1 | Episodik | Ne oldu, ne zaman, hangi koşulda, sonuç ve neden | Evet: olay defteri | "Neden" alanı mekanik çıkarımla dolar |
| 2 | Semantik | Ne nedir, neye bağlı | Hayır; etki kümesi profildeki etkilenen-test komutudur | `impact_miss` harita katmanı doğurur (`13`, `17`) |
| 3 | Prosedürel | Nasıl yapılır | Hayır | Ölçülmüş maliyet ya da başarısızlık boşluğunda skill taslağı |
| 4 | Zamansal | Ne zaman ne doğruydu | Evet: zincir, git, Rekor kökleri | `chain.asof` ilk okuyucusuyla; ölçek gerekince sembol düzeyi kimlik |
| 5 | Çalışma | Şu an ne yapılıyor | Evet: döngü durumu, kiralar | Döngü bitince kapanır; kalıcı olan episodik deftere geçer |
| 6 | Amaç ve değerler | Neden yapılıyor | Evet: çekirdek, yasalar, property'ler, anayasal politika | Büyümez; yalnız operatör yazar |
| 7 | Kaynak ve güven | Bunu nereden biliyorum | Evet: her satırda iki alan, önerilerde `origin` | Yeni türetme yolları eklenir |
| 8 | Öz değerlendirme | Nasıl performans gösteriyorum | Ölçüm evet; dersler ham satır olarak | Ders görünümü Aşama 2'de; kaçırma nedeni kategorileri |

## Öğrenmenin ölçüsü hatadır

Öğrenme, doğruyu yanlıştan ayırmak ve aynı hatayı yapmamak için vardır; daha iyisini ve daha
profesyonelini yapmanın yolu budur. Repoyu tanımak, neyin neye bağlı olduğunu çıkarmak, ders
tutmak: hepsi hata yapmamak içindir. Bu yüzden her öğrenme organı (hafıza, ders, harita katmanı,
bilgi) ancak ölçülmüş bir hata oranını düşürüyorsa ya da aynı maliyette kaliteyi artırıyorsa
kalır (Y5): geri alma, regresyon, FP, `impact_miss`, unresolved. Bunlardan hiçbirini oynatmayan
organ canlı yoldan çıkar; tanımı zincirde kalır.

## Tohumda zorunlu şema alanları

Her defter satırı, hangi hafızaya ait olursa olsun, şu alanları taşır:

- `derivation`: `tool` | `static_analysis` | `test_verified` | `llm_inference` | `name_similarity`
  | `imported`.
- `trust`: `verified` | `observed` | `inferred`. Merge kararına giren kanıt yalnız `tool`,
  `static_analysis` ya da `test_verified` kaynaklı olabilir. `llm_inference`, `name_similarity` ve
  `imported` yalnız "buraya bak" ipucudur; etki kümesine girebilir, güvenlik kararını taşıyamaz.
- `snapshot_id` ve `evidence_refs`.
- `cause`: başarısız ya da geri alınan olaylarda zorunlu; kapalı küme `26`'dadır. Nöbetçi, test
  çıktısı ve diff'ten mekanik çıkarılır; çıkarılamıyorsa `unknown`; LLM tahmini buraya yazılmaz.
- Öneri, ders ve bilgi satırlarında ayrıca `origin`: `repo_pattern` | `llm_prior` | `synthesis` |
  `own_outcome` (`21a`).

Bu alanlar ilk günden vardır, çünkü sonradan eklemek bütün geçmişi yeniden yazmak demektir.

## Hipotez ve ithal bilgi görünümdür, organ değil

Okuma hipotezleri, sandbox deney sonuçları ve başka repodan ithal bilgi tohumda organ olarak
verilmez; sinyali doğunca (`17`) defterin görünümü olarak açılır. Her biri `trust: inferred`
taşır, merge kararına kanıt olamaz (Y1); yürütmeyle doğrulanınca yeni bir `verified` satırıyla,
çürütülünce "şu koşulda yanlış" satırıyla kalır. İkisi de saklanır.

## Çalışma hafızası

Döngü başında açılır, sonunda kapanır: açık mikro görevler, her görevin kirası (hangi ajan, ne
zamana kadar), beklenen sonuçlar, `blocked` listesi. Kirası dolan görev serbest kalır ve deftere
düşer. Kapanmayan çalışma hafızası bayat gerçektir; sonraki döngü önce onu temizler.

## Kişisel hafıza yoktur

Ajanlar koşu başına durumsuzdur. Kişisel hafıza bağımsızlığı ve tekrar üretilebilirliği bozar;
rakibin aynı geçmişi taşıması korelasyonlu yanılma üretir. Bir ajanın geçmişi defterde ve
soyağacında durur; ortak proje hafızası herkesindir. Derslerin yapısı ve okuyucuları `22`'dedir.
Yeni hafıza türünün tetiği `17`'deki sinyallerdir; gerekliliği ablasyonla kanıtlanır (`12`).
