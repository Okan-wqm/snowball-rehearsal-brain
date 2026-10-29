# Aşama 4 §4.11 — Bütçe (başlangıç; yalnız operatör değiştirir)

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: hedef taslak · Sahibi: operatör
Okunma: Aşama 4 çalışırken
Çapa: beklemede: aşama 4 çıkış raporu

---

| Kalem | Tavan |
|---|---|
| Avcı koşusu | snapshot başına dev'de ölçülen ortalamanın 1,5 katı, en çok 8 USD ve 40 dk; `maxTurns` `policy.json`'da; prompt önbelleği zorunlu |
| Panel, faz 2–4 | bulgu başına dev ortalamasının 1,5 katı, en çok 3 USD; koltuk başına tek oturum, effort `low` |
| Oracle, faz 5 | bulgu başına ≤ 4 USD ve ≤ 20 dk |
| Dev döngüsü toplamı, panel ve oracle dahil | ≤ 600 USD |
| Exit koşusu | 1,5 × dev'de ölçülen snapshot başına (avcı + panel + oracle) × snapshot sayısı; ≤ 30 held-out ve 30 clean ile kanarya snapshot, birer koşu; en çok 800 USD |
| Maliyet inişi, yargılama dahil | ≤ 500 USD; yargılanmış parmak izleri yeniden kullanılır |
| İnşa-zamanı: Kurucu | ≤ 300 USD ve ≤ 25 oturum; rakip ≤ 30 USD |
| Aşama toplamı | aylık tavanın keşif ve ölçüm paylarının içinde |
| Takvim | oturum sayısıyla; K5 penceresi 14 gün; ileriye dönük havuzun dolma süresi ayrıca raporlanır |

Exit tavanı dev ölçümünden türetilir, çünkü önceden yazılmış snapshot başına tavan ile bulgu başına
yargılama tavanı birlikte bütçeyi aşabilir; türetilmiş tavan 800 USD'yi aşıyorsa exit koşulmaz ve
neden raporlanır.
