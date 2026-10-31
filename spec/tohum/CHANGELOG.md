# Değişiklik Günlüğü — Tohum

Tarih: 2026-10-29 · Sürüm: 2.2
Okunma: bir sayfanın geçmişi aranırken
Çapa: git geçmişi ve zincirdeki spec hash satırları

- 2.2 (2026-10-31, E249; sahibin sorusu, uzman tartışması): `main`'i salt okunur okumak dokunmak değildir; taban yaşının
  commit sayısı ve eskimiş bulgu oranı senkrondan önce de bu okumayla ölçülür (`07`). `07`'nin andığı eskimiş bulgu oranı
  sinyali `17`'de satırdır: eşik pencerede > %20, doğan şey organ değil Aşama 2'deki senkron izin kararıdır.
- 2.2 (2026-10-30, E301; sahip): hedefin ve sistemin kendi kodunun haritası insan okunur çizim olarak da üretilir, kodla yenilenir (`15` 4).
- 2.2 (2026-10-30, E280, E282, E287, E293, E294, E296, E297): Aşama 0 çıkışının karar verilemeyen koşulları.
  Kurucu defterinde kapatma, emekliliğin defterdeki karşılığı olan yeni kural: hakemin kabul ettiği ama anlam
  kurallarından birini (`part`, `kind`, `supersedes`) bozan satır silinmez, sonraki geçerli satır `supersedes`'iyle
  onun `row_hash`'ini adlandırarak onu kapatır; bayt ve zincir kırığı kapanmaz, kurcalama kanıtıdır; push'un eklediği
  bozuk satır kapatılsa da reddedilir; kapatılmamış anlam kırığı çıkışı kapalı tutar ve Kurucu'nundur; defterin
  içeriği değil yapısı denetlenir (`13`, `26`). Tohumun `control` komutunun döngü arayüzü: çağrı, çıkışlar, `go`,
  her işin bayt bayt ilk adımı ve `wiring` kuralı; kill switch ya da fren işi kırmızı durdurur, `loop_schedule`
  kapalıyken zamanlanmış koşu `paused`; adımın üstünde yalnız kuralın saydığı anahtarlar durur (`services` ve
  `container` ilk adımdan önce başlar) (yeni `29p`; `08`, `00b`). Sahip istisnası: ölçümü aşama başlamadan yapılacak
  bir işe dayanan koşul (bugün yalnız #durustluk) o iş yapılmadıysa adıyla istisna edilir; geçmiş ya da
  `UNMEASURABLE` sayılmaz, sonraki aşamanın çıkışına taşınır, ikinci istisna yoktur, insan dokunuşudur; yanında
  taşıma hedefinin ekiminin taahhüdü yoksa koşulu kaldırmaz (`02`, `26c`, `27`). Aşama 0'ın ilk durumu, durum
  kaybolunca da, kopya hedefin `identifiers`'ı ve `honesty_commitment` olmadan kurulmaz (`25`). 80 satır sınırı için
  2026-10-28 kaydı `CHANGELOG-2.md`'ye taşındı.
- 2.2 (2026-10-30, E246, E247; sahibin kararları): her zaman geri dönüş, kimsenin işi silinmez, veri katmanının beş
  korkuluğu. Y2: sistemin önerdiği her değişikliğin, en başta silmenin, geri dönüş yolu adımdan önce kanıtlanmıştır ve
  hiçbir sistem adımı onu sonradan kapatmaz; istisnası yoktur, sahibin onayı da açmaz. Y3: gerçek veri yok, migration
  yok (aynen), veritabanı şemasını değiştiren kod yok; hedefin verisine yalnız `koş`ta, migration'larından kurulmuş
  gerçek kayıtsız test kopyasında dokunulur ve kopyayı kuran migration koşusu yasağa girmez (E77'nin kararı yasada).
  Y4 sistemin kendisi içindir. Yeni `07a` tek kaynaktır, hedefin kodu, dokümanı ve verisi için: geri dönüşün biçimi
  (kodda merge'ün geri alınması, veride arşiv ve yedek; geri migration geri dönüş değildir); kullanılmıyor olmak ölü
  olmak değildir ve hangi sınıftan gelirse gelsin bir birimi kaldıran değişiklik silmedir; yarım ya da duraklatılmış
  iş (planı ve tasarım dokümanı dahil) silinmez, yalnız bildirilir (kanıt yükü silende); gerçekten aynı işi yapan
  parçalar yürütmeyle kanıtlanıp birleştirilir, kaldırılan kopya için de 1'in kanıtı gerekir; eskimiş artık yalnız
  sahibin onayladığı adayla; emin olunamıyorsa tutulur; sahibin onayı beklenmez (Y8); veriyi yok eden adım sahibin
  onayını, önce arşiv ya da yumuşak silmeyi ve geri yüklemesi denenmiş, saklama süresi sınırsız yedeği taşır. `01`'in
  "ölü kod sıfır"ı, `03` K2, `10`, `15`, `18a` `gross_delete_cap`'in K2 istisnası (kalktı) ve `31e`, `31g`, `31h`'nin
  kaldırmaları `07a`'ya bağlandı. Kapı migration'ları her sınıfta reddeder, veritabanı şemasının türetildiği tanıma
  dokunanı şemanın değişmediğini kanıtlamadıkça (`01b`); veriyi yok eden yol güvenlik yoludur, eklemediği
  gösterilemeyen değişiklik de (`05`); birim silen, veri yolu ya da sözleşme ucu içeren değişiklikte testsiz kenar her
  sınıfta `blocked`, içermediği gösterilemeyen değişiklik içeriyor sayılır, yolun testleri tabanda ve adayda yeşil
  (`05`); sözleşme değişikliği her ucu aynı değişiklikte ve sözleşme testiyle, ayrı dağıtılan tüketiciyi kırmadan,
  kırıcı biçim yalnız sürümle (`23`); yazar mandalı, yazar `31`'in modülü, yeni yazar eklemediği gösterilemeyen aday
  geçmez (`07`). Aşama spec'i tohumla çelişirse tohum geçerlidir (`02`). `00b`, `INDEX`.
- 2.2 (2026-10-30, E260, karar bekliyor: E07 (c)'yi değiştirir): yeniden üreticinin kutbu (`29` "Rakibin kuralları"). Yeniden üretici iki taraflıdır: belirti (`expect_*`) ve onun yerine doğru kodun gösterdiği (`correct_*`); doğru taraf belirtinin bir gözlenenini adlandırır, taraflardan biri ötekinden çıkamaz. Kanıt yalnız yargılandığı başta: belirti kod yüzünden görünür, doğru taraf görünmez. Açık iddianın sonraki baştaki gösterimi gözlemdir; rakip her açık iddiayı yeniden gönderebilir, incelenen başta yargılanır; çıkışta gösterdikleriyle listelenir. Kanıtlanmış kusur belirtisi göründükçe engeller (E08 aynen).
- 2.2 (2026-10-30, kararlar partisi 1): öneri yalnız güvenlik ve hariç yolları genişletebilir (eklenen yol ağaçta olmasa da), başka her farkta ret, birim adaylarının sırası ve eklenen aday dahil (`14`, `01b`); vakaları `29k`'de. Diff'in başa uygulanması `diffguard`'ın değil `gate.check`'in işidir (`29d`, `29k`). `install_scripts_required` elemanı kilit yolu (kök `""` değil) ya da `ad@sürüm`; başka eleman, ör. çıplak ad ya da kilitte olmayan yol, isteği kullanılamaz yapar (`deps.fetch` çıkış 2); vakaları `29g`'de (`26c`). `toolchain` `node@X.Y.Z`; lint yeşili: 0 ya da 1, üç koşuda aynı çıkış ve stdout (`26c`). 80 satır sınırı için `profile` ve `diffguard` arayüzleri yeni `29k`'de; `29f` `secrets` ve `contained`, `29g` `npmlock` ve `recipe` taşır (`29d`, `29h`–`29j`, `00b`).
- 2.2 (2026-10-29, daraltma): `docs/asama-0-daraltma.md` (K1–K5 onaylı; hedefin kendi ajan sistemi kapsam dışı; sistem %100 LLM'lerce kurulur ve işletilir) tohuma işlendi. Önyükleme hakemi Aşama 0'dan sonra da beyin reposunun itme yargıcıdır; hakem kodu aşama ya da parti çıkışında aktarılır, parti çıkışı (A) → aktarım → (B)'nin dar hâlidir (`01a`, `02`, `00`, `09a`). Kilit (A)'da (aşama, donmuş spec hash) çifti, açılışı `stage-open` ile `setup/stage.json`; `spec.lint` gelene kadar `02` listesini tohumun spec denetimi uygular (`02`, `18`). Kurucu defteri ilk oturumdan tohumun aracıyla zincirli; bildirim kanalı `reports/*.json` (`00a`). Gerçek test kuralına modülsüz kırmızı (`04`). `loop.yml` kuralları, koşu başına taze host dizini, birim imajı `@sha256`, servisler sonraki partide (`08`). `units[]`, ajan yapılandırması ve operatörün `excluded_paths`'ı, daraltma reddi (`14`). Beyin reposu yeni ve ayrı; Kurucu başlatıcısı ve yerleşim `24a`'da; hedefe yazım yalnız API ile `refs/heads/brain/**`'a; lisans kapısı yalnız ürüne giren bağımlılıklar için (`24`). Kurulum: üç repoda ruleset, kopya hedef ve aynalama, `targets[]` ve `unit_candidates`, tohum dönemi, dürüstlük ekimi, ilk koşu (`25`); aktarım önyükleme hakemine dokunmaz, `loop.yml`'u koyar, `stage-open` ve kopyanın adımları (`25a`). Araçlara "Gelir" sütunu, `unit.verify`, `target.write`, `activate` (`26a`); Aşama 0 dosyalarının şemaları `26c`'de, `operating{}` `26b`'de; okuyucular `27` ve `27a`'da; `operating{}` sınırları ve `stage_budgets.asama_0` (`18a`). Vektör grupları, veri biçimi ve genel koşucu `29d`'de; `drill` grubu ve ders provası yargıcı Aşama 2 partisinin, istatistik ve eşleme vektörleri P1'in (`29a`, `29c`, `22a`). Güvenlik gözlemi ve avcı koltuğu P2 ile Aşama 1'de (`03`, `26`, `30d`, `30f`). K5 (sahibin düzeltmesi): bütçe kaçak frenidir, kısıt değil; oturum sayısı ve USD ölçüdür, çıkış koşulu değildir ve Kurucu'yu durdurmaz; abonelik penceresine takılmak (429) operatör uyarısı ve kesintidir, ret değildir (`06`, `18`, `18a`, `24`, `25`, `28`). `29` ve `29b`'nin bekleyen düzenlemeleri `docs/asama-0-daraltma-29-29b.md`'dedir.
- 2.2 (2026-10-29): güvenlik birinci sınıf (kayıtta E56 ve E57, operatörün yönü ve onayı). Güvenlik kataloğu: 66 açık sınıfı, her biri için bulma yolu, yürüterek kanıtlayan kapanış testi, CWE ve OWASP karşılığı ve düzeltme yolu; OWASP Top 10:2025 ve 2021, API Security Top 10:2023 ve CWE Top 25:2025 maddelerinin her biri bir sınıfa düşer; çok kiracılık, GraphQL ve kaynak tüketimi ayrı sayfadadır (`30`–`30c`). Zamanlama: bulmak, kanıtlamak, bildirmek ve bekçi testi bağlamak Aşama 1'den; hedefe güvenlik düzeltmesi yalnız K6 canlı olunca; migration, manifest, sır, yapılandırma ve iş akışı hiçbir zaman sistemin işi değildir (`30`, `03`, `05`, `04a` 10, `asama-0/05`). Hedef güvenlik profili ve kural–test bağı (`30d`). Zincirli `security` defter bölümü: yaşam döngüsü, düzeltilmemiş açığın ayrıntısının açık yüzeye çıkmaması, her kapanışın bir dedektör, bir regresyon testi ve bir ders bırakması (`30e`, `13`, `16`, `22`, `21a`); hakemin kendi ilk sekiz satırı `seed/security-ledger.jsonl`'dadır. Bağımsız güvenlik avcısı koltuğu: salt okunur, Kurucu'dan ve rakipten ayrı bağlam, model ve bütçe; yalnız izinli lisanslı tarayıcılar ve katalogla sürülen LLM katmanı; ekilmiş açık provasıyla ölçülür (`30f`, `18`, `18a`, `18b`, `25a` 7, `26` `drill: security`, `26a` `security.*`, `27`, `00b`).
- 2.2 (2026-10-29): eksik kaydının (`docs/eksik-kaydi.md`) onaylanan kararları. İç kullanımda geçit ve API anahtarı yoktur: `llm.call` ve araç kullanan ajan tohum rakibi gibi `çağır`'da `claude` CLI'siyle koşar (`24`, `08`, `06`, `26a`). Rakip defteri görmez; yeniden üretici sözleşmesi, kontrol ağacı, kanıtlanmış kusur ve açık iddia hafızası (`29`); ret hafızası yalnız Kurucu'nun düzeltebildiğini sayar; kesinti ile `request_rejected` ayrıldı; durum yoksa durur, karşılaştır-ve-yaz; kill switch canlı, `stopped`; çıkışta yalnız sağ çıkan artefakt, `spec.lint` ve `gate.lock`; donmuş spec yeniden donmaz; bütçe bitince iş başlamaz (`29b`, `29a`, `28`). Kurulum hash'leri her sonuçta, kurtarma, uyarılar ve `oauth_token_expires` (`25`); açık hakem reposuna yalnız açık hedef.
- 2.2 (2026-10-29): iç kullanımda beyin ve hakem repoları açıktır (operatör kararı; satışta özel olur). Önyükleme
  hakeminde okuyucu App'i yoktur: açık beyin kimliksiz okunur, App yalnız özel hedef gelince kurulur. Standart
  koşucu dakikası açık repoda ücretsizdir; 60 gün etkinlik yoksa zamanlayıcı kapanır (`25`).
- 2.2 (2026-10-28): üçüncü inceleme ve önyükleme hakeminin yazılışı: `CHANGELOG-2.md`.
- 2.1 ve öncesi (2026-10-28): `CHANGELOG-1.md`.
