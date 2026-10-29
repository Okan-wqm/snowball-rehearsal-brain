# Aşama 0 — Ölçüm Zemini ve Hakem

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: aşama başında
Çapa: beklemede: aşama 0 çıkış raporu; kilit (aşama 0, spec hash)

---

**Ön koşul:** kurulumun birinci bölümü tamamlanmış (`tohum/25`): hakem reposunda önyükleme hakemi
(`tohum/29b`), tohum vektörleri (`tohum/29a`), tohum koltuk promptları (`tohum/29`), anayasal
`policy.json`, `control.json` ve kurulum özeti.

**Ne kurulur:** Kurucu, beyin reposunda hakemin tamamını `referee/` altında ve oyuncu iskeletini
yazar. Önyükleme hakemi her push'u denetler; Kurucu kendi yazdığını puanlayamaz (Y6). Hedefe bu
aşamada hiçbir şey yazılmaz; hedefe ilk yazım etkinleştirme koşusudur.

**Getirdiği yetenekler** (`tohum/18`): Her aşama. İnşa zamanındaki rakip çağrıları ve
etkinleştirme provası yetenek getirmez.

**Çıkış kapısı:** iki parça, ikisi birlikte `PASS` (§0.10): (A) pinli beyin SHA'sında önyükleme
hakeminin makine doğrulamalı sonucu; (B) operatör aktarımı ve aktarılan hakemin canlı etkinleştirme
koşusu. Kurulumun ikinci bölümü (`tohum/25a`) (B)'nin parçasıdır.

**Yerleşim:** hakemin adayı beyin reposunun `referee/` dizininde, aktarımdan sonra yalnız hakem
reposunda. Oyuncu kodu beyin reposunda. Veri etkinleştirmeden sonra hedefin `brain/state` dalında.
Mühürlü depo bu aşamada yoktur; ilk held-out havuzuyla açılır (`asama-4/03`). Tohum yasaları ve
tüm tohum sayfaları geçerlidir.

## Sayfalar

| Sayfa | Bölüm | Satır |
|---|---|---|
| `01-amac.md` | Amaç | 23 |
| `02-dogruluk-ozellikleri.md` | Doğruluk özellikleri | 32 |
| `03-roller.md` | Roller | 17 |
| `04-hata-seti.md` | Hata seti | 41 |
| `05-property-ve-sinif-etiketleri.md` | Property ve sınıf etiketleri | 39 |
| `06-snapshot-uretimi.md` | Snapshot üretimi | 29 |
| `07-bulgu-ve-kosu-semasi.md` | Bulgu ve koşu şeması | 33 |
| `08-puanlama-ve-metrikler.md` | Puanlama ve metrikler | 34 |
| `09-harness-in-kendi-testleri.md` | Harness'in ve hakemin kendi testleri | 58 |
| `10-cikis-testi.md` | Çıkış testi (hepsi birlikte PASS) | 51 |
| `11-yasaklar.md` | Yasaklar | 22 |
| `12-butce.md` | Bütçe (başlangıç değerleri; yalnız operatör değiştirir) | 22 |
| `13-teslim-listesi.md` | Teslim listesi | 33 |
| `14-sirali-mikro-ozellikler.md` | Sıralı mikro özellikler | 46 |

Rehearsal note: setup-day run.
