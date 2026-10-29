# Maliyet Merdiveni ve Bütçe

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: bir yetenek harness'te geçtikten sonra ve her bütçe kararında
Çapa: `ledger.jsonl` `part: cost` satırları; `policy.json` bütçe payları

---

Bir yetenek harness'te eşiği tutunca aynı yeteneğin daha ucuz basamakları sırayla denenir.
Sıra, kazancın büyüklüğüne göredir:

1. **Önbellek, varsayılan.** Prompt önbelleği her koşuda açıktır; girdi maliyetinin büyük
   kısmını siler ve bir basamak değil, zemin şartıdır.
2. **Küçük model.** Aynı prompt, Opus yerine Sonnet. Üretici-yargıç-oracle ayrıklığı korunur
   (`09a`); avcı Sonnet'e inerse karşı koltuklar avcıdan farklı modele, yani Opus'a çıkar ve
   basamağın maliyeti bu takas edilmiş modellerle hesaplanır. Ayrıklığı bozan iniş yapılmaz.
3. **Kısa prompt.**
4. **Mekanik dedektör.** Bulunan sınıf için LLM'siz dedektör; tek büyük tasarruf budur
   (Aşama 3'ten itibaren).
5. **Dar kapsam, kapsama tabanıyla.** Yalnız dev koşularının okuduğu dosyalardan türetilen glob;
   görülmeyen dosya payı artıyorsa bu basamak reddedilir, çünkü kör noktayı pekiştirir.

**Basamağın maliyeti bütündür.** Bir basamağın USD'si avcı + panel + oracle maliyetidir ve karara
bağlanmış bulgu başına hesaplanır. Maliyeti panele ya da oracle'a iten bir basamak yalnız avcı
maliyetine bakılırsa ucuz görünür; bu yüzden yalnız bütün maliyet sayılır.

**Karşılaştırma kuralı.** Her basamak önce dev setinde, aynı vakalarda eşli olarak denenir ve
`19`'daki non-inferiority kuralıyla doğrulanır: sabit marj δ = 0,05 (anayasal), tam test, en az
45 eşli vaka. Eşiği tutan en ucuz basamak üretim basamağı olur. Pahalı basamak silinmez;
bilinmeyen sınıfları aramak için keşif basamağı olarak kalır. Başarısız basamak deftere yazılır ve
vaka havuzu yarı yarıya büyüyünce bir kez daha denenir. **Her basamağın denenip başarısız olması
`FAIL`'dır**, geçiş değil: o sınıf o modelle ucuzlamıyor demektir ve mekanik dedektör üretimi
önceliğe geçer. Panelin faz 1 ve 2'si en ucuz modelde koşabilir.

**Ölçü.** USD / isabet değil, şiddet ağırlıklı değer / USD (`20`); yoksa sistem ucuz ve önemsiz
işi öğrenir. Maliyeti sıfır olan organlar (mekanik adapter, araç yolu) bu oranla değil, isabet ve
kapsama ile karşılaştırılır; sıfıra bölme sonsuz değer üretmez.

**Held-out bakışı.** Basamaklar dev setinde karşılaştırılır; held-out'a yalnız kazanan basamak,
bir bakışla gider (`19`).

**Bütçe.** Aylık USD tavanını ve aylık CI dakikası tavanını operatör koyar (`policy.json`,
anayasal; `18a`). Paylar başlangıçta: keşif ≤ %30, üretim ≤ %40, ölçüm ≤ %20, genel ≤ %10. Ölçüm
payı ablasyon, held-out koşuları ve panel kalibrasyonunu içerir. Aşama bütçeleri yargılama ve
oracle maliyetini de kapsar; "koşu başına" tavanlar bunların toplamını aşamaz.

İnşa-zamanı LLM bütçesi (Kurucu ve rakip) ile çalışma-zamanı LLM bütçesi (sistemin kendisi) ayrı
kalemlerdir; Aşama 0'ın çalışma-zamanı LLM maliyeti yalnız (B)'deki `llm.call` kanaryasıdır. Bütçe
tavanı istemcinin tahmini değil, sağlayıcı geçidinin ya da `çağır` işinin yanıttan ölçtüğü maliyettir
(`08`). İç kullanımda (API anahtarı yokken) her model çağrısının maliyeti `claude` CLI'sinin liste
fiyatı tahminidir, faturalanan tutar değildir; zaman aşımında çağrı başı tavan yazılır. Kurucu
oturumları Actions dakikası harcamaz (`24`).

**İç kullanımda bütçe kaçak frenidir, kısıt değil.** Sistem abonelikle, `claude` CLI'siyle koşar. Tavanlar
olağan işi hiçbir zaman durdurmayacak kadar yüksek kurulur; işleri döngüyü kesmektir (aynı commit'in
saatte bir yeniden koşması, art arda yinelenen rakip çağrıları). Sayılar `policy.json` anahtarıdır
(`18a`); frene takılan iş durur ve operatör uyarılır, Kurucu'nun reddi değildir. Oturum sayısı ve USD
toplamları ilerlemenin ve maliyetin **ölçüsüdür**: çıkış koşulu değildir, Kurucu'yu durdurmaz; sonraki
oturum öncekinin sonucu yeşilken başlar. Gerçek sınır aboneliğin kullanım penceresidir (5 saatlik ve
haftalık kota): ona takılmak (HTTP 429) operatör uyarısı ve kesintidir, Kurucu reddi ya da ret hafızasına
giren bir neden değildir (`29b`, `asama-0/12`). Satışta API anahtarına geçilince tavanlar fatura
sınırı olur.
