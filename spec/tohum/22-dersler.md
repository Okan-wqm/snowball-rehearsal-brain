# Dersler: Öğrenme Planlayıcıya ve Implementer'a Akar

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: plan yaparken, düzeltme yazarken
Çapa: beklemede: aşama 2 — ders görünümü; `run_meta.lessons_injected`; defterdeki `cause` satırları

---

Hafıza, okuyucusu olmadan arşivdir. Dersler aynı hatayı yapmamak içindir: doğruyu yanlıştan
ayırmanın birikmiş hâlidir ve ölçüsü hatadır (Y5, `16`). Derslerin okuyucuları iş yapan
ajanlardır: Aşama 2'den itibaren planlayıcı sıralama, kapsam ve etki tahmini için; düzeltici ve
implementer yaklaşım ve nereye dokunmama için. **Test-yazıcı ve oracle ders okumaz**; oracle'ın
bağımsızlığı derslere bağlı olamaz. Exit koşularında avcı ders almaz.

## Ham satır ilk günden, görünüm okuyucusuyla

Aşama 1'den itibaren her geri almanın ve her unresolved'ın `cause`'u, kapsamı ve sonucu deftere
yazılır; bunlar derslerin ham maddesidir ve hiçbiri kaybolmaz. Ders **görünümü** ve dispatcher'ın
derslerle prompt zenginleştirmesi Aşama 2'nin planlayıcısıyla açılır (Y4). Aşama 1'in düzelticisi
ders okumaz, çünkü o hacimde bir dersin etkisi ölçülemez (`rules.lesson_n_min`) ve ölçülemeyen
organ canlı yolda duramaz (Y5). Görünüm açıldığı gün geçmişin tamamından kurulur.

## Ders nedir

| Alan | Anlamı |
|---|---|
| `claim` | Tek cümle: "Alan adı değişince sözleşmeyi kullanan tüketiciler de incelenir" |
| `evidence_refs` | Dersi doğuran olayın kanıtı |
| `scope` | Hangi koşulda geçerli: sınıf, property, dosya kalıbı, koşullar (`21a`) |
| `origin_event`, `origin` | Zincirdeki olay satırı; kaynak: `repo_pattern`, `llm_prior`, `synthesis`, `own_outcome` |
| `hit`, `miss`, `withheld_hit`, `withheld_miss` | Verildiği ve saklandığı işlerin hayatta kalma ve geri alınma sayıları |
| `superseded_at` | Bugünün testi çürüttüyse, kanıtıyla |
| `derived_from` | Yeniden doğan dersin eski sürümü |

Şema `26b`'dedir. Ders ipucu olarak verilir, kanıt olarak değil (Y1). Hiçbir ders bir oracle'ı
geçersiz kılamaz.

## Yanlış ders silinmez

Bugün yanlış olan yarın doğru olabilir; o kısım ajanlara ve testlere kalmıştır. Sistem her gün o
gün için doğru olanı yapar ve bunu şöyle sağlar:

- Dersle çelişen bugünün testi kazanır; ders `superseded_at` alır, kanıt yazılır, zincirde kalır.
- Dersi kullanan iş geri alınırsa `miss` artar; ders silinmez, sırası düşer.
- Yarın yeniden doğrulanırsa aynı ders yeni sürüm olarak, `derived_from` ile geri gelir.
- Yanlış çıkan ders de bilgidir: hangi koşulda yanlış olduğu `scope.conditions`'a yazılır.

## Kredi ve sıralama

Hangi derslerin hangi koşuya verildiğini ajan değil **dispatcher** yazar (`lessons_injected`).
Sonuç (hayatta kaldı ya da geri alındı) sayaçlara hakem tarafından mekanik olarak işlenir.
Nedensellik için dispatcher **her dersi bağımsız olarak** uygun koşularda rastgele saklar; ders
yalnız verilen ve saklanan kollar arasındaki farkla kredi alır. Kredi, farkın Newcombe alt
sınırıdır (karma skor yöntemi, tek yönlü %90); deterministiktir, hakem yeniden hesaplar (`29c`). Kol
başına `rules.lesson_n_min` koşudan azsa dersin etkisi `UNMEASURABLE`'dır. Okuyucu dersleri ham
isabet oranına göre değil, fark alt sınırına göre sıralanmış ilk N olarak görür; ham isabet taban
oranını ödüllendirirdi. İki pencere boyunca verilmeyen ders arşive iner; farkın üst sınırı sıfırın
altında kalan ders zarar veriyordur ve kanıtıyla `superseded` olur.

## Doğuş

İlk ham ders satırı Aşama 1'de, geri alınan ilk düzeltmenin `cause`'uyla doğar; hayatta kalan
başarılar da satır doğurur. Yapısal dersler sabit şablondan üretilir; serbest metinli dersler
Aşama 2'nin planlayıcısıyla gelir ve her biri kanıt referansı taşır. Aynı `cause` üç kez
tekrarlanınca genesis derslerden bir skill ya da dedektör taslaklar (`17`).

Dersin doğduğu, doğru işe verildiği ve hatayı azalttığı provayla sınanır (`22a`); ders görünümünü
getiren aşama provanın satırlarını çıkış testinde taşır (`18`).
