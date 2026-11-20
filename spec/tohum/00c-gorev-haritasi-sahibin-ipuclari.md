# Görev Haritası, Devam: Sahibin İpuçları

Tarih: 2026-11-19 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: her oturumda, görev seçilirken (`00b`'nin devamı)
Çapa: elle yazılır; `00b` 80 satırı doldurduğu için (`15` 1) ipuçları burada sürer

---

**Öğrenme (sahibin ipucu, 2026-11-19, E649; ipucu, reçete değil).**
- Olgular (2026-11-19): defterde 20 `lesson` satırı var; 9'una sonraki kararlarda adıyla atıf var, 11'ine hiç yok.
  Hiçbirinde `scope` yok (`22`: sınıf, dosya kalıbı, koşullar). f1537: doğru bir ders, kendisinden önce yazılmış
  koda ulaşmadı, çünkü eski kodu yeni derse göre yeniden okuyan olmadı.
- İpucu: bir ders, geçerli olduğu iş geldiğinde bulunabilir olmalı. Yeni bir ders, ondan önce yazılmış kodu da
  kapsamalı. Tekrar eden ya da çürüyen dersler birleşmeli veya `superseded_at` almalı. Ajanlar devreye girince model
  sürümüne bağlı dersler de buna dahil olmalı (E644).

**Önleme ve yapı (sahibin ipucu, 2026-11-19, E650; ipucu, reçete değil).**
- Olgular: Kurucu'nun "aktarımdan önce yakala" türünde beş önerisi var (f1538, f1546, f1553, f1560, f1567); hiçbiri
  kurulmadı. 18 ve 19 Kasım'da dört (B) denemesi, aktarımdan önce görülebilecek bir eksik yüzünden kırmızı bitti;
  ölçüm aynası (`/work/logs/mirror.json`) bunların kaydını tutar. `status.depmap`'e göre `cli`'yı 45 modül içe
  aktarır, `loop.job` 36 modülü içe aktarır, ve iki sayı da büyüyor (`01` karmaşıklık maliyeti). f1551 hâlâ açık:
  hedefin kendi `@nx/enforce-module-boundaries` kuralı, kimse fark etmeden atlanıyor.
- İpucu: bir sonraki aktarımdan önce bu önerilerden en az biri kurulup ölçülsün. Yapı da ölçülerek sadeleşsin.
  Gerçek ürün reposundan önce, hedefin kendi kurallarından hiçbiri sessizce atlanmamalı.

**Tutarlı gelişim (sahip ilkesi, 2026-11-19, E653; ilke, ipucu değil).**
- Kurucu sistemini her yönüyle tutarlı geliştirir: kod, hakem, hafıza ve dersler, ajanlar ve skill'ler, araçlar,
  ölçüm, belgeler.
- Yeni bir parça var olanla çelişmez ve onu tekrar etmez. Aynı işi yapan iki yol bırakılmaz. Tek doğruluk kaynağı
  korunur.
- Bir yerde öğrenilen, geçerli olduğu her yere uygulanır. Eski kod yeni derse göre yeniden okunur.
- Her değişiklik ölçülür ve belgesiyle birlikte gelir.
- Tutarsızlık bulunduğunda kayda geçer ve kapatılır; susularak geçilmez.

**Sahibin ipucu (2026-11-19, E651; ipucu, reçete değil). MVP isteği.**
- Olgu: Sahip, Snowball'u dışarıdan değerlendirecek birine göstermek ve yatırım başvurusunda kullanmak için bir MVP
  istiyor. Bu kişi bir yatırımcı ya da ilk pilot müşteri olabilir.
- MVP'nin ne olduğuna, neyi kanıtlayacağına ve hangi sırayla geleceğine Kurucu karar verir. Tanımını ve gerekçesini,
  ölçülebilir kanıtlarıyla bir öneri olarak yazar. Öneri bir amaç değişikliği olduğu için sahibin onayına gider
  (anayasal karar: amaç, ilkeler, güvenlik sınırları sahiptedir).
- Sınırlar değişmez: gerçek ürün reposu için sahip şartları (E648); merge'ü sahibin yapması; her merge'ün geri
  alınabilir olması; aşama merdiveni ve hakem kuralları.
- MVP'ye ne kadar yaklaşıldığı ölçüm aynasının sayılarıyla izlenebilir.

**Sahibin ipucu (2026-11-19, E652; ipucu, reçete değil). Başka repolardan öğrenme.**
- Amaç: başka repolardan öğrenilen kalıplar, ileride daha küçük ve ucuz modeller Snowball'da çalıştığında onlara yol
  gösteren hipotezler olsun. Bilgi modelde değil repoda durur (`01` sahibin hedefi); bu yüzden her hipotez kendi
  başına anlaşılır ve yazıldığı gibi koşan bir kontrolüyle birlikte tutulur (`26g`). Böylece zayıf bir model de onu
  kullanabilir ve doğrulayabilir.
- İstek: Snowball'un hafızası, üzerinde çalışmadığı, iyi bilinen ve güvenilir açık kaynak projelerden de öğrenebilir.
  Bunu yapacak sistemi Kurucu tasarlar: hangi repo, ne okunur, nasıl saklanır, nasıl ölçülür. İkinci bir çalışma
  hedefi de genelliği gösterir (`21`).
- Olgu: sahibin önerdiği ilk aday şirketin kendi `tromso-mvp` reposudur (Python/Django, özel; çiftlik yazılımı). Hem
  okunarak öğrenilecek ilk kaynak hem de ikinci çalışma hedefi olabilir. Özel olduğu için Snowball onu doğrudan değil,
  operatörün kuracağı özel bir kopyası üzerinden okur ya da onda çalışır (`snowball-rehearsal-copy` gibi bir kopya,
  ama özel); kopyayı sahip ya da operatör kurar, gerekirse Kurucu bunu bir istek olarak yazar. Python bağımlılıkları
  ve araçları için hakemin bugünkü desteği (npm) yetmez.
- Sınırlar (sahip): okuma salt okunurdur, sürüm commit'e ve hash'e sabitlenir. Yalnız izin verici lisanslı repolar
  okunur; kod kopyalanmaz, kalıp ve fikir öğrenilir. Şirketin kendi repoları bu lisans kuralının dışındadır; hakları
  şirkettedir. Dışarıdan gelen bilgi `21a`'daki gibi hipotezdir: bağlamıyla tutulur, kendi hedefimizde kanıtlanana
  kadar karar vermez. Yabancı metin modele girdiği için E648'in saldırgan test seti bu okumaya da uygulanır.
- Etkisi ölçülür: kabul edilen iş başına maliyet okumalı ve okumasız karşılaştırılır (E644).
- Kaynak türleri, güçlüden zayıfa. Operatörün önerisi (bağlayıcı değil; Kurucu kabul eder, değiştirir ya da
  reddeder, gerekçesini yazar). Amaç, Kurucu'nun kendi öğrenme sistemini kurmasıdır. Bu liste yalnız bir başlangıç
  önerisidir.
  1. Snowball'un kendi sonuçları: hakem kararları ve dersler.
  2. Şirketin kendi diğer repoları (ör. `tromso-mvp`), kopyası üzerinden.
  3. Resmi araç belgeleri ve kural katalogları: linter ve tip denetleyici kuralları, örnekleriyle (Aşama 1–2).
  4. Bilinen açık veritabanları: OSV / GitHub Advisory (açıklı ve düzeltilmiş kod çiftleri), CWE / OWASP, Semgrep
     ve CodeQL kuralları test örnekleriyle (güvenlik, K6).
  5. Bakımlı projelerde testli düzeltme commit'leri (mantık hataları, K5). Hazır setler (ör. SWE-bench türü)
     öğrenmekten çok bağımsız sınav olarak kullanılır.
  6. Makaleler: yöntem kaynağıdır; hipotez olarak tutulur, kural olarak değil.
- Kaçınılacaklar: rastgele popüler repolar; doğrulanamayan forum veya blog tavsiyeleri; lisansı kopyalamaya izin
  vermeyen kod.
- Seçim ölçütleri: otoriter mi; izin verici lisanslı mı; içinde bir doğrulama (test, kural) taşıyor mu; sürümü
  sabitlenebilir mi; o aşamanın hata sınıfına uygun mu; etkisi ölçülebilir mi.
