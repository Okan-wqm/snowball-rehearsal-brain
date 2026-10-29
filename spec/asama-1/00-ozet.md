# Aşama 1 — İlk Adapter: Lint (K0), Döngü En Basit Hâliyle

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: aşama başında
Çapa: beklemede: aşama 1 çıkış raporu; kilit (aşama 1, spec hash)

---

**Ön koşul:** Aşama 0 PASS satırı `brain/state`'te ve Rekor'da; aktarılan hakem canlı; kurulumun
ikinci bölümü tamamlanmış (`tohum/25a`); hedef yazma modunda (`tohum/21`).

**Ne kurulur:** yalnız oyuncu organları: lint adapter, taban, iki düzeltici yolu, aday paketi,
sayfa üreticisi. Hakem Aşama 0'dan donuktur ve bu aşamada değişmez.

**Getirdiği yetenekler** (`tohum/18`): Her aşama; Çalışma-zamanı LLM çağrısı (araçsız Sonnet
düzelticisi); Entegrasyona merge.

**Çıkış kapısı:** §1.8'deki koşulların tamamı makine doğrulamalı; verdict `PASS`. PASS satırını
hakem yazar.

**Yerleşim:** oyuncu kodu beyin reposunda; çalışma zamanında yalnız kabul edilmiş beyin SHA'sı,
hakemin `koş` işinde koşar ve aday paketi o işin `candidates/<id>/` çıktısıdır. Hakem kodu yalnız
hakem reposunda. Veri `brain/state`'te; çalışma dalı `brain/integration` (`tohum/24`). Tohum
yasaları ve tüm tohum sayfaları geçerlidir.

**Bilerek bu aşamada olmayanlar** ve her birinin açılış tetiği §1.12'nin sonundadır.

## Sayfalar

| Sayfa | Bölüm | Satır |
|---|---|---|
| `01-amac.md` | Amaç | 25 |
| `02-dogruluk-ozellikleri.md` | Doğruluk özellikleri | 23 |
| `03-girisler.md` | Girişler | 24 |
| `04-roller.md` | Roller | 18 |
| `05-dongu-adim-adim.md` | Döngü, adım adım | 37 |
| `06-sirali-mikro-ozellikler.md` | Sıralı mikro özellikler | 23 |
| `07-harness-olcumu.md` | Harness ölçümü | 21 |
| `08-cikis-testi.md` | Çıkış testi (hepsi birlikte PASS) | 44 |
| `09-yasaklar.md` | Yasaklar | 21 |
| `10-butce.md` | Bütçe (başlangıç değerleri; yalnız operatör değiştirir) | 18 |
| `11-sonuc-ne-soyler.md` | Sonuç ne söyler | 21 |
| `12-teslim-listesi.md` | Teslim listesi ve bilerek olmayanlar | 36 |
