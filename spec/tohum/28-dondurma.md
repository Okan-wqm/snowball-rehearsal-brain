# Dondurma: Ne Durur, Nasıl Kalkar

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Gözcü kararlarında ve her dondurmada
Çapa: beklemede: aşama 0 — ledger.jsonl part=freeze satırları

---

Dondurma bir ağrı refleksidir: zarar büyümeden eylemi durdurur, gözlemi durdurmaz. Kuralları
deterministiktir; Gözcü uygular, eşikleri `policy.json` anayasal bölümündedir. Her kural tek
yerde, burada yazılır; başka sayfa buraya atıf yapar.

**Yumuşak dondurma.**

- **Tetik:** regresyon kuralı (`20`); aynı pencerede iki kapsayıcılık ihlali (`08`), tek tetik
  dosyası kök neden başına bir kez sayılır; salınım birikimi; bütçe ya da Actions dakikası
  tavanına ulaşmak (bütçe dondurması; ay dönünce kendiliğinden kalkar).
- **Kapsam:** merge kapısı ilgili sınıf için kapanır; genesis yeni ACTIVE geçişi yapmaz. Keşif,
  ölçüm, SHADOW koşuları ve oracle sürer.
- **Kayıt:** `ledger.jsonl`'a `part: freeze` satırı: tetik, kapsam, ölçüm, başlangıç.
- **Kalkış:** dondurulmuş sistem boşta olduğu için "üç döngü sınır içinde" kanıt değildir ve
  30 günlük geri alma sayısının kendiliğinden düşmesi beklenmez. Kalkış için **sonda döngüsü**
  gerekir: dondurulmuş kapsamda `policy.json`'daki sayıda düzeltme ayrı bir sonda dalında koşar,
  oracle'dan ve kapının yeniden koşusundan geçer, sonda dalında nöbetçi her birinden sonra
  yeşildir. Sonda döngüsü üst üste iki kez temizse dondurma kalkar; kalkış da bir satırdır.

**Sert duruş.**

- **Tetik:** bir pencerede `policy.json`'daki sayıdan fazla yumuşak dondurma; kurulum kayması
  (`drift.check`, `01b`); zincir kırığı (`13`); Rekor'a ya da attestation'a yazılamaması;
  etkinleştirme ya da aktarım hatası (`25a`); beyan dışı bir aktörün `brain/*` ref değişikliği;
  kill switch.
- **Kapsam:** hiçbir oyuncu koşusu ve hiçbir yazım yapılmaz; yalnız hakem okuma işleri ve
  raporlama sürer.
- **Kalkış:** döngü dışı bir operatör işidir; sistem ondan onay beklemez, durur. `status.md`
  sert duruşun nedenini, kanıt satırını ve gereken eylemi en üstte yazar; kalkış insan dokunuşu
  sayacına girer.

**İşaret, dondurma değil.** Kümülatif eşik kayması (`18`), koltuk benzerliği (`09a`) ve genesis
kuyruğu taşması Gözcü işaretidir: eylemi durdurmaz, şerit yazarına görev yazar.
