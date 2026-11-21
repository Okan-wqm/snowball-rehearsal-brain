# Kapı Kuralları, Devam: `drift.check`'in Taban Çizgisi

Tarih: 2026-11-20 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: `drift.check` yazılırken, operatör kurulum özetinin `drift` nesnesini yazarken ve `policy.json`'a sayı yazılırken
Çapa: beklemede: P1 — `drift.check` (`asama-0/09` test 24); hakem reposunun `setup/summary.json` `drift`'i

---

`01b` "Döngü bir işlemdir"in beş maddesi hangi okumayla ve hangi tabana karşı karşılaştırılır (bağımsız inceleme ekibi
kararı, 2026-11-20, seed-080; okumalar, sayılar ve izinler bağımsız inceleme ekibi kararı (2026-11-21), seed-082).
Arayüz olgularıdır; kodun nasıl yazılacağı Kurucu'nundur.

**Her döngüde, döngünün okuması.**
- Madde 1: her dalın etkin kuralları ve ruleset listesi (kimlikler), tabana karşı. Hash yalnız etkin kural içeriğini
  kapsar; `updated_at`, `_links` ya da kimin okuduğuna bağlı alanlar asla girmez.
- Madde 4: bugün kurulduğu gibi.
- Madde 5, döngünün tuttuğu dosyalar için: anayasal politikanın, vektör ağacının ve koltukların hash'leri, özete
  karşı.
- Madde 2'nin ikinci yarısı: etkinlik API'sinin aktörleri ve yazar App'inin kendi kurulum kapsamı ile izinleri.

**Operatörün dönemsel denetimi**, özette `operator_checked_at` olarak kaydedilir: madde 2'nin ilk yarısı, kurulu öbür
App'ler (kullanıcıya ait bir repoda bunun REST okuması yoktur); madde 3, hakem reposunun iş akışı izni (döngünün
hiçbir kimliğinde `administration` yoktur); `bypass_actors` (`29o`'nun genesis için kabul ettiği gibi).
`operator_checked_at` 7 günden eskiyse döngü sert duruşla değil, temiz bir duruşla biter ("operator check stale"):
hiçbir şey yazılmaz, operatör görünür bir uyarı alır ve iş kırmızı değildir.

**Taban: `setup/summary.json`'un `drift` nesnesi.** Üst düzeydedir, asla `targets[]`'in içinde değildir. `drift`'siz
bir özet kullanılamaz girdidir ve döngü durur; `drift.check` bugünkü nedenlerine asla geri düşmez. `drift` varken
bugünkü nedenler de denetlenir. Biçim:
- `writer_app_id` (tamsayı); `writer_app_permissions` (`GET /app`'in `permissions` nesnesi, olduğu gibi);
- `targets.<id>.{rulesets: [kimlik], rules: {<dal>: etkin kural içeriğinin sha256'sı}}`; `rules` `brain/state`,
  `brain/integration` ve `main`'i adlandırır (öbür dallar da karşılaştırılır), birini adlandırmayan özet kullanılamaz;
- `activity: {operator_logins: [login], not_before: ISO-8601 UTC}`;
- `hashes: {constitutional_sha256, vectors_sha256 (ağaç hash'i), seats_sha256}`;
- `visibility: {<repo>: public|private}`;
- `operator_checked_at: ISO-8601 UTC`.
Zamanlar yalnız `YYYY-MM-DDTHH:MM:SSZ`'dir; başka biçim ve işin saatinden sonraki `operator_checked_at` kullanılamaz.
Taslaktaki `apps[]` (hiçbir okuma onu karşılaştıramaz) ve `referee_workflow_permission` (o denetim operatöründür)
yoktur. Politika anahtarı `constitutional_sha256`'dır: genesis `policy_sha256`'yı bütün dosya için kullanır (`29o`).
**Hash tarifleri** (operatör tabanı bunlarla yazar, döngü aynılarıyla okur; RFC 8785 `canonical`, küçük harf onaltılık, `13`):
- `rules.<dal>`: `GET /repos/{r}/rules/branches/{dal}` dizisinin her öğesi `{type, parameters}`'a indirgenir (`parameters`
  yoksa `{}`), öğeler `canonical(öğe)`'nin UTF-8 baytlarına göre sıralanır; değer `sha256(canonical(dizi))`'dir;
- `constitutional_sha256`: `sha256(canonical(policy.json["constitutional"]))`;
- `vectors_sha256`, `seats_sha256`: hakem reposundaki `vectors/` ve `seats/`'in ağaç hash'i, `25a` 1'deki hakem kodu
  tarifiyle (`sha256("".join(sorted(f"{sha256(içerik)}  {göreli_yol}
")))`, git arşivi üzerinden).

**Politikanın sayıları.** `policy.json` hash'lenen bir dosyadır (`18`, `29o`): `26` "Sayılar" ona da uyar ve hiçbir
yerinde kayan nokta yoktur. Tamsayı olmayan her değer tam altı ondalıklı sabit ondalık dizgidir (`"0.900000"`); sayım,
boyut, tutar ve gün JSON tamsayısıdır. Noktalı ya da üslü bir JSON sayısı dosyanın neresinde olursa olsun geçersizdir:
o yolu okuyan okuyucu `policy_invalid:<yol>` ile reddeder. `constitutional_sha256`'nın tarifi böylece değer taşır.

**Okumalar ve nedenler.** Klasörler hakem reposunun kökündeki operatör dosyalarıdır (aktarım onları `main`'den korur,
`25a` 1), beyinden gelmez. Hash işin checkout'undaki düzenli dosyaların baytları üzerindendir: hakem reposunda
`.gitattributes` yoktur, git arşivi ile checkout aynı blob baytlarını verir; bağ ya da düzenli olmayan dosya reddedilir.
Ruleset listesi `GET /repos/{r}/rulesets?per_page=100`'dür (`includes_parents` varsayılanıyla, her sayfa); kimlikler
tabana küme olarak karşılaştırılır (taban artan, tekrarsız tamsayılardır). `visibility` `GET /repos/{r}`'nin
`visibility` alanıdır; harita her hedefin reposunu adlandırır, özetin adlandırdığı her repo okunur ve karşılaştırılır;
kayıtlıdan başka bir değer (`internal` dahil) farktır. `writer_app_permissions` `GET /app`'in `permissions`'ıyla
eşitlik olarak karşılaştırılır. Nedenler: `constitutional_hash_mismatch`, `vectors_hash_mismatch`, `seats_hash_mismatch`,
`rulesets_changed`, `visibility_changed:<repo>`, `writer_app_permissions_changed`. Aşama 1'de tabanın ve kural hash'inin
vektörü yoktur. Önyükleme hakemi `vectors_sha256` ve `seats_sha256`'yı bir başı yargılayan her `pull`'da kendi
hash'leriyle karşılaştırır, farkta durur (`25`); boşta geçen yoklama `pull`'u koşmaz.

**Etkinlik API'si.** `GET /repos/{r}/activity?per_page=100`, süzgeçsiz; `refs/heads/brain/` altındaki ref'ler
yargılanır. Pencere, `drift.activity.not_before` ile önceki döngünün başlangıç satırının `ts`'sinden 10 dakika
öncesinin geç olanından başlar; başlangıç satırı defterin bu döngününkinden önceki son `events`/`cycle_start`
satırıdır (`29n`), yoksa pencere `not_before`'dan başlar; pencerelerin örtüşmesi sorun değildir. Okuma pencereyi
başından gösteremezse (dolu bir sayfanın en eski girdisi pencerenin başından eski değilse) girdi kullanılamaz. Durma
satırı Gözcü'nün `hard_stop` satırıdır (`26i`) ve aykırı girdileri adlandırır; operatör durmayı `not_before`'u
ilerleterek kaldırır. Yazar App'inin botu `GET /app`'in `slug`'ı ve ardından `[bot]` login'idir. İzinli aktörler:
- yazar App'inin botu `brain/*`'a push eder (`push`), dal açar (`branch_creation`) ve PR merge eder (`pr_merge`); dal
  silemez, force-push yapamaz;
- `operator_logins` yalnız dal siler (`branch_deletion`; `25a` "Başarısızlık");
- `brain/state` ya da `brain/integration`'ı kimse force-push edemez, silemez;
- başka her `activity_type` (`force_push`, `merge_queue_merge` dahil), `null` aktör ya da başka bir login döngüyü durdurur.

**Hedef türü.** `toy` ve `copy` dışındaki tür kullanılamaz girdidir (çıkış 2, hiçbir şey yazılmaz, operatör uyarılır)
ve asla `copy` diye okunmaz; `drift.check` önyükleme hakeminin reddettiği bir türü kabul etmez. Yeni bir tür, madde
4'teki okumasını adlandıran bir tohum sayfasıyla gelir; varsayılanı Actions kapalıdır.
