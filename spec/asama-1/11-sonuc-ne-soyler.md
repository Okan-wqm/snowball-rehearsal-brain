# Aşama 1 §1.11 — Sonuç ne söyler

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 1 çalışırken
Çapa: beklemede: aşama 1 çıkış raporu

---

- **PASS:** döngü kapanıyor, her dosyanın okuyucusu bir kararı değiştiriyor, kapı yeniden koşuya
  bakıyor, maliyet tabanı yazılı. Aşama 2 aynı döngüye K1 ve K2 adapter'larını, planlayıcıyı, ders
  enjeksiyonunu ve kendi güvenlik kararıyla `main` senkronunu ekler; döngüye dokunmaz.
- **FAIL, kural sayımında kaçırma:** adapter aracı o kural için yanlış sarıyor; aracın ham çıktısı
  ile bulgu dosyası satır satır karşılaştırılır; sonraki çıkış yeni tohumla çekilir.
- **FAIL, kabul oranı düşük:** Sonnet aralığın dışına taşıyor ya da `fix` aralığı yeni ihlal
  üretiyor; ikisi ayrı sayıdır.
- **FAIL, merge sonrası kırmızı:** etkilenen-test komutu eksik koşuyor. Döngünün en pahalı
  kusurudur; `impact_miss` satırları nerede olduğunu gösterir. Aşama 2 bu düzelmeden açılmaz.
- **FAIL, kırmızı kontrol yeşil ya da kayma:** hakemde ya da kurulumda kusur; sert duruş ve
  operatörün döngü dışı işi.
- **UNMEASURABLE:** çıkış örneklemi kural sayımını sağlayamıyor ya da merge sayısı yetersiz;
  nedeni yazılır. Merge eksiği için canlı kanıt oyuncak hedeften gelir.
