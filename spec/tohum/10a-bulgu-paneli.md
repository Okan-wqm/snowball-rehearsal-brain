# Bulgu Paneli (K5 ve üstü): Beş Faz

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: K5 ve üstü bulgu değerlendirirken
Çapa: beklemede: aşama 4 — faz ölüm sayıları; yargıç kalibrasyon defteri

---

Panelin amacı bulguyu "doğru mu" diye oylamak değil, beş fazda kanıtla çürütmeye çalışmak ve
çürütülemeyeni implementer'a eksiksiz bir dosya olarak vermektir.

**Bağımsızlığı üreten şey karakter değil, yapıdır.** Yargıçlara "birbirinize güvenmeyin" yazılmaz;
dört şey yazılır: zıt ispat yükü (üç koltuk, üç farklı soru), mühürlü karar (her fazda kararlar
hash'lenir, sonra açılır, tek çürütme turu), ayrı bağlam ve ikili ayrık model (`09a`), ve son
sözü yürütmenin söylemesi.

**Test talebi bir karardır.** Tartışmayı bitirmenin en ucuz yolu kanıttır: herhangi bir yargıç
herhangi bir fazda üreme testi talep edebilir; tartışma durur ve test-yazıcı testi yazar; testi
hiçbir yargıç yazmaz. Ama talep bedava değildir: talep, mühürlü bir "belirsiz" karardır ve faz 5
sonucuna karşı diğer kararlar gibi puanlanır; oracle'ın maliyeti talep eden yargıcın λ·USD'sine
yazılır (`11`). Böylece "her şeye test iste" baskın strateji olmaz ve bulguların çoğu faz 1 ve 2'de
ölmeye devam eder. "Bir an önce teslim edip kurtulma" dürtüsü sisteme böyle bağlanır.

| Faz | Soru | Yük | Kapanış |
|---|---|---|---|
| 1 Varlık | Referanslar var mı, kod iddia edileni söylüyor mu, kendi çıktısı kanıt sayılmış mı | Mekanik | Referans doğrulaması, bedava |
| 2 Erişilebilirlik | Gerçek bir çağırandan ya da girdiden bu koda yol var mı | Savcı yolu gösterir; Savunma ölü ya da korumalı olduğunu | Repo haritasında yol + kod referansı |
| 3 Sonuç | Kim neyi yanlış görür, ne bozulur; konvansiyon mu | Savcı sonucu adlandırır; Savunma kasıt kanıtı getirir | Sonuç adlandırılmış, kasıt kanıtı yok; niyet kanıtı yalnız beyin dışı yazardan (`04a` 11) |
| 4 Düzeltme ve etki | Ne değişecek, etki kümesi, maliyet, katman iddiası | Uygulayıcı temsilcisi; Savunma düzeltmenin bir şeyi bozacağını gösterebilir ve daha iyi bir düzeltme biçimi önerir (`10`) | `required_change` yapısal, etki kümesi, katman doğrulanmış (`23`) |
| 5 Üreme | Test kırmızı mı, düzeltmeyle yeşil mi, etki kümesi yeşil mi | Test-yazıcı ve düzeltici | Yürütme, `04a` şartlarıyla |

**Konuşma kuralları.** Her koltuk bir bulgu için tek bir oturumda kalır ve fazlar arasında o
oturuma devam eder; bağlam her fazda yeniden okunmaz. Effort `low`'dur. Her tur, her yargıç için
yapılandırılmış bir karardır: `{decision, refs[], sentence}`; `sentence` en fazla bir cümle,
`refs` en az bir `path:line`. Referanssız "katılıyorum" ya da "katılmıyorum" geçersizdir; o yargıç
o turda söz hakkını kaybeder. Kabul eden yargıç hangi referansın onu ikna ettiğini yazar. İki
turda kapanmayan faz faz 5'e gider: test karar verir. Turda karar mühürlemeyen yargıç o fazda eksi
puan alır. Bir bulgu bir fazı geçemezse orada ölür ve defter fazı, her yargıcın kararını ve
referansını yazar. Faz 4'ün `required_change` dizisi yapılandırılmış çıktının bir alanıdır.

**Implementer'a giden dosya.** Yalnız beş fazı geçen bulgu gider ve yalnız şunlarla: iddia,
kanıt referansları, erişim yolu, görünür sonuç, yapısal `required_change`, etki kümesi, üreme
testi, okunması gereken dersler. Tartışma dökümü arşivlenir, implementer'a verilmez.

**Düzeltme sonrası ikinci panel.** Implementer'ın diff'i 2., 3. ve 4. fazlardan bir kez daha
geçer: yol kapandı mı, etki kümesinde yeni kenar doğdu mu, güvenlik sınırına dokunuldu mu,
katman iddiası tutuyor mu. Geçemeyen diff merge kapısına ulaşmaz. İkinci panelin maliyeti
bulgunun bütçe satırındadır.

**Kalite takıntısı bir sayıdır.** Her yargıcın her fazdaki kararı, "belirsiz" talepleri dahil,
faz 5 sonucuna karşı puanlanır ve `11`'deki kurallarla ağırlığı değişir. Panelin öldürdüğü
bulgulardan gizli tohumla seçilen rastgele bir örnek oracle'la yeniden denetlenir; yanlış öldürme
oranı panelin kalibrasyonudur (`19`). Bağımsızlık `09a` ile ölçülür.
