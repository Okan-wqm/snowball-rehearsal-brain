# Prova Vektörleri: Ders Provasının Referans Yargıcı

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: ders provasının yargıcını (`harness.drill`) yazarken (Aşama 2 partisi) ve ders provası tasarlanırken
Çapa: `seed/drill/` (referans yargıç, simüle beyinler, testler); `seed/bootstrap/vectors/drill/`

---

Ders provasının (`22a`) kararını Kurucu'nun yazdığı hakem verir, ama Kurucu kendi yargıcı olamaz
(Y6). Bu yüzden prova yargıcının ne demesi gerektiği tohumla gelir: `seed/drill/` altında standart
kütüphaneyle yazılmış bir referans yargıç, onu sınayan simüle beyinler ve onlardan üretilmiş
vektörler. Kurucu'nun `harness.drill`'i vektörlerde referans yargıçla aynı kararı verir; önyükleme
hakemi bunu, yargıcı getiren Aşama 2 partisinin MF'si bitince her push'ta denetler (`asama-1/13`, `29b`);
Aşama 0'da `drill` grubu sahipsizdir ve koşmaz. Aşama 0'ın geri alma provası (MF14) bu yargıcı
kullanmaz: tek prova türü `revert`'tür, vektörleri `revert_drill` grubundadır (`29d`).

## Yargıcın kuralları

Girdi tek bir prova dosyasıdır: koşudan önce yazılan taahhüt, koşudan sonra açılan cevap anahtarı,
hakemin kaydettiği döküm ve parametreler (`gate_rules.lesson_drill`, `18a`). Aile, koşul ve sonuç
yalnız cevap anahtarından ve hakemin kayıtlarından okunur; beynin kendisi hakkında söylediği okunmaz.

| Soru | PASS | UNMEASURABLE |
|---|---|---|
| Taahhüt | `sha256(canonical(anahtar))` taahhüde eşit; değilse her soru FAIL | — |
| Doğuş | Ailenin örneğine tohumlanmış kötü merge geri alınmış; `cause` anahtardakiyle aynı; dersin `origin_event`'i o `cause` satırı; `scope.family` aile | — |
| Kullanım | Ailedeki planlayıcı ve düzelticiye ders verilmiş, başka aileye verilmemiş; test-yazıcı ve oracle hiç ders almamış; anahtarda olmayan örnek FAIL | Olumlu ya da olumsuz örnek yok |
| Etki | Ailedeki k ayrı örnekte (bir örnek iki kez kaydedilmişse FAIL) uyuşmaz çift ≥ 8, çoğu dersten yana, tam tek yönlü McNemar p < α | k'dan az örnek ya da derssiz kol k'nın %70'inden azında kırılmış |
| Yanlış ders | Zararlı koşulda ders verilip örneğin kendi tuzak testi kırılınca ders o anda geri çekilmiş (`superseded` ya da koşul dışlanmış, ders kaydında) ve sonraki zararlı örneklere verilmemiş; "sonra" dosya sırası değil `seq` | Çelişki yok ya da ondan sonra zararlı örnek yok |
| Plasebo | Kredi, verilen ve saklanan kolların farkının Newcombe alt sınırıdır (tek yönlü %90); beynin bildirdiği kredi hakeminkine ±0,0001 içinde eşit; sıralama krediyi izler; plasebonun kredisi %99 düzeyinde sıfırı geçmez | Bir kol 8'den küçük |
| Kalıcılık | Defterden yeniden kurulan görünüm bayt bayt aynı; yeniden başlatmadan sonra aileye aynı ders aynı hash'le veriliyor; boş hash kanıt değildir | — |

Bir FAIL provayı FAIL yapar; FAIL yoksa ve bir soru ölçülemezse prova UNMEASURABLE'dır ve aile
değiştirilir; yalnız yedi PASS provayı PASS yapar. Plasebonun sıkı düzeyi şundandır: %90'da
gerçekten ilgisiz bir ders de on provada bir sıfırı şans eseri geçer ve öğreneni haksız düşürür.

## Arayüz ve vektörler

`python -m harness.drill judge <dosya>` → stdout'ta tek satır JSON `{"drill": ..., "verdicts":
{commitment, birth, use, effect, wrong_lesson, placebo, persistence}}`. Vektörler öğrenen beynin bir
provası, 14 kusurlu beynin birer provası ve bunlardan koşudan sonra düzenlenmiş dört provadır
(değiştirilmiş girdi, ikinci tablo). Beklenen kararlar `vectors.json`'un `drill` grubundadır;
`python -m snowball_drill vectors` onları yeniden üretir ve tohum testleri dosyaların simülasyondan
aynen çıktığını denetler.

| Simüle beyin | Kusuru | Yakalayan soru |
|---|---|---|
| `learner` | yok | — (PASS) |
| `wrong_cause`, `unbound_lesson`, `unscoped` | Neden yanlış; ders olaya bağlı değil; kapsamsız ders | Doğuş |
| `no_injection`, `leaky` | Ders verilmiyor; başka aileye ve oracle'a sızıyor | Kullanım |
| `ignores_lessons`, `shortcut` | Ders alınıyor ama kullanılmıyor; aile koda gömülü | Etki (FAIL; UNMEASURABLE) |
| `stubborn`, `unrecorded_withdrawal`, `stale_dispatcher` | Yanlış ders geri çekilmiyor; çekiliyor ama yazılmıyor; dağıtıcı eski durumu okuyor | Yanlış ders |
| `raw_rate_ranker`, `rank_ignores_credit` | Kredi ham isabet oranı; sıralama krediyi izlemiyor | Plasebo |
| `amnesic`, `lossy_ledger` | Ders yalnız bellekte; deftere eksik yazılıyor | Kalıcılık |

Düzenlenmiş provalar hiçbir simüle beynin ulaşmadığı kuralları Kurucu'nun yargıcına bağlar: kuralı
atlayan yargıç bunlarda başka karar verir.

| Düzenlenmiş prova | Düzenleme | Beklenen |
|---|---|---|
| `tampered_key` | Öğrenenin cevap anahtarı koşudan sonra değişmiş | Her soru FAIL |
| `reused_instances` | Öğrenenin doğuşu plasebo ailesinden bir örnek; etki ilk 10 örneği ikişer kez sayıyor | Doğuş ve etki FAIL |
| `missing_evidence` | Öğrenenin kullanımında başka aile yok; görünüm hash'leri boş | Kullanım UNMEASURABLE, kalıcılık FAIL |
| `stubborn_reversed` | `stubborn`'un yanlış ders kayıtları ters sırada | `stubborn`'unkiyle aynı: yanlış ders FAIL |

## Ölçülen ayırma gücü

Her beyin 500 bağımsız provada koştu: öğrenen 498'inde PASS, 2'sinde UNMEASURABLE aldı, hiç FAIL
almadı; 14 kusurlu beynin hiçbiri bir kez bile PASS almadı. Referans yargıcı birer satırla bozan 37
mutantın hepsini tohum testleri yakalar (`seed/drill/local/mutate_drill.py`).

Güç etkinin büyüklüğüne bağlıdır (k = 20, 1.000 prova; dersle / derssiz başarı → PASS, FAIL):
0,9/0,1 → %99,7, %0; 0,7/0,1 → %98,9, %0,8; 0,7/0,3 → %57,9, %2,7 (kalan ölçülemez); 0,5/0,3 →
%32, %28,7. Bu yüzden tuzak ailesi, derssiz düzelticiyi en az %70 kıracak biçimde seçilir; zayıf
aile FAIL değil UNMEASURABLE üretir ve değiştirilir. Zayıf ders ise FAIL alabilir: prova, güçlü bir
tuzakta hatayı ölçülebilir biçimde azaltan ders bekler (Y5).

**Sınır.** Simüle beyinler gerçek beyin değildir ve olasılıklar dünyaya dair varsayımdır. Bu sayfa
yargıcın öğreneni öğrenmeyenden ayırdığını gösterir. Gerçek beynin öğrendiğini ve kullandığını,
prova gerçek beyinle koşunca gösterecektir.
