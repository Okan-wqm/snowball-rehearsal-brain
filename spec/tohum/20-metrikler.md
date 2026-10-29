# Metrikler: Bir Bakım Sistemi Neyi Sayar

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: `status.md` üretilirken ve her Gözcü değerlendirmesinde
Çapa: `status.md` bölümleri; `ledger.jsonl` `part: cost` ve `part: events` satırları

---

Recall ve precision planted vakalar üzerinde ölçülür ve yalnız bilineni ölçer. Bir bakım sistemi
şunları da sayar; hepsi `status.md`'de, hepsi defterde ve her döngünün kök kaydında.

| Metrik | Tanım | Kullanımı |
|---|---|---|
| Regresyon oranı | 100 merge başına geri alma ve nöbetçinin sisteme bağladığı kırmızı, 30 gün | Anayasal: `regression_freeze` → yumuşak dondurma (`28`) |
| Etki kaçırması | `impact_miss` geri almaları / merge; kırmızının nedeni beyan edilen etki kümesi dışında | Harita adapter'ının doğum sinyali ve hata ölçüsü (`13`, `17`) |
| Kaçış oranı | Sistemin taradığı dosyalarda, hata oradayken insanların yazdığı düzeltmeler; property başına | Her kaçış yeni vaka; farklı modelli avcıların yakalamaları arasında capture–recapture ile gerçek kaçırma tahmini |
| Değer / USD | Şiddet ağırlıklı hayatta kalan sonuç (`severity_map`) bölü USD; bir basamağın USD'si avcı + panel + oracle maliyetidir, karara bağlanmış bulgu başına | USD / isabetin yerine; itibar ve merdiven bunu okur |
| Düzeltme süresi | Bulgudan merge'e medyan ve p90, sınıf başına; `blocked` işlerin yaşı | Gözcü eğilimi |
| Risk ağırlıklı kapsama | Dosya × property × sınıf; güvenlik yolları ağırlıklı | Kör noktayı gösterir; gap sinyali |
| Oracle geçerliliği | Flake oranı (3/3 kırmızı, 3/3 yeşil şartı), TP düzeltmelerinin geri alınma oranı | Oracle takımının itibarı |
| Maliyet payları | Keşif, üretim, ölçüm, genel; aylık USD tavanına karşı | Anayasal |
| CI dakikası | Aylık Actions dakikası, `monthly_cap_ci_minutes`'e karşı; döngü ve gün başına | Anayasal; tavanda bütçe dondurması (`28`) |
| İnsan dokunuşu | Operatör aktarımları, sert duruştan kalkışlar ve kurulum dışı her insan eylemi; tarihiyle | `status.md` üst bölümü; sistemin ne kadar özerk olduğunun dürüst sayısı |
| Tohum dışı organ | Tohumda adı geçmeyen ve ablasyonda katkısı kanıtlanmış organ sayısı | `status.md` üst bölümü; sıfırsa sistem kendini geliştirmiyor (`17`) |

**Üst bölüm.** `status.md`'nin ilk satırları sert duruş ya da dondurma nedeni, insan dokunuşu,
tohum dışı organ, regresyon oranı, etki kaçırması, görülmeyen dosya payı ve bütçe durumudur;
dondurma, bütçe ve insan dokunuşu bloğunu hakemin `status.block`'u yazar (`15`).

"Geçen yıl bugün" bölümü bu tablonun o günkü ve bugünkü değerlerini yan yana koyar; ilk okuyucusu
doğunca `chain.asof`'tan üretilir (`13`). Sistemin ne öğrendiği bir anlatı değil, bu farktır.
