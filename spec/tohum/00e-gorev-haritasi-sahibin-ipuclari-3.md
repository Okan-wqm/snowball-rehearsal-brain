# Görev Haritası, Devam: Sahibin İpuçları III

Tarih: 2026-11-21 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: her oturumda, görev seçilirken (`00d`'nin devamı)
Çapa: elle yazılır; `00d` 80 satıra yaklaştığı için (`15` 1) ipuçları burada sürer

---

**Sahibin ipucu (bu kez kural esnetildi; 2026-11-21, E692; ipucu, reçete değil; korkuluklar bağlayıcıdır). İlk ajan:
denetlenen ve ölçülen.**
- Olgu: E643 ve E667 her oturumda, yanlışlanabilir bir neden kaydedilmeden ertelendi: f1735, f1748 ve f1799 E667'yi
  sıradaki işler arasında adlandırır ve yapmaz; f1844 ve f1853 "alt ajan kullanılmadı" der. Defterin oturum başlangıç
  satırları rakibin `refutation_reproduced` ile reddettiği 18 push adlandırır (f32'den f1777'ye); son beşinden üçü bir
  sayfa sözünün kaçağıdır: f1595 (canlı yolda çağıranı olmayan organ koşucusu), f1673 (`13`'ün "en çok 3 çağrı" sözü),
  f1720 (offline okumadan önce koşan drift). Her ret yaklaşık bir oturuma mal olur.
- İpucu: ilk ajan, push'tan önce koşan bir uyum denetçisi olsun; inceleme yaptığı için modeli `opus`'tur (E643:
  `opus` ajanları analiz, inceleme ve planlama içindir; hakeme giden kodu `sonnet` yazar). Push'un diff'ini rakip gibi
  okur ve bulgularını prepush'tan önce sana bildirir. Tasarım (istem, kapsam, ne zaman koştuğu) senindir.
- Korkuluklar (sahibin koşulu; bağlayıcıdır, kaliteden ödün verilmez):
  1. Ajan kendiliğinden hiçbir şey sokmaz. Her değişiklik yine senin incelemenden, tam prepush'tan, önyükleme
     hakeminden ve rakipten değişmeden geçer. Ajan bir denetim ekler, hiçbirinin yerini almaz.
  2. Her ajan koşusu bir `founder` defter satırıdır, türü `build` ya da `decision` (türler kapalı kümedir, `26`; yeni
     tür uydurulmaz); `summary`'si ajan kimliğini, modeli ve çabayı (E644), tanım sha256'sını, diff'in sha'sını,
     bulguları, token ve maliyeti, duvar süresini taşır.
  3. Ölçülür: gerçek yakalama, ajanın bir bulgusudur ki onu düzeltmesinden önce kırmızı, sonra yeşil olan bir testle
     doğruladın ve satıra yazdın; rakibin ya da hakemin doğrulaması da sayılır. Yanlış alarm, nedeniyle reddettiğin
     bulgudur. E692 ve E693 yalnız oturum başına değil, bulgu başına ayrı ölçülür (atıf), birbirini karıştırmaz;
     ajanlı ve ajansız oturumlar ret, duvar süresi ve maliyetle karşılaştırılır.
  4. Yanlışlanabilir emeklilik: ajanlı 5 oturumdan sonra gerçek yakalama 0 ise ya da maliyeti kazandırdığı dakikaları
     aşıyorsa, bunu kaydeder ve ajanı emekli eder ya da yeniden tasarlarsın.
  5. Ajanın tanımı `agents/` altındadır ve kökeni gövdesindedir (`09`, E675); kapsülün araç kuralları geçerlidir
     (yasaklı araç yok).

**Sahibin ipucu (bu kez kural esnetildi; 2026-11-21, E693; ipucu, reçete değil). Akıllı doğrulama, aynı güç.**
- Olgu: oturumlarında bütün mutant tablolarını (`tests/mutate.py -j 4`) ve bütün unittest keşiflerini oturum başına
  birkaç kez koşuyorsun. 20261121T211913Z oturumunda kapsayıcı %100 CPU'da kaldı (operatörün ölçümü); zaaf uzlaşısı
  oturum süresinin %72–87'sinin kendi denetimlerini beklemekle geçtiğini ölçtü (E677).
- İpucu: doğrulamayı akıllı yap, gücünü düşürme. Oturum içinde yalnız değişikliğin etkileyebileceğini koş: E689'un hızlı
  geçişi ve `04`'ün zaten tanımladığı değişen satırların mutant seçimi. Bütün bildirimi ve bütün mutant tablolarını bir
  kez, push'tan önceki son prepush'ta koş. Önyükleme hakemi ve rakip her push'ta yine her şeyi, değişmeden koşar;
  kapının gücü düşmez.
- Ölç: oturum başına CPU dakikası ve duvar süresi, önce ve sonra; kaçaklar: son tam koşunun ya da hakemin yakalayıp
  kapsamlı koşuların kaçırdığı her şey. Kaçak görülürse kapsamı genişletirsin. Nasıl kurulacağı senindir.
