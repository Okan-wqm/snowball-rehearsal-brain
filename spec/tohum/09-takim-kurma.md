# Takım Kurma Kuralları

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: takım kurarken ve ajan önerirken
Çapa: ajan dosyalarındaki köken alanları; `ledger.jsonl` `part: accept` satırları

---

- **Birim çekişme protokolüdür** (`10`): üretici, Savcı, Savunma, Uygulayıcı temsilcisi ve
  oracle. Kurucu, kendi yazdığı hiçbir artefakt için koltuklardan birine oturamaz.
- **Ajan ancak ölçülmüş boşluk için doğar** (`17`). Öneride boşluğun ölçümü, kapsam, başarının
  hangi sayıyla ölçüleceği ve hedef değer / USD yazar.
- **Ajan ölçülmüş katkısı yoksa emekli olur**; mekanizma ablasyon ve, sınıfta iki aday doğunca,
  itibardır (`11`, `12`).
- **Her ajan koşu başına durumsuzdur.** En az araç, varsayılan salt okunur, yazma yalnız izole
  worktree'de. Kişisel hafıza yoktur (`16`). Araç gerekmiyorsa ajan araçsızdır: Aşama 1
  düzelticisi araçsız tek bir model çağrısıdır; yapılandırılmış düzenlemesini deterministik bir
  uygulayıcı yalnız hedef aralığa yazar.
- **Ajan tanımları üretilmiş artefaktlardır.** Her ajan dosyası hangi boşluk için, hangi
  ölçümle, hangi aşamada doğduğunu ve tanım hash'ini taşır; kökeni belirsiz ajan dosyası yoktur.
  Kapı yalnız tanım hash'i izin listesinde olan organın çıktısını merge'e götürür (`12`). Her
  ajanın kendi üretilmiş sayfası vardır (`15`).
- **Uzmanlık havuzu profilden doğar.** Sabit roller: harness ve ölçüm mühendisi, test ve CI
  mühendisi, ajan ve prompt yazarı, maliyet mühendisi, her artefakt için rakip ve yargıç. Alan
  uzmanları (dil, çerçeve, veri katmanı, kenar) tohumda adla geçmez; profildeki baskın
  teknolojiler için genesis'ten doğar ve ablasyonla kalır.
- **Model politikası.** Yüksek işler **Opus 5.5** (`claude-opus-5-5`): Kurucu, spec taslakçısı,
  planlayıcı, keşif basamağındaki avcı, K5 ve üstü implementer, şerit yazarı. Düşük işler
  **Sonnet 5.5** (`claude-sonnet-5-5`): tohum rakibi, test-yazıcı, oracle düzelticisi, K0–K2
  düzelticisi, merdivenin alt basamakları, defter bakımı. En ucuz model `policy.json`'da
  adlandırılır ve yalnız panelin faz 1–2'si için izinlidir. Kimlikler `24`'tedir; bağımsızlık
  kuralı `09a`'dadır ve model politikasının üstündedir.
- **Takım boyutu aşama spec'inde yazar.** Aşama 0 ve 1 için iki ajan: Kurucu ve tohum rakibi
  (dürüstlük ekimini kurulumda operatörün ayrı bir ajanı bir kez yapar, `asama-0/10`); Aşama 0'ın
  çalışma-zamanı modeli yalnız (B)'deki `llm.call` kanaryası, Aşama 1'inki düzelticinin Sonnet çağrısı
  ve P2'nin güvenlik avcısıdır. Aşama 2 ve 3'te altı ya
  da yedi. Sayı bütçeyle sınırlıdır; her ajanın hangi sayıyı oynattığı çıkış raporunda yazar.
- **Anlaşma değil, çürütme.** İki ajanın aynı sonuca varması kanıt değildir. Bir artefakt ancak
  farklı modelden ve ayrı bağlamdan bir rakip onu çürütmeyi deneyip başaramadığında kabul edilir.
  Başarılı çürütme, kabul kadar değerli bir çıktıdır.
- **Kopyalamak değil, daha iyisini bulmak.** Tasarım artefaktlarında (yeni organ, örüntü önerisi,
  kalıcı düzeltmenin biçimi) karşı koltuk yalnız çürütmez, kendi bilgisinden referanslı en az bir
  alternatif önerir; kazananı yürütme seçer (`10`).
- **Sözleşmeyle bağlanır, konuşarak değil.** Ortak arayüz koddan önce yazılır ve iki tarafın
  testi yeşil olunca donar; ilk arayüz bulgu şemasıdır (`05`, `26`).
- **Entegrasyon tek canlı koşudur.** Takımın ortak çıktısı harness'te uçtan uca, gerçek veriyle,
  tek koşuda ölçülür. Dikişleri birim testi değil, bu koşu bulur.
- **Ajana kalıp verilmez, soru verilir.** Avcıya "şunu ara" değil, "bu özellik nerede bozuluyor ve
  bir insanın ne değiştirmesi gerekir"; yargıca "kural tetiklendi mi" değil, "üründe birinin
  değiştirmesi gereken bir hata var mı ve kanıtı ne".
- **Olgunluk ölçümdür** (`23`).
