# Şemalar, Devam: Döngünün Nöbetçi, Geri Alma ve Prova Satırları

Tarih: 2026-11-01 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0'ın D7 ve D8'ini yazan kod yazılırken
Çapa: beklemede: aşama 0 — hedeflerin `brain/state` defterindeki `sentinel`, `revert`, `commit` ve `plant` satırları

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
Tohumun canlı prova fikstürleri, oyuncağa ekilecek kötü merge'ler, bu tohumda yoktur: `/vec`'in `revert_drill`
kataloğu yalnız vektör içindir, adlandırdığı yamaların baytları hiçbir yerde değildir; içerikleri oyuncağın (A)'da
imzalanan ağacına bağlıdır. Yerleri ve biçimleri bir tohum dönemiyle gelir; o zamana kadar D8 canlı koşamaz ve
(B)'nin #geri-alma'sı ölçülemez.
