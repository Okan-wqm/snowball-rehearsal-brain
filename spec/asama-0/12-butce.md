# Aşama 0 §0.12 — Bütçe (başlangıç değerleri; yalnız operatör değiştirir)

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken
Çapa: beklemede: aşama 0 çıkış raporu

---

| Kalem | Tavan |
|---|---|
| Çalışma-zamanı LLM | 0. Kendi testlerindeki `llm.call` ve dispatch kanaryası çağrıları inşa-zamanı kalemindendir |
| İnşa-zamanı LLM: Kurucu | ≤ 300 USD; oturum başına tavan `policy.json`'da (başlangıç 20 USD) |
| İnşa-zamanı LLM: tohum rakibi (Sonnet) | ≤ 30 USD |
| Actions dakikası | Anayasal aylık tavanın içinde (`monthly_cap_ci_minutes`, başlangıç 1.800); önyükleme koşusu push başına ≤ 20 dk |
| Harness koşusu | Tek snapshot ≤ 15 dk; 20 snapshot ≤ 2 saat |
| Operatör emeği | Kurulumun birinci bölümü; çıkışta aktarım ve ikinci bölüm; arada 0 |
| Takvim | ≤ 30 Kurucu oturumu; sonraki oturum öncekinin önyükleme sonucu yeşilken başlar; aşım spec'i gevşetmez |

Kurucu oturumları Actions'ta koşmaz (`tohum/24`); dakika tavanı yalnız hakem işlerine aittir.
Tavana varılınca iş temiz durur ve Gözcü bunu bütçe dondurması olarak yazar. Tablodaki değerler
`stage_budgets.asama_0`'dır ve aşama toplamıdır; aylık tavan (`monthly_cap_usd`) ayrıca bağlar:
dolunca bütçe dondurması gelir ve takvim uzar. Kurucu maliyetinin ölçümü `tohum/24`'tedir.
