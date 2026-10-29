# Aşama 1 §1.4 — Roller

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 1 çalışırken
Çapa: beklemede: aşama 1 çıkış raporu

---

| Rol | Ne yapar | Ne yapamaz |
|---|---|---|
| Kurucu, Opus | Oyuncu organlarını ve testlerini yazar: lint adapter, taban, iki düzeltici yolu, aday paketi, `docs.render`. Parti adaylarını (§1.13) beyin reposunda `referee/` altında yazar. Her push önyükleme hakeminden geçer (`tohum/29b`) | Puanlayamaz, merge edemez, eşik değiştiremez, aktaramaz; hakem reposuna yazmaz |
| Önyükleme hakemi | Beyin reposunun itme yargıcı: her push'ta testler, vektörler, modülsüz kırmızı, tohum rakibi; kabul edilen SHA'yı imzalar | Hedefe yazmaz; aktarımla değişmez, yalnız tohum dönemiyle |
| Döngü hakemi, aktarılmış | Yoklar; `çek`, `getir`, `koş`, `çağır`, `yaz` işlerini koşar; kapıyı uygular, merge eder, nöbetçiyi koşar, geri alır, defter ve Rekor yazar; durum bloğu; P1'den sonra Gözcü ve kayma | Yalnız parti ya da aşama çıkışındaki aktarımla değişir |
| Lint adapter | Mekanik; aracı koşar, çıktıyı bulgu önerisine çevirir | LLM çağıramaz |
| Düzeltici, `fix` aralığı yolu | Aracın hedef mesajdaki `fix` aralığını deterministik uygular | Aralık dışına yazamaz |
| Düzeltici, Sonnet yolu | Prompt şablonunu ve yapılandırılmış düzenleme şemasını verir; çağrıyı hakemin `llm.call`'ı yapar; deterministik uygulayıcı çıktıyı yalnız hedef dosyanın o aralığına yazar | Aracı yoktur; bulgu dışı satıra ve test yollarına yazamaz; ders almaz |
| Tohum rakibi, Sonnet, ayrı bağlam | Kurucu'nun her beyin push'unu önyükleme hakeminin yolunda çürütmeye çalışır; çürütmesi yeniden üreticiyle sayılır | Çalışma zamanındaki düzeltmeleri yargılamaz: K0'da yargıç aracın kendisidir (`tohum/10`) |
| Gözcü, deterministik | P1 ile: `tohum/28` kuralları | LLM değildir |
| Güvenlik avcısı | P2 ile: bağımsız, salt okunur gözlem (`tohum/30f`) | Düzeltmez |
| Operatör | Döngü dışı; parti ve çıkış aktarımları, `stage-open` | Onay vermez |
