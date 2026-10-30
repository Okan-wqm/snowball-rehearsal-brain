# Mimari İlkeler Kataloğu: Danışma, Seçim, Kanıt

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: bir tasarım ya da düzeltme biçimi seçilirken; iki yerde bulunan hata, aynı veriyi isteyen ikinci servis, yeni ekosistem, kaynakla ya da kodla çelişen rapor ve doküman; rakip tekrar ve ikinci kaynak iddiası kurarken
Çapa: `founder-ledger.jsonl` `kind: decision` satırları; İngilizce katalog ve kaynak listesi `catalog.md` (bu taslağın yanında)

---

**Neden var.** Sistem tekrar eden ve dağılmış koddan kaçınmak, her durumda uygun mimari ilkeyi kendisi
seçmek ister. Katalog bilinen ilkeleri tek yerde toplar ki Kurucu bir tasarım seçerken, rakip bir artefaktı
çürütürken (ilgili tohum sayfası olarak, `29`) ve düzeltici kök nedeni tasarlarken (`23`) neye bakacağını
bilsin. Sayfalar: `31a` doğruluk ve veri sahipliği, `31b` tekrar ve uyum, `31c` sınırlar ve yapı, `31d`
değişim, durum ve olaylar, `31e` güvenilirlik ve evrim, `31f` dokümantasyon ve bilgi, `31g` karar rehberi,
`31h` çatışmalar ve tarama sinyalleri. Her ilkenin tanımı, ne zaman ve ne zaman değil, repoda nasıl
bulunduğu, mekanik doğrulaması, ilişkileri ve kaynakları İngilizce katalogdadır; bu sayfalar onun özetidir.

**Katalog danışmadır, reçete değildir.** Hiçbir ilke kural değildir. Kurucu her durumda hangi ilkelerin
uygulanacağını kendisi seçer ve listede olmayan bir ilkeyi de kullanabilir. Her seçimi ve nedenini
defterine `decision` satırı olarak yazar (`26`): `summary` seçilen ilkenin kimliğini (ör. `ssot`),
düşünülüp bırakılan alternatifleri ve seçimi doğru tutacak kontrolü anar; `refs[]` kanıtın `path:line`'larını
taşır. Bir ilke, bu kodda tuttuğunu ya da çiğnendiğini gösteren bir kontrol koşana kadar hipotezdir (Y1,
Y8). Yürütülebilir kontrolü olmayan ilke danışma olarak kalır ve hiçbir şeyi kapılamaz.

**Tekrar ve ikinci kaynak: önce açık iddia.** Tekrarlanan mantık ya da ağacın zaten tuttuğu bir gerçek için
ikinci bir doğruluk kaynağı (aynı tabloya ikinci yazar, aynı ayara ikinci varsayılan, şemayı elle kopyalayan
tip, aynı metriğin ikinci hesabı, kodu yeniden anlatan doküman) bir risk sinyalidir, kendi başına kusur
değildir. Rakip onu iki ucun `path:line`'ıyla açık iddia olarak bildirir (`29`, `open_claim`). İki kopya
yeniden üretilebilir bir kusura ayrıştığında ise çürütmedir: yeniden üretici yalnız ayrışma yüzünden
görülen çıktıyı gösterir (bir kopyada düzeltilip ötekinde kalan hata, aynı olduğunu iddia eden iki tanımın
aynı girdide farklı sonuç vermesi) ve hakem onu `reproduced: true` görür; totoloji denetimi aynen geçerlidir.
Klon araştırması bu ayrımı destekler: istenmeden ayrışan klon değişikliklerinin yaklaşık yarısı hata
doğurur, ama klonların büyük bir kısmı bilinçli ve zararsızdır (`31b`).

**Sınır (Y3).** Düzeltmesi göç, feature flag, bağımlılık manifesti ya da sır gerektiren ilkeyi (tabloyu
sahibine taşımak, outbox tablosu eklemek, yazma yetkisini daraltmak, bayrakla geçiş) sistem uygulamaz:
kanıtla bildirir, mümkünse bekçi testi bağlar, sahibi düzeltir (`30`'daki zamanlama gibi). Alan doğruluğu
hedef değildir (`01`): sistem hangi iş kuralının doğru olduğunu değil, aynı olduğunu iddia eden iki tanımın
birbirini tutup tutmadığını sorar.

**Kanıt etiketi.** Her ilke kanıtının türünü taşır; mimarinin çoğu uzlaşı değil uygulayıcı görüşüdür.

| Etiket | Anlamı |
|---|---|
| `[consensus]` | Bağımsız yetkili kaynaklar hemfikir; yaygın, çoğu zaman standart |
| `[practice]` | Etkili uygulayıcı görüşü; ampirik olarak sınanmamış |
| `[empirical]` | Yayımlanmış çalışmayla desteklenmiş |
| `[contested]` | Güvenilir kaynaklar çelişir; iki taraf da yazılır |

**Sahibin tek cümlesi, keskinleştirilmiş.** "SoR veriyi doğru üretir, SSOT onu merkezî mimariye bağlar,
ambar analiz eder, SVoT raporlar, DRY kodu temiz tutar."

| Terim | Bu katalogdaki anlamı |
|---|---|
| SoR | Bir gerçek için yazımı otoriter olan sistem; kopyalar çelişirse o kazanır. Mesele **yazma sahipliğidir** |
| SSOT | Her gerçeğin tek otoriter yeri vardır; öteki her kopya ondan türetilir, ona başvurur ya da bayatlığını beyan eder. **Merkezî olmak zorunda değildir**: farklı gerçeklerin farklı sahibi olabilir |
| Ambar, pano | Analiz için kurulmuş türetilmiş, tarihsel kopya; işlemsel bir gerçeğin sahibi değildir |
| SVoT | Metrik başına üzerinde anlaşılmış tek **tanım ve hesap**; depolama yeri değil, anlam anlaşmasıdır. Vikipedi terimi başka anlamda (tek merkezî depo) kullanır |
| DRY | Kod, yapılandırma, doküman ve testteki **bilgi** için SSOT; aynı görünen metin için değil |
| Veri güveni | Türetilmiş kopyanın hâlâ sadık olduğunun ölçülmüş kanıtı: kalite, tazelik, soy, erişim |
| Tek yazar | SoR'nin koddaki biçimi: bir tabloyu, konuyu ya da anahtarı tek modül yazar |
| Doküman | Kodun, şemaların ve doğrulanmış haritanın türetilmiş görünümü; doğruluk kaynağı değildir (`31f`) |

**Terim uyarısı.** SoR, SSOT, "source of truth" ve "golden record" sektörde tutarsız kullanılır;
Kleppmann'ın kitabı SoR ile "source of truth"u eş anlamlı sayar. Tablodaki ayrımlar bu kataloğun çalışma
tanımlarıdır, standart değildir.

**Seçim, kontrol ve katman.** Benimsenen her ilke iki şeyle gelir: `decision` satırı ve bir mimari uygunluk
fonksiyonu, yani bugün yeşil olan ve ekilmiş bir ihlalde kırmızıya dönen kontrol (`31e`; `30`'daki bekçi
kuralı). Kontrolün yeri `23`'ün katmanlarıdır: imkânsız kılmak (sınırda ayrıştırma, modül sınırı), otomatik
kılmak (tek şemadan kod ve doküman üretimi), tespit edilebilir kılmak (uygunluk fonksiyonu), belgelemek
(yalnız 1–3 imkânsızsa; kararın kaydı).

**Katalog büyür, ama tohumdur.** Sayfaları yalnız operatör değiştirir. Kurucu'nun listede olmayan bir
ilkeyle verdiği karar `decision` satırında ilkenin adıyla ve kaynağıyla durur; aynı ilke birden çok kararda
kontrolüyle tutarsa operatör onu kataloğa alabilir.
