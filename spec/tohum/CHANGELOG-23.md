# Değişiklik Günlüğü — Tohum, 2.2'nin Yirmi İkinci Kayıtları

Tarih: 2026-11-28 · Sürüm: 2.2
Okunma: bir sayfanın geçmişi aranırken
Çapa: git geçmişi ve zincirdeki spec hash satırları

- 2.2 (2026-11-28, E751–E752; tohum dönemi AN; tohumun kendi testleri gerçek bir gecikme beklemez; seed-105'e
  rapor masası uzlaşısı: vakanın grubu).
  **İlk iş** (`25` 10b). Teslimden itibaren önyükleme hakeminin hiçbir denetimi kırmızı olmaz: bu dönem yalnız
  tohumun kendi testlerini ve `04`'ün, `26m`'nin ve `26n`'nin sonunu değiştirir; ne bir tablo, ne bir vektör, ne
  hakemin kodu değişir. Kurucu'nun bugünkü işi sürer, sırası `CHANGELOG-14`'ünkidir.
  Tohumun ipuçsuz tam mutasyon koşusu parça 19'da kırmızıydı (2026-11-25, 2026-11-26 ve koşu 46072742202):
  `manifest_read_retries` kabul edilmiş manifestin okumasını `gh_read`'in yeniden deneme gecikmelerine geri koyar,
  bir test onlara mock'suz ulaşıp gerçekten uyudu ve bütün takım 900 s'yi geçti (zaman aşımı, öldürme değil, E738).
  Sınıf testlerin kendi katmanında kapandı (E751): her test modülü önce `tests/no_real_delays.py`'yi içe aktarır ve
  tohumun kodunun sıfırdan büyük her uykusu o anda kırmızıdır (`RealDelay`). Kural `04`'ün sonundadır (`04:50-59`);
  `04:1-48` yer değiştirmedi. Testler `test_panel_epoch_an`; mutantlar, biri muhafızı kaldırır.
  Gevşetme yok.
  Yanıtlanan rapor (rapor masası uzlaşısı, Opus ve Sonnet paneli, iki panelin madde satırları birleşik; operatör
  kararı, sahibin yetkisiyle); her madde raporun yazıldığı hâliyle, kendi etiketiyle bir satırdır:
  `seed-105-which-names-are-a-paket-manifesti-for-a-case-s-group` → `26m:77-80`, `26n:73-78`:
  - (1) Nx'in `project.json`'ı paket manifesti mi: yanıtlandı, hayır (`26m:77-79`): paket manifesti temel adı
    `package.json` olan düzenli dosyadır, kapının `manifest`'i (`29k:51`) ve `01b:17`'nin bağımlılık manifesti;
    `project.json` bir Nx projesini bildirir (profilin kendi sözü, beyin `6f36fba` `referee/profile/derive.py:67-68`),
    paket adlandırmaz, npm onu okumaz, grup işaretlemez; hiçbir sayfa `project.json`'ı adlandırmaz; `package.json` tek
    başına aynı ya da daha kaba grubu verir, `26e:69`'un sıkılaştırma dediği yön;
  - (1, olgu) profil bir projenin dizinini `package.json` ya da `project.json` ile işaretler: teyit edildi
    (`derive.py:170`, `:573-580`); profilin okuması Kurucu'nundur ve ayrı bir sorudur ("proje", "paket manifesti"
    değil), bu yanıt ona dokunmaz;
  - (1, hedef) 59 `project.json` dizini, 34 `package.json`, ikisi yalnız `project.json` taşıyan iki birim, ağacın
    kökünün tek grup olacağı okuma: yanıtlandı, sıkılaştırma (`26m:79-80`): arama değiştirilen dosyanın dizininden
    birimin köküne kadardır, kök dahil, üstüne çıkmaz; yolda manifest yoksa grup birimin köküdür (`26e:68-69`); o iki
    birimin her biri kendi kökü olan gruptur, hiçbir grup iki birimi kapsamaz, grup bölmesi (`asama-1/13a:38-39`)
    gruplarını korur; kurulan yürüyüş birimin kökünün üstüne çıkar (beyin `6f36fba` `referee/cases/build.py:134-136`,
    `:484-493`; `referee/tests/test_cases.py:903-904` onu sabitler) ve kökte `package.json` taşıyan her hedefte
    sayfanın geri dönüşünü erişilmez kılardı; birimin kökünün üstüne çıkan yürüyüş benimsenmedi; sayılar panellerce
    yeniden sayılmadı;
  - (1, hiç düzenlenmez) yazılmış satır düzenlenmez, sonradan reddedilen bir okumayla yazılmış grup kümede kalır:
    teyit edildi (`26m:35-36`); böyle bir satır yoktur: kurulan kuralla (grup yalnız iki liste anlaşınca) yazılmış her
    satırın grubu birimin kökünde ya da altındadır, çünkü kurulan profil birimin kökünde bir manifest ister
    (`derive.py:573-580`); bu yanıt her birine aynı grubu verir (`26m:35` durur);
  - (1, yapım) grup yalnız iki liste aynı dizini verince yazılır, ayrılınca mutasyon `group_undecided` ile reddedilir
    ve yeniden önerilir: yanıtlandı, ara çözüm bu yanıtla yerini yitirdi (`26n:77-78`; kurulduğu gibi benimsenmedi:
    sayfa artık tek listeyi adlandırır, karar verilmemiş bir şey kalmaz); bundan sonra açık grup yüzünden hiçbir
    mutasyon reddedilmez, şimdiye dek reddedilenler yeniden önerilir ve gruplarını alır; `group_unmade` değişmez;
    ikinci listeyi nasıl bırakacağı, `group_undecided`'ın ve testinin ne olacağı Kurucu'nundur; sayfa sessizken
    reddetmek doğruydu;
  - (2) başka bir ekosistemin manifesti (`pyproject.toml`, `Cargo.toml`, `go.mod`, ...) sayılır mı: Aşama 1 için
    yanıtlandı, hayır, hiçbiri işaretlemez (`26m:78-79`); sonraki adlar npm olmayan bir birim ya da araç getiren
    döneme ertelendi (neden: Aşama 1'in tek aracı `eslint`'tir, `29za:25`; yeni ekosistem kendi tanımlayıcısıyla,
    manifest ve kilit desenleriyle veri olarak gelir, `31c:23-27`, `31g:32-35`); kural araç başınadır;
  - (2, yapım) yalnız böyle bir dosya taşıyan dizin işaretlemez ve yürüyüş yukarı sürer: ilk yarısı kurulduğu gibi
    benimsendi (bilinmeyen ekosistem kapalıya düşer, `31g:35`); ikinci yarısı değişti: yürüyüş yalnız birimin köküne
    kadar, kök dahil, sürer (`26m:79-80`);
  - soru (manifestleri adlandıran bir cümle ya da onları adlandıran kural, araç başına mı profil başına mı,
    `project.json` biri mi): yanıtlandı (`26m:77-79`, `26n:73-75`): tek ad `package.json`, kapının `manifest` listesi
    (`29k:51`), böylece kapının manifesti ile grubun manifesti aynı şeydir; kural araç başınadır; `project.json` biri
    değildir; profil başına reddedildi (profil manifest listesi türetmez, `29k:12-38`; profilden ya da Kurucu'dan
    gelen bir liste ölçünün bulaşma birimini, `19:69`, kaydırabilirdi);
  - (kendi okumaları) okunmayan manifest (bağ, dizin) işaretlemez, ağacın kökü `.`'dır (`build.py:130-136`): kurulduğu
    gibi benimsendi (`26n:75-76`; bir birimin manifestini `derive.py:573-580` da düzenli dosya diye yargılar);
  - not (hiçbir şey kırmızı değil, adı geçen testler geçer): not edildi (paneller testleri yeniden koşmadı); iki
    kurulan test sınırsız yürüyüşü ve iki liste kuralını sabitler
    (`Group.test_a_manifest_above_the_unit_s_root_is_still_the_nearest`,
    `Built.test_a_group_the_page_leaves_open_is_refused`); onları değiştirmek Kurucu'nun kendi işidir, kırmızı
    değildir.
  Gevşetme yok: sınır hiçbir sayfa satırını gevşetmez (`26e:69`'un geri dönüşünün işleyebildiği okumadır), kurulan
  koda göre daha çok grup verir; `census_min_groups` (`18a:51`), K0'ın kuralı (`19:24`) ve vektörler değişmez; sahip
  kararı gerekmez; mevcut işi engellemez.
