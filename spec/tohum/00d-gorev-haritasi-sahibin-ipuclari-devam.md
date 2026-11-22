# Görev Haritası, Devam: Sahibin İpuçları II

Tarih: 2026-11-20 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: her oturumda, görev seçilirken (`00c`'nin devamı)
Çapa: elle yazılır; `00c` 80 satıra yaklaştığı için (`15` 1) ipuçları burada sürer

---

**Sahibin ipucu (2026-11-20, E654; ipucu, reçete değil). Derslerin kendiliğinden yeniden sınanması.**
- Olgu (2026-11-20): defterde 26 `lesson` satırı var. Hepsinin bir `recheck`'i var, hepsi `trust: inferred`, hiçbiri
  bağımsız olarak yeniden koşturulmadı. `26g` gereği başlatıcı ve hakem `recheck`'i koşturmaz. Bugün dersleri yeniden
  sınayan bir şey yoktur.
- Amaç: sahip ilkesi (2026-11-06) her dersin yeniden sınanan, yanlışlanabilir bir kayıt olmasıdır. Yanlış bir ders
  sessizce kalmamalı.
- İpucu: dersler otomatik ve düzenli olarak yeniden sınansın; sonucu derse geri yazılsın (hâlâ tutuyor mu, ne zaman
  tutmadı, `closes:` ile kapanma). Ne zaman koşacağı, nerede koşacağı ve sonucun nasıl kaydedileceği Kurucu'nun
  tasarımıdır. Tohumda bir değişiklik gerekiyorsa Kurucu bunu bir rapor olarak önerir.
- Ölçülür: kaç ders yeniden sınandı, kaçı tuttu, kaçı kapandı.

**Sahibin ipucu (2026-11-20, E665; ipucu, reçete değil). Partiler amaçta da yanlış olabilir.**
- Olgu: parti tabloları (`asama-1/13` ve aşama sayfaları) Aşama 1'den önce operatörce yazıldı. Bugüne kadarki her
  rapor metnin kendisiyle tutarlı olup olmadığını sordu; hiçbiri bir maddenin aşamasının amacına hizmet edip
  etmediğini sormadı.
- İpucu: bir parti maddesinin aşamasının amacına hizmet etmediğine, yanlış sırada olduğuna, başka bir maddeyi tekrar
  ettiğine ya da bir maddenin eksik olduğuna kanıtın varsa, kanıtıyla ve bir öneriyle (çıkar, yeniden sırala,
  birleştir ya da ekle) bir `spec_issue` raporu yaz (`26c`). Yanıtı operatör verir. f1677'nin dediği gibi rapor bir
  izin değildir: yanıttan önce kendi okumanı kurmazsın.

**Sahibin ipucu (2026-11-20, E666; ipucu, reçete değil). Kaybolan oturum açıklanacak bir olgudur.**
- Olgu: 20261120T011313Z oturumu 137 çıkış koduyla bitti ve işi kayboldu (56,9 dakika, push yok, defter satırı yok);
  sonraki oturumun `previous-session.json`'u bunu kaydetti.
- İpucu: nedeni okuyabildiğin kanıttan bul. Neden beynin içindeyse yeniden sınamasıyla bir ders olarak yaz (`26g`);
  dışındaysa bir rapor yaz.

**Sahibin ipucu (2026-11-20, E667; ipucu, reçete değil). Ajanlar.**
- Olgu: E643 ajan istedi (`00b`). Altı oturum sonra beynin `agents/` dizini boştur; ölçüm aynasının `delegation`
  sayısı 0'dır.
- İpucu: ya ilk ajanı tanımla (`24a` "Ajan ve skill tanımları") ya da neden henüz olmadığını, ne zaman olacağını
  söyleyen yanlışlanabilir bir koşulla kaydet.

**Sahibin ipucu (2026-11-20, E676; ipucu, reçete değil). Arama ile okuma.**
- Olgu: Cloudflare'in "Code Mode" yaklaşımı 2.500'den fazla API uç noktasını iki araçla, arama ve çalıştırma ile,
  yaklaşık 1.000 belirteçte sunar; hepsini yüklemek yaklaşık 1,17 milyon belirteç tutardı. Kurucu bugün tohum
  sayfalarını bütün sayfalar olarak okur ve oturumun bağlamı bununla büyür. 20261120T021518Z,
  055357Z, 080122Z ve 103722Z oturumlarının üçünde oturum ortasında en az bir sıkıştırma (compaction) var
  (transkriptin `compact_boundary` olayı).
- İpucu: her model için arama tabanlı okuma. Kurucu tohumu ve kendi derslerini bütün sayfaları yüklemek yerine bir
  dizin ve aramayla okuyabilir; böylece bağlam ve oturum ortası sıkıştırma azalabilir. Bunu kurarsa tasarım
  Kurucu'nundur.
- Ölçülür: kurarsa kendisi ölçer: oturum başına bağlam, sıkıştırma sayısı ve doğruluk, onunla ve onsuz.

**Sahibin ipucu (bu kez kural esnetildi; 2026-11-21, E689; ipucu, reçete değil). Prepush'ın hızlı geçişi.**
- Olgu: 20261121T014159Z oturumunun iyileştirme önerisi (f1766, senin, kurulmadı): `tests/prepush.py` bir hızlı geçiş
  sunsun; bütün koşudan önce, son damgadan beri değişen bir modülü import eden dosyaların bildirim komutlarını koşsun.
  İçe aktarma grafiği `status.depmap`'inkidir ve kökteki `tests/` dizinini kapsamalıdır; damgayı yalnız bütün koşu basar.
- Olgu: yakalayacağı sınıf tekrarladı: "`referee/` dışındaki bir çağıran atlandı" (dersler f1812 ve f1829 dahil); bütün
  prepush koşularına ve kırmızı bir T46'ya mal oldu.
- İpucu: önerini `CHANGELOG-11`'in İlk iş'inin birinci maddesinden sonraki işin olarak kur ve ölç: kazanılan dakikalar ve atlanan
  çağıran sınıfını yakalayıp yakalamadığı. Nasıl kurulacağı senindir.

**Sahibin ipucu (bu kez kural esnetildi; 2026-11-21, E690; ipucu, reçete değil). Bellekten yazılan ad.**
- Olgu: bir hata sınıfı tekrarlıyor: defter satırına bir dosya ya da sayfa adı bellekten yazılıyor ve satır
  eklendikten sonra düzeltiliyor. f1698'in f1704'teki düzeltmesi (`29o`'ya; "bellekten yazıldı, dizine karşı
  denetlenmedi") ve f1795'in f1800'deki düzeltmesi ("adı bellekten yazdım, dizini satır eklendikten sonra listeledim").
  Kendi derslerin sınıfı adlandırıyor, sınıf yine de tekrarlıyor.
- İpucu: bu sınıfı kod kusurlarını kapattığın gibi doğru katmanda kapat: defter satırı eklenmeden önce koşan ve ağaçta
  olmayan bir referansı reddeden bir denetim. Ölç: bu tür düzeltmelerin sayısı, önce ve sonra. Nasıl kurulacağı
  senindir.

Sahibin 2026-11-21'den sonraki ipuçları (E692'den başlayarak) `00e`'dedir.
