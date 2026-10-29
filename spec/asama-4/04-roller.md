# Aşama 4 §4.4 — Roller

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: hedef taslak · Sahibi: operatör
Okunma: Aşama 4 çalışırken
Çapa: beklemede: aşama 4 çıkış raporu

---

| Rol | Model | Ne yapar | Ne yapamaz |
|---|---|---|---|
| Kurucu | Opus | Avcı promptunu yazar, dev setinde yineler, exit talep eder | Held-out sonucunda verdict dışında bir şey göremez; hakeme yazamaz |
| Avcı | Opus, keşif basamağı | Tek ajan; snapshot içinde `Read`, `Grep`, `Glob`; her koşu soğuk, dispatch sözleşmesiyle | Alt ajan, yazma, ağ, önceki koşu çıktısı yok; exit'te ders yok |
| Savcı | Avcıyla aynı olabilir | Bulgunun gerçek olduğunu kanıtlar; avcıyla aynı taraftadır | |
| Savunma | ≠ avcı, ayrı bağlam | Yanlış, erişilemez ya da kasıtlı olduğunu kanıtlar; avcının promptunu görmez | Testi yazamaz |
| Uygulayıcı temsilcisi | ≠ avcı, ayrı bağlam | Düzeltme maliyeti, etki kümesi, katman iddiası; düzeltme tasarımına referanslı en az bir alternatif | |
| Test-yazıcı ve oracle düzelticisi | ≠ avcı, Savunma'dan ayrı bağlam | Tohum koltuğu (`tohum/29`); girdi property ve konum; `tohum/04a` | Ders okumaz; Savunma'nın çıktısını görmez |
| Implementer | Opus | Kalıcı düzeltmeyi kök neden kuralıyla yazar (`tohum/23`) | Testi değiştiremez |
| Maliyet mühendisi | Sonnet | Merdiveni koşar | Eşik değiştiremez |
| Gözcü | Deterministik | `tohum/28` | |

Karşı koltuklar ve oracle avcıdan farklı modeldedir; ayrıklık `run_meta` ile kapıda doğrulanır
(`tohum/09a`). Avcı Sonnet basamağına inerse karşı koltuklar ve oracle Opus'a çıkar; o basamağın
panel maliyeti takas edilmiş modellerle fiyatlanır (§4.9).

Savunma ve Uygulayıcı temsilcisi koltuklarını şerit yazarı taslaklar; rakipten ve kanaryadan
geçen taslak operatör aktarımıyla hakem reposuna girer ve orada donar (`tohum/09a`).
