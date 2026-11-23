# Değişiklik Günlüğü — Tohum, 2.2'nin On Beşinci Kayıtları

Tarih: 2026-11-22 · Sürüm: 2.2
Okunma: bir sayfanın geçmişi aranırken
Çapa: git geçmişi ve zincirdeki spec hash satırları

- 2.2 (2026-11-22, E720–E724; tohum dönemi AG; rapor masası uzlaşısı, sahibin yetkisiyle operatör kararı; başlatıcının
  üç düzeltmesini sahip onayladı). **İlk iş** (`25` 10b; Kurucu'nun dersi f1741). Teslimden itibaren önyükleme hakeminin
  hiçbir denetimi kırmızı olmaz: bu dönem ne bir tablo, ne bir vektör, ne bir zorunlu politika yolu, ne hakemin kodu
  değiştirir; yalnız başlatıcı ve aynası değişir. Kurucu'nun bugünkü işi sürer, sırası `CHANGELOG-14`'ünkidir. Bu dönemin
  yanıtları iki yerde ondan öncedir: MF12 sayılmadan önce MF10 ve MF11'in kurulmuş satırları `26p`'ye uyar (seed-098,
  seed-099; modül sayfayı izler), ve push-reviewer'ın ajanlı beşinci oturumundan önce E692'nin 4. korkuluğu bir koşunun
  maliyetini `26o`'dan okur (seed-097). Raporların teyidi `26l`'nin kuralı olarak kalır, bu listenin bir maddesi değildir.
  Yeni `26o` (`24a` ve `26h` ona işaret eder): oturumun bütün maliyet satırı ve bekleyişi, ajan koşusunun maliyeti, rakip
  kesintisi, haftalık kota. Yeni `26p` (`26j` ona işaret eder): organın çıktısı ve çalışma-zamanı adayının yeniden
  koşusu. Gevşetme yok. Sıkılaştırmalar: aday kimliği noktasızdır (099 (1)); diff UTF-8'dir (099 (2)); geçersiz koşu ve
  bağ ya da özel dosya taşıyan çıktı hiçbir şey tutmaz, hiçbir şey sessizce atlanmaz (098). Modülden farklar: kararı
  `verified` olmayan yeniden koşu kapıda `kos:<neden>` ile reddedilir (099 (5)); aday kimliğinde nokta yok (099 (1)).
  Başlatıcı (E720–E722): maliyet satırı son turun değil bütün oturumun toplamlarını ve model başına CLI'nin tokenlarını,
  `costUSD`'sini ve `costBasis`'ini taşır; bekleyen satır `/work/logs/cost-pending.json`'dadır; `mirror.json`
  `delegation.runs` her ajan koşusunu çağrının `tool_use_id`'siyle, operatörün fiyat tablosundan türetilmiş maliyetle
  verir; rakibin `api_error`'ü kesintidir (`verdict: null`, `evaluated: false`, `unjudged`), oturum açılmaz, hakem
  yoklanır, bekleyiş `pilot-log.md`'de söylenir; haftalık kotanın tarihli açılışı okunur, anahtar dosyasının oturumun başından beri değişmesi
  bekleyişi bitirir. Doğrulama: oturum
  günlüğündeki mesajların `output_tokens`'ı akışın başındaki sayıdır, son sayı değildir (`26o:34-36`).
  Yanıtlanan raporlar; her madde raporun yazıldığı hâliyle, kendi etiketiyle bir satırdır:
  `seed-097-an-agent-runs-cost-is-shown-to-no-session` → `26o:12-49`:
  - "00e:22-24 her ajan koşusunun satırını tokenı ve maliyetiyle bağlar": yanıtlandı (bağ durur; maliyet artık
    okunur, `26o:23-49`);
  - "oturuma Agent çağrısının tokenları ve duvar süresi gösterilir, maliyeti gösterilmez": yanıtlandı (`26o:25-30`);
  - "çalışan oturumun günlüğünde maliyet alanı yok": yanıtlandı, sınırıyla (`26o:12-13`: yalnız bir turun sonundaki
    `result` olayında, birikimli; `26o:46-48`: koşunun maliyeti sonraki oturumdan okunur);
  - "bir modelin token fiyatı hiçbir sayfada yok": yanıtlandı (`26o:37-39`, `delegation.prices`);
  - "başlatıcının maliyet satırı oturum bittikten sonra yazılır ve ajanın değil bütün oturumundur": yanıtlandı
    (`26o:12-22`: bütün oturum ve model başına; bekleyen satır `cost-pending.json`'da; koşu başına kayıt `mirror.json`'da);
  - "`cost_usd_micros` yalnız bir `not_measured` metniyle `null`, `cost_unknown`": yanıtlandı (seçim durur; nedenler
    `26o:40-42`);
  - "sahibin dördüncü koşulu yalnız token ve duvar süresiyle okunur": yanıtlandı (`26o:46-48`: maliyet okunur; nasıl
    tartıldığı Kurucu'nun, E692'nin 4. korkuluğu);
  - soru (bir oturumun ya da sonrakinin bir ajan koşusunun maliyetini okuyabileceği tek yer): yanıtlandı (`26o:23-30`);
  - "örneğin başlatıcının maliyet satırında Agent çağrısının kimliğiyle ajan başına maliyet": reddedildi o yer için
    (satır oturum başınadır ve kabul edilmemiş işin arkasında bekleyebilir); aynı kimlikle `mirror.json`'da (`26o:25`);
  - "ya da `/work/logs/policy.json`'da token fiyatları": reddedildi (`policy.json` operatörün sınırlarıdır; fiyatlar
    `seed/founder/prices.json`'dadır, `26o:37-39`);
  - "olduğunda koşu satırları ölçülen değerle düzeltilir (`agent_run`'ın `amends`'i)": yanıtlandı (`26o:46-48`: satır
    `mirror.json`'u, damgayı ve `tool_use_id`'yi adlandırır; düzeltmenin biçimi Kurucu'nun);
  - operatörün maddesi (raporda yok): rakibin `api_error:http_429`'u: yanıtlandı (`26o:50-64`, E721).
  `seed-098-the-form-of-an-organs-output-is-on-no-page` → `26p:13-34`:
  - (a) çıktı ne (stdout, `/out`'taki dosyalar ya da ikisi): yanıtlandı (`26p:14-16`);
  - (b) çıktı listesinin dosya adı ya da biçimi: ad yanıtlandı (`26p:28-30`, `findings.json`); satır biçimi ertelendi:
    Aşama 1 MF1'i getiren döneme (ilk yazıcısı; P1 öneri okumaz);
  - (c) tek hash bütün çıktıyı mı tek dosyayı mı kapsar: yanıtlandı (`26p:17-20`);
  - (d) sonuçlarda nerede durur: yanıtlandı (`26p:17-20`, `o/<sha256>`, dizin girdisi);
  - (e) geçersiz koşunun çıktısı: yanıtlandı (`26p:24-27`, tutulmaz);
  - (f) sıfırdan farklı çıkan giriş noktasının çıktısı: yanıtlandı (`26p:21-23`, geçerliyse tutulur);
  - (g) düzenli dosya olmayan girdi: yanıtlandı (`26p:24-27`, hiçbir şey tutulmaz);
  - (h) giriş noktası çıktısını `koş`'a nasıl verir: yanıtlandı (`26p:14-16`, `/out`'a dosya bırakarak);
  - (i) `candidates/<id>/package.json` sonuçların mı, tutulmuş çıktının mı yolu: yanıtlandı (`26p:31-33`, ikisi de);
  - vektör yok notu: reddedildi (`26p:67`; MF10–MF12'nin vektör grubu yok, testler 56–58 bağlar);
  - Kurucu'nun okuması (yedi cümle): ilk altısı kurulduğu gibi benimsendi (`26p:14-27`); paket cümlesi seed-099'un
    okumasıyla değişti (`26p:31-33`);
  - soru (biçim ve tutma kuralı için bir sayfa cümlesi): yanıtlandı (`26p:13-34`).
  `seed-099-the-rerun-of-a-run-time-candidate-leaves-its-form-and-bounds-unstated` → `26p:35-67`:
  - (1) teslim, aynı `<id>` farklı baytlarla, aday kimliği olmayan `<id>`: yanıtlandı (`26p:37-42`; noktasız kimlik);
  - (2) `diff`'in JSON türü ve kodlaması: yanıtlandı (`26p:43-46`, UTF-8);
  - (3) JSON olmayan ya da `diff`'siz paket: yanıtlandı (`26p:47-48`, `package_unusable`);
  - (4) yeniden koşunun adı ve paket baytlarına bağı: yanıtlandı (`26p:49-51`, `r/<id>/`, `package_sha256`);
  - (5) yeniden koşusuz adayın nedeni, `verified` olmayan yeniden koşu: yanıtlandı (`26p:52-58`; modülden farklı);
  - (6) paket sayısının sınırı: ertelendi: Aşama 1 MF5'i (`candidate.publish`) getiren döneme, o MF'nin canlı koşusundan
    önce (ilk canlı paket orada; o zamana kadarki sınırlar `26p:59-63`);
  - (7) yeniden koşunun tabanı: yanıtlandı (`26p:64-66`, aynı taban koşusu);
  - vektör yok notu: reddedildi (`26p:67`);
  - Kurucu'nun okuması: kurulduğu gibi benimsendi (`26p:37-51`, `26p:64-66`), (5)'teki fark ve sayı sınırı yukarıda;
  - soru (teslim, diff, ad, nedenler, sınır için birer cümle): yanıtlandı (`26p:35-67`).
