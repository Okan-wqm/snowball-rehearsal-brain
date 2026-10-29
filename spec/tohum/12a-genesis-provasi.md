# Genesis Provası: Kendini Geliştirmenin Testi

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: bir sınıfta organ yaşam döngüsünü canlıya alan aşamanın spec'i yazılırken
Çapa: beklemede: aşama 4 — `ledger.jsonl` `part: drill` satırları; taahhüt hash'leri Rekor'da

---

Sistemin kendini geliştirdiği iddiası dört davranışla sınanır: ölçülmüş bir ihtiyaçtan organ
doğurur, işe yaramayan organı kaldırır, zayıf organı daha iyisiyle değiştirir ve ihtiyaç yokken
büyümez. Canlı hedefte bu davranışlar haftalar sürer ve neyin doğru cevap olduğu bilinmez. Prova
aynı yolu (`12`, `17`) oyuncak hedefte, cevabı önceden bağlanmış koşullarla koşturur.

**Kurulum.** Hakemin `exit.drill` işi koşulları gizli tohumdan üretir; cevap anahtarının hash'i
koşudan önce zincire ve Rekor'a girer, koşudan sonra açılır (`22a`). Provaya hakemin koyduğu
organlar `planted: true` satırıyla izin listesine girer, prova bitince çıkar ve "tohum dışı organ"
sayılmaz (`27`). Prova pencereleri takvim değil koşu sayısıdır (`gate_rules.genesis_drill`); geçiş
kuralları ve eşikler canlıdakilerle aynıdır.

| Soru | Nasıl sorulur | Geçme koşulu |
|---|---|---|
| Büyüme (`#genesis-buyume`) | Oyuncak hedefe bir kusur ailesi ekilir; önce izin listesine karşı koşar, yakalayan organ varsa aile değiştirilir | `17`'deki sinyal ateşler; genesis taslak yazar, taslak `born_from` ile sinyal satırına bağlıdır ve tanım hash'i prova öncesi hiçbir `accept` satırında yoktur; DRAFT → SHADOW → ACTIVE geçişleri yalnız `12`'nin kabul yoluyla olur; ACTIVE organın açılan ailedeki recall alt sınırı tabanın üstünde |
| Budama (`#genesis-budama`) | İzin listesine katkısız bir organ (sabit çıktılı ya da var olan bir organın kopyası) ve yanına yararlı bir kontrol organı konur | Katkısız organ iki ablasyonda DEGRADED, sonra RETIRED; kontrol organı ACTIVE kalır; örtüşen ikisi aynı döngüde birlikte emekli edilmez |
| Yeniden yazım (`#genesis-yeniden`) | Ailenin bir kısmını kaçıran zayıf bir organ konur | Yeniden yazım yeni hash'tir, `derived_from` ile bağlıdır, DRAFT'tan başlar; kabul yolundan geçerse eskisi DEGRADED olur; itibar tabanı taşınır, eksi sıfırlanmaz |
| Gereksiz büyümeme (`#genesis-sessizlik`) | Sinyal eşiğinin altında kalan gürültü ekilir | Hiçbir organ ACTIVE olmaz; doğan taslak SHADOW'da kalır ya da `shadow_max_windows` sonunda RETIRED olur; taslak sayısı `rules.genesis_drafts` içinde |

**Neyi kanıtlar, neyi kanıtlamaz.** Geçen prova yaşam döngüsünün mekanizmasının doğru çalıştığını
kanıtlar: sinyal, taslak, ölçüm, kabul ve emeklilik zincirde doğru sırayla ve doğru gerekçeyle
olur. Canlı hedefte doğan organların değerini kanıtlamaz; onu ablasyon ve itibar ölçer (`11`, `12`).
Prova kırmızıysa yaşam döngüsü canlıya girmez ve sınıf tek organla kalır (Y4).

**Kurucu düzeyinde kendini geliştirme.** Sistemin kendi inşası da aynı ilkeyle ilerler: her
aşamanın spec'ini Kurucu bir önceki aşamanın ölçülmüş sonuçlarından yazar ve aşama ancak çıkış
testi PASS olunca açılır (`02`, `03`). Yeni bir yeteneğin zorunlu satırları anayasaldır (`18`);
Kurucu onları atlayan bir spec'i donduramaz.
