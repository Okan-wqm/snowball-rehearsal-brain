# Mimari İlkeler VIII: Çatışmalar ve Tarama Sinyalleri

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: iki ilke aynı durumda farklı yön gösterdiğinde; bir repo ilkeler açısından taranırken; rakip bir tasarımı çürütmeye çalışırken
Çapa: beklemede: Aşama 3 — repo haritasının (b) katmanı ve sinyallerin kontrolleri; kaynaklar `catalog.md` "Where principles conflict" ve "Scan signals" bölümleri

---

Katalog danışmadır (`31`). İlkeler çoğu zaman birbirini sınırlar; çatışma bir hata değil, kararın kendisidir.
Aşağıdaki sezgiler cevap değil, `decision` satırında tartılacak ağırlıklardır.

| Gerilim | Neden gerçek | Sezgi |
|---|---|---|
| `dry` ve bağlam özerkliği | Bağlamlar arası paylaşılan kod yayını ve anlamı birbirine bağlar | Alan mantığını değil, **üretilmiş sözleşmeyi** paylaş; bağlamlar arası kazara tekrarı kabul et |
| `dry` ve `dry-limits`, `yagni` | İki kopya meşru olarak ayrışabilir, soyutlama yanlış olabilir | Varsayılan üç kuralı; daha erken birleştirme yalnız birlikte değişme ya da ayrışma kanıtıyla |
| `ssot` ve erişilebilirlik, gecikme | Tek otorite uzak okuma ve tek hata noktası demektir | Tek otorite, bayatlık sınırı ve yeniden kurma kontrolüyle **beyanlı** türetilmiş kopyalar |
| `svot` ve bağlam sınırları | Tek kelime, birden çok meşru anlam | Ayrı adlı metrikler; SVoT'yi kelime başına değil ad başına uygula |
| `event-sourcing`, `cqrs` ve `kiss` | Pek çok sistemin hiç kullanmadığı yarar için büyük ve kalıcı bedel | Bugünkü gereksinim iste: denetim, zaman sorgusu, ayrışan okuma biçimleri |
| Mikroservis ve tutarlılık | Yerel işlemler yalıtımsız sagalara dönüşür | Saga çok karmaşıksa telafi yazmadan önce sınırı sorgula |
| `immutability`, `ledger` ve silme hakkı | Yalnız ekleyen yapı unutamaz | Hash ve başvuru sakla; kişisel veri zincirin dışında kalır |
| Şema uyumluluğu ve değişim hızı | Uyumluluk kapısı bazı değişiklikleri engeller | Kırmak yerine genişlet-daralt; daraltma adımı kayıtlı |
| `flags` ve davranışın SSOT'si, `kiss` | Bayrak gizli ikinci davranış yaratır | Bayrak başına sahip ve son tarih; tam yayılımda kaldır (sistem bayrak eklemez, Y3) |
| `registry` ve `yagni` | Az çeşitte dolaylılık | Kaydı ikinci ya da üçüncü gerçek çeşitte, ya da çekirdekte çeşit adları belirince getir |
| Katı ayrıştırma ve hoşgörülü okuma | Hoşgörü kusuru gizler, katılık zararsız eklemede kırılır | İhtiyacın olanda katı ol; bilinmeyen alanları yalnız açık bir politikayla yok say |
| Tek pano ve ekip özerkliği | Merkezî panolar çürür, yerel olanlar ayrışır | Ortak anlam kuralları, yerel panolar |
| Üretilmiş doküman ve insan bilgisi | Üreteç gerekçe ve öğretici üretemez; yeniden üretim düzenlemeyi ezer | Yalnız başvuruyu üret; gerekçe çapalı kayıtta; üretilmiş bölgeleri işaretle (`31f`) |
| "Kod kazanır" ve "kusur kodda" | Doküman amaçlanan davranışı doğru anlatıyor olabilir | Varsayılan doküman düzeltmesi; kodu değiştirmek kendi oracle'ı olan ayrı bulgu ister |

**Tarama sinyalleri.** Sinyal yalnız aday üretir (`trust: observed` ya da `inferred`); karar sütundaki
kontrolün sonucudur.

| Repodaki sinyal | Aday ilkeler | Mekanik kontrol |
|---|---|---|
| İki Nx uygulaması ya da servis aynı tabloya yazıyor | `sor`, `single-writer`, `outbox` | Statik yazar haritası; DB rolü yetki testi; kayıp güncelleme yeniden üreticisi |
| Aynı enum, sabit ya da regex TS, Python ve Rust'ta | `ssot`, `dry`, `schema-registry` | Diller arası eşlik testi; kod üretimi ve yeniden üret-karşılaştır |
| GraphQL SDL ya da proto'yu aynalayan elle yazılmış tipler | `ssot`, `schema-registry` | Üretilmiş tipler; yeniden üretimde CI farkı |
| Tek işleyicide önce `save()` sonra `publish()` | `outbox`, `idempotency` | Hata enjeksiyonu testi; statik çift yazım taraması |
| Yan etkili, ayıklamasız tüketici | `idempotency` | İki kez ve bozuk sırayla teslim property testi |
| Birçok dosyada `if (ecosystem === …)` | `registry`, `ports-adapters` | Genellik taraması; eklenti başına uyum takımı |
| Başka uygulamanın iç dosyalarına import | `bounded-context`, `dependency-rule` | Nx module boundaries ya da dependency-cruiser |
| Import döngüleri | `dependency-rule` | Döngü sayısı sıfır |
| Bir metriğin iki yerde hesaplanması | `svot` | Tek fikstür verisinde eşitlik |
| TTL'siz ya da geçersizleştirmesiz, Postgres'i aynalayan Redis anahtarı | `derived` | Yeniden kur ve karşılaştır; yazım yollarında geçersizleştirme kapsaması |
| `process.env.X` birçok dosyada farklı yedek değerle | `config`, `parse-boundary` | Anahtar envanteri; açılışta şema doğrulaması |
| Çağırana özgü bayraklı paylaşılan fonksiyon | `dry-limits` | Çağıran başına dal sayısı; yeşil testlerle geri göm ve yeniden çıkar |
| Bağlamlar arası klon eşleşmesi | `dup-kind`, `dry`, `bounded-context` | Birlikte değişme geçmişi; farklılık testi |
| Alan imzalarında üretici SDK tipleri | `acl`, `ports-adapters` | Import kuralı: dış tipler yalnız adaptörde |
| Uzun süredir her ortamda sabit bayraklar | `flags`, `yagni` | Bayrak envanteri; ortamlar arası sabitlik tespiti |
| Kullanımı izlenmeyen `@deprecated` | `evolve` | Kullanım sayısı; sıfırda kaldırma |
| Servisler arasında tekrarlanan yetki kuralı | `policy`, `ssot` | Envanter × koruma testi; politika birim testleri |
| Farklı anlamda aynı telemetri metriği | `observability`, `svot` | Anlam kurallarına karşı ad lint'i |
| Dokümanın andığı env, bayrak, uç ya da varsayılan kodda yok ya da farklı | `docs-derived`, `doc-drift` | Kod envanterleriyle iddia eşleme; çapa çözümleme |
| OpenAPI ya da GraphQL şemasının yanında elle tutulan API dokümanı | `living-docs`, `ssot` | Şemadan üret; yeniden üret ve karşılaştır |
| Arkasında model olmayan diyagram görüntüleri | `model-views` | Model öğeleri kod artefaktlarına ve doğrulanmış kenarlara çözülür |
| Dokümanda hiç koşmayan kod blokları | `executable-docs` | CI'da doküman testleri; bozuk örnek denetimi |
