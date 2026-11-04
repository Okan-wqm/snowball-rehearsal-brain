# Şemalar, Devam: Döngünün Nöbetçi, Geri Alma ve Prova Satırları

Tarih: 2026-11-01 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0'ın D7 ve D8'ini ve kopyanın genesis kapısını yazan kod yazılırken
Çapa: beklemede: aşama 0 — hedeflerin `brain/state` defterindeki `sentinel`, `revert`, `commit`, `plant` ve `copy_gate` satırları

---

`26`'nın devamıdır: satır alanları (`row_id`, `part`, `kind`, `payload`, `cause?`, zincir) ve kurallar oradadır; alan
adını yalnız `26`–`26f`, `30d` ve `30e` tanımlar (`26`). Bu sayfa döngünün D7 ve D8 satırlarının yükünü verir.

**Nöbetçinin sonu** (`part: events`, `kind: sentinel`): `payload {merge_sha, verdict: green|flaky, red: [],
flaky: [test kimliği]}`. `verdict`, `red` ve `flaky` MF12'nin (`sentinel.run`, `29j`) kararının alanlarıdır: `green`
ya da `flaky` kararı bu satırla yazılır; `rerun` karar değildir, satır yazılmaz; `red` kararın sonu geri alma
satırıdır (aşağıda), ayrıca `sentinel` satırı yazılmaz. Yazarı nöbetçiyi koşan devrin `yaz`'ıdır (D7, `asama-0/01`).

**Geri alma** (`part: events`, `kind: revert`): üst düzey `cause` (`26`'nın kapalı kümesi, MF13'ün kuralı, `29j`) ve
`payload {merge_sha}`; aynı satır biçimi provanın ektiği merge'ün geri alınmasıdır (`29m`).

**Nöbetçinin bitişi.** Bir merge'ün (`events` `kind: merge` ya da `drill` `kind: plant`) nöbetçisi, sonra gelen ve
`merge_sha`'sı onunki olan ilk `sentinel` satırında ya da ilk `revert` satırında biter. Nöbetçisi bitmemiş merge
varken kapı merge etmez (`asama-0/08` ölçüt 8, `07` "Merge'ler sıralıdır").

**Geri alma provasının satırları** (`part: drill`, `drill: revert`, `29m`): taahhüt `kind: commit`, `payload {drill:
revert, family: revert, commitment_sha256}`; ekme `kind: plant`, `payload {drill: revert, family: revert,
instance_id, merge_sha}`. `26`'nın drill yükünün öbür alanları (`question`, `arm`, `revealed_sha256`, `outcome`,
`verdict`) ders ve bağlam provalarınındır; geri alma provasının yargısı `29m`'nin `judge` çıktısıdır.

**D8'in canlı girdileri.** `exit.drill` `yaz`'da koşar (`26a`); taahhüt uygulamadan önceki bir devrin `yaz`'ındadır
(`asama-0/01` D8). Prova tohumu hakem reposunun sırrıdır (`25` 7): adı `loop.yml`'un adlandırdığıdır ve operatör onu o
adla yazar (`25a`'nın sırları gibi); yalnız `yaz`'ın onu kullanan adımının `env`'indedir (`08` 1). Devirlerin
bölüşümü (hangi devrin taahhüt ettiği, ektiği, izlediği) MF17'nin bileşimidir, Kurucu'nundur (`asama-0/14`).

**Canlı prova fikstürleri** (oyuncağa ekilecek kötü merge'ler; `22a`, `asama-0/01` D8). Hakem reposunun ikinci prova
sırrıdır: adı `loop.yml`'un adlandırdığıdır, operatör onu o adla yazar ve prova tohumu gibi yalnız `yaz`'ın onu kullanan
adımının `env`'indedir; `çek`, `getir`, `koş` ve `çağır` onu hiç taşımaz. Hakem reposunda bir dosya değildir: repo
açıktır (`25` 0) ve `koş` ile `çağır` onu bütünüyle checkout eder. Tohumda, beyinde, `spec/tohum`'da, istemde,
günlükte ya da artefaktta da yazılı değildir; Kurucu'ya bu biçim ve kurallar ulaşır, baytlar hiçbir yoldan ulaşmaz.
Değeri tek satır base64'tür; açılışı RFC 8785 JSON'u `{import_line_sha256, instances: [{id, cause, patch}]}`'dir:
- `import_line_sha256`: kümenin bağlı olduğu aktarım satırının LF'siz baytlarının sha256'sı (`26d`'deki aynı adlı alanın
  kuralı). Sayacın son aktarım satırınınki değilse prova kapalıdır ve nedeni adlanır. Her aktarım yeni bir küme alır;
  kırmızı bir (B)'de yanmış bir küme (ekimleri oyuncağın açık geçmişindedir) yeniden kullanılmaz (`25a` "Başarısızlık").
- `instances` `29m`'nin kataloğudur. `id` tekil, 32 rastgele küçük onaltılık karakterdir ve nedeni anlatmaz: ekme
  satırı onu geri almadan önce açık deftere yazar (yukarıda). `cause` `test_regression`, `build_break` ya da
  `lint_regression`'dır: yama o aktarımın oyuncak ağacında `29j`'nin kural sırasıyla tam bu nedeni verir; her örneğin
  tek bir nedeni vardır ve her nedenin örnek sayısı eşittir (en az bir, `asama-0/10a` #geri-alma).
- `patch` yamanın metnidir (`/vec`'in `revert_drill` kataloğunda aynı ad bir dosya adıdır ve yalnız vektör içindir):
  hazır adayın `diff.patch`'i biçiminde birleşik diff (`26c`), var olan tek bir düzenli dosyayı yerinde değiştirir,
  dosya bir güvenlik yolunda değildir ve diff o aktarımın oyuncak ağacına (`toy_tree_sha256`) kendi satırlarında,
  kaydırmadan uygulanır.

Küme bütün (B) boyunca sabittir: her taahhüdün anahtarı ona bağlıdır (`29m`). Merge'ü beklenen (`expect.json`
`decision: merge`) hiçbir oyuncak adayı bir yamanın değiştirdiği dosyayı değiştirmez. Kural satır başına değil dosya
başınadır: ekim `brain/integration`'ın başına konumuyla uygulanır, merge'ler sıralıdır (`07`) ve geri alınan ekim
dosyayı baytı baytına geri getirir; aynı dosyadaki bir merge satırları kaydırır. Kümeyi operatör, aktarımdan sonra ve
etkinleştirmeden önce (`25a` 7) tohumun `drill-fixtures` komutuyla üretir: komut aktarım satırını ve oyuncak ağacını
okur, her etiketi oyuncağın kendi araçlarıyla kum havuzunda ölçer, bu kuralları tutmayan ya da 48 KB'yi aşan kümeyi
reddeder ve hiçbir yamanın içeriğini basmaz. Kayda kümenin yalnız sha256'sı girer.

**Kopya kapısı satırı** (`part: events`, `kind: copy_gate`; oyuncak defterinde, hakemin kendi satırı, `26d`):
`payload {conditions: [koşul etiketi]}`. Oyuncağın sıradan devrinin `yaz`'ı `asama-0/08` 1–5'in koşullarını oyuncağın
`brain/state`'i üzerinde yargılar; yargı prova tohumunu ve fikstürleri ister, ikisi de yalnız `yaz`'dadır. Kapı açıksa
`yaz` satırı o devrin satırlarına yazar, son genesis'ten sonra bir kez. Sonraki koşunun `çek`'i satırı oyuncağın D1'de
doğrulanmış defterinden okur ve ancak o zaman iki başı da olmayan kopyayı `targets[].base_sha`'da genesis devri olarak
sunar (`29s`). Yük yalnız koşul etiketlerini taşır, prova tohumundan ya da fikstürlerden türeyen hiçbir değeri taşımaz
(defter açıktır); `stage` ile `verdict: "PASS"`'i birlikte taşımaz (`stage-open` PASS satırını bu ikiliyle sayar, `26d`
kural 3). `stage-open` kapı satırını okumaz.
