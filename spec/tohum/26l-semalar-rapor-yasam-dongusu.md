# Şemalar, Devam: Raporların Yaşam Döngüsü

Tarih: 2026-11-22 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: bir rapor yazılırken ya da durumu değiştirilirken, bir tohum döneminden sonraki ilk oturumda ve imzalı sonucun rapor uyarıları okunurken
Çapa: `seed/bootstrap/reports/answers.json`; imzalı sonucun `reports[]`'ı, `reports_open` ve `reports_unconfirmed` uyarıları

---

`26c`'nin `reports/*.json` satırının ve `00a` "Bildirim kanalı"nın devamı (rapor masası uzlaşısı (2026-11-22),
operatör kararı, sahibin yetkisiyle). Arayüz olgularıdır; kodun nasıl yazılacağı Kurucu'nundur.

**Durumlar** (kapalı küme): `open`, `confirmed`, `declined`, `superseded`, `withdrawn`. Hepsini Kurucu
`reports/<id>.json`'a yazar; operatör, teslim adımı, başlatıcı ve hakem `reports/`'a hiçbir şey yazmaz.
- `open`: yazıldı, kapanmadı. Yanıtlanmış ama Kurucu'nun henüz yargılamadığı rapor da `open`'dır.
- `confirmed`: Kurucu teslim edilmiş bir dönemin yanıtını okudu; yanıt raporun yazıldığı hâliyle her maddesini kapatır.
  Yanıt bir kural, bir vektör, açık bir erteleme ya da raporun aleyhine bir karar olabilir.
- `declined`: operatörün reddini kaydeder (dönemin günlük satırı `<id>` → declined).
- `superseded`: eksik kalan ya da tutmayan yanıt için yeni bir rapor açıldı; `superseded_by` yenisinin `id`'sidir.
- `withdrawn`: Kurucu kendi raporunu geri alır; yalnız hiçbir dönem raporu adlandırmadan önce.
`confirmed`, `declined`, `superseded` ve `withdrawn` sondur: durum onlardan çıkmaz. Sonraki bir olgu eski `id`'yi
adlandıran yeni bir rapordur; eski dosya yine `update_*` notu alabilir, yeni bir durum almaz.

**Okuma kapalıdır.** Başka bir değer, olmayan ya da dizgi olmayan `state`, aşağıdaki kanıtı taşımayan `confirmed` ya da
`declined`, operatörün reddi kayıtlı olmayan `declined`, kapanmamış bir `superseded` ve bir dönemin adlandırdığı
`withdrawn` `open` sayılır. Rapor dosya adıyla (`.json`'suz) anılır: `id`'si olmayan ya da dosya adından farklı rapor
`open`'dır. `superseded` yalnız ardılı beyindeyse, ardılın `derived_from`'u bu raporun `id`'siyse, ardıl `withdrawn`
değilse ve `superseded_by` zinciri kendine dönmüyorsa kapanır.

**Operatörün yanıtı.** Dönemin günlük satırıdır ("Yanıtlanan rapor(lar)"), artı önyükleme hakeminin okuduğu tipli
kopyası: tohum verisinde (`seed/bootstrap/reports/answers.json`, hakem reposunda `bootstrap/reports/answers.json`) her
yanıt bir girdi `{id, changelog, kind}`'dir. `changelog` dönemin günlüğüdür (`CHANGELOG-<n>`; aşağıdaki kanıtın `epoch`'u
bir commit'tir, bu değil); `kind` `answered` (raporun her maddesi yanıtlandı ya da açıkça ertelendi), `partial` (bir
kısmı; satır yanıtsız maddeleri adlandırır) ya da `declined`'dır. Bir rapor birden çok girdi alabilir.
Girdiyi yalnız operatör yazar; tek kaynaktır.

**Ne zaman teyit edilir.** Bir girdinin adlandırdığı her rapor, o dönemin tesliminden sonraki ilk oturumda `confirmed`,
`declined` ya da eksik kalan için açılan yeni bir raporla `superseded` olur. Yapım ilerlemesi raporu açık tutmanın
nedeni değildir: teyit yanıtı yargılar, yapımı değil; kuralın kurulduğunu `done_mf`, testler ve defter gösterir.

**Teyidin kanıtı** (`confirmed` ve `declined` için tipli alanlar, serbest metnin yanında):
- `epoch`: okunan dönemin `setup/summary.json` `seed_epochs[]` satırının tam `commit`'i (40 küçük onaltılık);
- `answered_by`: yanıt olarak okunan sayfa başvurularının boş olmayan listesi (en çok 50), her biri `<sayfa>`,
  `<sayfa>:<satır>` ya da `<sayfa>:<satır>-<satır>` (`26k:12-36`, `asama-1/13d:19`);
- `check`: beyin kökünden koşan ve 0 ile çıkan bir komut, en çok 500 karakter;
- `check_kind`: `test` (yanıtı bağlayan bir test koşar) ya da `read` (yalnız sayfaları okur, yanıt henüz kurulmamıştır;
  gevşetme L-AD1).
Hakem bu alanların biçimini okur, komutu koşmaz; komut Kurucu'nun kanıtıdır, herkes yeniden koşabilir. Alanlar
sonradan da eklenebilir; durum değişmez. `update_*` anahtarları ve "Recheck:" notları veridir, kanıt değildir (`00a`).

**Kalanlar ve yanlış yanıtlar.** Bir yanıtın açık bıraktığı ya da yanlış yanıtladığı soru `derived_from: <eski id>`
taşıyan yeni bir rapordur; eski rapor `superseded` olur. Aynı `id` içinde yeniden sorulmaz ve hiçbir rapor büyüyen bir
kalanlar listesiyle `open` tutulmaz.

**İki sayım.** İkisi de imzalı sonucun uyarısıdır, hiçbir zaman ret nedeni değildir:
- `reports_open:<n>`: `open` sayılan ve hiçbir girdinin adlandırmadığı raporlar; operatörün borcu (gevşetme L-AD3:
  sayım önceden yanıtlanmış raporları da sayıyordu, onlar artık aşağıdakindedir);
- `reports_unconfirmed:<n>` (yeni): `open` sayılan ve bir girdinin adlandırdığı ya da taşınan raporlar; Kurucu'nun
  borcu.
Yol sırasıyla ilk 200 raporun ötesindekiler okunmaz ve `reports_open`'a sayılır. İmzalı sonucun `reports[]`'ı değişmez:
`{id, kind, ref, state, sha256}`.

**Eski teyitler** (gevşetme L-AD2). Beyin `6b5966a`'da `confirmed` olan 73 rapor tohum verisinde `(id, sha256)` olarak
taşınır. Baytları değişmeyen taşınan rapor yeni kanıt alanları olmadan kapalı kalır; baytları değişen taşınan rapor
kanıt alanlarını ister, o zamana kadar `reports_unconfirmed`'a sayılır. O commit'ten sonra yeni alanlar olmadan yazılan
bir teyit taşınmaz: kanıt alanları eklenene kadar `reports_unconfirmed`'dadır (bir uyarı). Hiçbir toplu tarama istenmez.
