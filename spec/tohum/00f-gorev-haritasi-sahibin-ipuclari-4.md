# Görev Haritası, Devam: Sahibin İpuçları IV

Tarih: 2026-11-23 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: her oturumda, görev seçilirken (`00e`'nin devamı)
Çapa: elle yazılır; `00e`'de bu ipucuna yer kalmadığı için (`15` 1) ipuçları burada sürer

---

**Sahibin ipucu (bu kez kural esnetildi; 2026-11-23, E736; görev, reçete değil; korkuluklar bağlayıcıdır). Doğrudan da
yanlıştan da öğren; her sorunu bir sınıf olarak kapat; hiçbirinin üstünü örtme.**
- Olgu (sayfalarda zaten yazılı):
  - Dersler başarısızlıktan da başarıdan da doğar: ilk ham ders satırı geri alınan ilk düzeltmenin `cause`'uyla doğar,
    hayatta kalan başarılar da satır doğurur (`22:62-63`).
  - E697 ajanlar için der ki: zaafları ölçülen başarımdan kendin bulursun ve her sınıfı vaka başına bir yamayla değil,
    kurallarda mimari bir değişiklikle kapatırsın; kurallar yanlışlanabilir kayıtlardır (`00e:58-60`).
  - Ölçüm aynası tekrar eden sınıfları zaten gösterir: `/work/logs/mirror.json`'da `per_model` model sürümü başına
    `rejected_rows_by_reason`'ı, `repeats` 14 günlük penceresinde birden çok reddedilmiş ya da dondurulmuş satırın
    ya da döngü koşusunun taşıdığı ret nedeni ve kırmızı iş sınıflarını, sayı ve tarihleriyle verir (alanlar
    `26o:59-60`; tanımları `seed/founder/mirror.py`'nin `SOURCES`'undadır, `26h:50-55`).
  - Geçmiş bir kararı gevşeten değişiklik reddedilir (`02:79-80`).
  - Sınıf kuralını ajanların ötesine, senin bütün işine taşıyan bir sayfa henüz yok.
- Görev (tasarım senindir):
  1. E697'nin sınıf kuralı yalnız ajanlarına değil, bütün işine uygulanır: bir ret, rakibin bir çürütmesi, kendi
     denetimlerinin ya da ajanlarının yakaladığı bir hata ve işe yarayan kabul edilmiş bir değişiklik, her biri
     yanlışlanabilir bir kaydın kaynağıdır (`22`'nin ders satırları).
     Kaydın biçimi senindir.
  2. Geri gelen bir neden (aynı sınıf iki kez) doğduğu katmanda, dönerse kırmızı olan bir denetimle kapanır; ikinci bir
     vaka başına düzeltmeyle değil (`23`'ün test sorusu, `23:12-15`). `22:64-65`'in genesis kuralı olduğu gibi kalır.
  3. Hiçbir şey üstü örtülerek kapanmaz: zayıflatılmış, atlanmış ya da silinmiş test ya da denetim yok, düşürülmüş eşik
     yok; neyin açık kaldığını ve ne zaman yeniden sınandığını adlandıran bir neden satırı olmadan erteleme ya da
     muafiyet yok. `02:79-80`'in kuralı olduğu gibi kalır; bu madde onun senin kendi işindeki yüzüdür.
  4. Yanlışlanabilir: bu görevle geçen 5 oturumdan sonra aynanın pencere başına tekrar eden sınıfları artmaz ve kapanan
     her sınıfın dönüşünü yakalayacak denetimi vardır. Artarlarsa yaklaşımını (kendi kuralını) yeniden yazarsın, kanıtı
     adlandıran bir `decision` satırıyla.
- Korkuluklar (sahibin koşulu; bağlayıcıdır):
  1. Bu ipucu hiçbir hakemi ya da denetimi gevşetmez ve yeni bir hakem kuralı getirmez: önyükleme hakemi, rakip ve tam
     prepush değişmeden kalır.
  2. Teslimde hiçbir yeniden yapım istenmez: görev bundan sonraki işine uygulanır; işin sırası `CHANGELOG-14`'ünkidir.

Sahibin E739'dan başlayarak ipuçları `00g`'dedir.
