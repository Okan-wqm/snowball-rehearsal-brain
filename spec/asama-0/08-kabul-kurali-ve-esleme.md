# Aşama 0 §0.8 — Kabul kuralı, K0 eşlemesi, devir sırası

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken
Çapa: beklemede: aşama 0 çıkış raporu

---

**Kabul kuralı (D5).** Bir aday ancak şunların hepsi tutarsa merge olur; her biri bir ret nedenidir ve
`events` satırına yazılır. Parantezdekiler §0.14'ün MF'leridir.

1. Diff `brain/integration` başına uygulanır; yalnız düz dosya; yalnız birimin `inputs`'u içinde; güvenlik
   yolu, hariç yol, ajan yapılandırması, yapılandırma, manifest, kilit dosyası ve `.gitattributes`
   değişmez (7; `tohum/04a`).
2. Diff, defter satırları ve giden prompt `secrets.scan`'den temiz geçer (2).
3. **K0 oracle'ı ayırt eder:** taban ağaçta araç adayın hedef bulgusunu `(rule_id, path, line)` olarak
   verir; aday ağaçta aynı kuralın eşlenmiş satırda ihlali yoktur; araç üç koşuda bayt bayt aynı çıktıyı
   verir (8).
4. Diff hedef bulgunun aracın verdiği `fix` aralığının içindedir; değilse `scope_violation` (8).
5. Mandal: araç başına toplam ihlal artmaz (8).
6. Etkilenen testler: en az bir test koştu ve hepsi yeşil; sıfır test kırmızıdır (`tohum/04`) (8).
   Etki kümesi Aşama 0'da birimin servissiz testlerinin tamamıdır ve `kaba` işaretlidir (`tohum/05`).
7. Kırmızı kontroller kırmızı (`tohum/08`); `control.json` `merge_paused` yanlış (8).
8. Nöbetçisi bitmemiş başka merge yok (`tohum/07`) (8).

**Eşlenmiş satır.** Taban ağaçtaki satır `L` adayın hunk'larıyla kaydırılır: `L` hiçbir hunk'ın taban
aralığında değilse eşlenmiş satır `L` artı `L`'den önce biten her hunk'ın eklenen eksi silinen satır
sayısıdır; `L` bir hunk'ın taban aralığındaysa eşlenmiş satır o hunk'ın aday tarafındaki aralığın
tamamıdır. Kural `(rule_id, eşlenmiş satır)`'a bakar; satır kayması yeni ihlal sayılmaz. Tanım
tohumun `k0map` vektörleriyle sabittir (`tohum/29d`); P1'in hunk eşlemesi aynı kuralı kullanır
(`asama-1/13e`).

**Kapsama kaydı.** `hunk_covered` (`true`, `false`, `unmeasured` ve nedeni) her birleşen hunk için
yazılır; Aşama 0'da kapılamaz ve varsayılanı hiçbir zaman `true` değildir.

**Devir sırası.** (B)'de operatör her devri elle tetikler; zamanlayıcı kapalıdır.

| # | Hedef | Ne olur | Kanıtladığı (MF) |
|---|---|---|---|
| 1 | oyuncak | genesis, `brain/integration` kesimi, gözlem: araç çıktısı ve `fix` aralıkları `events`'e | 18, 4, 6 |
| 2 | oyuncak | hazır iyi aday merge olur; dört hazır kötü aday kendi nedeniyle reddedilir: aralık dışı, mandal artışı, test kıran, yasak yol | 7, 8, 9, 10 |
| 3 | oyuncak | nöbetçi yeşil | 12 |
| 4 | oyuncak | geri alma provası, üç `cause` kategorisi (§0.10a #geri-alma) | 13, 14 |
| 5 | — | `llm.call` kanaryası: gerçek CLI, gerçek tavan; ekilmiş sırlı prompt gönderilmez | 15, 2 |
| 6 | kopya | genesis `targets[].base_sha`'da; tarif doğrulaması; gözlem | 18, 6, 5 |
| 7 | — | Kurucu yalnız `candidates/<kopya>/`'yı değiştiren bir push yapar: yayımlanan bir `fix`'i aynen uygulayan iyi aday ve bir birim testini kıran kötü aday; önyükleme hakemi kod isteği gibi yargılar, `referee/` ağacı değişmemiş olmalı | itme yolu |
| 8 | kopya | iyi aday merge, kötü aday ret, nöbetçi yeşil | 7–12 |
| 9 | oyuncak | PASS satırı | §0.10a |

Kurucu adayı hedef kodunu koşturarak değil, hakemin yayımladığı araç çıktısından yazar: hedefin lint
yapılandırması koddur ve yalnız `koş`ta koşar. Oyuncak hedef Kurucu'nun kendi fikstürüdür; adaylarını
(A)'dan önce hazırlayabilir, yanlış çıkarsa adım 7'deki gibi yalnız aday push'uyla düzeltir, (A)
tekrarlanmaz. Kopyaya geçiş ayrı bir aşama ya da aktarım değildir: oyuncağın 1–5'i yeşil olunca aynı
aktarılmış hakem ikinci hedefte koşar.

**Birim seçimi.** Operatör `setup/summary.json` `targets[]`'ta kopyanın aday birimlerini sırayla adlandırır
(`tohum/25`). Kalın ölçütleri MF4 ve MF6 mekanik olarak doğrular; tutmazsa sıradaki aday denenir:
1. Hariç yol değil, ajan yapılandırması altında değil; küçük, iyi test edilmiş bir alan birimi.
2. **Servissiz test kümesi var:** testlerin veritabanı ya da kuyruk istemeyen alt kümesi depodaki
   adlandırmayla ayrılır. Servis isteyen birim `services[]` partisini bekler.
3. **Araç zinciri ve kilit pinli:** dil sürümü dosyası ve `integrity`'li kilit.
4. **Lint aracı kural kimliği, satır ve makinece uygulanabilir `fix` verir.**
5. **Birimin kendi lint yapılandırmasıyla, güvenlik yolu dışındaki bir dosyada en az bir düzeltilebilir
   ihlal var;** kural eklenmez, yapılandırma gevşetilmez (`asama-1/09`).
6. **HEAD'de lint ve servissiz testler 3/3 yeşil, ağsız, `operating{}` sınırlarının içinde** (§0.12).
7. Orijinalde düşük değişim (aynalama çakışması az).
