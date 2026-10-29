# Aşama 4 §4.9 — Çıkış testi, ikinci kapı: maliyet inişi

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: hedef taslak · Sahibi: operatör
Okunma: Aşama 4 çalışırken
Çapa: beklemede: aşama 4 çıkış raporu

---

Birinci kapı geçince maliyet mühendisi merdiveni koşar (`tohum/06`): önbellek zaten açık; küçük
model (avcı Sonnet'e inerse karşı koltuklar ve oracle Opus'a çıkar ve panel maliyeti bu takasla
fiyatlanır); kısa prompt; TP'lerden üretilen mekanik dedektör; kapsama tabanlı dar kapsam.

Her basamak aynı dev vakalarında eşli denenir ve tam (exact) non-inferiority testiyle, anayasal
sabit marj δ = 0,05 ve n ≥ 45 ile doğrulanır. Basamağın USD'si avcı, panel ve oracle maliyetinin
karara bağlanmış bulgu başına toplamıdır; panele itilen maliyet basamağı ucuz göstermez.
Held-out'a yalnız kazanan basamak gider ve bir bakış harcar. Birinci kapıyı tutan en ucuz basamak
üretim basamağı olur; tutmayan basamak deftere yazılır ve vaka havuzu yarı yarıya büyüyünce bir
kez daha denenir.

**İkinci kapı PASS:** en az bir basamak non-inferiority'yi geçer ve değer / USD'si keşif
basamağınınkinden yüksektir. **FAIL:** her basamak denenmiş ve hiçbiri geçmemiştir; bu, sınıfın bu
modelle ucuzlamadığının ölçülmüş cevabıdır, Aşama 4'ü bitirmez ve mekanik dedektör üretimine
sinyal olur (`tohum/17`). Gerekçe: pahalı bulmak bir kez kabul edilir; ikinci kez aynı maliyet,
ölçülmemiş bir tercihtir.

| Koşul | Kural |
|---|---|
| #non-inferiority Daha ucuz basamak | Aynı dev vakalarında eşli, tam non-inferiority; δ = 0,05, n ≥ 45 (`tohum/19`) |
| #genesis-buyume #genesis-budama #genesis-yeniden #genesis-sessizlik Genesis provası | TP'den üretilen dedektör K5'te ikinci adaydır; yaşam döngüsü canlıya girmeden `tohum/12a`'nın dört sorusu geçer |
