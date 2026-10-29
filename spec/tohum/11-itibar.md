# İtibar ve Puanlama

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: dispatch ve yeniden yazım kararlarında
Çapa: beklemede: bir sınıfta ikinci aday organ — itibar görünümü; puanlayıcı deterministik koddur

---

Her ajan kimliğinin (tanım hash'i: prompt hash + model + araç yüzeyi) bir itibarı vardır. İtibar
bir görünümdür: yazarı defteri okuyan deterministik puanlayıcı (hakemde), okuyucusu dispatcher ve
genesis, değiştirdiği karar "bu işi kime, hangi modelle, ne bütçeyle vereceğim ve kimi yeniden
yazacağım"dır. Puanı hiçbir zaman bir LLM vermez.

**Ne zaman açılır.** Bu karar ancak bir sınıfta en az iki aday organ varken gerçektir; tek organlı
sınıfta "kime" sorusu yoktur. Bu yüzden itibar görünümü bir sınıfta ikinci aday doğduğunda açılır
(Y4). Ondan önce gereken ham satırlar ilk günden yazılır: her sonucun `organ_id`'si,
`prompt_sha256`'sı, hayatta kalma ya da geri alma satırı ve ölçülmüş maliyeti. Görünüm bunlardan
sıfırdan kurulur (`16`).

**Skor.** İki sayıdan oluşur:
- **Güvenilirlik:** Beta posterioru (hayatta kalan, başarısız) karar sayılarına uygulanır; önsel
  `policy.json`'da. Alt sınır `19`'daki güven düzeyindedir.
- **Değer:** karar başına ortalama net değer = (hayatta kalan sonuçların şiddet ağırlığı − λ ·
  USD) / karar sayısı.
Sıra = güvenilirlik alt sınırı × karar başına ortalama net değer. Reel değerli bir toplamın Beta
alt sınırı tanımsızdır; bu yüzden Beta yalnız sayımlara uygulanır. λ ve pencere `policy.json`'da.
Hacim puan getirmez; kredi kök neden başınadır. **Şiddet avcıdan gelmez:** property ve sınıftan
`policy.json`'daki haritayla türetilir; avcının yazdığı şiddet yalnız ipucudur.

| Rol | Artı | Eksi |
|---|---|---|
| Avcı, adapter | Pencereyi geçmiş TP; faz 1–2'de ölmeyen bulgu oranı | FP; faz 1'de ölen bulgu; parmak izi bölme |
| Düzeltici, implementer | Hayatta kalan düzeltme; katman iddiası panelde tutmuş | Geri alınan düzeltme, etki kümesi büyüklüğüyle orantılı; izinsiz yola yazım |
| Yargıç | Faz 5 ile uyuşan faz kararı | Faz 5'in çürüttüğü karar; referanssız söz; talep ettiği testin oracle maliyeti λ · USD olarak |
| Maliyet mühendisi | Eşiği tutan daha ucuz basamak | Eşiği tutmayan basamağa harcanan bütçe |
| Oracle takımı | Flake'siz, geri alınmayan TP | Flaky test; geri alınan TP düzeltmesi |

**Maliyeti ajan yazmaz.** USD, okunan dosyalar ve sunulan model `çağır` işinin ya da sağlayıcı
geçidinin ölçümüdür (`08`); ajanın beyanı skora girmez.

**Soğuk başlangıç ve dilimler.** Bir ajan en az on karara bağlanmış sonucu olmadan sırasızdır;
SHADOW'daki oracle-doğrulanmış sonuçlar `policy.json`'daki indirimle sayılır, çünkü geri alınma
riski taşımazlar. İki üyeli sınıfta karar ikili karşılaştırmadır; lig tablosu üç ve üstü üyede
kurulur. Yeniden yazım yalnız mutlak alt sınır iki pencere üst üste sınıf eşiğinin altında kalınca
olur, her pencerede değil.

**Hayatta kalma ve yarı ömür.** Hiçbir sonuç merge anında puanlanmaz; pencere sınıfa göredir
(`07`). Yarı ömür (`policy.json`, başlangıç 30 gün) eski kararları yeni kararlara göre hafifletir;
eski kazanç bugünkü işi taşımaz. **Yeni karar yoksa çürüme yoktur:** boşta kalan bir ajanın
sayıları yalnız zaman geçti diye düşmez, aksi hâlde kusursuz ama boşta bir ajan yeniden yazıma
itilirdi.

**Kaynak başına itibar.** Her öneri `origin` taşır (`repo_pattern`, `llm_prior`, `synthesis`,
`own_outcome`, `10`). Aynı Beta ve değer hesabı kaynak ve koşul (`21`) başına da tutulur; sistem
zamanla hangi koşulda başka bir reponun kalıbına, hangi koşulda modelin kendi bilgisine, hangi
koşulda sentezine güveneceğini ölçerek öğrenir.

**İtibar ne yapar.** Aynı sınıfta en yüksek sıraya sahip ajan işi önce alır ve daha geniş
bütçe kullanır. Model basamağı değişiklikleri en az iki pencere bekler (histerezis); Sonnet'te
kazanan Sonnet'te kalır, düşen o sınıf için Opus'a çıkar. Geride kalan ajan genesis şeridine
gider: yeni kimlik, deneme süresi, soyağacı. `derived_from` zincirinde itibar tabanı taşınır;
yeniden yazım eksiyi sıfırlamaz. İki yeniden yazımdan sonra da alt dilimde kalan tür emekli olur.

**Puan için iş.** Aynı dosyada ardışık küçük düzeltmeler, aynı kök nedenden bulgu bölmeleri,
pencere sonrası geri almalar Gözcü'nün ölçtüğü kalıplardır; ölçülen ajan o pencerede sıfır
puan alır ve kalıp harness'e puan kanaryası olarak girer. Ders okuma kaydını ajan değil
dispatcher tutar. Lig tablosu sınıf ve basamak başınadır ve `status.md`'de görünür.
