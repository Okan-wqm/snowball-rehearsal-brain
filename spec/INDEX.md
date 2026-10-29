# Dizin

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: sayfa ararken; görev seçmek için `tohum/00b-gorev-haritasi.md`
Çapa: bu dizin dosya başlıklarından üretilir; elle düzenlenmez ve 80 satır sınırından muaftır

---

## Tohum: çekirdek, yasalar ve protokoller

| Sayfa | Başlık | Okunma |
|---|---|---|
| `tohum/00-cekirdek.md` | Çekirdek — Kurucu Ajan ve Yasalar | her oturumda |
| `tohum/00a-sinirlar-operator-ilk-gorev.md` | Kurucu'nun Sınırları, Operatörün İşi, İlk Görev | her oturumda, çekirdekten hemen sonra |
| `tohum/00b-gorev-haritasi.md` | Görev Haritası | her oturumda, görev seçilirken |
| `tohum/01-hedef-sistem.md` | Hedef Sistem | ilk oturumda |
| `tohum/01a-mimari-ve-yetki.md` | Mimari ve Yetki: Dört Yer | ilk oturumda ve her yeni repoya bağlanırken |
| `tohum/01b-kapi-kurallari.md` | Kapı Kuralları, Tetik, Döngü İşlemi | her merge ve her state yazımında |
| `tohum/02-asama-protokolu.md` | Aşama Protokolü | her aşama başında ve sonunda |
| `tohum/03-sinif-merdiveni.md` | Sınıf Merdiveni ve Aşama Sırası | yeni sınıf ya da aşama açılırken |
| `tohum/04-is-boyutu-ve-gercek-test.md` | İş Boyutu ve Gerçek Test | her mikro görevde ve her test yazarken |
| `tohum/04a-oracle-sertlestirme.md` | Oracle Sertleştirme: Test Yanlış Nedenle Yeşile Dönmesin | her oracle koşusunda ve test-yazıcı tasarlarken |
| `tohum/05-etki-kumesi-ve-baglanti.md` | Etki Kümesi ve Bağlantı Kuralı | koda dokunmadan önce ve yeni organ tasarlarken |
| `tohum/06-maliyet-merdiveni.md` | Maliyet Merdiveni ve Bütçe | bir yetenek harness'te geçtikten sonra ve her bütçe kararında |
| `tohum/07-entegrasyon-dali-ve-geri-alma.md` | Entegrasyon Dalı, Nöbetçi, Geri Alma, Bulgu Kimliği | her döngü başında ve her merge'de |
| `tohum/08-sandbox-ve-durust-bildirim.md` | Sandbox ve Dürüst Bildirim (Y10) | her hakem işi tasarlanırken ve her ajan dispatch'inde |
| `tohum/09-takim-kurma.md` | Takım Kurma Kuralları | takım kurarken ve ajan önerirken |
| `tohum/09a-bagimsizlik.md` | Bağımsızlık, Donmuş Koltuklar, Şerit Yazarı | her dispatch'te ve her koltuk değişikliğinde |
| `tohum/10-cekisme-protokolu.md` | Çekişme Protokolü: Her Artefakt İçin | her artefakt üretildiğinde |
| `tohum/10a-bulgu-paneli.md` | Bulgu Paneli (K5 ve üstü): Beş Faz | K5 ve üstü bulgu değerlendirirken |
| `tohum/11-itibar.md` | İtibar ve Puanlama | dispatch ve yeniden yazım kararlarında |
| `tohum/12-genesis.md` | Genesis: Organ Yazma, Ölçme, Kaldırma, Yeniden Yazma | yeni organ yazarken ve ablasyonda |
| `tohum/12a-genesis-provasi.md` | Genesis Provası: Kendini Geliştirmenin Testi | bir sınıfta organ yaşam döngüsünü canlıya alan aşamanın spec'i yazılırken |
| `tohum/13-memory-ve-zincir.md` | Memory Kuralları ve Zincirli Defterler | yeni memory açarken ve her defter yazımında |
| `tohum/14-repoya-baglanma.md` | Repoya Bağlanma | yeni repoda ve property eklerken |
| `tohum/15-dokumantasyon.md` | Dokümantasyon: Tarihli Sayfalar, Üretilmiş Raporlar, Hedefin Kendi Dokümanı | her sayfa yazarken, her döngüde doküman üretilirken ve her K8 işinde |
| `tohum/16-hafiza-modeli.md` | Hafıza Modeli: Sekiz Hafıza, Tek Defter | yeni hafıza türü önerirken ve her defter şeması değişikliğinde |
| `tohum/17-kas-buyutme-sinyalleri.md` | Kas Büyütme Sinyalleri: Hangi Ölçüm Hangi Organı Doğurur | her döngü sonunda, genesis kuyruğu kurulurken |
| `tohum/18-politika-ve-dinamik-esikler.md` | Politika Dosyası ve Dinamik Eşikler | her kapı kararında, her aşama spec'i dondurulurken ve her eşik değişikliği önerisinde |
| `tohum/18a-politika-baslangic-degerleri.md` | Politika Başlangıç Değerleri: Anayasal Bölüm | kurulumda `policy.json` yazılırken ve bir eşiğin ilk değeri aranırken |
| `tohum/18b-politika-performans-degerleri.md` | Politika Başlangıç Değerleri: Performans Bölümü | etkinleştirmede performans bölümü yazılırken ve bir eşiğin ilk değeri aranırken |
| `tohum/19-olcum-istatistigi.md` | Ölçüm İstatistiği: PASS Ne Zaman Anlamlıdır | her çıkış testi tasarlanırken ve her verdict okunurken |
| `tohum/20-metrikler.md` | Metrikler: Bir Bakım Sistemi Neyi Sayar | `status.md` üretilirken ve her Gözcü değerlendirmesinde |
| `tohum/21-cok-repo.md` | Çok Repo: Bağlanma Modu, Ne Taşınır, Ne Taşınmaz | beyin yeni bir repoya bağlanırken |
| `tohum/21a-kuresel-bilgi-ve-terfi.md` | Küresel Bilgi: Bağlam, Koşul, Sentez ve Terfi | ikinci repo bağlanınca, ithal bilgi kullanılırken ve bir bilgi ya da organ terfi edilirken |
| `tohum/22-dersler.md` | Dersler: Öğrenme Planlayıcıya ve Implementer'a Akar | plan yaparken, düzeltme yazarken |
| `tohum/22a-ders-provasi.md` | Ders Provası: Öğrenmenin ve Kullanmanın Testi | ders görünümünü, merge'ü ya da çok repolu terfiyi getiren aşamanın spec'i yazılırken |
| `tohum/23-yama-degil-mimari-cozum.md` | Yama Değil, Mimari Çözüm | her düzeltme tasarlanırken ve panel faz 4'te |
| `tohum/24-calisma-modeli.md` | Çalışma Modeli: Beyin, Hakem ve Kurucu Nasıl Koşar | Aşama 0 inşasından önce ve her dispatch değişikliğinde |
| `tohum/24a-kurucu-ve-yerlesim.md` | Çalışma Modeli, Devam: Kurucu Başlatıcısı ve Yerleşim | Kurucu başlatıcısını yazarken, beyin reposunu kurarken ve her yerleşim değişikliğinde |
| `tohum/25-kurulum-gunu.md` | Kurulum, Birinci Bölüm: İnşadan Önce | ilk başlatmadan önce, bir kez; her tohum döneminde satır 10b |
| `tohum/25a-kurulum-etkinlestirme.md` | Kurulum, İkinci Bölüm: Aşama 0 Çıkışında Aktarım ve Etkinleştirme | Aşama 0 çıkışının (A) parçası yeşil olduğunda, bir kez; her parti ve aşama çıkışında satır 1; her yeni hedefte satır 3–7 |
| `tohum/26-semalar.md` | Şemalar ve Kanonik Biçimler: Defter, Bulgu, Vaka, Koşu | Aşama 0 inşasında ve her şema değişikliğinde |
| `tohum/26a-arac-imzalari.md` | Araç İmzaları: Aşama 0 ve 1 | araç yazarken ve çağırırken |
| `tohum/26b-semalar-devam.md` | Şemalar, Devam: Bilgi, Organ, Profil, Politika | Aşama 0 inşasında ve her şema değişikliğinde |
| `tohum/26c-semalar-asama-0.md` | Şemalar, Devam: Aşama 0'ın Dosyaları | Aşama 0 inşasında, kurulumda ve operatör dosyası yazılırken |
| `tohum/27-sozluk-ve-okuyucular.md` | Sözlük ve Okuyucular | yeni terim ya da dosya eklerken |
| `tohum/27a-okuyucular-hedef-durumu.md` | Okuyucular, Devam: Hedefteki Durum Dosyaları | yeni durum dosyası, bölüm ya da görünüm eklerken |
| `tohum/28-dondurma.md` | Dondurma: Ne Durur, Nasıl Kalkar | Gözcü kararlarında ve her dondurmada |
| `tohum/29-tohum-koltuklari.md` | Tohum Koltukları: Rakip, Test-Yazıcı, Şerit Yazarı | kurulumda ve Aşama 0 başında |
| `tohum/29a-tohum-vektorleri.md` | Tohum Vektörleri: Değişmeyen Beklenen Çıktılar | zincir, istatistik ve puanlama kodu yazarken |
| `tohum/29b-onyukleme-hakemi.md` | Önyükleme Hakemi: Aşama 0'ın Yargıcı | kurulumda ve Aşama 0 boyunca |
| `tohum/29c-prova-vektorleri.md` | Prova Vektörleri: Ders Provasının Referans Yargıcı | ders provasının yargıcını (`harness.drill`) yazarken (Aşama 2 partisi) ve ders provası tasarlanırken |
| `tohum/29d-vektor-gruplari.md` | Tohum Vektörleri, Devam: Aşama 0'ın Grupları ve Genel Koşucu | Aşama 0'ın her mikro özelliğini yazarken ve önyükleme hakeminin vektör koşucusu değişirken |
| `tohum/30-guvenlik-katalogu.md` | Güvenlik Kataloğu: İlkeler, Zamanlama, Ortak Kader | her güvenlik işinde, her bildirimde ve yeni bir hedefe bağlanırken |
| `tohum/30a-katalog-erisim-ve-enjeksiyon.md` | Güvenlik Kataloğu I: Erişim, Kimlik, Enjeksiyon, Web | kapsam bu sınıflara dokunduğunda; güvenlik avcısı, Kurucu ve Aşama 5'ten K6 işinde |
| `tohum/30b-katalog-kiracilik-ve-graphql.md` | Güvenlik Kataloğu II: Çok Kiracılık, GraphQL, Kaynak Tüketimi | profil `tenancy.model` `none` değilse ya da hedef GraphQL sunuyorsa; güvenlik avcısı ve K6 işinde |
| `tohum/30c-katalog-bellek-sir-tedarik.md` | Güvenlik Kataloğu III: Bellek, Kripto, Sır, Tedarik Zinciri, Hata İşleme, Ajanlar | kapsam bu sınıflara dokunduğunda; hakemin ve beynin kendi denetiminde her zaman |
| `tohum/30d-hedef-guvenlik-profili.md` | Hedef Güvenlik Profili: Tehdit Modeli ve Kural–Test Bağı | yeni bir hedefe bağlanırken, her güvenlik testi bağlanırken ve her K6 işinde |
| `tohum/30e-guvenlik-defteri.md` | Güvenlik Defteri: Zincirli Kayıt, Yaşam Döngüsü, Öğrenme | her güvenlik bulgusunda, düzeltmesinde, testinde ve feragatinde; yeni bir hedefe bağlanırken |
| `tohum/30f-guvenlik-avcisi.md` | Güvenlik Avcısı: Bağımsız, Salt Okunur, Ölçülen | P2 aktarımında (koltuk), her güvenlik koşusunda ve avcının kanaryası tasarlanırken |
| `tohum/CHANGELOG.md` | Değişiklik Günlüğü — Tohum | bir sayfanın geçmişi aranırken |

## Aşama 0 — Yürüyen İskelet: İlk Canlı Döngü

| Sayfa | Başlık | Okunma |
|---|---|---|
| `asama-0/00-ozet.md` | Aşama 0 — Yürüyen İskelet: İlk Canlı Döngü | aşama başında |
| `asama-0/01-amac.md` | Aşama 0 §0.1 — Amaç | Aşama 0 çalışırken |
| `asama-0/02-dogruluk-ozellikleri.md` | Aşama 0 §0.2 — Doğruluk özellikleri | Aşama 0 çalışırken |
| `asama-0/03-roller.md` | Aşama 0 §0.3 — Roller | Aşama 0 çalışırken |
| `asama-0/04-hata-seti.md` | Aşama 0 §0.4 — Hata seti (P1'e taşındı) | Aşama 0 çalışırken |
| `asama-0/05-property-ve-sinif-etiketleri.md` | Aşama 0 §0.5 — Property ve sınıf etiketleri (P1'e taşındı) | Aşama 0 çalışırken |
| `asama-0/06-snapshot-uretimi.md` | Aşama 0 §0.6 — Snapshot üretimi (P1'e taşındı) ve çalışma ağacı | Aşama 0 çalışırken |
| `asama-0/07-bulgu-ve-kosu-semasi.md` | Aşama 0 §0.7 — Bulgu ve koşu şeması (P1'e taşındı) | Aşama 0 çalışırken |
| `asama-0/08-kabul-kurali-ve-esleme.md` | Aşama 0 §0.8 — Kabul kuralı, K0 eşlemesi, devir sırası | Aşama 0 çalışırken |
| `asama-0/09-harness-in-kendi-testleri.md` | Aşama 0 §0.9 — Hakemin kendi testleri | Aşama 0 çalışırken |
| `asama-0/10-cikis-testi.md` | Aşama 0 §0.10 — Çıkış testi, (A): pinli SHA'da önyükleme hakemi | Aşama 0 çalışırken |
| `asama-0/10a-cikis-canli-dongu.md` | Aşama 0 §0.10a — Çıkış testi, (B): aktarım ve canlı döngü | Aşama 0 çalışırken ve (A) yeşil olduğunda |
| `asama-0/11-yasaklar.md` | Aşama 0 §0.11 — Yasaklar | Aşama 0 çalışırken |
| `asama-0/12-butce.md` | Aşama 0 §0.12 — Bütçe (kaçak freni; değerleri yalnız operatör değiştirir) | Aşama 0 çalışırken |
| `asama-0/13-teslim-listesi.md` | Aşama 0 §0.13 — Teslim listesi | Aşama 0 çalışırken |
| `asama-0/14-sirali-mikro-ozellikler.md` | Aşama 0 §0.14 — Sıralı mikro özellikler | Aşama 0 çalışırken |
| `asama-0/CHANGELOG.md` | Değişiklik Günlüğü — Aşama 0 | bir sayfanın geçmişi aranırken |

## Aşama 1 — İlk Adapter: Lint (K0), Döngü En Basit Hâliyle

| Sayfa | Başlık | Okunma |
|---|---|---|
| `asama-1/00-ozet.md` | Aşama 1 — İlk Adapter: Lint (K0), Döngü En Basit Hâliyle | aşama başında |
| `asama-1/01-amac.md` | Aşama 1 §1.1 — Amaç | Aşama 1 çalışırken |
| `asama-1/02-dogruluk-ozellikleri.md` | Aşama 1 §1.2 — Doğruluk özellikleri | Aşama 1 çalışırken |
| `asama-1/03-girisler.md` | Aşama 1 §1.3 — Girişler | Aşama 1 çalışırken |
| `asama-1/04-roller.md` | Aşama 1 §1.4 — Roller | Aşama 1 çalışırken |
| `asama-1/05-dongu-adim-adim.md` | Aşama 1 §1.5 — Döngü, adım adım | Aşama 1 çalışırken |
| `asama-1/06-sirali-mikro-ozellikler.md` | Aşama 1 §1.6 — Sıralı mikro özellikler | Aşama 1 çalışırken |
| `asama-1/07-harness-olcumu.md` | Aşama 1 §1.7 — Harness ölçümü | Aşama 1 çalışırken |
| `asama-1/08-cikis-testi.md` | Aşama 1 §1.8 — Çıkış testi (hepsi birlikte PASS) | Aşama 1 çalışırken |
| `asama-1/09-yasaklar.md` | Aşama 1 §1.9 — Yasaklar | Aşama 1 çalışırken |
| `asama-1/10-butce.md` | Aşama 1 §1.10 — Bütçe (kaçak freni; değerleri yalnız operatör değiştirir) | Aşama 1 çalışırken |
| `asama-1/11-sonuc-ne-soyler.md` | Aşama 1 §1.11 — Sonuç ne söyler | Aşama 1 çalışırken |
| `asama-1/12-teslim-listesi.md` | Aşama 1 §1.12 — Teslim listesi | Aşama 1 çalışırken |
| `asama-1/13-aktarim-partileri.md` | Aşama 1 §1.13 — Aktarım partileri | Aşama 0 çıkışından sonra, her parti yazılırken ve aktarılırken |
| `asama-1/13a-hata-seti.md` | Aşama 1 §1.13a — P1: Hata seti | P1 partisi yazılırken ve Aşama 1 çalışırken |
| `asama-1/13b-property-ve-sinif-etiketleri.md` | Aşama 1 §1.13b — P1: Property ve sınıf etiketleri | P1 partisi yazılırken ve Aşama 1 çalışırken |
| `asama-1/13c-snapshot-uretimi.md` | Aşama 1 §1.13c — P1: Snapshot üretimi | P1 partisi yazılırken ve Aşama 1 çalışırken |
| `asama-1/13d-bulgu-ve-kosu-semasi.md` | Aşama 1 §1.13d — P1: Bulgu ve koşu şeması | P1 partisi yazılırken ve Aşama 1 çalışırken |
| `asama-1/13e-puanlama-ve-metrikler.md` | Aşama 1 §1.13e — P1: Puanlama ve metrikler | P1 partisi yazılırken ve Aşama 1 çalışırken |
| `asama-1/CHANGELOG.md` | Değişiklik Günlüğü — Aşama 1 | bir sayfanın geçmişi aranırken |

## Aşama 4 — LLM Avcı: Mantık Hataları (K5), Kalıpsız

| Sayfa | Başlık | Okunma |
|---|---|---|
| `asama-4/00-ozet.md` | Aşama 4 — LLM Avcı: Mantık Hataları (K5), Kalıpsız | aşama başında; Aşama 3 PASS alınca yeniden yazılır |
| `asama-4/01-amac.md` | Aşama 4 §4.1 — Amaç | Aşama 4 çalışırken |
| `asama-4/02-dogruluk-ozellikleri.md` | Aşama 4 §4.2 — Doğruluk özellikleri | Aşama 4 çalışırken |
| `asama-4/03-girisler.md` | Aşama 4 §4.3 — Girişler | Aşama 4 çalışırken |
| `asama-4/04-roller.md` | Aşama 4 §4.4 — Roller | Aşama 4 çalışırken |
| `asama-4/05-avci-bildigi-ve-ciktisi.md` | Aşama 4 §4.5 — Avcının bildiği ve çıktısı | Aşama 4 çalışırken |
| `asama-4/06-kosu-protokolu.md` | Aşama 4 §4.6 — Koşu protokolü | Aşama 4 çalışırken |
| `asama-4/07-panel-ve-oracle.md` | Aşama 4 §4.7 — Panel, oracle ve kalıcı düzeltme | Aşama 4 çalışırken |
| `asama-4/08-cikis-birinci-kapi.md` | Aşama 4 §4.8 — Çıkış testi, birinci kapı: isabet | Aşama 4 çalışırken |
| `asama-4/09-cikis-ikinci-kapi.md` | Aşama 4 §4.9 — Çıkış testi, ikinci kapı: maliyet inişi | Aşama 4 çalışırken |
| `asama-4/10-yasaklar.md` | Aşama 4 §4.10 — Yasaklar | Aşama 4 çalışırken |
| `asama-4/11-butce.md` | Aşama 4 §4.11 — Bütçe (başlangıç; yalnız operatör değiştirir) | Aşama 4 çalışırken |
| `asama-4/12-sonuc-ve-teslim.md` | Aşama 4 §4.12 — Sonuç ne söyler ve teslim listesi | Aşama 4 çalışırken |
| `asama-4/13-sirali-mikro-ozellikler.md` | Aşama 4 §4.13 — Sıralı mikro özellikler | Aşama 4 çalışırken |
| `asama-4/CHANGELOG.md` | Değişiklik Günlüğü — Aşama 4 | bir sayfanın geçmişi aranırken |
