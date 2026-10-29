# Oracle Sertleştirme: Test Yanlış Nedenle Yeşile Dönmesin

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: her oracle koşusunda ve test-yazıcı tasarlarken
Çapa: beklemede: aşama 4 — oracle koşu kayıtları

---

Yürütme oracle'ı sistemin son sözüdür; bu yüzden en çok burada oyun aranır. K0–K2 ve K4'te
oracle sınıfın aracının yeniden koşusudur (Y8, `03`); 1–6 ve 11–13 test oracle'ı içindir ve
`oracle.run` ile Aşama 4'te açılır. 7–10 her sınıfta geçerlidir.

1. **Test önce mühürlenir.** Test-yazıcının testi, düzeltici görmeden hash'lenir ve zincire
   yazılır. Test yolları profildeki `test_path_rules`'dur ve satır içi test modüllerini de kapsar.
   Düzeltici test yollarına yazamaz.
2. **Test, property'den ve konumdan yazılır.** Test-yazıcının girdisi property tanımı ve konumdur
   (dosya, sembol, hunk); bulgunun iddiası, avcının gerekçesi ve dersler değildir. Çıktısı
   `{status: test|not_derivable, expected_assertion_message, test_file, must_cover_lines}`'dır.
   Property'den doğru davranış türetilemiyorsa `not_derivable` yazar ve bulgu `unresolved` olur;
   uydurulmuş bir test yazılmaz (`29`).
3. **Kırmızı, beklenen assertion'ın başarısızlığıdır.** Kırmızı ancak test-yazıcının önceden
   yazdığı `expected_assertion_message` ile eşleşen bir assertion başarısızlığıdır. Derlenmeyen
   kod, eksik sembol, import hatası ya da başka bir assertion kırmızı sayılmaz.
4. **3/3 kırmızı, 3/3 yeşil.** Önbellek kapalı, taze konteyner. Üçte biri bile sapıyorsa test
   flaky'dir; bulgu `unresolved` olur.
5. **Hunk kapsaması.** Yeşil koşuda test, düzeltilen hunk'ın satırlarını (`must_cover_lines`)
   gerçekten çalıştırmış olmalıdır; satır kapsaması ölçülür. Projede test koşmuş olması yetmez.
6. **Mutant öldürme.** Test, düzeltilen hunk'ın en az bir mutantını kırmızıya düşürür. Mutantları
   hakemin kendi aracı üretir; hedef repoya bağımlılık eklenmez.
7. **Oracle kapsamı dar, kapı kapsamı geniş.** Oracle koşusu yalnız üreme testini ve hunk'ı
   kapsayan testleri koşar. Profildeki etkilenen-test komutunun tamamını merge anında kapı bir kez
   koşar; sıfır test koşması kırmızıdır (`04`).
8. **Yapısal hedef.** `required_change` bir dizidir (`26`); düzeltici yalnız o dosyalara yazar ve
   `op` sınıfa göre izinli küme içindedir.
9. **Deterministik diff-guard.** Kapı (`gate.diffguard`) reddeder: profildeki dil başına
   `banned_constructs` (bastırma yorumları, tip kaçışları, susturma kalıpları, test atlama),
   `policy.json`'daki yasaklı ifadeler, yapılandırma ve manifest değişikliği, `.gitattributes`,
   tavanın üstünde **brüt** silme ve düz dosya olmayan her şey: sembolik bağ, alt modül, `../`
   içeren ya da çalışma ağacı dışına çıkan yol. Doküman yolları yalnız K8 sınıfında geçer.
10. **Güvenlik yolları.** K6 oracle'ı canlı olana kadar güvenlik yollarına hiçbir yol dokunamaz,
    biçimleyici dahil. K6 canlı olunca yalnız K6 kapısından geçer.
11. **Niyet kanıtı.** Panelde "belgelenmiş niyet" savunması yalnız git blame yazarı beyin ya da
    hakem olmayan bir kaynağa dayanabilir; doküman niyet kanıtı değil, koda karşı doğrulanacak
    bir iddiadır (Y1).
12. **TP penceresi.** Hayatta kalma penceresinde geri alınan TP, geriye dönük FP sayılır.
13. **Oracle geçerliliği ölçülür.** Flake oranı, `not_derivable` oranı ve TP düzeltmelerinin geri
    alınma oranı oracle takımının itibarıdır.

Bu oracle insan etiketinden zayıftır: bir test yanlış şeyi ölçebilir ve yanlış bir iddiayı
doğrulayan bir test de kırmızıdan yeşile döner. Bu şartlar zayıflığı sınırlar, sıfırlamaz;
rapor bunu açıkça yazar.
