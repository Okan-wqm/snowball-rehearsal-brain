# Aşama 1 — İlk Adapter: Lint (K0), Döngü En Basit Hâliyle

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: aşama başında
Çapa: beklemede: aşama 1 çıkış raporu; kilit (aşama 1, spec hash)

---

**Ön koşul:** Aşama 0 PASS satırı iki hedefin `brain/state`'inde ve Rekor'da; aktarılan döngü hakemi
canlı; kurulumun ikinci bölümü tamamlanmış (`tohum/25a`); `setup/stage.json` `stage: 1`; hedef yazma
modunda (`tohum/21`).

**Ne kurulur:** oyuncu organları: lint adapter, taban, iki düzeltici yolu, aday paketi, sayfa üreticisi.
Hakem donuk değildir ama yalnız aktarımla değişir: P1 (organ ve ölçüm), P2 (güvenlik gözlemi) ve çıkış
partisi, her biri ilk okuyucusundan hemen önce (§1.13). Önyükleme hakemi beyin push'larını yargılamayı sürdürür.

**Getirdiği yetenekler** (`tohum/18`): Her aşama; Çalışma-zamanı LLM çağrısı (araçsız Sonnet
düzelticisi); Entegrasyona merge.

**Çıkış kapısı:** §1.8'deki koşulların tamamı makine doğrulamalı; verdict `PASS`. PASS satırını
hakem yazar.

**Yerleşim:** oyuncu kodu beyin reposunda; çalışma zamanında yalnız önyükleme hakeminin kabul ettiği
beyin SHA'sı, hakemin `koş` işinde koşar ve aday paketi o işin `candidates/<id>/` çıktısıdır. Hakem kodu
canlıda yalnız hakem reposunda; parti adayları beyinde `referee/` altında. Veri `brain/state`'te; çalışma dalı `brain/integration` (`tohum/24`). Tohum
yasaları ve tüm tohum sayfaları geçerlidir.

**Bilerek bu aşamada olmayanlar** ve her birinin açılış tetiği §1.12'nin sonundadır.

## Sayfalar

| Sayfa | Bölüm | Satır |
|---|---|---|
| `01-amac.md` | Amaç | 26 |
| `02-dogruluk-ozellikleri.md` | Doğruluk özellikleri | 24 |
| `03-girisler.md` | Girişler | 25 |
| `04-roller.md` | Roller | 20 |
| `05-dongu-adim-adim.md` | Döngü, adım adım | 40 |
| `06-sirali-mikro-ozellikler.md` | Sıralı mikro özellikler | 31 |
| `07-harness-olcumu.md` | Harness ölçümü | 21 |
| `08-cikis-testi.md` | Çıkış testi (hepsi birlikte PASS) | 51 |
| `09-yasaklar.md` | Yasaklar | 22 |
| `10-butce.md` | Bütçe (kaçak freni) | 28 |
| `11-sonuc-ne-soyler.md` | Sonuç ne söyler | 21 |
| `12-teslim-listesi.md` | Teslim listesi ve bilerek olmayanlar | 41 |
| `13-aktarim-partileri.md` | Aktarım partileri | 55 |
| `13a-hata-seti.md` | P1: Hata seti | 45 |
| `13b-property-ve-sinif-etiketleri.md` | P1: Property ve sınıf etiketleri | 43 |
| `13c-snapshot-uretimi.md` | P1: Snapshot üretimi | 31 |
| `13d-bulgu-ve-kosu-semasi.md` | P1: Bulgu ve koşu şeması | 34 |
| `13e-puanlama-ve-metrikler.md` | P1: Puanlama ve metrikler | 37 |
