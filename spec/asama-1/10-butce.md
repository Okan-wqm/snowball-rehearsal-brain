# Aşama 1 §1.10 — Bütçe (kaçak freni; değerleri yalnız operatör değiştirir)

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 1 çalışırken
Çapa: beklemede: aşama 1 çıkış raporu

---

Bütçe Aşama 0'daki gibi bir kısıt değil, kaçak frenidir (`asama-0/12`): olağan işi durdurmayacak kadar
yüksek kurulur, döngüyü keser. Değerler `stage_budgets.asama_1` ve anayasal anahtarlardır; tablo
başlangıç fren değerlerini verir. USD liste fiyatı tahminidir (`tohum/06`).

| Kalem | Başlangıç fren değeri |
|---|---|
| Adapter koşusu | 0 USD; `operating{}` sınırları (`kos_wall_s`) |
| Sonnet düzeltmesi | Bulgu başına 0,50 USD ve 5 dk; sınırı `llm.call`'ın çağrı başı tavanı uygular (iç kullanımda `claude` CLI'sinin `--max-budget-usd`'si) |
| Çalışma-zamanı LLM, aşama toplamı | 50 USD |
| İnşa-zamanı LLM: Kurucu | aşama toplamı 150 USD; oturum başına `session_cap_usd` |
| İnşa-zamanı LLM: tohum rakibi | 15 USD |
| Actions dakikası | Döngü başına `cycle_caps`; döngü sıklığı aylık anayasal tavandan türetilir (`policy.json`) |
| Operatör emeği | Parti ve çıkış aktarımları, `stage-open`; her biri sayılır |

**Ölçüm, kapı değil.** Kurucu oturum sayısı, USD toplamları ve takvim (tahmin: yaklaşık 12 oturum, artı
partiler ve hayatta kalma penceresi) ölçüdür; çıkış koşulu değildir, Kurucu'yu durdurmaz. Frene takılmak
operatör uyarısıdır, ret değil; olağan işse operatör değeri yükseltir.

**Gerçek sınır abonelik penceresidir.** 5 saatlik ya da haftalık kotaya takılmak (HTTP 429) operatör
uyarısı ve kesintidir; Kurucu reddi ya da kapı nedeni değildir.
