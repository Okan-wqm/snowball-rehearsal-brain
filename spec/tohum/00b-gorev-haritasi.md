# Görev Haritası

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: her oturumda, görev seçilirken
Çapa: elle yazılır; INDEX.md üretilir

---

| Görev | Oku |
|---|---|
| Her oturum | `00`, `00a` |
| Kurulum, aktarım ve etkinleştirme | `25`, `25a`, `24`, `01a`, `01b`, `29b`, `29u`, `29y`, `29z` |
| Yeni repoya bağlanma | `01`, `14`, `21`, `21a` |
| Aşama açma ve kapama | `02`, `03`, `19`, `26c`, `26d`, `26e`, `29e`, ilgili `asama-N/00-ozet.md` |
| Hakem bileşeni yazma (Aşama 0 ve partiler) | `01a`, `01b`, `08`, `26a`, `26c`, `26d`, `26e`, `26f`, `29`, `29a`, `29b`, `29e`, `29p`, `29r`, `29s`, `29t`, `29u`, `29v`, `29y`, `29z`, `asama-0/14`, `asama-1/13` |
| Koda ya da dokümana dokunma | `04`, `04a`, `05`, `07`, `07a`, `08`, `23` |
| Mimari seçim: doğruluk kaynağı, tekrar, sınırlar, değişim, evrim, belge (danışma) | `31`, `31a`, `31b`, `31c`, `31d`, `31e`, `31f`, `31g`, `31h` |
| Güvenlik: açık arama, bildirim, test, defter | `30`, `30a`, `30b`, `30c`, `30d`, `30e`, `30f`, `03`, `05` |
| Artefakt üretme ve değerlendirme | `10`, `10a`, `09a`, `11`, `29` |
| Organ yazma ve kaldırma | `09`, `12`, `12a`, `17` |
| Hafıza, defter, ders | `13`, `15`, `16`, `22`, `22a`, `26g`, `27` |
| Bağımlılık ekleme, başka repodan yararlanma | `24`, `21a`, `18a` |
| Eşik, bütçe, dondurma | `18`, `18a`, `18b`, `29v`, `06`, `20`, `28` |
| Şema ve araç imzası | `26`, `26b`, `26c`, `26d`, `26e`, `26f`, `26g`, `26a` |
| Tohum vektörleri ve koltuklar | `29`, `29a`, `29c`, `29d`, `29f`, `29g`, `29h`, `29i`, `29j`, `29k`, `29m`, `29n`, `29o` |
| Terim ve okuyucu | `27` |
| Sayfa yazma | `15` |

**Sahibin ipucu (2026-11-18, E643; ipucu, reçete değil).** Sahibin Kurucu'ya açık ipucudur, beslememe kuralının
istisnasıdır; ölçüm ipucuyla bulunanı Kurucu'nun kendi bulduğundan ayırır.
- Kurucu (Fable) mimar ve yönetici olarak kalır. Tekrar eden, iyi tanımlı işleri (mutant koşturmak, test sonucu
  okumak, defter satırı hazırlamak, dar bir düzeltme) beynin `agents/` dizininde tanımladığı ajanlara verebilir.
- Ajanın modeli tanımının `model` alanıyla seçilir (`24a` "Ajan ve skill tanımları") ve `sonnet` ya da `opus`'tur;
  `haiku` şimdilik kullanılmaz (sahip kararı).
- Hangi işin hangi modele gittiği ve kabul edilmiş değişiklik başına maliyeti defterde kaydedilir; karar varsayımla
  değil ölçümle verilir (`01` "Sahibin hedefi").
- Olgu: rakip `opus`'tur. Hakeme giden kodu aynı modelin yazması rakibin bağımsızlığını zayıflatır (`03` K5).
- Sahibin tercihi (ipucu, denetim değil): hakeme giden kodu yazan ajanlar `sonnet`'tir (rakipten farklı model);
  `opus` ajanları analiz, inceleme ve planlama içindir.

**Model seçimi amaçla ve ölçümle (sahip ilkesi, 2026-11-19, E644; ilke, ipucu değil).**
- Her model çağrısı neden çağrıldığını (amacını) ve onu yargılayan kalite denetimini adlandırır; denetim bazen
  tekniktir (test, derleme, hakem kararı), bazen kullanıcı deneyimine bağlıdır.
- Model, amaç başına, kabul edilmiş sonuç başına ölçülen toplam maliyetle seçilir; yeniden denemeler, inceleme ve
  hakem koşuları bu maliyete dahildir. Token fiyatı ölçü değildir.
- Örnek: token başına dört kat ucuz bir model 100 işin 10'unu, pahalısı 90'ını geçiriyorsa ucuz olan pahalıya gelir.
- Yeni bir model çıktı diye görev ona bağlanmaz; yeni model, aynı işlerde mevcut modelle ölçülü bir denemeden geçerek
  girer.
- Her ölçüm ve öğrenim kaydı modelin tam sürümünü taşır: model kimliği (ör. `claude-sonnet-5-5`) ve effort. Bir
  modelin başarısı yalnız o sürüm için geçerlidir; sürüm değişince eski ölçüm yeni sürüme taşınmaz, yeni sürüm yeniden
  ölçülür. Hangi sürümün hangi amaçta ne verdiği defterde sürümüyle birlikte durur.
- Bu fikri geliştirmek Snowball'un işidir; ilke yalnız yönü verir.

**Sahibin ipucu (2026-11-19, E645; ipucu, reçete değil).**
- Olgu: (B)10 kırmızısı (koşu 44094922317, `referee_tree_mismatch`) şöyle oldu: döngünün `çek`'i en yeni önyükleme
  sonucunu okuyor; (B) sürerken Kurucu'nun her push'u yeni bir sonuç doğuruyor ve `çek` bozuluyor. Operatör bu yüzden
  her (B) boyunca `STOP` koyuyor; Kurucu her (B)'de 1–1,5 saat boş kalıyor.
- İpucu: `çek` aktarılan beyin SHA'sının sonucunu okusun; o sonucun parmak izi aktarım satırında (`result_sha256`,
  `26c`) zaten var. Böylece (B) sırasındaki push'lar döngüyü bozmaz, `STOP` gerekmez, Kurucu (B) sürerken çalışabilir.
- Tasarım Kurucu'nundur ve hakemin denetimini gevşetmez: çalışan kod yine yalnız kabul edilmiş ve aktarılmış koddur.

**Sahibin ipucu (2026-11-19, E648; ipucu, reçete değil).**
- Olgu: hedefin dosyaları modele giden metne girer; bir dosyanın içine yazılmış bir talimat (prompt injection)
  modeli yönlendirmeye çalışabilir. Tohumun güvenlik kataloğu (`30a`) hedefin kendi enjeksiyon açıklarını anlatır,
  modele yöneleni anlatmaz.
- Sahip şartı: Snowball gerçek ürün reposunda çalışmadan önce, kapılar saldırgan bir test setinden kanıtla
  geçmelidir. Set üç şeyi kapsar: hedef dosyalara gömülü prompt injection, diff denetiminden kaçmaya çalışan
  değişiklikler, gizlenmiş ya da kodlanmış secret'lar. Seti hakem koşar.
- Tasarım Kurucu'nundur.

Sahibin 2026-11-19 tarihli öteki ipuçları (E649 öğrenme, E650 önleme ve yapı) `00c`'dedir.
