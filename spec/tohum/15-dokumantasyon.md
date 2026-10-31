# Dokümantasyon: Tarihli Sayfalar, Üretilmiş Raporlar, Hedefin Kendi Dokümanı

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: her sayfa yazarken, her döngüde doküman üretilirken ve her K8 işinde
Çapa: INDEX.md üretimi; çapa çözümleme kontrolü; docs/organs ve docs/findings

---

1. **Bir özellik, bir sayfa.** Bir organ, bir kural, bir karar, bir aşama bölümü: her biri tek
   sayfa. Sayfa 80 satırı geçerse bölünür. Üretilmiş dizinler bu sınırdan muaftır.
2. **Tarih başlıkta.** Tarih, sürüm, durum ve sahibi; sürüm yalnız başlıkta yaşar.
3. **Her sayfanın çapası vardır.** Sayfayı kanıtlayan dosya, defter ya da test. Çapası
   çözülmeyen sayfa bayattır ve bir kapıyı kırmızıya boyar. Tek istisna: `taslak` ya da
   `hedef taslak` sayfada "beklemede: aşama N" çapası; aşama N PASS alınca çözülmelidir.
4. **Üretilebilen sayfa üretilir.** Defterden türetilebilen her şey elle yazılmaz; her döngüde
   yeniden üretilir. Üretilmiş sayfa elle düzenlenemez; düzenleme zincir kırığıdır. Hedefin ve
   sistemin kendi kodunun haritası (neyin neye bağlı olduğu, `13`) insanın okuyacağı bir çizim
   olarak da üretilir ve ilgili kod değişince yeniden üretilir; bayat çizim bayat sayfadır (E301).
5. **Dizin mekaniktir.** `INDEX.md` başlıklardan `docs.index` ile üretilir. Görev haritası elle
   yazılan ayrı bir sayfadır (`00b`).
6. **Aşama spec'i sayfadır.** Her bölüm ayrı sayfa; özet sayfası ön koşulu, çıkış kapısını ve
   sayfa listesini taşır. Çıkış raporu `brain/state`'te hakemin yazdığı bir defter satırıdır;
   aşama dizinindeki tarihli sayfa onun kopyasıdır ve hash'i satırla eşleşir (`spec.lint`).
7. **Değişiklik günlüğü ayrı ve sıralıdır.** Sayfalar bugünü anlatır; geçmiş `CHANGELOG.md`'de
   ve zincirdedir.
8. **Spec operatörün dilinde, sistem çıktısı İngilizce.** Bulgular, organ sayfaları, defterler ve
   `status.md` İngilizcedir; ajanlar ve dış okuyucular için tek dil.

**Her organın sayfası.** `<state_root>/docs/organs/<kimlik-hash>.md`, zincirden üretilir: amaç ve
kapsam, doğduğu boşluk ve ölçüm, prompt ve araç yüzeyi hash'i, kabul ve yaşam döngüsü geçişleri
tarihleriyle, itibar eğrisi, ablasyon sonuçları, soyağacı, ürettiği bulgular, yaptığı düzeltmeler,
hayatta kalma ve geri alma sayıları, maliyet.

**Her bulgunun sayfası, iki format.** Makine için `findings.jsonl` satırı; insan için
`<state_root>/docs/findings/<fingerprint>.md`: iddia ve kanıt, sınıf ve property, bulan organ,
panel fazları ve her fazın kararı (hangi yargıç, hangi referansla), oracle sonucu (K0–K2'de araç
yeniden koşusunun, K5'ten itibaren test koşularının hash'leri), düzeltme özeti ve etki kümesi,
merge ve hayatta kalma durumu, geri alındıysa nedeni, doğan dersler, toplam maliyet. Unresolved
ve FP bulgular da sayfa alır; kapanış nedeni yazılır. İndeksler üretilir.

**Şablon ve güvenlik.** Üretilmiş sayfalar, PR başlık ve gövdeleri ve commit mesajları sabit
şablondan yazılır; ajan metinleri kaçışlı, uzunluk sınırlı kod alanlarına konur; bağlantı, HTML,
kişi anma ve "kapatır" anahtar kelimeleri temizlenir. Üretilmiş sayfalar memory değil rapordur:
okuyucusu operatördür, defterden yeniden üretilebilir. `status.md`'nin dondurma, bütçe ve insan
dokunuşu bloğunu hakemin `status.block`'u yazar; geri kalanı oyuncunun `docs.render` önerisidir.

**K6 ambargosu.** K6 bulgularının sayfaları, testleri ve iddiaları mühürlü depodadır. Açık
hedefte bir K6 düzeltmesi `main`'e terfi edilebildiği güne kadar yalnız özel ve çatallanmamış bir
aynada yaşar; açık bir repodan alınan çatal özel olamaz.

## Hedef reponun dokümanı da geliştirilir

Geliştirme yalnız kodla değil dokümanla da yapılır: snowball hedef reponun dokümanını da yazar ve
düzeltir. Bu iş K8 sınıfıdır (`03`): bayat doküman ve davranışı değişmiş kodun eksik dokümanı.

- **Referans koddur** (`14`). Doküman kodla çelişirse doküman düzeltilir; kodu dokümana
  uydurmak ancak kodun yanlış olduğunu gösteren ayrı bir bulguyla ve onun oracle'ıyla olur.
  Doküman düzeltmesi de silme kurallarına uyar (`07a`).
- **Her doküman iddiası koda çapalıdır:** `path:line` ya da sembol. Oracle mekaniktir: çapa
  çözülür; denetlenebilir iddialar (imza, CLI bayrağı, yapılandırma anahtarı, uç adı, varsayılan
  değer) koda karşı doğrulanır; çözülmeyen çapa kırmızıdır.
- **Reponun kendi düzenine uyulur:** dil, dosya yeri, biçim ve başlık yapısı profilden çıkarılır;
  bu sayfadaki kurallar hedefin dokümanına dayatılmaz.
- **Aynı kapı.** Doküman değişikliği aday olarak yayımlanır ve aynı kapıdan geçer; doküman yolları
  diff-guard'dan yalnız K8 sınıfında geçer, kod yoluna dokunan K8 adayı reddedilir.
- **Ölçü.** Çözülen bayat çapa, eklenen çapalı iddia ve doküman düzeltmelerinin hayatta kalma
  oranı; K8 bulgu birikimi doküman organının doğum sinyalidir (`17`).

**Yerleşim.** Beyne ait sayfalar `tohum/`, aşama sayfaları `asama-N/`, repoya özgü üretilmiş
sayfalar `<state_root>/docs/`. Kurucu her oturum `00` ve `00a` ile başlar; görev başına `00b`'nin
gösterdiği sayfaları okur, fazlasını değil; `INDEX.md` sayfa aramak içindir.
