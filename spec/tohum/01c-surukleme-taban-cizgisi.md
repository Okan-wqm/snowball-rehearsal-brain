# Kapı Kuralları, Devam: `drift.check`'in Taban Çizgisi

Tarih: 2026-11-20 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: `drift.check` yazılırken ve operatör kurulum özetinin `drift` nesnesini yazarken
Çapa: beklemede: P1 — `drift.check` (`asama-0/09` test 24); hakem reposunun `setup/summary.json` `drift`'i

---

`01b` "Döngü bir işlemdir"in beş maddesi hangi okumayla ve hangi tabana karşı karşılaştırılır (bağımsız inceleme ekibi
kararı, 2026-11-20, seed-080). Arayüz olgularıdır; kodun nasıl yazılacağı Kurucu'nundur.

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
`operator_checked_at` 7 günden eskiyse döngü sert duruşla değil, temiz bir duruşla biter ("operator check stale").

**Taban: `setup/summary.json`'un `drift` nesnesi.** Üst düzeydedir, asla `targets[]`'in içinde değildir. `drift`'siz
bir özet kullanılamaz girdidir ve döngü durur; `drift.check` bugünkü nedenlerine asla geri düşmez. `drift` varken
bugünkü nedenler de denetlenir. Biçim:
- `writer_app_id` (tamsayı);
- `targets.<id>.{rulesets: [kimlik], rules: {<dal>: etkin kural içeriğinin sha256'sı}}`;
- `activity: {operator_logins: [login], not_before: ISO-8601 UTC}`;
- `hashes: {constitutional_sha256, vectors_sha256 (ağaç hash'i), seats_sha256}`;
- `visibility: {<repo>: public|private}`;
- `operator_checked_at: ISO-8601 UTC`.
Taslaktaki `apps[]` (hiçbir okuma onu karşılaştıramaz) ve `referee_workflow_permission` (o denetim operatöründür)
yoktur. Politika anahtarı `constitutional_sha256`'dır: genesis `policy_sha256`'yı bütün dosya için kullanır (`29o`).
**Hash tarifleri** (operatör tabanı bunlarla yazar, döngü aynılarıyla okur; RFC 8785 `canonical`, küçük harf onaltılık, `13`):
- `rules.<dal>`: `GET /repos/{r}/rules/branches/{dal}` dizisinin her öğesi `{type, parameters}`'a indirgenir (`parameters`
  yoksa `{}`), öğeler `canonical(öğe)`'ye göre sıralanır; değer `sha256(canonical(dizi))`'dir;
- `constitutional_sha256`: `sha256(canonical(policy.json["constitutional"]))`;
- `vectors_sha256`, `seats_sha256`: hakem reposundaki `vectors/` ve `seats/`'in ağaç hash'i, `25a` 1'deki hakem kodu
  tarifiyle (`sha256("".join(sorted(f"{sha256(içerik)}  {göreli_yol}
")))`, git arşivi üzerinden).

Önyükleme hakemi `vectors_sha256` ve `seats_sha256`'yı bir başı yargılayan her `pull`'da kendi hash'leriyle
karşılaştırır, farkta durur (`25`); boşta geçen yoklama `pull`'u koşmaz.

**Etkinlik API'si.** `GET /repos/{r}/activity?per_page=100`, süzgeçsiz; `refs/heads/brain/` altındaki ref'ler
yargılanır. Pencere, `drift.activity.not_before` ile önceki döngünün başlangıç satırının `ts`'sinden 10 dakika
öncesinin geç olanından başlar; pencerelerin örtüşmesi sorun değildir. Durma satırı aykırı girdileri adlandırır;
operatör durmayı `not_before`'u ilerleterek kaldırır. İzinli aktörler:
- yazar App'inin botu `brain/*`'a push eder, dal açar ve PR merge eder; dal silemez, force-push yapamaz;
- `operator_logins` yalnız dal siler (`25a` "Başarısızlık");
- `brain/state` ya da `brain/integration`'ı kimse force-push edemez, silemez;
- `null` aktör ya da başka bir login döngüyü durdurur.

**Hedef türü.** `toy` ve `copy` dışındaki tür kullanılamaz girdidir (çıkış 2, hiçbir şey yazılmaz, operatör uyarılır)
ve asla `copy` diye okunmaz; `drift.check` önyükleme hakeminin reddettiği bir türü kabul etmez. Yeni bir tür, madde
4'teki okumasını adlandıran bir tohum sayfasıyla gelir; varsayılanı Actions kapalıdır.
