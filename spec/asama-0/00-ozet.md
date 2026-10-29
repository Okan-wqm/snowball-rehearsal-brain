# Aşama 0 — Yürüyen İskelet: İlk Canlı Döngü

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: aşama başında
Çapa: beklemede: aşama 0 çıkış raporu; kilit (aşama 0, spec hash)

---

**Ön koşul:** kurulumun birinci bölümü tamamlanmış (`tohum/25`): hakem reposunda önyükleme hakemi
(`tohum/29b`), tohum vektörleri (`tohum/29a`), tohum koltuk promptları (`tohum/29`), anayasal
`policy.json`, `control.json`, kurulum özeti ve birinci tohum dönemi; yeni, ayrı beyin reposu; oyuncak
hedef ve gerçek hedefin kopyası (`tohum/24`, `tohum/25`); dürüstlük ekimi ve taahhüdü (§0.10).

**Ne kurulur:** yürüyen iskelet: ilk canlı döngünün okuduğu 18 mikro özellik (§0.14), fazlası değil.
Kurucu onları beyin reposunda `referee/` altında yazar. Önyükleme hakemi her push'u yargılar ve Aşama
0'dan sonra da beyin reposunun itme yargıcı olarak kalır; Kurucu kendi yazdığını puanlayamaz (Y6). Hakemin
geri kalanı ilk okuyucusundan hemen önceki parti aktarımıyla gelir (`asama-1/13`).

**Getirdiği yetenekler** (`tohum/18`): Her aşama; Entegrasyona merge (oyuncak hedefte ve kopyanın tek
biriminde, hazır adaylarla); Çalışma-zamanı LLM çağrısı (yalnız (B)'deki kanarya). İnşa zamanındaki
rakip çağrıları yetenek getirmez.

**Çıkış kapısı:** iki parça, ikisi birlikte `PASS`: (A) pinli beyin SHA'sında önyükleme hakeminin imzalı
sonucu (§0.10); (B) operatör aktarımı ve döngü hakeminin önce oyuncak hedefte, aynı (B) içinde kopyanın
tek biriminde canlı koşusu (§0.10a). Kurulumun ikinci bölümü (`tohum/25a`) (B)'nin parçasıdır.

**Yerleşim:** döngü hakeminin adayı beyin reposunun `referee/` dizininde; aktarımdan sonra hakem
reposunun kökünde, önyükleme hakeminin yanında. Veri iki hedefin `brain/state` dalında, çalışma dalı
`brain/integration`. Aşama 0'da tek bağımlılık ekosistemi npm'dir; oyuncak hedef JavaScript'tir.
Mühürlü depo bu aşamada yoktur (`asama-4/03`). Tohum yasaları ve tüm tohum sayfaları geçerlidir.

## Sayfalar

| Sayfa | Bölüm | Satır |
|---|---|---|
| `01-amac.md` | Amaç, parçalar, döngünün adımları | 48 |
| `02-dogruluk-ozellikleri.md` | Doğruluk özellikleri | 30 |
| `03-roller.md` | Roller | 17 |
| `04-hata-seti.md` | Hata seti (P1'e taşındı) | 17 |
| `05-property-ve-sinif-etiketleri.md` | Property ve sınıf etiketleri (P1'e taşındı) | 15 |
| `06-snapshot-uretimi.md` | Snapshot üretimi (P1'e taşındı) ve çalışma ağacı | 23 |
| `07-bulgu-ve-kosu-semasi.md` | Bulgu ve koşu şeması (P1'e taşındı) | 15 |
| `08-kabul-kurali-ve-esleme.md` | Kabul kuralı, K0 eşlemesi, devir sırası | 66 |
| `09-harness-in-kendi-testleri.md` | Hakemin kendi testleri | 76 |
| `10-cikis-testi.md` | Çıkış testi, (A) | 46 |
| `10a-cikis-canli-dongu.md` | Çıkış testi, (B) | 45 |
| `11-yasaklar.md` | Yasaklar | 27 |
| `12-butce.md` | Bütçe (kaçak freni) | 39 |
| `13-teslim-listesi.md` | Teslim listesi | 39 |
| `14-sirali-mikro-ozellikler.md` | Sıralı mikro özellikler | 57 |
