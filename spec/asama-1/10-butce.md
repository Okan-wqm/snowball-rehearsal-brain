# Aşama 1 §1.10 — Bütçe (başlangıç değerleri; yalnız operatör değiştirir)

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 1 çalışırken
Çapa: beklemede: aşama 1 çıkış raporu

---

| Kalem | Tavan |
|---|---|
| Adapter koşusu | 0 USD; ≤ 15 dk |
| Sonnet düzeltmesi | Bulgu başına ≤ 0,50 USD ve ≤ 5 dk; sınırı `llm.call`'ın bütçe belirteci uygular |
| Çalışma-zamanı LLM, aşama toplamı | ≤ 50 USD |
| İnşa-zamanı LLM: Kurucu | ≤ 150 USD; oturum başına tavan `policy.json`'da |
| İnşa-zamanı LLM: tohum rakibi | ≤ 15 USD |
| Actions dakikası | Döngü başına ≤ 45 dk; döngü sıklığı aylık anayasal tavandan türetilir (`policy.json`) |
| Operatör emeği | 0 |
| Takvim | ≤ 12 Kurucu oturumu; 72 saatlik hayatta kalma penceresi takvime eklenir |
