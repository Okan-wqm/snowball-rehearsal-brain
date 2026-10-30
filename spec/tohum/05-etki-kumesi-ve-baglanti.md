# Etki Kümesi ve Bağlantı Kuralı

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: koda dokunmadan önce ve yeni organ tasarlarken
Çapa: `impact_miss` satırları; repo haritası kenarları; organ başına tek başına koşu

---

**Neden var.** Repoyu, neyin neye bağlı olduğunu öğrenmenin tek amacı hata yapmamaktır: bir yeri
yaparken başka bir yeri bozmamak ve bir güvenlik açığı açmamak (Y5, öğrenmenin ölçüsü hatadır).
Bu yüzden etki kümesinin değeri tek bir sayıyla ölçülür: **etki kaçırması** (`impact_miss`), yani
merge sonrası kırmızının nedeninin beyan edilen etki kümesinin dışında çıkması.

**Etki kümesi kuralı.** İş yapan hiçbir ajan, dokunacağı dosyaların etki kümesini okumadan
yazamaz. Etki kümesi en az profildeki etkilenen-test komutunun verdiğidir; repo haritası doğunca
(`13`) harita kenarlarıyla genişler: bu dosyayı kim import ediyor, hangi event'i üretiyor ya da
tüketiyor, hangi tabloya yazıyor, hangi sözleşmenin ucu, hangi güvenlik sınırının içinde, hangi
bağımlılığa dayanıyor. Oracle doğrulama kapsamını bu kümeyle kurar.

- **Harita ilk okuyucusuyla açılır.** Aşama 1'de etki kümesi etkilenen-test komutudur; düzeltme
  aracın `fix` aralığıyla sınırlı olduğu için bu yeterliliği nöbetçi ölçer. Harita adapter'ı ilk
  `impact_miss` sinyaliyle (`17`) ya da K2 silmeleriyle doğar ve ablasyonla kalır.
- Etki kümesinde testi olmayan bir kenar kapsama boşluğudur ve değişikliği `blocked` yapar: birim
  silen (`07a`), veri yolu (bir tabloya ya da konuya yazım ya da okuma) ya da sözleşme ucu içeren
  değişiklikte her sınıfta, ötekilerde K5'ten itibaren. Bunlardan birini içermediğini kapının
  gösteremediği değişiklik içeriyor sayılır. Veri yolunun kenarı, yolun davranışını (yetki, kiracı
  yalıtımı, idempotency dahil) sınayan testlerle testlidir: düzeltilen davranışınki dışındakiler
  tabanda ve adayda yeşil koşar; kum havuzunda koşamayan test (servis yok) test sayılmaz.
- Graf aracı yalnız proje düzeyinde bağ veriyorsa etki kümesi proje düzeyindedir ve "kaba" olarak
  işaretlenir; dosya düzeyi bağ ihtiyacı bir kas sinyalidir.
- Güvenlik sınırı kenarına dokunan değişiklik, hangi sınıf bulmuş olursa olsun K6'dır; K6 oracle'ı
  canlı değilse `blocked` kalır. Harita katmanı (c) gelene kadar güvenlik sınırını profildeki
  `security_paths` tanımlar. K6 canlı olana kadar güvenlik yollarına hiç dokunulmaz, biçimleyici
  ve `--fix` dahil (`04a` 10). Güvenlik testi bağlamak ve açık bildirmek dokunmak değildir: test hedefe
  değil `<state_root>/security/tests/`'e yazılır ve Aşama 1'den her döngü koşar (`30`, `30d`).
- Kalıcı veriyi silen, üzerine yazan ya da bilgi kaybettirerek dönüştüren bir yolu ekleyen ya da
  genişleten değişiklik (koşulsuz silme ya da güncelleme, bir yazımın süzgecini kaldırmak), hangi
  dosyada olursa olsun güvenlik yoludur: K6 canlı olana kadar `blocked`'dır, sonra yalnız K6
  kapısından ve `07a`'nın veri şartlarıyla geçer. Böyle bir yol eklemediğini ve genişletmediğini
  kapının gösteremediği değişiklik de böyle sayılır.
- Bağımlılık manifesti değişikliği K6'dır ve Y3 gereği `blocked`'dır; bağımlılık eklemek
  sistemin işi değildir.
- Derleme grafiğinin dışında kalan dizinlerdeki değişiklik, o dizin için profilde bir araç zinciri
  yoksa `blocked`'dır ve kapsama boşluğu sinyali üretir.

Bu mekanizma ajanın dikkatine değil yapıya dayanır; ajan dikkatli olsa da olmasa da kapı aynı
kümeyi yeniden koşturur.

**Bağlantı kuralı.** Organlar veriyle bağlanır, kodla değil. Her organın çıktısı bir sonrakinin
girdisidir ve her yazarın bir okuyucusu vardır; döngü böyle kapanır. Ama hiçbir organ bir
diğerinin kodunu import ederek bağlanmaz: her organ tek başına koşulabilir, ölçülebilir ve
değiştirilebilir. Kar topu katman katman büyür; bir katman ancak harness'te anlamlı bir sayı
oynatınca yapışır (Y5). Her şeyin her şeyi import ettiği bir sistemde hiçbir parça tek başına
ölçülemez ve hiçbir parça silinemez.

**Sözleşme önce.** Organlar arasındaki ilk ortak arayüz bulgu biçimidir ve şeması `26`'dadır;
ayrı bir sözleşme dosyası istemez. İkinci bir ortak arayüz doğduğunda (örneğin planlayıcı ile
düzeltici arasında) birlikte çalışan organlar onu koddan önce `<state_root>/contracts/` altında
yazar; öneri referansla kabul ya da çürütülür, iki tarafın testi yeşil olunca donar. `contracts/`
bu ikinci arayüzle açılır (Y4).
