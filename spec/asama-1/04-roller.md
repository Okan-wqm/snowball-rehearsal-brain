# Aşama 1 §1.4 — Roller

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 1 çalışırken
Çapa: beklemede: aşama 1 çıkış raporu

---

| Rol | Ne yapar | Ne yapamaz |
|---|---|---|
| Kurucu, Opus | Oyuncu organlarını ve testlerini yazar: lint adapter, taban, iki düzeltici yolu, aday paketi, `docs.render`. Her değişiklik `brain.accept`'ten geçer | Puanlayamaz, merge edemez, eşik değiştiremez; hakem reposuna ve `referee/`'ye yazmaz |
| Hakem, aktarılmış ve donuk | Yoklar; `çek`, `getir`, `koş`, `çağır`, `yaz` işlerini koşar; kapıyı uygular, merge eder, nöbetçiyi koşar, geri alır, defter ve Rekor yazar; Gözcü ve durum bloğu | Bu aşamada değişmez |
| Lint adapter | Mekanik; aracı koşar, çıktıyı bulgu önerisine çevirir | LLM çağıramaz |
| Düzeltici, `fix` aralığı yolu | Aracın hedef mesajdaki `fix` aralığını deterministik uygular | Aralık dışına yazamaz |
| Düzeltici, Sonnet yolu | Prompt şablonunu ve yapılandırılmış düzenleme şemasını verir; çağrıyı hakemin `llm.call`'ı yapar; deterministik uygulayıcı çıktıyı yalnız hedef dosyanın o aralığına yazar | Aracı yoktur; bulgu dışı satıra ve test yollarına yazamaz; ders almaz |
| Tohum rakibi, Sonnet, ayrı bağlam | Kurucu'nun her beyin kodu değişikliğini `brain.accept` yolunda çürütmeye çalışır; çürütmesi yeniden üreticiyle sayılır | Çalışma zamanındaki düzeltmeleri yargılamaz: K0'da yargıç aracın kendisidir (`tohum/10`) |
| Gözcü, deterministik | `tohum/28` kuralları | LLM değildir |
| Operatör | Döngü dışı | |
