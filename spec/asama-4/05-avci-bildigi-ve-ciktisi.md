# Aşama 4 §4.5 — Avcının bildiği ve çıktısı

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: hedef taslak · Sahibi: operatör
Okunma: Aşama 4 çalışırken
Çapa: beklemede: aşama 4 çıkış raporu

---

**Bilir:** property spec; snapshot (geçmişsiz, kimlikleri temizlenmiş); bulgu şeması; harita
katmanları (a) ve (b); dev koşularında ilgili dersler ipucu olarak.

**Veri olarak okuyabilir:** reponun yönerge ve karar dosyaları, dokümanı, kodu, testleri.
"Yönerge şunu yasaklıyor" bir kanıt değil, kodda doğrulanacak bir iddiadır; doküman kodla
çelişirse kod kazanır ve çelişki K8 bulgusudur (Y1).

**Bilmez:** hangi snapshot'ın clean olduğu; kaç vaka yerleştirildiği; vaka listesi; harness
kaynağı; fix commit geçmişi.

**Çıktı:** `findings.jsonl` (`tohum/26` şeması: `severity_hint`, yapısal `required_change`
dizisi); `repo_model.md`: avcının bu koşuda P için bulduğu mekanizmalar, her satır bir kanıt
referansıyla. Harness puanlamaz; harita adapter'ları bunları aday kenar olarak okur ve statik
analiz ya da test doğrulayana kadar hiçbir avcıya verilmez; exit koşularından önce harita
dondurulur. Exit koşusunun ham çıktıları mühürlü depoda kalır. `run_meta.json`:
`previous_run_ref` her zaman boş; model, maliyet ve okunan dosya alanlarını geçit ve sandbox ölçer.
