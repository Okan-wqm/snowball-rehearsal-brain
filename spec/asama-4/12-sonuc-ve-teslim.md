# Aşama 4 §4.12 — Sonuç ne söyler ve teslim listesi

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: hedef taslak · Sahibi: operatör
Okunma: Aşama 4 çalışırken
Çapa: beklemede: aşama 4 çıkış raporu

---

- **İki kapı PASS:** kalıpsız LLM gerçek hatayı buluyor ve daha ucuza tekrar buluyor; Aşama 5
  için ölçülmüş taban ve maliyet tabanı var.
- **Birinci kapı FAIL, recall düşük:** avcı spec'i repoya çeviremiyor; `repo_model.md` ve kaçırma
  nedeni kategorileri okunur; spec belirsizliği, model yetersizliği ve snapshot bilgi eksikliği
  ayrı test edilir.
- **Birinci kapı FAIL, precision düşük:** avcı kalıp kontrolcüsü gibi davranıyor;
  `required_change` ve clean koşular bunu ölçmek için var.
- **İkinci kapı FAIL:** bu sınıf bu modelle ucuzlamıyor; mekanik dedektör üretimi önceliklidir.
- **UNMEASURABLE:** ileriye dönük havuz dolmadı ya da vaka arzı yetersiz; bekleme süresi ve
  sinyal genesis'e gider.

**Teslim:** `properties/P.md`; `hunters/hunter-v1/prompt.md`, `prompt-ledger.jsonl`; `runs/`;
`panel/` kararları; `oracle/` testler, düzeltmeler, `fp-corpus.jsonl`, `unresolved.jsonl`, yeni
vaka adayları; `ledger.jsonl` `cost` ve `looks` satırları; mühürlü depoda mühür, havuz ve ham
çıktılar; hakem reposunda Savunma, Uygulayıcı temsilcisi ve test-yazıcı koltukları; üretilmiş
bulgu sayfaları; `asama-4/` altında tarihli çıkış raporu (iki kapı).
