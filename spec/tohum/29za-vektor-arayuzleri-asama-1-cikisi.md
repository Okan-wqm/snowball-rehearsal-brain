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
