# İş Boyutu ve Gerçek Test

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: her mikro görevde ve her test yazarken
Çapa: profildeki CI erişilebilirlik denetimi; PR'daki kasıtlı bozma kaydı

---

**İş boyutu kuralı.** Bir aşama, çıkış testiyle ölçülebilecek kadar özellik içerir. İş birimi
mikro görevdir: tek oturumda biter, tek bir şeyi ekler ya da düzeltir, kendi gerçek testiyle
gelir. Her aşama spec'i mikro özelliklerini sırayla listeler; her biri kendi canlı koşusuyla
kapanır ve bir sonraki, öncekinin koşusu yeşilken başlar. Bitmeyen iş "devam ediyor" değil,
yanlış boyutlanmıştır ve bölünür.

**Bir mikro özellik, bir mekanizma.** Bir mikro özellik ve onun PR'ı tek bir mekanizma getirir:
tek bir araç, tek bir kural, tek bir defter bölümü ya da tek bir koltuk. "Dispatcher, kira, geçit
ve model kaydı" bir satır değil dört satırdır. Birden fazla mekanizma taşıyan satır `spec.lint`'te
kırmızıdır; bölünür, kök neden bölünmez (`23`).

**Gerçek test kuralı.** Bir test ancak üç şartı birden sağlıyorsa testtir:

1. **Kasıtlı bozma.** Değişiklik geri alındığında test kırmızıya döner ve bu PR'da gösterilir.
   Geri alındığında yeşil kalan test, test değildir.
2. **Canlı yol.** Test, mekanizmayı üretim kodunun çağırdığı yoldan çalıştırır; yardımcı
   fonksiyonu doğrudan çağırmaz. Yardımcıyı doğrudan çağıran suite, üretim yolu onu hiç
   çağırmasa da yeşil kalır.
3. **Erişilebilir hedef.** Test, CI'da bir şeyin gerçekten çalıştırdığı bir hedefte koşar. Beyin
   bunu her repoda profildeki CI tanımından doğrular; repoda böyle bir denetim yoksa beyin kendi
   erişilebilirlik denetimini `<state_root>` için kurar. Aşama 0'da bu hedef önyükleme hakeminin
   `koş` işidir (`29b`).

Mock yalnız dış dünya için kullanılır: ağ, LLM sağlayıcısı, saat ve GitHub API'si. Organlar
arasındaki dikişler mock'lanmaz; onları aşama çıkışındaki tek canlı koşu test eder. Mock'lu prova
çıkış kanıtı değildir; yalnız canlı koşudan önceki elemedir.

**Sıfır test, kırmızıdır.** Etkilenen bir projede hiç test koşmamışsa sonuç yeşil değil
kırmızıdır; atlanan suite, geçmiş suite sayılmaz. Bu kural kapının içindedir (`gate.check`),
testi yazan ajanın beyanında değil.

**Kırmızı kontrol.** Kod yürüten her hakem koşusu, sonucu bilinen kötü bir adayı da koşturur ve
o aday her koşuda kırmızı çıkmak zorundadır (`08`). Kırmızı kontrolü yeşil çıkan koşu, bütün
sonuçlarıyla birlikte geçersizdir: ölçüm aracı ölçmüyordur.
