# Aşama 4 §4.2 — Doğruluk özellikleri

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: hedef taslak · Sahibi: operatör
Okunma: Aşama 4 çalışırken
Çapa: beklemede: aşama 4 çıkış raporu

---

1. Avcıya kalıp verilmez; prompt ve property spec kalıp sızıntısı denetiminden geçer.
2. Hiçbir bulgu model görüşüyle gerçek sayılmaz; yalnız yürütme oracle'ı (`tohum/04a`).
3. Held-out mühürlü depodadır ve ileriye dönüktür: avcının prompt hash'i mühürlenir, yalnız
   mühürden sonra merge edilen insan düzeltmeleri sayılır (`tohum/19`).
4. Bakış yalnız verdict döndürür; held-out koşusunun her ham çıktısı mühürlü depoda kalır.
5. TP'ler Aşama 1'deki aynı döngüden `brain/integration`'a gider; K6 sınırına dokunan bulgular
   `blocked`.
6. Her yargıç kararı faz 5'e karşı puanlanır; panel bağımsızlığı ölçülür (`tohum/09a`).
7. Araç kullanan her ajan dispatch sözleşmesiyle, kendi işinde `id-token` ve docker soketi
   olmadan, modele yalnız sağlayıcı geçidinden ulaşarak koşar (`tohum/24`).
8. Maliyet inişi aynı kapıdan geçer; eşik gevşetilmez.
