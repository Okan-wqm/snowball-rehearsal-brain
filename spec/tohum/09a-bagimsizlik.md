# Bağımsızlık, Donmuş Koltuklar, Şerit Yazarı

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: her dispatch'te ve her koltuk değişikliğinde
Çapa: hakem reposundaki koltuk özetleri; `run_meta` model alanları

---

**Model kuralı.** Yalnız iki model ailesiyle bağımsızlık yapıyla sağlanır:

1. Bir artefaktın **karşı koltukları** (Savunma, Uygulayıcı temsilcisi, rakip) ve **oracle'ı**
   üreticiden farklı modeldedir. Karşı koltuk ile oracle aynı modelde olabilir; o zaman ayrı
   bağlamda koşar ve birbirinin çıktısını görmez. Savcı üreticiyle aynı taraftadır, aynı modelde
   olabilir.
2. Kapı ayrıklığı `run_meta`'dan doğrular: her koşu yargıladığı koşuyu `subject_run_id` ile
   gösterir; model alanlarını ajan değil `çağır` işi ya da sağlayıcı geçidi yanıttan yazar.
3. Aynı aileden iki model birlikte yanılabilir. Bu yüzden hiçbir karar model görüşüyle kapanmaz,
   yürütmeyle kapanır (Y8). Operatör, rakip için başka bir sağlayıcı yapılandırabilir; yapılandırılmışsa
   kapı onu zorunlu kılar.

**Donmuş koltuklar hakem reposundadır.** Rakip ve oracle koltukları, Gözcü, taban avcı, harness,
kapı, dispatcher ve (doğduğunda) itibar puanlayıcısı hakem reposundadır; hakem reposuna yalnız
operatör yazar (`01a`).

- **Tohum koltukları.** Tohum rakibinin, test-yazıcının ve şerit yazarının promptları tohumla
  gelir (`29`); kurulumda operatör onları hakem reposuna kopyalar ve hash'leri kurulum özetine
  girer. Kurucu onları yazmaz. Rakip kurulumdan itibaren önyükleme hakeminde çalışır (`29b`);
  test-yazıcı ve şerit yazarı ilk çağıranlarında kurulur ve o anda donar. Hiç koşmamış bir koltuk
  dondurulmaz.
- **Kurulum istisnası yalnız Aşama 0'dadır.** Hakemin ilk sürümünü Kurucu beyin reposunun
  `referee/` dizininde yazar, çünkü başka yazar yoktur. Onu tohumla gelen önyükleme hakemi, tohum
  vektörleri (`29a`) ve farklı modelden rakip denetler; operatör Aşama 0 çıkışında hakem reposuna
  aktarır ve donar. Sonra Kurucu hakeme yazamaz. Bu sistemin güven köküdür; zayıflığı (Kurucu'nun
  yazdığı testler ve vektörlerin yalnız taban olması) açıktır ve çıkış raporunda yazılır.
- **Şerit yazarı.** Donmuş bir koltuğu ya da hakem kodunu değiştirmeyi yalnız şerit yazarı önerir:
  Kurucu değildir, Kurucu'nun defterini görmez, yalnız tipli alanları okur (hakem raporları, Gözcü
  işaretleri, kanarya sonuçları); serbest metin ona talimat olarak ulaşmaz. Önerisi yeni bir
  kendi-testi ekler, arşivde yeniden oynatılır, farklı modelden rakip çürütmeye çalışır ve kanarya
  geçer. Yeni donmuş koltuklar (Savunma, Uygulayıcı temsilcisi) de onun taslağıyla doğar.
- **Aktarım yolu.** Hakem reposu Free özel planda ruleset ve ortam taşıyamadığı için hiçbir App ona
  yazmaz; şerit yazarının kabul edilmiş önerisi hakem reposuna operatör aktarımıyla, aşama
  çıkışında girer ve "insan dokunuşu" sayacına yazılır. Hakem reposu ruleset ve ortam taşıyabildiği
  gün (açık ya da Pro) bu yol değişir: ayrı bir denetçi App'i kontrolü raporlar, ayrı bir yazar
  App'i merge eder, ruleset denetçinin kontrolünü zorunlu kılar, sırlar ortamlara bölünür ve
  görevdeki kapı halefini kendisi doğrular; aktarım gerekmez.
- **Geri dönüş.** Kanaryada başarısız olan koltuk, son pinli sürümüne geri döner ve şerit yazarına
  bir görev düşer; sistem koltuksuz kalmaz. Hiç koşmamış koltuk için geri dönüş tanımsızdır; bu
  yüzden koltuk ilk çağıranında kurulur.

**Rakip kanaryası.** Hakem, rakiplere ara sıra kusurlu artefaktlar verir: gerçek geçmiş
artefaktlara mekanik olarak enjekte edilmiş kusurlar (sızdıran snapshot, önemsizce sağlanan
eşleşme, belirti düzelten yama, talimat veren artefakt). Eşiğin altını çürüten rakip son pinli
sürüme döner. Kanarya kaçırmayı ölçene kadar rakip tek deneme yapar ve açık `not_refuted`
dışındaki her sonuç kabul değildir (`29`).

**Gözcü deterministik koddur.** LLM değildir, itibarla puanlanmaz; kuralları `28`'de, eşikleri
`policy.json`'dadır. **Bağımsızlık ölçülür:** iki koltuğun karar ve referans benzerliği eşiği
aşarsa Gözcü işaret yazar; işaretin okuyucusu şerit yazarıdır.
