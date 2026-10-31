# Ders Provası, Gerçek Beyinde: Gizli Havuz, Kalibrasyon, Sınav

Tarih: 2026-10-31 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: ders provası gerçek beyinde koşulmadan önce, aile havuzu yazılırken ve kendini geliştirmenin kanıtı tartışılırken
Çapa: beklemede: aşama 2 — havuz taahhüdü (`pool_sha256`) zincirde ve Rekor'da; `seed/drill/` (`calibrate`, referans yargıç)

---

Sahibin MVP cümlesi "kendini geliştirdiğini kanıtlayan bir organizma"dır. Kanıt dört şey ister: işle
değişmeyen bir ölçüt (cevabı önceden bağlanmış görevler), karşı-olgu (aynı model, öğrendiği olmadan),
veriden önce yazılmış bir karar kuralı ve öğrenciden bağımsız bir yargıç. Canlı pilotta ilk üçü yoktur:
spec, vektörler, rakibin kuralları ve operatörün yardımı yol boyunca değişti. Pilotun sayıları bu yüzden
gözlemdir; karne (`docs/karne.md`, E310) onları dereceleriyle gösterir ve hiçbirine "kanıtlandı" demez.
Kanıtı yalnız gerçek beyinde koşan ders provası (`22a`) verir; karnenin sınav satırı onun imzalı kararını okur.

## Sınav kuralları açık, sorular gizli

Provanın kuralları açıktır (`22a`, `29c`); aileler gizlidir. Tohum bir ailenin adını, içeriğini ya da
dersini hiç söylemez; açık olan yalnız **aile sözleşmesidir**. Bir aile şunları taşır:

- görünür iş ve bağlam dosyaları; bağlam doğru düzeltme için yeterlidir;
- açık gözlemler: `paths`, `class_level`, `property` (dersin kapsamı yalnız bunlarla yazılabilir, `26b`);
- gizli tuzak testleri, koşullar ve doğuş örneği için kapalı kümeden beklenen `cause`;
- yanlış ders ailesinde gözlenebilir bir zararlı koşul; doğru ders ailesinde hakemin ekeceği ilgisiz
  kırmızı testler; plasebo ailesinde dersin ilgisiz olduğu kolay işler.

**Havuz.** Operatör en az üç tuzak ailesi, bir yanlış ders ailesi, bir doğru ders ailesi ve bir plasebo
ailesi yazar; havuz hiçbir açık repoda durmaz. Ekilen dersler (yanlış, doğru, plasebo) operatörün
metnidir ve hiçbiri tuzak ailesine ipucu değildir. Beynin kendi dersi doğuştan doğar; prova ona ders
metni vermez. Bir açık sayfada ya da vektörde adı ya da örneği geçen aile havuza girmez (`22a`'nın
örneği ve `drill` vektörlerinin aileleri de). Ders görünümünü getiren aşamanın (Aşama 2) spec isteğinden
önce `pool_sha256 = sha256(canonical(havuz))` operatörün zincir satırına, Rekor'a ve pilot günlüğüne
yazılır: aile, Kurucu'nun tasarımı ve kodu görüldükten sonra seçilemez. Açılan aile kamuya açılır ve bir
daha kullanılmaz; `UNMEASURABLE` de aileyi harcar.

## Kalibrasyon

Etki sorusu derssiz kolun `k` örnekten en az `min_broken_without`'unda kırılmasını ister (`18a`:
30'da 21). Derssiz kolu %70 kıran bir aile provaların %41'ini yapısı gereği `UNMEASURABLE` yapar,
%85 kıran %1'ini (E319). Bu yüzden her tuzak ailesi havuza girmeden ders okuyabilecek her koltuğun
modeliyle (`03`: Sonnet düzeltici, Opus planlayıcı), derssiz, en az 20 kez koşulur ve en az %85'ini
kırması gerekir: `python -m snowball_drill calibrate <kırık> <koşu>` riski ve kararı verir. Bu kapı gözlenen
oranı gerçek oran gibi okur: 20'de 17 hazırdır, ama aile %95 güvenle ancak en az %66 kırar ve o oranda
provaların %61'i `UNMEASURABLE` olur; gerçekte %70 kıran aile kapıdan %11, %75 kıran %23 olasılıkla geçer,
%85 kıran %35 olasılıkla geri çevrilir. `calibrate` riski bu alt sınırda da verir; kapıyı alt sınıra
bağlamak daha çok kalibrasyon koşusu ister ve açıktır (E319). Ailenin düzeltilebilir olduğu da sınanır:
yalnız operatörün bildiği bir ipucuyla düzeltici çoğunlukla geçer. Kalibrasyon ve ipucu gizli kalır;
Kurucu hiçbirini görmez.

## Ne zaman, kimin üstünde

Aşama 0 çıkışında ders organı yoktur: aşama planında çalışma zamanındaki tek LLM çağrısı kanaryadır, ders
görünümü ve ilk okuyucusu Aşama 2'dedir (`03` aşama tablosu, `22`), ders provası yargıcı `harness.drill`
de Aşama 2 partisiyle, ders görünümünden önce gelir (`asama-1/13`). Prova o an koşulsa sorularının
sınayacağı organı bulamaz; FAIL ya da `UNMEASURABLE` verir. Prova bu yüzden ders görünümünü ve ilk
okuyucusunu getiren aşamayla (`03`: Aşama 2) koşar ve sahibin MVP sınavı odur: gerçek beyinde koşan ilk
ders provasının imzalı PASS'ı (E317). Provanın partisi o aşamanın ilk partisidir (`asama-1/13`); Kurucu o
aşamanın spec'inde ders yeteneğini ve sınanacak okuyucuyu ilk sıraya koyar, organlarını kendisi seçer.
Prova daha önceki bir aşamanın çıkışına bağlanmaz: Aşama 1'in tek LLM koltuğu yalnız bir lint aralığına
yazar (`asama-1/01`) ve `22`'nin örnek dersi onun hiçbir kararını değiştiremez; yalnız oyuncakta yaşayan
bir ders organı ise canlı yolda çağıranı olmayan mekanizmadır (Y4; `18`: yetenek gerçek hedefte bir karara
girince getirilmiş sayılır). Organların adı bir çözüm değildir: `22` ve `22a` ders kaydını, görünümü,
dispatcher'ı, `lessons_injected`'ı ve `superseded_at`'i zaten adlandırır; prova adları değil, organların
ölçülen davranışını sınar.

Öğrenen beynin kendi organlarıdır (ders kaydı, görünüm, dispatcher, okuyan koltuk), model `llm.call`
üzerinden gerçek modeldir. Kurucu'nun kendisini öğrenen sayıp defterin bir ön ekiyle "derssiz kol"
kurmak geçersizdir: kapsül beyni bütün geçmişiyle klonlar ve dersler kodda da yaşar (E317).

## PASS neyi gösterir

PASS, ders tesisatının (doğuş, kapsam, verme, geri çekme, kredi, kalıcılık) operatörün oyuncak
ailelerinde araçsız bir modelin başarısını ölçülebilir biçimde artırdığını gösterir. Kurucu'nun kendi
inşasını geliştirdiğini göstermez (`22a`: prova canlı ölçümün yerine geçmez). FAIL orta büyüklükte bir
etkide sık sık "gösterilemedi" demektir (`29q`); `UNMEASURABLE` sonraki aileye geçer.

Hakemin çekilişi, eşit kollar ve denemelerin yargılanması `22c`'dedir.
