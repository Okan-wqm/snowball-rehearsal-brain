# Prova Vektörleri, Devam: Ayırma Gücü ve Ailelerin Kalibrasyonu

Tarih: 2026-10-31 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: ders provası tasarlanırken, tuzak ailesi havuza alınırken ve bir provanın FAIL ya da UNMEASURABLE'ı okunurken
Çapa: `seed/drill/` (`power.py`: `power_table`, `effect_power`, `calibration`; `tests/test_drill.py`; `local/mutate_drill.py`)

---

`29c`'nin yargıcı öğreneni öğrenmeyenden ayırıyor mu, bir provanın kararı ne kadar güvenilir ve bir
tuzak ailesi provaya ne zaman hazırdır: bu sayfa üçünü de ölçer. Her sayı `seed/drill/`'den yeniden
üretilir (`python -m snowball_drill power 500`, `effect <p_dersli> <p_derssiz> 1000 [deneme]`, `calibrate <kırık> <koşu>`).

## Ayırma gücü

Her beyin 500 bağımsız provada koştu (k = 30, birinci deneme, `α_1` = 0,05): öğrenen 500'ünün hepsinde
PASS aldı, hiç FAIL almadı; 20 kusurlu beynin hiçbiri bir kez bile PASS almadı (`ignores_lessons` 498 FAIL,
2 UNMEASURABLE; `shortcut` 500 UNMEASURABLE; ötekiler 500 FAIL). Referans yargıcı birer satırla bozan 69
mutantın hepsini tohum testleri yakalar (`seed/drill/local/mutate_drill.py`).

## Etkinin büyüklüğüne göre güç

Etki sorusu, 1.000 prova, k = 30, derssiz kol ≥ 21 kırık. `i`'nci deneme `α_i = 0,10 · 2^-i` ile
yargılanır (`22c`, E323); eski sabit 0,10 karşılaştırma için yanındadır. UNMEASURABLE α'ya bağlı değildir,
FAIL kalandır:

| Dersli / derssiz | UNMEASURABLE | PASS, sabit 0,10 | PASS, 1. deneme (0,05) | 2. deneme (0,025) | 3. deneme (0,0125) |
|---|---|---|---|---|---|
| 0,9 / 0,1 | %0,1 | %99,9 | %99,9 | %99,9 | %99,9 |
| 0,7 / 0,1 | %0,1 | %99,9 | %99,9 | %99,6 | %99,3 |
| 0,7 / 0,2 | %6,7 | %93,1 | %92,8 | %91,3 | %88,9 |
| 0,6 / 0,2 | %6,7 | %90,6 | %87,2 | %81,9 | %73,9 |
| 0,7 / 0,3 | %40,3 | %59,5 | %58,8 | %56,5 | %52,8 |
| 0,5 / 0,3 | %40,3 | %41,5 | %31,2 | %21,8 | %15,6 |

Etkisiz bir ders (0,15 / 0,15, kalibre bir aile) 4.000 provada sabit 0,10'da %2,5 PASS alır ve her yeniden
deneme bu şansı yeniden verir (üç denemede ~%7); `α_i` ile birinci denemede %1,3, ikincide %0,6, üçüncüde
%0,2; bütün denemelerin toplam yanılma payı 0,10'u geçmez. Bedeli güçtür: 0,6 / 0,2'de 4.000 provada sabit 0,10
%91,2, birinci deneme %87,9 PASS (500 provada %91,0 ve %87,6).

k = 20'den 30'a çıkmak orta büyüklükteki etkilerde FAIL'ı yarıya ya da dörtte birine indirir (sabit 0,10'da,
0,6 / 0,2 → %12,0'dan %2,7'ye). Güçlü bir tuzakta PASS neredeyse kesindir; orta bir etkide FAIL çoğu kez
"gösterilemedi" demektir, "öğrenmedi" değil. Zayıf ders yine de FAIL alabilir: prova, hatayı ölçülebilir
biçimde azaltan ders bekler (Y5).

## Kalibrasyon

Derssiz kolu az kıran aile ölçmez, harcanır. Derssiz kol örnek başına `p` olasılıkla kırılıyorsa provanın
yapısı gereği UNMEASURABLE olma şansı `P(Binom(30, p) < 21)`'dir: p = 0,70'te %41,1, 0,85'te %1,0.
`gate_rules.lesson_drill` bu yüzden aileyi havuza almadan önce derssiz kolda en az 20 koşu ve en az %85
kırık ister (`22b`, E319); `calibrate` oranı, riski ve kararı (`ready`) verir.

Kapı bir nokta tahminidir, gerçek oranı bilmez. 20 koşuda gerçekte %70 kıran aile %10,7, %75 kıran %22,5
olasılıkla hazır çıkar; %85 kıran %35,2 olasılıkla geri çevrilir (`power.ready_chance`). Bu yüzden
`calibrate` riski oranın tek yönlü %95 Clopper–Pearson alt sınırında da verir: 20'de 17 hazırdır ama alt
sınır 0,66'dır ve orada risk %61'dir; 20'de 20'nin alt sınırı 0,86, riski %0,6'dır. Kapıyı alt sınıra
bağlamak (örneğin alt sınır ≥ 0,80: 20'de 20 ya da 30'da 28) daha çok kalibrasyon koşusu ister; karar
açıktır (E319).

## Sınır

Simüle beyinler gerçek beyin değildir ve olasılıklar dünyaya dair varsayımdır. Bu sayfa yargıcın
öğreneni öğrenmeyenden ayırdığını gösterir. Gerçek beynin öğrendiğini ve kullandığını, prova gerçek
beyinle koşunca gösterecektir (`22b`).
