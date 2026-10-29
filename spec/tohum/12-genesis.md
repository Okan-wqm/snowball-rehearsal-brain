# Genesis: Organ Yazma, Ölçme, Kaldırma, Yeniden Yazma

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: yeni organ yazarken ve ablasyonda
Çapa: `ledger.jsonl` `part: accept` satırları; ablasyon raporları; genesis-queue.jsonl

---

Genesis bir aşama değil, döngünün organ ekleme yoludur. Aşamalar genesis'in hangi sınıfta ve
hangi organ türünde çalışabileceğini açar. Organ türleri kapalı bir küme değildir: adapter,
dedektör, skill, ajan, memory türü, property, harita adapter'ı, ders kümesi ve sistemin önerdiği
yeni türler (yeni bir öğrenme kipi, yeni bir hafıza türü, yeni bir sinyal türü). Yeni türün tek
şartı Y4, Y5 ve çekişme protokolüdür (`10`).

**İzin listesi.** Merge kapısına yalnız tanım hash'i kapının izin listesinde olan organın çıktısı
gider. Listeye giriş hakem kabul yoludur: Aşama 1'de `brain.accept` (beyin kodu testleri, tohum
vektörleri, rakip), sonra genesis'in ACTIVE geçişi. Listede olmayan bir hash'in ürettiği aday,
içeriği ne olursa olsun reddedilir.

**Yaşam döngüsü ne zaman canlıdır.** Bir sınıfın ilk organı kabul yoluyla girer; aynı sınıfta
ikinci aday doğduğu an (bir sinyalin taslağı ya da bir yeniden yazım) o sınıfta yaşam döngüsü,
`genesis-queue.jsonl` ve itibar görünümü (`11`) canlı olur. Tek organlı sınıfta "hangisi" kararı
yoktur (Y4). Geçişler yalnız ölçümle olur ve zincire yazılır; eşik kuralları `policy.json`'da.

| Durum | Anlamı | Geçiş koşulu |
|---|---|---|
| DRAFT | Yazıldı, çekişme protokolünden geçiyor | Aşamanın açık fazları (`10`); oracle PASS |
| SHADOW | Canlıda koşuyor, ölçülüyor, hiçbir karara girmiyor | Dev setinde tabanı anlamlı geçer (aşağıda), clean'de oracle'ın reddettiği bulgu yok, bütçe içinde; en az `shadow_min_runs` koşu |
| ACTIVE | Tanım hash'i izin listesinde; çıktısı karara ve merge kapısına giriyor | Dev harness sayıları; itibar penceresi ACTIVE'den sonra dolar, önce değil |
| DEGRADED | Ölçülüyor, karara girmiyor, izin listesinden çıkmış | İtibar alt sınırı iki pencere eşik altı, ablasyonda katkının üst sınırı marjın altında, kapsayıcılık ihlali |
| RETIRED | Dispatch dışı; tanımı ve geçmişi zincirde | İki yeniden yazımdan sonra da alt dilim; iki ablasyon üst üste marjın altında; ya da `shadow_max_windows` pencere boyunca SHADOW'da kalıp ACTIVE olamamak |

SHADOW çıktılarının oracle sonuçları indirimle itibara sayılır (`11`); aksi hâlde hiçbir organ
ACTIVE'e ulaşamaz. Bir organı ACTIVE'e taşıyan, merge'e götüren ya da hayatta kalma sayan eşikler
eylemi kapılar ve yalnız sıkılaşır (Y11, `18`).

**Kabul.** Bir organ ancak şu iki yoldan biriyle kabul edilir (`19`): (1) üstünlük: aynı
vakalarda eşli, tam tek yönlü McNemar, en az 8 uyuşmaz çift, ayarda kullanılmamış vakalarda,
p < 0,10, yön lehte; (2) değer: aynı isabette (non-inferiority, δ = 0,05) değer / USD oranının eşli
bootstrap alt sınırı ≥ 1,2. Tek koşuluk fark kabul değildir.

**Gereklilik ablasyonla ölçülür.** Bir organın gerekliliği, onsuz harness'in ne kaybettiğidir.
Ölçü tek sayı değil bileşik skordur: recall, precision, değer / USD, kapsama ve öğrenme
organlarında düşürdüğü hata oranı (Y5). Bedava organlar her döngü, LLM organları rastgele yüzde
yirmilik alt kümelerle ve aylık harcamanın en fazla onda biriyle ablasyona girer. Karar nokta
tahminine değil üst sınıra bakar: katkının %90 üst sınırı `ablation_margin`'in altındaysa organ
DEGRADED'e iner, bir sonraki ablasyonda da öyleyse RETIRED olur. Nokta tahmini sıfır ama üst
sınırı marjın üstündeyse organ kalır ve ablasyon örneklemi büyür; küçük alt kümede sıfır görmek
gürültüdür. Aynı döngüde birbiriyle örtüşen iki organ birlikte emekli edilmez; biri gidince öteki
yeniden ölçülür. "İleride lazım olur" gerekçe değildir.

**Yeniden yazım soyağacıdır.** Yeniden yazılan organ yeni kimliktir (yeni hash), `derived_from`
ile eskisine bağlıdır ve DRAFT'tan başlar; aynı repo içinde itibar tabanı zincir boyunca taşınır,
yeniden yazım eksiyi sıfırlamaz. Repo sınırında zincir kesilir (`21`). "Bu ajan geçen yıl neydi,
kaç kez yeniden yazıldı, her sürüm ne kadar isabet etti" tek sorgudur.

**Sınırlar.** Genesis harness'i, yasaları, `policy.json`'un anayasal bölümünü, donmuş koltukları,
itibar puanlayıcısını ve şemaları yazamaz; bunlar hakem reposundadır. Yeni bir `cause` ya da
`miss_reason` kategorisi ihtiyacı şerit yazarının görevidir (`09a`). Bir pencerede üretilen taslak
sayısı bütçeyle sınırlıdır; taşma Gözcü'nün işaretidir, çünkü çok taslak çoğu zaman ölçülmemiş bir
boşluğun izidir. Tetikler `17`'dedir.

**Kendini geliştirmenin testi.** Bir sınıfta yaşam döngüsünü canlıya alan aşama, genesis
provasının satırlarını çıkış testinde taşır (`12a`, `18`): büyüme, budama, yeniden yazım ve
gereksiz büyümeme.
