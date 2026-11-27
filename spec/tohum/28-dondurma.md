# Dondurma: Ne Durur, Nasıl Kalkar

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Gözcü kararlarında ve her dondurmada
Çapa: beklemede: P1 aktarımı (Gözcü) — ledger.jsonl part=freeze satırları

---

Dondurma bir ağrı refleksidir: zarar büyümeden eylemi durdurur, gözlemi durdurmaz. Kuralları
deterministiktir; Gözcü uygular, eşikleri `policy.json` anayasal bölümündedir. Her kural tek
yerde, burada yazılır; başka sayfa buraya atıf yapar.

**Yumuşak dondurma.**

- **Tetik:** regresyon kuralı (`20`); aynı pencerede iki kapsayıcılık ihlali (`08`), tek tetik
  dosyası kök neden başına bir kez sayılır; salınım birikimi; bütçe ya da Actions dakikası
  tavanına ulaşmak (bütçe dondurması; ay dönünce ya da operatör freni yükseltince kendiliğinden
  kalkar). Bütçe iç kullanımda kaçak frenidir (`06`): dondurma olağan işi değil döngüyü keser ve
  Kurucu'nun reddi değildir. Abonelik kullanım penceresine takılmak (HTTP 429) dondurma değil
  kesintidir: operatör uyarılır, iş pencere açılınca sürer. P1 aktarımına kadar Gözcü yoktur: rakip
  frene takılınca önyükleme hakemi iş başlatmaz (yoklama uyarıyla geçer) ve aynı baş ay dönünce ya da
  politika değişince kendiliğinden yargılanır; dakikayı ölçmez, freni GitHub harcama sınırıdır
  (`25` 8, `29b`).
- **Kapsam:** merge kapısı ilgili sınıf için kapanır; genesis yeni ACTIVE geçişi yapmaz. Keşif,
  ölçüm, SHADOW koşuları ve oracle sürer.
- **Kayıt:** `ledger.jsonl`'a `part: freeze` satırı: tetik, kapsam, ölçüm, başlangıç (biçimi `26i`; Aşama 1'i `28a`).
- **Kalkış:** dondurulmuş sistem boşta olduğu için "üç döngü sınır içinde" kanıt değildir ve
  30 günlük geri alma sayısının kendiliğinden düşmesi beklenmez. Kalkış için **sonda döngüsü**
  gerekir: dondurulmuş kapsamda `policy.json`'daki sayıda düzeltme ayrı bir sonda dalında koşar,
  oracle'dan ve kapının yeniden koşusundan geçer, sonda dalında nöbetçi her birinden sonra
  yeşildir. Sonda döngüsü üst üste iki kez temizse dondurma kalkar; kalkış da bir satırdır.

**Sert duruş.**

- **Tetik:** bir pencerede `policy.json`'daki sayıdan fazla yumuşak dondurma; kurulum kayması (`drift.check`, `01b`);
  zincir kırığı (`13`); Rekor'a (`13`: bir `yaz` işinde üç çağrının hiçbiri başarmadıysa) ya da attestation'a
  yazılamaması; etkinleştirme ya da aktarım hatası (`25a`); beyan dışı bir aktörün `brain/*` ref değişikliği; kill
  switch. Kill switch'in yolları `25` 9'dadır: `control.json` bayrağı, `gh run cancel`, `gh workflow disable`,
  belirteç sırrını silmek, sağlayıcı tavanı, App askıya alma. Her iş bayrağı `main`'den canlı okur; bayrak açıkken iş
  başlamaz, koşan koşuda `yaz` kabul etmeyen ve harcamayı yazan bir `stopped` sonucu imzalar; iptal edilen koşu hiçbir
  şey imzalamaz.
- **Kapsam:** hiçbir oyuncu koşusu ve hiçbir yazım yapılmaz; yalnız hakem okuma işleri ve
  raporlama sürer.
- **Kalkış:** döngü dışı bir operatör işidir; sistem ondan onay beklemez, durur. `status.md`
  sert duruşun nedenini, kanıt satırını ve gereken eylemi en üstte yazar; kalkış insan dokunuşu
  sayacına girer.

**İşaret, dondurma değil.** Kümülatif eşik kayması (`18`), koltuk benzerliği (`09a`) ve genesis
kuyruğu taşması Gözcü işaretidir: eylemi durdurmaz, şerit yazarına görev yazar.

**Hedefe yazımın başarısızlığı bir kesintidir** (rapor masası uzlaşısı (2026-11-24), seed-103 (3)). Bir `yaz` işinde
hedefe başarısız olan bir GitHub yazımı (ilk yazımı da, sonrakiler de) bu sayfanın sert duruşu değildir: tetikleri
(`28:35-38`, `26i:24-25`'in kapalı kümesi) değişmez ve onu saymaz. `28:19-20`'nin HTTP 429'u gibi bir kesintidir: iş
biter ve hiçbir şey tutmaz (satır yok, `status.md` duruşu yok, operatör adımı yok); sonraki zamanlanmış devir koşar,
çektiğinden yeniden karar verir ve başarısız işin bıraktığını devralır (`07` "Yarım kalmış geri alma", `26p` "Yarım
kalmış merge"). `yaz` işinin satırı bu sonu `hard_stop`'tan ayrı bir adla adlandırır; `hard_stop` yalnız bu sayfanın
sert duruşunu adlandırır (`26i:24`). Değişmeyenler: genesis devrinde başarısız yazım `activation`'dır (`28:37`, `25a`
satır 7); bir (B) koşusunda hedefe yazdıktan sonra kırmızı biten koşu yeniden tetiklenmez (`25a:44-46`); P1'den önce
`çek`'in zincir kırığı reddi (`13:56-57`) olduğu gibidir. **Gevşetme L-AM1** (sahibe bildirilir): iki okumanın
gevşeğidir; başarısız yazım operatör adımı istemez.
