# Değişiklik Günlüğü — Tohum, 2.2'nin Yirmi Birinci Kayıtları

Tarih: 2026-11-24 · Sürüm: 2.2
Okunma: bir sayfanın geçmişi aranırken
Çapa: git geçmişi ve zincirdeki spec hash satırları

- 2.2 (2026-11-24, E745–E750; tohum dönemi AM; seed-103 ve seed-104'e rapor masası uzlaşısı (Opus ve Sonnet paneli,
  madde satırları birleşik; operatör kararı, sahibin yetkisiyle) ve sahibin ipucu E750). **İlk iş** (`25` 10b).
  Teslimden itibaren önyükleme hakeminin hiçbir denetimi kırmızı olmaz: bu dönem ne bir tablo, ne bir vektör, ne bir
  zorunlu politika yolu, ne hakemin kodu değiştirir; yalnız sayfalar değişir. Kurucu'nun bugünkü işi sürer, sırası
  `CHANGELOG-14`'ünkidir. Yarım kalmış dalların devralınması (beyin `2e5d6ab`, `f02cb97`, `af708d9`) kurulduğu gibi
  benimsendi. Yeni iş üç sıkılaştırmadır: `branch_differs` yalnız o adayın reddidir (devir sürer), `candidate_id_used`
  ve `pull_closed`; ayrıca başarısız yazımın `yaz` satırındaki adı `hard_stop` değildir (`28` sonu). Raporların teyidi
  `26l`'nin kuralı olarak kalır, bu listenin bir maddesi değildir. Sahibin ipucu (bu kez kural esnetildi; görev, reçete
  değil; `00g:66-80`): canlı döngünün sağlığı önce gelir; kurulmuş düzeltmeleri canlı döngüye taşıyan yolu Kurucu seçer
  (sayfaların yolu P1'in çıkış isteğidir) ve `session_end` satırında önündekini söyler; gevşetme ve yeni hakem kuralı
  yok. Bu öncelik `CHANGELOG-14`'ün iş sırasıyla çelişmez: o sıra P1'in çıkış isteğiyle biter (`CHANGELOG-14:10`);
  aktarılmış kodu Kurucu değiştirmez (`01a:60-61`). **Gevşetme L-AM1** (sahibe bildirilir; `28:51-60`): hedefe başarısız
  bir GitHub yazımı `28`'in sert duruşu değil, bir kesintidir, operatör adımı istemez. **Gevşetme L-AM2** (sahibe
  bildirilir; `07:78-79`, `01b:78`): yazarın korumasına iki okuma yolu: `GET commits/<sha>/pulls` (kurulmuş, `f02cb97`)
  ve kapalı PR'ların okuması (yeni); yazma, merge ve ref kuralı değişmez. **Gevşetme L-AM3** (sahibe bildirilir;
  `07:79-80`, `26p:75`): yazarın bu devirde yapmadığı duran commit, ağacı ve ebeveynleri tam olarak işinki ise
  devralınır; mesajı ve yazarı karşılaştırılmaz. Başka gevşetme yok.
  Yanıtlanan raporlar; her madde raporun yazıldığı hâliyle, kendi etiketiyle bir satırdır:
  `seed-103-a-revert-that-ended-before-its-merge-has-no-rule-for-the-next-cycle-and-no-field-that-shows-it` →
  `07:66-80`, `28:51-60`, `26f:80`:
  - (1) önceki devrin başlayıp bitiremediği geri alma: yanıtlandı, kurulduğu gibi benimsendi (`07:66-80`): dal
    `brain/revert/<merge_sha>` yalnız başı tam olarak geri alma commit'iyse (ilk ebeveynin ağacı, tek ebeveyni merge;
    `29i:20-23`, `asama-0/09` test 25) açık tek PR'ıyla devralınır, PR yoksa biri açılır; başka her şey
    `revert_branch_differs`, hiçbir şey yazılmaz, kırmızı merge kalır ve ondan sonra merge yok (`26f:20-22`); mesaj ve
    yazar karşılaştırılmaz, satırın `cause`'u bu devrin `gate.revert` kararıdır (`29j:53-58`); check ve sabitlenmiş
    merge her denemede (`07:45-48`); geciken geri alma yine geri almadır (`07:49-51`); geri almanın kapatılmış PR'ı onu
    bitirmez, aynı daldan yenisi açılır; nöbetçi kararı geri alma olmayan devir duran geri almaya yazmaz (`26f:12-15`);
    `29i:20-23`'ün `revert` komutu ve vektörleri değişmez, devralma çağıranındır;
  - (1, başka kural) deneme başına yeni dal adı: reddedildi (bir merge bir kez geri alınır: geri almadan sonra
    `onto`'nun başı merge değildir, `29i:21-22`; ad önceki denemeyi bulmayı sağlar, yeni ad önceki PR'ı kapatacak yolu
    olmadan açık bırakırdı); eski ref'i silmek: reddedildi (yazar ref silmez, `25a:33`; silme bir insan dokunuşudur,
    yazara silme hakkı bir gevşetme olurdu);
  - (2) böyle bir devir nerede görünür: yanıtlandı (`07:76-77`, `26f:80`): defterde değil; geri alma satırı `{merge_sha,
    head_sha}` kalır (`26f:17-18`), geri almayı bir kez, merge'ü inince yazar; devralma ve tekrar gönderim `yaz` işinin
    satırında (`reason`, `written`) ve hedefin geçmişindedir (önceki denemenin commit, PR ve check'leri; satırın
    `head_sha`'sı onlara götürür); `yaz`'ı başarısız biten iş `brain/state` commit'i yapmaz (devir başına tek commit, en
    son; `asama-0/01` D6), başlangıç ya da bitiş satırı bırakmaz;
  - (2, alan) bir devirde biten geri almayı üç devirde bitenden ayıran alan: reddedildi (hiçbir sayfa, ölçü ya da yargıç
    onu okumaz; `26f`'nin satır biçimini ve vektörlerini değiştirirdi);
  - (3) `yaz` işinin başarısız GitHub yazımındaki `hard_stop`'u `28`'in sert duruşu mu: yanıtlandı, değil (`28:51-60`):
    tetik kümesi kapalıdır (`28:35-38`, `26i:24-25`), döngü `lift` yazmaz (`26i:26`); `28:19-20`'nin 429'u ve
    `25a:41-46`'nın dış kesintisi gibi bir kesintidir, hiçbir şey tutulmaz; sıkılaştırma (Opus): işin satırı onu
    `hard_stop`'tan ayrı adlandırır (uzlaşı; Sonnet'in okuması yerine); değişmeyen: genesis devrinde `activation`
    (`28:37`), (B)'de yazdıktan sonra kırmızı koşu yeniden tetiklenmez (`25a:44-46`); gevşetme L-AM1;
  - (3, soru) `28`'in duruşuysa nerede tutulur: yanıtlandı, uygulanmaz (duruş değildir, tutulan yok; sonraki devir
    hedefi ve defteri yeniden okur; `13:56-57`'nin `çek` reddi olduğu gibidir);
  - (3, bağımlılık) bu itmenin devralması o okumaya dayanır: teyit edildi (yapımda değişecek bir şey yok);
  - yapım (`target.write` "Standing revert", okuma yolu `GET commits/<sha>/pulls`, 405'in yeniden gönderimi `2e5d6ab`):
    kurulduğu gibi benimsendi; her gönderim aynı sabitlenmiş sha'yı taşır ve PR'ı korumanın kurallarıyla yeniden okur;
    okuma yolu gevşetme L-AM2 olarak adlandırıldı;
  - (bulunan) `01b:54-55` "sonraki devir çökmüş devrin aday dallarını ve kiralarını temizler": yanıtlandı (`01b:79-80`):
    devralma ya da ret, asla silme; kurulumda bitiş satırı ve kira yoktur.
  `seed-104-a-candidate-id-whose-branch-stands-from-an-earlier-merge-has-no-rule` → `26p:69-80`, `01b:75-80`:
  - (1) önceki devrin başlayıp bitiremediği merge (`brain/c/<id>`, `brain/drill/<devir>`): yanıtlandı, kurulduğu gibi
    benimsendi, bir sıkılaştırmayla (`26p:69-75`): dal yoksa kesilir, tabandaysa commit'i alır, başı tam olarak
    commit'se (tek ebeveyni taban, ağacı adayın dosyasının tabandaki ağacı) açık PR'ıyla devralınır ya da PR açılır;
    başka her şey PR ve check'ten önce `branch_differs`; sıkılaştırma (Sonnet): ret yalnız o adayındır, devir sürer
    (`26k:37-38` T2, `26p:47-48`), devri bitiren sert duruş değildir; karşılaştırma ağaç ve ebeveyndir, mesaj değil;
    check ve merge devralınan başa sabitlenir;
  - (2) aday kimliği yeniden kullanılabilir mi: yanıtlandı, sıkılaştırma (`26p:76-80`): hayır; kimlik hedef başına iki
    genesis arasında tek merge içindir;
  - (2, kim ve hangi nedenle) yanıtlandı: defterin merge yazdığı kimliği (`decision` merge ve `merge` satırı) `yaz`
    yalnız o kimlik için, kapı devrin merge'ünü seçmeden önce `candidate_id_used` ile reddeder; `26p:53-55`'in nedenleri
    gibi hedef satırındadır, kapı nedeni ya da `cause` değildir, devir sürer; geri alınmış düzeltme aynı kimlikle
    yeniden merge edilmez, yeniden isteyen yeni bir kimlik kullanır;
  - (2b) merge edilmiş adayın dalını kim, ne zaman siler: reddedildi (silinmez, sonraki genesis'in silmesine kadar
    durur, `25a:29-33`, insan dokunuşu; yazara silme hakkı gevşetme olurdu; yeniden kullanımı defter belirler);
  - (3) birleşmeden kapatılmış PR'ın düzeltmesi ikinci bir PR alır mı: yanıtlandı, sıkılaştırma (`01b:75-80`): hayır,
    bir kişinin kapatması düzeltmeyi bitirir, `pull_closed`, yalnız o kimlik, hiçbir şey yazılmaz (`01b:40-41`); yazar
    PR kapatmaz; geri almanın PR'ı muaftır (Sonnet), kapatılmışı geri almayı bitirmez; kurulumun kapatılmıştan sonraki
    ikinci PR'ı `01b:40-41`'i gevşetiyordu, bu onu kapatır (Opus);
  - (3, okuma yolu) kapalı PR'ları okuyan yol: yanıtlandı, evet, yalnız GET; gevşetme L-AM2 olarak adlandırıldı;
  - soru (her madde için bir cümle): yanıtlandı (her bölüm bir cümleyle açılır);
  - not (hiçbir şey kırmızı değil, adı geçen testler geçer): not edildi (paneller testleri yeniden koşmadı).
