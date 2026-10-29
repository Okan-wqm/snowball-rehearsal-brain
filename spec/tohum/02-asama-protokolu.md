# Aşama Protokolü

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: her aşama başında ve sonunda
Çapa: aşama çıkış satırları (`brain/state`); kilit (aşama, spec hash, çıkış satırı) anahtarlı; `setup/stage.json`

---

1. Kurucu spec'i taslaklar. En az şu sekiz bölümü vardır: amaç, doğruluk özellikleri, roller,
   sıralı mikro özellikler, çıkış testi, yasaklar, bütçe, teslim listesi; aşamaya özgü ek bölüm
   ayrı sayfa olabilir. Aşama özeti ön koşulu ve çıkış kapısını taşır. Tohumla gelen Aşama 0 ve 1
   spec'i Kurucu'nun ilk taslağı sayılır: listeden geçmezse Kurucu düzeltip rakibe sunar, geçerse
   incelemesini aşamanın `CHANGELOG.md`'sine tarihli satır olarak ekleyip sunar (`29b`); anayasal
   bir değer gerektiren düzeltme `blocked` olur.
2. Spec **yapısal kontrol listesinden** geçer ve tohum rakibi (`29`) onu çürütmeyi dener. Çürütme
   ancak hakemin yeniden koşturduğu bir yeniden üreticiyle sayılır; açık `not_refuted` dışındaki her
   sonuç kabul değildir. Liste temiz ve çürütme yoksa spec donar ve hash'i zincire yazılır (Aşama
   0'da önyükleme hakeminin sonuçlarına ve Rekor'a). Listenin mekanik maddelerini tohumun spec
   denetimi (önyükleme hakeminin kodu; spec brain arşivinden okunur, kapsayıcıda koşmaz) uygular;
   `spec.lint` Aşama 1 çıkış partisiyle gelir ve aynı listeyi uygular:
   - sekiz bölüm var ve boş değil;
   - her eşik ya `policy.json`'a ya da anayasal tabana atıf;
   - bütçe `policy.json` tavanının altında;
   - aşama özeti getirdiği yetenekleri `18`'deki adlarla listeler ("Her aşama" her zaman); listedeki
     her yeteneğin her `#kimlik`'i çıkış testinde bir satırın başında var; biri eksikse spec
     reddedilir;
   - her mikro özellik tek mekanizma getirir (`04`);
   - property spec'lerinde kalıp yok (`asama-4/06`);
   - hedef repoya özgü yol, araç ya da karar belgesi adı yok;
   - her yeni dosyanın okuyucusu `27`'de ve okuyucu bu aşamada bir kararı değiştiriyor (Y4);
   - her çapa ya çözülüyor ya da "beklemede: aşama N".
3. Kurucu inşa eder; takımı bu aşamanın bütçesi içinde kurar.
4. Hakem harness'i ölçer. Çıkış testi canlı ve uçtan ucadır; birim testi ve taklit çıkış kanıtı
   değildir, yalnız ön provadır. Verdict `PASS`, `FAIL` ya da `UNMEASURABLE`'dır (`19`).
5. **Çıkış kararı bir defter satırıdır.** PASS, `brain/state`'te hakemin yazdığı ve kökü Rekor'a
   bağlanan bir satırdır; Aşama 0'ın satırını etkinleştirmede aktarılan hakem yazar. Kurucu satırın
   kopyasını aşama dizinine tarihli sayfa olarak koyar; spec denetimi sayfanın hash'inin satırla
   eşleştiğini denetler. Bir sonraki aşamanın ajan dosyaları, araçları ve izinleri ancak kilit
   açılınca canlıya girer; kilit (aşama, spec hash, çıkış satırı) üçlüsüne anahtarlıdır ve yalnız
   PASS satırı onu açar. Kilit iki adımdır: (A)'da önyükleme hakemi yalnız (aşama, donmuş spec hash)
   çiftini denetler; açılışta operatör `stage-open` ile PASS satırını, zinciri ve kökü doğrular ve
   `setup/stage.json`'u yazar, önyükleme hakemi onu her `pull`'da okur (`asama-0/10a`). `lock.check`
   aracı döngü hakemine Aşama 1 çıkış partisiyle gelir. Hakem kodunu değiştiren her şey ayrıca operatör
   aktarımı ister (`01a`).
6. **Parti çıkışı.** Aşama içinde ilk okuyucusu doğan hakem parçası (`asama-1/13`) aynı protokolün
   dar hâliyle gelir: Kurucu partiyi `referee/` altında yazar, önyükleme hakemi her push'u yargılar;
   partinin mikro özellikleri bitince parti çıkış isteği (A), operatör aktarımı, (B)'de partinin ilk
   okuyucusunun canlı koşusu. Her aktarım bir insan dokunuşudur; aşama kilidi değişmez.

**Dikey dilim kuralı.** Hiçbir aşama döngünün tek bir fazını "tamamen" kurmaz. Her aşama
döngünün tamamını daha dar bir kapsamda canlı çalıştırır, sonra kapsam genişler.

**Bir aşama ileri kuralı.** Yalnız bir sonraki aşamanın spec'i donar. Daha sonraki aşamaların
sayfaları "hedef taslak" durumundadır: okunur, sırası gelince yeniden yazılır ve ancak o zaman donar.
Donmuş bir aşama dizinine dokunan spec isteği reddedilir (`spec_already_frozen`); donmuş spec yalnız
operatör kararıyla açılır.

**Çapa kuralı.** `taslak` ya da `hedef taslak` durumundaki sayfada çapa "beklemede: aşama N"
olarak yazılabilir. Aşama N PASS alınca çapa çözülmelidir; çözülmeyen çapa bayatlıktır.

**Harness şeridi.** Harness ve donmuş koltuklar hakem reposundadır (`01a`). Değişiklik adayını
yalnız şerit yazarı yazar ve beyin reposunda `referee/` altında yayımlar. Aday hatayı gösteren yeni
bir kendi-testi ekler (kasıtlı bozma), mevcutları ve tohum vektörlerini (`29a`) yeşil tutar,
performans eşiklerini yalnız `18`'deki prosedürle oynatır ve farklı modelden rakip yeniden
üretilmiş bir çürütme getiremez. Arşivde yeniden oynatma **yalnız dev arşivinde** yapılır;
held-out görünümüne dokunan hiçbir şerit işlemi yoktur. Geçmiş bir kararı gevşeten değişiklik
reddedilir. Kabul edilen aday canlıya aşama ya da parti çıkışında, operatör aktarımıyla girer.
