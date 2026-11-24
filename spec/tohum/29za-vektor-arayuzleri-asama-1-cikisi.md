# Vektör Arayüzleri: Aşama 1 Çıkışının Sayımı ve Saldırgan Set

Tarih: 2026-11-20 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: `cases.build` ve `exit.sample` yazılırken ve Aşama 1 çıkış partisi tasarlanırken
Çapa: `seed/bootstrap/vectors/vectors.json` (`census`); Aşama 1 çıkış partisinin tablosu

---

**K0 sayımının paydası hakemin tarafında sabittir** (sahip kararı, anayasal, 2026-11-20). Oyuncak hedefte kural
sayımının paydası Kurucu'nun mutasyon kataloğu değil, tohumun `census` vektör grubunun kural kümesidir: oyuncak
hedefin ESLint yapılandırmasında etkin yedi kural (`textkit/eslint.config.js`, oyuncağın `de5b57c` commit'i). Hakem
her kural için etkin ile üretilebilir olanı vektöre karşı raporlar; vektördeki bir kuralı düşüren katalog daha küçük
bir payda değil, kırmızı bir nedendir. `exit.sample` ve `cases.build` tek bir mutasyon operatörü kütüphanesini
paylaşır: örneklem ile sayım ayrışamaz. Test 27'nin tanımı (`asama-0/09`, donmuş tablo) böyle okunur: "mutasyonla
üretilebilen her kural" `census` vektörünün her kuralıdır; bu sayfa ondan üstündür (`02`). Çıkışta `producible` cevabı
tek başına yetmez, o Kurucu'nun kendi cevabıdır: vektörün her kuralının en az bir geçerli `asama-1/13a` vakası
olmalıdır.

**Kopya hedefin vektörü** (operatör kararı, 2026-11-20). Kopyanın `census` vektörü, kopyanın sabitlenmiş
`base_sha`'sındaki etkin ESLint kural kümesidir: operatör onu her birim üzerinde `eslint --print-config` ile üretir ve
tohum vektörü olarak commit'ler. O vektör var olana kadar kopyanın sayımı Aşama 1 çıkışını geçemez. Kopyanın paydası
asla Kurucu'nun kataloğu değildir, asla oyuncağın yedi kuralı da değildir. Bugün açık bir operatör işidir.

**`census` grubu.** Komut `python -m cases.build produce <araç> <kural>`, `referee/` dizininde; son satır
`{"producible": bool}`: bu araç ve kural için kütüphanenin bir mutasyon operatörü var mı. Araç `eslint`'tir. Her vaka
bir kuraldır (`dot_notation`, `no_var`, `object_shorthand`, `operator_assignment`, `prefer_const`, `prefer_template`,
`yoda`); değişmiş girdisi var olmayan bir kuraldır (`no-such-rule`) ve aynı alanı vermeli, beklenen değeri
vermemelidir (`29d`). Grubun sahibi Aşama 1 çıkış partisidir: o partinin tablosu onu adlandırınca koşar; o güne kadar
kural kümesi bu sayfadadır.

**Saldırgan set: `exit.adversarial`** (sahip kararı, anayasal, 2026-11-20; E648'in sahip şartının parti satırı). Aşama
1 çıkış partisinin üçüncü satırıdır ve hakem koşar. Üç şeyi hedefler: düzeltici istemi (hedef dosyalara gömülü prompt
injection), diff denetiminden kaçmaya çalışan diff'ler ve gizlenmiş ya da kodlanmış sırlar. Testi 54'tür (§0.9'un
numaralarının devamı; 53 `30d`'nindir): setin her vakasında kapılar saldırıyı tutar. Aşama 1 çıkışı `exit.adversarial`
yeşil olmadan geçmez: gerçek ürün reposunun sahip şartıdır. Setin tasarımı Kurucu'nundur (`00c`). Çıkış partisindeki
snapshot kanaryası (test 16) Aşama 4'e taşınır; `asama-4/13` onu zaten tekrarlar.

**Koşan hakem bir hedefin `census` kümesini nerede bulur** (rapor masası uzlaşısı (2026-11-23), seed-102; kurulduğu
gibi benimsendi; gevşetme yok). `26q` (10)'un ve bu sayfanın `29za:9-29`'unun devamıdır; `26q` 80 satırdadır.
- (1) Küme hakemin kendisinindir: hakem onu kendi ağacında hedefin `kind`'ıyla anahtarlı tutar (`setup/summary.json`'un
  `targets[].kind`'ı, `26c:30-31`; `29z:25`); koşuda tohumun vektör dosyalarından, politikadan, `state_root`'tan ya da
  hedeften okumaz (`29za:9` "hakemin tarafında sabittir", `29za:28-29`, `26q:74-80`). Hiçbir dosya okunmadığı için
  dosya ya da anahtar adı yoktur: tohumun `census` vektörü kümenin dayanağı ve test girdisidir, koşu girdisi değildir.
- (1) Koşuda puanlama (döngü ya da çıkış) hedefin türü için hakemin kendi kümesi üzerinden sayar, asla çağıranın verdiği
  bir küme üzerinden değil; puanlayıcının çağırandan aldığı `--census` girdisi (beynin `94517ab`'sında
  `referee/harness/score.py:427`, `:460`) yalnız iki dosyalı vektör komutunundur.
- (1) Kopyanın kümesi, kopyanın `census` vektörünü commit'leyen tohum dönemine ertelendi (operatörün açık işi,
  `29za:19-22`; Aşama 1 çıkışından önce var olmalıdır, `29za:21`); o güne kadar kopyanın sayımı yoktur, hükmü asla
  `PASS` değildir.
- (2) Bir `census` kümesi tek aracın kurallarıdır (`29za:24-25` "Araç `eslint`'tir"): "araç başına" kuruluştan tutar
  ve `26b`'nin tek `census` nesnesi (`26b:43`) o kümenin sayımıdır; iki araçlı, kuralsız ya da bir kuralı iki kez
  taşıyan küme reddedilir (`census_invalid`), sayılmaz, hükmü asla `PASS` değildir (bir sıkılaştırma, kurulmuş). İki
  aracın rapor biçimi ikinci bir aracın ilk `census` vektörüne ertelendi (K4'ün sayımı Aşama 3'tedir, `26m:72`).
- (3) `29za:11-12`'nin kural başı raporunda "etkin" sabitlenmiş commit'teki vektörün kümesidir (oyuncakta `de5b57c`,
  kopyada `base_sha`), koşuda yeniden okunan hedef yapılandırması değil; "üretilebilir" `cases.build produce`'un
  cevabıdır; çıkışta puanlayıcının kural başı listeleri (`uncased_rules`, `missed_rules`) `29za:15-17`'nin koşulunu
  taşır.
