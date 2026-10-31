# Sınıf Merdiveni ve Aşama Sırası

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: yeni sınıf ya da aşama açılırken
Çapa: aşama çıkış satırları, sınıf başına; profile.json araç zinciri

---

Adapter'lar en basit hata sınıfından başlar ve sınıf sınıf çoğalır. Sınıflar alan bağımsızdır;
her sınıfın adapter'ı profildeki aracı sarar. LLM, mekanik aracın bittiği yerde başlar.

| Sınıf | Hata türü | Avcı | Oracle |
|---|---|---|---|
| K0 | Lint ve format | Profildeki lint araçlarını saran adapter | Aracın yeniden koşusu |
| K1 | Tip ve derleme hataları | Sarıcı adapter | Araç |
| K2 | Ölü kod, kullanılmayan export, koşmayan test hedefi; kullanılmıyor olmak ölü olmak değildir (`07a`) | Sarıcı adapter, repo invariantları | Bulguda araç; silmede `07a`'nın kanıtları ve etki kümesi testleri |
| K3 | Sözleşme paritesi: iki uçlu sözleşmeler | LLM'siz mekanik çapraz kontrol | Kasıtlı bozma |
| K4 | Şema yerleşimi ve mevcut invariant testleri | Sarıcı adapter | Araç |
| K5 | Mantık hataları: eksik await, ters koşul, yanlış sıra, yarım idempotency | LLM avcı, Opus | Test oracle'ı, avcıdan farklı model |
| K6 | Güvenlik, yetki sınırı, tenant izolasyonu, bağımlılık değişikliği | LLM avcı, Opus | Test oracle'ı, avcıdan farklı model |
| K7 | Performans | Profildeki benchmark ve sorgu planı araçları | Baseline'a karşı ölçüm |
| K8 | Hedef reponun dokümanı: bayat doküman, davranışı değişmiş kodun eksik dokümanı | Çapa çözümleme; doküman-kod çelişkisi | Her iddia koda çapalı (`path:line` ya da sembol) ve çapa çözülür; imza, CLI bayrağı, yapılandırma anahtarı ve uç adı gibi mekanik iddialar koda karşı doğrulanır; çözülmeyen çapa kırmızı |

Bir sınıf grubu ancak bir önceki aşama PASS alınca açılır. Aşama 1'den sonra hangi grubun açılacağını Kurucu'nun
aşama spec'i, önkoşulları kapanmış sınıflar arasından seçer; aşama tablosu varsayılandır ve Savunma'nın zorunlu
alternatifi (`10`) varsayılan satırdır. Varsayılandan sapan seçim tek sınıf getirir ve `18`'in Varsayılandan sapma
satırlarını taşır. Kök (Aşama 0 ve 1) ve son aşama (6, sınıf değildir) sabittir; seçim satırdaki `18` atıflı yeteneği
o aşamadan düşürmez (`02`). K3'ün aracı yoktur; oracle'ı kasıtlı bozmadır. Her açılış aynı döngüyü yeniden
koşturur: adapter → oracle → düzeltme → merge → defter → maliyet inişi.

**Sınıf önkoşulları** (`class_requires`; prosedür yalnız ekler, operatör siler; "aynı çıkışta" en geç sınıfın kendi
çıkışı demektir, öbür girdi seçimden önce kapanır):

| Sınıf | Önkoşul |
|---|---|
| K1, K2 bulgu, K3, K4, K8 | K0'ın Aşama 1 PASS satırı |
| K2 silme | + `07a` kanıtları, harita (a) aynı çıkışta |
| K5 | + LLM avcı, Held-out havuzu, Panel aynı çıkışta |
| K6 düzeltme | K5 yetenekleri önceki PASS'ta + Güvenlik avcısı ve bekçi testleri + Güvenlik yoluna dokunma aynı çıkışta |
| K7 | + LLM avcı |
| K3, K7, K8 | `class_floors` yazılı |

**Oracle'ı hazır olmayan sınıf rapor eder, değiştirmez.** Oracle'ı hakemin bu hedefte gizli tohumla ektiği bozmayı
yakalamadan sınıf merge etmez; bulguları `blocked` satırdır (Y8). Geçen aşama ya da açık sınıf sayısı hiçbir puana girmez.

**K6 Aşama 1'den gözlenir, önkoşulları kapanınca düzeltilir.** Açık bulmak, kanıtlamak, bildirmek ve bir kuralı bekçi
testine bağlamak davranışı değiştirmez; bunu Aşama 1'den, P2 partisiyle gelen hakemin bağımsız güvenlik
avcısı yapar (`30f`, `asama-1/13`). Aşama 0'ın güvenlik mikro özelliği `secrets.scan`'dir.
Hedefin koduna güvenlik düzeltmesi yalnız K6 canlı olunca yazılır. Bilinen açık sınıfları, bulma yolları
ve kapanış testleri `30`–`30c`'de, hedefin tehdit modeli `30d`'de, güvenlik defteri `30e`'dedir.

**K8, dokümanı kodla birlikte geliştirir.** Kod ile doküman çelişirse referans koddur (Y1); doküman
ilk bağlanmada okunur ama hiçbir karar ona dayanmaz. Doküman düzeltmesi ve yeni doküman kod
düzeltmesiyle aynı kapıdan geçer; doküman yolları yalnız K8 adaylarında diff-guard'dan geçer
(`01b`). Reponun kendi doküman düzenine uyulur.

| Varsayılan aşama sırası (0, 1 ve 6 sabit) | Döngüde canlı olan | Oracle |
|---|---|---|
| 0 | Yürüyen iskelet: ilk canlı döngünün okuduğu 18 mikro özellik beyin reposunun `referee/` dizininde, önyükleme hakeminin denetiminde (`29b`): zincir, `secrets.scan`, kum havuzu, profil ve birim, `deps.fetch` (npm), tarif doğrulaması, diff-guard, kapı, hedef yazıcı, defter, Rekor, nöbetçi, geri alma ve provası, `llm.call`, durum bloğu, `loop.yml`, etkinleştirme. Çıkışta aktarım; döngü önce oyuncak hedefte, aynı (B) içinde gerçek hedefin kopyasında tek birimde hazır adaylarla koşar. Çalışma zamanında tek LLM çağrısı kanaryadır | Kendi-testleri, tohum vektörleri, modülsüz kırmızı, kırmızı kontrol, rakip; (B)'de K0 oracle'ı (aracın yeniden koşusu, mandal) ve canlı merge'ler |
| 1 | K0 döngüsü uçtan uca, oyuncu organları: lint adapter, taban, `fix` aralığı düzelticisi, araçsız Sonnet düzelticisi, aday yayımlama, üretilmiş sayfalar. Hakem parçaları ilk okuyucularından önce partilerle gelir (`asama-1/13`): P1 organ ve ölçüm (snapshot, vaka seti, harness, Gözcü, `drift.check`), P2 güvenlik gözlemi, Aşama 1 çıkış partisi (`exit.sample`, `spec.lint`, `lock.check`) | Kural sayımında sıfır kaçırma; araç yeniden koşusu ve mandal; kapının etkilenen-test koşusu; canlı merge'ler |
| 2 | K1 ve K2 adapter'ları; **Plan fazı**: Opus planlayıcı; Ders görünümü ve enjeksiyonu (`18`), ilk okuyucusuyla; gerçek beyinde ders provası, sahibin MVP sınavı (`22b`); harita katmanı (a), K2 silmeleri ya da ilk `impact_miss` sinyaliyle; `main` senkronu ölçülmüş ihtiyaçla | Araç; planlayıcı sırası rastgele sıradan daha yüksek değer / USD verir; ders provası (`22a`) |
| 3 | K3 ve K4; ilk araç-dışı mekanik dedektörler; maliyet inişi canlı; harita katmanı (b) | Kasıtlı bozma, araç |
| 4 | K5: kalıpsız LLM avcı, mühürlü depo ve held-out havuzu, beş fazlı panel, test oracle'ı, TP'den dedektör üretimi | Held-out `human_fix` recall alt sınırı, yürütme oracle'ı, değer / USD |
| 5 | K6, K7, K8; harita katmanları (c) ve (d); genesis tüm organ türlerine ve property'lere açık | Harness deltası, maliyet deltası, ablasyon; K8'de çapa çözümü |
| 6 | `main`'e terfi: entegrasyon dalında N gün yeşil, canary, otomatik geri alma; push'ta deploy olmadığı kanıtlı | Soak süresi ve geri alma provası |

Genesis organ ekleme yoludur (`12`). Aşama 1'de adapter ve düzeltici kapının izin listesine
önyükleme hakeminin kabul ettiği SHA'dan, döngünün yazdığı `accept` satırıyla girer; organ yaşam döngüsü ve genesis kuyruğu bir sınıfta en az iki aday organ
doğunca canlıdır ve o aşamanın çıkışı genesis provasını taşır (`12a`). Aşamalar genesis'in
kapsamını açar. Öğrenme de aynı biçimde sınanır: merge getiren aşama geri alma provasını, ders
görünümünü getiren aşama ders provasını taşır (`22a`).

**Neden yalnız Aşama 0, 1 ve 4 yazılı.** Aşama protokolü gereği her aşamanın spec'ini Kurucu, bir
önceki aşamanın ölçülmüş sonuçlarıyla taslaklar (`02`); tohum yalnız bu tablodaki hedef satırını
verir. Aşama 0 ve 1 başlangıç noktası ve güven kökü olduğu için tohumla gelir. `asama-4/` K5'in hedef
taslağıdır (varsayılan sırada Aşama 4): sistemin varmak istediği yeri (kalıpsız LLM avcı) ve önceki
aşamaların neyi teslim etmesi gerektiğini göstermek için yazıldı; K5'i getiren aşamanın spec'i olarak
yeniden yazılır, ön koşulu yukarıdaki önkoşul tablosudur (`02` 1). Öbür aşamaların spec'i önceki
aşamanın sonuçları olmadan yazılırsa ölçülmemiş bir tahmin olurdu.
