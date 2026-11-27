# Şemalar, Devam: Organın Çıktısı ve Çalışma-Zamanı Adayının Yeniden Koşusu

Tarih: 2026-11-22 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: P1 MF10–MF12 yazılırken ya da değiştirilirken, bir organın çıktısı ya da bir aday paketi okunurken
Çapa: beklemede: P1 aktarımı — `runner/organ_output.py`, `runner/candidate_rerun.py`, `runner/kos.py`

---

`26j` MF10 ve MF11'in devamı (rapor masası uzlaşısı (2026-11-22), seed-098 ve seed-099; operatör kararı, sahibin
yetkisiyle). Arayüz olgularıdır; kodun nasıl yazılacağı Kurucu'nundur. "Kurulduğu gibi benimsendi" Kurucu'nun
yapımını arayüz yapar (`26j:17`'nin emsali); sayfanın ondan ayrıldığı yerde modül sayfayı izler.

**Organın çıktısı** (seed-098, E723; Kurucu'nun okuması kurulduğu gibi benimsendi, `runner/organ_output.py`).
- Organın çıktısı, kapsanmış koşusunun `/out` altında bıraktığı düzenli dosyalardır, her biri oradaki yoluyla. Giriş
  noktasının stdout'u ve stderr'i çıktı değildir, koşunun kaydıdır (dizin girdisi stdout'un hash'ini tutar); boş dizin,
  dosya kipi ve zamanı da değildir. Giriş noktası çıktısını `koş`'a yalnız `/out`'a dosya bırakarak verir.
- Tek hash bütün çıktıyı kapsar: manifestinki, `{"files": {<yol>: <sha256>}}` (sıralı anahtarlar, boşluksuz, sonda
  satır sonu). Hash organın `koş` dizin girdisindedir; manifestin ve dosyaların baytları sonuçlarda `o/<sha256>`
  altındadır. `yaz` çıktıyı yalnız o hash'le okur: manifestte ya da bir dosyada değişmiş tek bayt bütün çıktıyı
  reddeder ve hiçbir parçası okunmaz.
- Tutma kuralı: çağrılmış bir organın geçerli koşusu, giriş noktasının çıkış kodu ne olursa olsun tutulur (kod girdidedir;
  bir lint aracının 1'i bulgusudur, `26c`). Tutulmuş çıktı saklanmış kanıttır, organın başardığını söylemez; okuyucunun
  sıfırdan farklı bir çıkışın çıktısıyla ne yaptığı o okuyucunun sayfasınındır.
- Geçerli olmayan koşu (kırmızı kontrol yeşil kaldı, ya da bir sınır: `limit_hit:<anahtar>`) hiçbir şey tutmaz. Düzenli
  dosya ya da dizin olmayan bir girdi (bağ, fifo, aygıt) ya da host'un okuyamadığı bir dosya taşıyan çıktı da hiçbir şey
  tutmaz (`output_entry:<tür>`, `output_entry:unreadable`). Her durumda organın girdisi nedeni adlandırır, devir sürer
  (`26k` T2).
- Öneri listesi (`26j:25` "çıktı listesi"): bulgu öneren organın (`lint.discover`, `26a`'nın "bulgu dosyası") listesi
  çıktısının kökündeki `findings.json` dosyasıdır (Kurucu'nun kodunun kullandığı ad). Satır biçimi ilk yazıcısıyla,
  Aşama 1 MF1'i getiren dönemde gelir: P1 hiçbir öneri okumaz, MF8 Aşama 1 MF1'e kadar boş girdiyle koşar (`26j:27-28`).
- `candidates/<id>/package.json` hem tutulmuş bir çıktının bir dosyasıdır (manifestin o anahtarı) hem de `koş`'un
  sonuçlarındaki aynı yoldur; ikincisi birincinin baytlarıdır (aşağıda (1)). seed-098'in "sonuçlardaki o yolda bir dosya
  değil" okuması seed-099'un okumasıyla değişti.

**Çalışma-zamanı adayının yeniden koşusu** (seed-099, E724; (1)–(5) ve (7) kurulduğu gibi benimsendi,
`runner/candidate_rerun.py`, iki sıkılaştırma ve (5)'te bir farkla).
- (1) Teslim. Tutulmuş bir çıktının yolu `candidates/<id>/package.json` olan dosyasını `koş` sonuçlarının aynı yoluna
  yazar; organ sonuçların hiçbir yoluna kendisi yazmaz. Aday kimliği `[A-Za-z0-9][A-Za-z0-9_-]{0,127}`'dir, noktasız
  (sıkılaştırma: kimlik aynı zamanda `brain/c/<id>` dalının adıdır; git `..`'yı, sondaki `.`'yı ve `.lock` sonunu
  reddeder). Başka bir `<id>` `candidate_id_invalid` ile reddedilir, altına bir şey yazılmaz. İki çıktının farklı
  baytlarla taşıdığı bir `<id>` `package_id_twice` ile reddedilir, ikisi de yazılmaz; aynı baytlar iki kez tek pakettir.
  Her ret yalnız o kimliği reddeder.
- (2) `diff` bir JSON dizgisidir; diff o dizginin UTF-8 baytlarıdır ve hazır adayın `diff.patch` baytlarının yerini
  tutar. Sıkılaştırma: UTF-8 biçimi olmayan bir diff (tek başına bir vekil karakter, ikili yama; `26c`: yalnız düz
  dosyalar) Aşama 1'de çalışma-zamanı adayı olamaz. Kapının denetleyip uyguladığı diff, yeniden koşu girdisinin hash'ini
  taşıdığı paketin `diff`'idir; ikinci bir okuma yoktur.
- (3) UTF-8 JSON olmayan, nesne olmayan ya da böyle bir `diff`'i olmayan paket yalnız o aday için `package_unusable` ile
  reddedilir; onun için bir şey koşmaz, devir sürer (`26j:58`, `26k` T2).
- (4) Yeniden koşunun üç kapı dosyası sonuçların `r/<id>/` altındadır (hazır adayınkiler `c/<cid>/` altında olduğu
  gibi). Dizinin `reruns.<id>` girdisi kararını, nedenlerini ve `package_sha256`'yı, koştuğu paket baytlarının
  sha256'sını taşır: bağ budur, bir baytı farklı paketin yeniden koşusu yoktur.
- (5) Çalışma-zamanı adayı kapıya yalnız yeniden koşusu varsa ulaşır: paketi sonuçlarda durur ve `reruns.<id>`'nin
  `package_sha256`'sı ona uyar. Yoksa tam bir neden `yaz`'ın o hedef satırında adlandırılır: `package_missing` ya da
  `rerun_missing`; kararı `verified` olup üç dosyası tam olmayan girdi `rerun_files_missing`. Bunlar kapı nedeni ya da
  `cause` değildir. Fark: kararı `verified` olmayan yeniden koşu "yok" sayılmaz; aday kapıya ulaşır ve girdisinin her
  nedeniyle `kos:<neden>` olarak reddedilir (bugün reddedilmiş girdili bir hazır aday gibi), döngü dersini tutar.
  Modülün `rerun_not_verified` okuması (hiçbir şey vermemek) bundan farklıdır; modül sayfayı izler. Gevşetme değildir:
  iki yol da merge etmez.
- (6) Bir koşunun paket sayısının sınırı ertelendi: Aşama 1 MF5'i (`candidate.publish`; canlı koşuda kapı adayı
  reddetse de `koş` onu kapıdan önce yeniden koşar) getiren dönem, o MF'nin canlı koşusundan önce bandıyla bir
  `operating{}` sayı anahtarı ekler; aşan paketler kimlik başına reddedilir, devir değil. O zamana kadar bir paket onu
  üreten organ koşusunun `operating.output_bytes`'ıyla, bütün yeniden koşular `koş` işinin `operating.kos_wall_s`'iyle
  sınırlıdır (`18a`); ona ulaşmak `limit_hit:kos_wall_s`'dir.
- (7) Yeniden koşu, işin taban koşusunun taban çalışma ağacının taze bir kopyasında koşar; hazır adaylar aynı taban
  koşusunu kullanır (`index.json` `base_run_sha256`). Lint ve test koşuları, kırmızı kontrol dahil, o taban koşusuyla
  karşılaştırılır.
- Vektör: MF10–MF12'nin vektör grubu yoktur (`26e`); seed-098 ve seed-099 için vektör reddedildi, testler 56–58 bağlar.

**Yarım kalmış merge** (rapor masası uzlaşısı (2026-11-24), seed-104; (1) kurulduğu gibi benimsendi, beyin `af708d9`,
bir sıkılaştırmayla; (2) sıkılaştırma). Önceki denemenin bıraktığı `brain/c/<id>` ya da `brain/drill/<devir>` dalını
aynı commit'i aynı tabana indiren sonraki devir kullanır: dal yoksa kesilir; tabandaysa commit'i alır; başı tam olarak
bu commit'se (tek ebeveyni taban, ağacı adayın dosyasının tabanınkinde verdiği ağaç) açık tek PR'ıyla devralınır, PR
yoksa biri açılır. Başka her şey PR açılmadan ve check gönderilmeden `branch_differs` ile reddedilir; ret yalnız o
adayındır, devir sürer (`26k:37-38` T2, `26p:47-48`), devri bitiren bir sert duruş değildir. Duran commit'in mesajı
karşılaştırılmaz (L-AM3, `07`).
- Aday kimliği hedef başına iki genesis arasında tek merge içindir (kimlik aynı zamanda dalın adıdır, `26p:38-39`).
  Defterin o hedefte son genesis'ten beri merge'ünü yazdığı kimliği (`candidate`'inin `decision` merge ve `merge`
  satırı) `yaz` yalnız o kimlik için, kapı devrin merge'ünü seçmeden önce `candidate_id_used` ile reddeder;
  `26p:53-55`'in nedenleri gibi hedef satırında adlandırılır, kapı nedeni ya da `cause` değildir. Merge edilmiş adayın
  dalı silinmez: sonraki genesis'in silmesine kadar durur (`25a:29-33`, insan dokunuşu).
