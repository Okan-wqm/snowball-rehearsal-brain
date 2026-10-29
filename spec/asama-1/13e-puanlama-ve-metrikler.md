# Aşama 1 §1.13e — P1: Puanlama ve metrikler

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: P1 partisi yazılırken ve Aşama 1 çalışırken
Çapa: beklemede: aşama 1 çıkış raporu

---

Bu sayfa Aşama 0 2.2'nin §0.8'inin puanlama ve metrik kısmıdır; P1 partisiyle gelir (§1.13). Eşlenmiş
satırın tanımı Aşama 0'da kalır (`asama-0/08`).

**`match-rule v2`, sürümlü.**

- **K0–K2:** bulgu, vakayı ancak `tool`, `rule_id` ve hunk üzerinden eşlenmiş satır aynıysa
  isabet eder; dokuz yüz ihlali döken bir adapter tesadüfen isabet alamaz.
- **K3 ve üstü:** `evidence_refs`'ten biri vakanın dokunulan dosyasında ve aynı sembolde ya da
  hunk'ın ±`stage_params.match_window_lines` (15) satırı içinde; `property` eşit; `required_change` dolu.
- Bir bulgu en fazla bir vakayı, bir vaka bir koşuda en fazla bir kez.

| Metrik | Tanım |
|---|---|
| `census` | Deterministik sarıcı sınıflarda (K0, K1, K2, K4) çıkış ölçüsü: kapsanan kural sayısı, toplam kural, kaçırma. Kapı: her kural kapsanmış, kaçırma sıfır |
| `recall`, `recall_lb` | İsabet / planted. Tek yönlü Clopper–Pearson alt sınırı; etkin n = grup sayısı G, etkin başarı `x_eff = recall · G` (gerçel argümanlı Beta). Sayım sınıflarında raporlanır, kapılamaz |
| `clean_findings` | Clean'deki her bulgu sayılır; hiçbiri sayımdan düşürülmez |
| `precision`, `precision_lb` | n = TP + FP + unresolved; unresolved FP gibi sayılır. Aşama 4'ten itibaren panelin öldürdüğü bulgulardan rastgele bir örnek oracle'la denetlenir ve sonucu sayıma girer |
| `cost_usd`, `value_per_usd` | Şiddet ağırlıklı değer / USD; basamak USD'si karara bağlanmış bulgu başına avcı + panel + oracle'dır. Maliyet sıfırsa oran raporlanmaz, isabet ve kapsama karşılaştırılır |
| `verdict` | `PASS` / `FAIL` / `UNMEASURABLE` |

**Görünümler.** Vaka bazlı görünüm yalnız hakemde kalır; Aşama 4'ten itibaren held-out'unki
mühürlü depodadır. Ajan görünümü toplamlardır. K0 çıkışı her seferinde taze bir örneklemdir; bu
yüzden kaçırılan kurallar raporlanır: deterministik sarıcıda kaçırma bir kural kusurudur ve
sonraki çıkış yeni tohumla çekilir. Held-out havuzlu sınıflarda bir bakış yalnız verdict
döndürür; kaçırma nedenleri yalnız dev koşularından gelir (`tohum/19`).

**Maliyet bölümü.** `ledger.jsonl`'ın `cost` bölümü Aşama 0'dan beri her çağrıya satır ekler
(`asama-0/14` MF15). Okuyucuları: frenler ve P1'den Gözcü (frende temiz duruş), Aşama 4 partisinden taban
satırı, Aşama 3'ten itibaren maliyet merdiveni.
