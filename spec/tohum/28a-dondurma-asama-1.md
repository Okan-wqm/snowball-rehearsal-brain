# Dondurma, Devam: Aşama 1'de Gözcü

Tarih: 2026-11-21 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Gözcü (P1 MF7) yazılırken ve test 41 okunurken
Çapa: beklemede: P1 aktarımı (Gözcü) — `gozcu/evaluate.py`, test 41

---

`28`'in Aşama 1'deki hâli (bağımsız inceleme ekibi kararı (2026-11-21), seed-084, seed-085). Arayüz olgularıdır; kodun nasıl
yazılacağı Kurucu'nundur. Satırların, kapsamın ve görünümlerin biçimi `26i`'dedir. Bu sayfa `28` ile çelişirse bu sayfa
geçerlidir (`02`).

**Aşama 1'in yargıladıkları.** Gözcü, ölçüsü ve kaynağı bir sayfada olan her kuralı yargılar:
- **Regresyon** (`20`, `18a`): `window_days` penceresinde `M` merge ve `R` geri alma varken, `M` ≥ `min_merges` ise
  `R` > `revert_rate` × `M`, değilse `R` ≥ `min_reverts` bir yumuşak dondurmadır. Sayım bütün sınıfları birlikte sayar;
  kapsam sayılan geri almaların sınıflarıdır (`26i`).
- **USD bütçesi** (`06`): ayın harcaması (`26i`) `monthly_cap_usd` × 1.000.000 mikro USD'ye ulaşınca (≥) bütçe
  dondurması. Kendi kalkışı vardır (aşağıda).
- **`soft_freeze_limit`**: başlangıcı pencerede olan yumuşak dondurmalar, kalkmış olsun olmasın ve bütçe dondurması
  dahil, bu çağrının başlattıklarıyla birlikte sayılır; sayı `soft_freeze_limit`'ten büyükse sert duruştur.
- **Devredilen sert duruş olguları** (`28` "Sert duruş"): kurulum kayması, zincir kırığı, Rekor'a ya da attestation'a
  yazılamama, etkinleştirme ya da aktarım hatası, beyan dışı bir aktörün `brain/*` ref değişikliği, kill switch. Onları
  başka denetimler bulur; Gözcü kanıtlarını `hard_stop` satırına kopyalar.
- **Kapsayıcılık dondurması** (`08`), eşik kayması, koltuk benzerliği ve genesis işaretleri (`28` "İşaret"): kuralları
  vardır ve yargılanır; görünümleri Aşama 1'de boştur (`26i`; seed-085 e).

**Pencereler.** Kapsayıcılık dondurmasının ve `soft_freeze_limit`'in penceresi `performance.windows.measure` gündür
(`18b`), regresyonunki `window_days`'tir. `d` günlük pencere `now − d·86400 < ts ≤ now` olan satırlardır: başında
açık, `now`'da kapalı.

**Kalkış.** Bütçe dondurması kendiliğinden kalkar: kuralı yargılanıp artık tetiklenmeyince (ay döndü ya da operatör
tavanı yükseltti, `28`) Gözcü bir `lift` satırı yazar. Regresyon ve kapsayıcılık dondurması Aşama 1'de kalkmaz:
kalkışları sonda döngüsüdür (`28`) ve o Aşama 1'de yoktur (L3); dondurma yürürlükte kalır.

**Anahtarlar.** Yaprak adları `18a` ve `18b`'dedir: `constitutional.regression_freeze` `{min_merges, window_days,
revert_rate, min_reverts}`, `performance.rules.genesis_drafts` `{per_window, queue}`; `soft_freeze_limit` ve
`containment_freeze` `18a`'nın `constitutional.gate_rules` satırlarıdır. Kesirler `01c`'nin biçimindedir
(`revert_rate` `"0.020000"`). Aşama 1'in zorunlu yedi Gözcü yolu: `constitutional.monthly_cap_usd`,
`constitutional.regression_freeze`'in dört yaprağı, `constitutional.gate_rules.soft_freeze_limit` ve
`performance.windows.measure` (`29v`). Biri yoksa ya da biçim dışıysa politika kullanılamaz ve döngü ilk yazımından önce
temiz durur (`29v` "Döngüde eksik anahtar"); bu asla "yargılanmadı, devam" değildir. Öbür Gözcü anahtarları Aşama 1'de
zorunlu değildir: yoksa kuralları `unjudged` olarak adlandırılır, duruş değildir.

**Test 41** (P1 MF7) böyle okunur: Aşama 1'in yargıladığı her kural sentetik girdide doğru dondurmayı, kalkışı ya da
sert duruşu verir. MF7'nin vektör grubu yoktur (`26e`).

**Aşama 1'de olmayanlar** (operatör kararı, sahibin yetkisiyle (2026-11-21)).
- **L1, salınım birikimi.** Hiçbir sayfada ölçüsü yoktur. Kaynağı `findings.jsonl`'un durumlarıdır (`07`: üç kez
  `reopened` olan bulgu salınımdır); yazıcısı P1 MF8'dir (`26h`), MF7'den sonra. Ölçüsü, penceresi ve anahtarı MF8'den
  sonraki bir tohum dönemiyle gelir; şimdi anahtarı yoktur.
- **L2, Actions dakikasının kaynağı.** Hiçbir sayfa dakikanın okumasını adlandırmaz: dakika ölçülmez ve devrin
  çıktısı onu ölçülmemiş olarak adlandırır (seed-085 d). Fren GitHub harcama sınırı olarak kalır (`25` 8). Okumayı
  adlandıran bir sayfayla gelir.
- **L3, sonda döngüsü ve kalkışı** (`28`, `performance.rules.probe_cycle`): P3'ün tablosunun bir satırı olarak gelir
  (`26h`; seed-085 g).
