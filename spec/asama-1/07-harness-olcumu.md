# Aşama 1 §1.7 — Harness ölçümü

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 1 çalışırken
Çapa: beklemede: aşama 1 çıkış raporu

---

**Adapter, dev.** Harness adapter'ı K0 dev snapshot'larında (planted, clean, kanarya) puanlar.
Beklenen: dev'deki her kural isabet alır, clean'de yalnız gerçek ihlaller vardır.

**Adapter, çıkış.** `exit.sample` adapter SHA'sı pinlendikten sonra taze bir örneklem çeker ve
ölçü kural sayımıdır: mutasyonla üretilebilen her kural kapsanır, kaçırma sıfırdır. Adapter
deterministik bir sarıcıdır; bir kaçırma o kuralın sarma kusurudur, aracın değil. Düzeltilir,
sonraki çıkış yeni tohumla çekilir. CP alt sınırı raporlanır, kapılamaz (`tohum/19`).

**Düzeltici.** Dev vakalarında kabul oranı, `fix` aralığı / Sonnet oranı, değer / USD,
`gate.diffguard` ret oranı ve `cause` başına unresolved oranı.

**Maliyet.** Oracle duvar saati, CI dakikası ve `llm.call` maliyeti `cost` bölümüne yazılır;
dakikalar aylık anayasal tavana karşı izlenir.
