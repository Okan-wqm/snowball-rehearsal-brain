# Mimari İlkeler VI: Dokümantasyon ve Bilgi

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: bir repo ilk kez haritalanırken; doküman ile kod çeliştiğinde; her K8 işinde; sistem hedefin dokümanını yazmaya ya da üretmeye başlarken
Çapa: K8 oracle'ı (`03`: her doküman iddiası koda çapalı, çözülmeyen çapa kırmızı); üretilmiş sayfa kuralı (`15` madde 4); kaynaklar `catalog.md` bölüm F

---

Katalog danışmadır (`31`). **Doküman türetilmiş bir görünümdür, doğruluk kaynağı değildir.** Doğruluk
kaynağı kod, şemalar, yapılandırma ve doğrulanmış repo haritasıdır; doküman bunların görünümüdür (SSOT'nin
SVoT görünümleri, `31a`). Sistem dokümanla iki evrede çalışır:

1. **Haritalarken: doküman ipucudur.** README, mimari karar kaydı, yorum ve wiki ilk bağlanmada okunur ama
   kodda doğrulanana kadar `trust: inferred` ipucudur; bayat olabilir (`14`: kod referanstır, doküman
   iddiadır). Kodun çeliştiği doküman iddiası bir bulgudur: bayat doküman, K8 (`03`).
2. **Ustalık doğrulandıktan sonra: doküman üretilir.** Sistem dokümanı doğrulanmış haritasından ve koddan
   kendisi üretir ve kod her değiştiğinde yeniden üretir; elle yazılmış hiçbir kopya kaymaz. Kaynağı yalnız
   koddan ve `trust: verified` harita kenarlarından gelir (`13`). Üretim K8 canlı olunca başlar (`03`);
   "ustalık doğrulandı"nın ölçütünü o aşamanın spec'i yazar (`02`). Üretilmiş doküman da aday olarak aynı
   kapıdan geçer, hedefin kendi doküman düzenine uyar (`15`).

| Kimlik · kanıt | İlke | Ne zaman | Bedel, yanlış uygulama | Bulma | Doğrulama |
|---|---|---|---|---|---|
| `docs-derived` · consensus (kayma) | Doküman kodun, şemanın, yapılandırmanın ve doğrulanmış haritanın görünümüdür; çelişkide referans koddur, çelişki bayat doküman bulgusudur | Her haritalamada; her doküman iddiası doğrulanana kadar ipucudur | Her bilgi kodda yaşamaz: niyet, gerekçe, reddedilen alternatifler, öğreticiler, runbook'lar türetilemez; bunlar çapalanır ve kısmen denetlenir (`adr`, `31e`). Kod da kusurlu olabilir: kodu dokümana uydurmak yalnız kendi oracle'ı olan ayrı bir bulguyla olur (`15`) | Env değişkeni, CLI bayrağı, port, uç, GraphQL alanı, varsayılan değer, imza ve bileşen adı anan dokümanlar; diyagramlar; davranışı yeniden anlatan yorumlar | Çapa çözümleme (`path:line` ya da sembol snapshot'ta çözülür); mekanik iddiaların (imza, bayrak, anahtar, uç, varsayılan) koddan çıkarılan envanterlerle karşılaştırılması; çözülmeyen çapa kırmızı |
| `docs-as-code` · practice | Doküman kodla aynı araçlarla yazılır ve bakılır: sürüm denetimi, düz metin işaretleme, kod incelemesi, CI'da derleme ve test; sahibi ve "tazelik tarihi" vardır | Doküman anlattığı kodun yanında; davranış değişikliği dokümanını aynı commit'te değiştirmeli | Araç ve inceleme bedeli; tek başına kaymayı önlemez, kaymayı incelenebilir ve test edilebilir kılar | `docs/`, site üreteci yapılandırması, markdown lint, CI'da bağlantı denetimi. Repo dışı wiki bir snapshot'ta denetlenemez: kapsama boşluğu olarak yazılır | Doküman CI'da derlenir; bağlantı ve çapa denetleyicisi (lychee); doküman ile çapaladığı kodun birlikte değişmesi |
| `living-docs` · practice | Yazılımla aynı hızda değişen doküman; burada kodun, şemanın, testin ve haritanın kendisinden üretilip her değişiklikte yeniden üretilerek: NestJS dekoratörlerinden OpenAPI, code-first GraphQL şeması ve iç gözlemle sunulan açıklamaları, TypeDoc ve rustdoc başvurusu, modelden diyagram, karar dizini, tohumun üretilmiş sayfaları | Başvuru malzemesi: API, yapılandırma anahtarları, CLI, şema, olay kataloğu, modül grafiği. Diátaxis'e göre başvuru "bilgi odaklıdır", "makineyi anlatır" ve yapısı ürünün yapısını izler: koddan türetilebilen kısım tam budur | Yalnız imzayı tekrarlayan üretilmiş metin bilgi katmaz; üreteç bakım ister; hedef repoda yeniden üretim, işaretlenmemiş insan düzenlemesini ezer; öğretici, nasıl-yapılır ve açıklama üretilemez | Swagger ve OpenAPI kurulumu, `autoSchemaFile`, TypeDoc yapılandırması, üretilmiş doküman dizinleri; mevcut bir şemanın yanında elle tutulan API dokümanı (ikinci kaynak) | CI'da yeniden üret ve karşılaştır (üretilmiş doküman taze üretime eşit); üretilmiş bölgeler işaretli ve elle düzenlenmemiş; işaretli bölgede bulunan elle düzenleme ezilmez, bildirilir |
| `model-views` · practice | Mimari tek bir model olarak tanımlanır (kişiler, yazılım sistemleri, konteynerler, bileşenler) ve farklı yakınlıkta diyagramlara işlenir: diyagram modelin görünümüdür, ayrı bir çizim değil (C4, Structurizr) | Aynı sistemi birden çok diyagram anlatıyor; diyagramlar koddan kaymış; konteyner ve bileşen görünümleri haritadan türetilebilir (Nx proje grafiği, compose dosyaları, Kubernetes manifestleri) | Model bakımı; büyük sistemin üretilmiş diyagramı derlenmeden okunmaz; bağlam düzeyindeki diyagram kodun tutmadığı insan niyeti taşır | Arkasında model olmayan ikili diyagramlar (PNG, draw.io); Structurizr DSL, Mermaid ya da PlantUML kaynakları | Her model öğesi bir kod artefaktına (proje, servis, dağıtım), her ilişki doğrulanmış bir harita kenarına çözülür; diyagramlar CI'da modelden işlenir; modelsiz ikili diyagram doğrulanamaz olarak bildirilir |
| `executable-docs` · practice | Dokümandaki örnekler derlenip test olarak koşar (Rust doküman testleri, Python doctest); örnekle yazılmış şartname koşar ve canlı doküman olur | README ve API dokümanındaki kod örnekleri; yapılandırma parçaları; açık kütüphane API'leri | Kırılgan örnekler; daha yavaş takım; düz yazının çoğu yürütülemez | Doküman yorumlarında ve docstring'lerde kod blokları; `cargo test --doc`, doctest ya da markdown kod bloğu koşucusu CI'da gerçekten koşuyor mu | Doküman testleri CI'da koşar; kasten bozulan örnek onları kırmızıya boyar (`fitness` doğrulama kuralı, `31e`) |
| `doc-drift` · empirical (yorum-kod tutarsızlığı) | Kodun çeliştiği ya da artık desteklemediği doküman iddialarının mekanik tespiti | İlk haritalama; her kod değişikliği (değişen koda çapalı dokümanlar); her K8 işi | Düz yazıda, açıkça planlanmış özelliklerde ve başka sürümün dokümanında yanlış pozitif. Bir modelin düz yazıdan çıkardığı iddia yalnız `trust: inferred` ipucudur | Güçlüden zayıfa: (1) yürütme (örnek koşar); (2) üretilmiş dokümanda yeniden üret ve karşılaştır; (3) çapa çözümleme; (4) iddia eşleme: kod parçası ve tablolardaki adlar (env, bayrak, uç, alan, port, varsayılan) koddan çıkarılan envanterlerle (`config`, uçlar, şema); (5) bağlantı denetimi; (6) birlikte değişme bayatlığı: çapaladığı kod değişmiş ama doküman dokunulmamış. Altıncısı aday üretir, tek başına bulgu değildir | Dedektörün kendisi doğrulanır: ekilmiş kayma (kodda bir yapılandırma anahtarını yeniden adlandır) bildirilir; temiz ağaç bildirim üretmez |

**Kanıt ve dürüst sınır.** Yorum-kod tutarsızlığı araştırması kaymanın gerçek olduğunu ve önemli olduğunu
gösterir: iComment, Linux, Mozilla, Wine ve Apache'de 60 tutarsızlık buldu; bunların 33'ü koddaki hata, 27'si
kötü yorumdu. Yani bir çelişki her zaman dokümanın değil, *bir yerin* kusurudur; varsayılan doküman
düzeltmesidir, kodu değiştirmek ayrı bulgu ister. Üretim, kaymayı kurgu gereği sıfırlar ama yalnız türetilebilen
başvuru kısmında; gerekçe ve öğretici insan yazımı kalır ve çapa denetimiyle korunur.

**Rakip kuralı burada da geçerlidir** (`31`). Kodu yeniden anlatan elle yazılmış doküman, ağacın zaten
tuttuğu bir gerçeğin ikinci kaynağıdır: rakip onu açık iddia olarak bildirir; doküman ile kod yeniden
üretilebilir biçimde ayrıştığında (çapa çözülmüyor, belgelenen bayrak ya da varsayılan kodda farklı) bulgu
kanıtlanmıştır.

**Kaynaklar** (`catalog.md`): `docs-derived` [SWE-DOCS] [ICOMMENT] [WEN-2019]; `docs-as-code` [WTD-DAC]
[SWE-DOCS] [LYCHEE]; `living-docs` [MARTRAIRE] [OPENAPI] [NEST-OPENAPI] [NEST-GQL] [GQL-SPEC] [TYPEDOC]
[DIATAXIS]; `model-views` [C4] [STRUCTURIZR]; `executable-docs` [RUSTDOC] [DOCTEST] [ADZIC]; `doc-drift`
[ICOMMENT] [WEN-2019] [LYCHEE].
