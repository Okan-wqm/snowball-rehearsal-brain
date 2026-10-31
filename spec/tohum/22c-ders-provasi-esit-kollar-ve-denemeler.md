# Ders Provası, Gerçek Beyinde, Devam: Eşit Kollar ve Denemeler

Tarih: 2026-10-31 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: prova hakemi (`exit.drill`) ve yargıcı (`harness.drill`) yazılırken, bir prova denemesi açılırken ve bir etki kararı okunurken
Çapa: beklemede: aşama 2 — her denemenin anahtar taahhüdü ve açılımı zincirde ve Rekor'da; `seed/drill/` (`judge.py`: `_effect`, `attempt_alpha`)

---

Ders provasının kararı yalnız hakemin kaydettiğini okur (`22a`, `29c`). Bu sayfa, o kayıtlarda etkinin
dersten başka bir şeye yüklenemeyeceği iki kuralı yazar: kolları hakem çeker ve kollar eşit koşar; açılan
her prova bir denemedir ve sonraki deneme daha sıkı yargılanır. Havuz, kalibrasyon, provanın ne zaman
koştuğu ve PASS'ın neyi gösterdiği `22b`'dedir.

## Hakemin çekilişi ve eşit kollar

Plasebo kollarında dersi kimin alacağı hakemin çekilişidir: cevap anahtarındaki `withhold_seed` koşudan önce
taahhüt edilir; örnek `i` için `HMAC-SHA256(withhold_seed, i)`'nin ilk baytının en düşük biti 1 ise ders
saklanır. Dispatcher çekilişe uyar; uymayan kol yargıçta FAIL'dır. Bir dersin iki kolu, plasebonun
kollarında da etkinin her çiftinde de, aynı model, çaba, tur ve bütçe sınırıyla koşar; ayrı koşan kol
yargıçta FAIL'dır (E65). Etki çifti aynı işin iki koşusudur: ders bloğu çıkarılınca iki promptun hash'i de
aynıdır, ayarlar bütün çiftlerde aynıdır, hakem iki koşuyu da kaydeder ve kaydı eksik çift de FAIL'dır
(E321). Böylece bir dispatcher dersi kolay örneklere verip kredisini, dersli kola büyük bütçe ya da fazladan
metin verip etkisini şişiremez.

## Denemeler

Açılan her prova, `UNMEASURABLE` olan da, zincirde bir denemedir ve ailesini harcar (`22b`). Denemenin
sırası `i` cevap anahtarındadır ve anahtarla birlikte koşudan önce taahhüt edilir; etki sorusu
`α_i = 0,10 · 2^-i` ile yargılanır (0,05; 0,025; 0,0125; …), böylece bütün denemeler birlikte 0,10'dan
fazla yanılmaz (E323). Sıra anahtarda yoksa ya da 1'den küçükse etki FAIL'dır. Sabit 0,10'da kalibre bir
ailede (derssiz kol %85 kırık) etkisiz bir ders etki sorusunu provaların %2,5'inde geçerdi ve her yeniden
denemede bu şans yeniden gelirdi (üç denemede ~%7); `α_i` ile birinci denemede %1,3, ikincide %0,6, üçüncüde
%0,2. Bedeli güçtür: orta bir etkide (dersli 0,6, derssiz 0,2) PASS %91,2'den birinci denemede %87,9'a iner
(4.000 prova, `29q`).
