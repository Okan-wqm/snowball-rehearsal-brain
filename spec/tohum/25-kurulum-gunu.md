# Kurulum, Birinci Bölüm: İnşadan Önce

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: ilk başlatmadan önce, bir kez; her tohum döneminde satır 10b
Çapa: hakem reposundaki `setup/summary.json`

---

Döngü içinde insan yoktur; döngüden önce iki kısa insan işi vardır. Hepsi listededir; listede
olmayan hiçbir şey sonradan insandan istenmez. Ön şart: tohumla gelen önyükleme hakeminin kodu
(`seed/bootstrap/`, `29b`) yazılmış ve kendi testlerinden geçmiş olmalıdır; yoksa kurulum başlamaz.

| # | İş | Neden |
|---|---|---|
| 0 | **Plan gerçeğini kaydet.** Hesap Free; özel repoda ruleset, dal koruması ve ortam sırrı yok, ayda ~2.000 Actions dakikası var; App izinleri kurulum genelinde. İç kullanımda (operatör kararı, 2026-10-29) beyin, hakem, oyuncak ve kopya repoları açıktır ve standart koşucu dakikası ücretsizdir; satışta beyin ve hakem özel olur. Hakem reposu açıkken koşu günlükleri ve artefaktları da açıktır: yalnız açık hedefler ve eğitim hedefi bağlanır; ilk özel hedeften ya da mühürlü depodan önce hakem reposu özel olur. Hakem reposuna hiçbir App yazmaz, hakem kodu yalnız operatör aktarımıyla değişir (`01a`) | Tasarımın dayandığı gerçek yazılı olsun; değişirse `drift.check` görür |
| 1 | **Beyin reposunu aç:** yeni ve ayrı bir repo (`snowball-mcp` değil; iç kullanımda açık), yerleşimi `24a`'da. **Kurucu belirteci**: yalnız beyin reposuna içerik yazan ince taneli belirteç, `workflows` yok; hakem reposunda yalnız okuma (içerik ve Actions sonuçları). Kurulum provası: bu belirteçle hakeme push, artefakt silme ve `.github/workflows`'a dokunan push 403 | Oyuncu kendi iş akışını ve hakemini değiştiremesin |
| 2 | Hakem reposunu aç (iç kullanımda açık). Yazma izinli hiçbir App kurulmaz, ortak çalışan eklenmez; iş akışı varsayılan izni salt okunur | Hakemi yalnız operatör yazsın |
| 2a | **Ruleset'ler:** `snowball-mcp`, beyin ve hakem repolarında `main`'e `non_fast_forward` ve `deletion`, bypass aktörü yok; özete ve kayma denetimine girer | Geçmiş yeniden yazılamasın; kurtarma `base`'i geri merge etmektir |
| 3 | Önyükleme hakemini kur: `seed/bootstrap/` → hakem reposunda `bootstrap/`, `seed/bootstrap/workflow/bootstrap.yml` → `.github/workflows/`, `seed/bootstrap/vectors/` → `vectors/`, `29` → `seats/`; `bootstrap.json`'u yaz (beyin reposu ve dalı, `@sha256` ile pinli imaj, rakip modeli, `effort`, tur sayısı ve çağrı başı USD tavanı, sınırlar); sır `CLAUDE_CODE_OAUTH_TOKEN` (operatörün `claude setup-token` çıktısı; bir yıl geçerlidir, son kullanma tarihi `control.json`'a `oauth_token_expires` olarak yazılır; dolunca rakip `api_error` verir: ret hafızasına işlenmez, aynı SHA'da üçüncüsünden sonra günde bir, en çok 7 gün yeniden denenir; iç kullanımda API anahtarı yoktur); hash'leri özete yaz | Aşama 0'ın yargıcı Kurucu'dan önce var olsun (Y6); itme yargıcı olarak kalır |
| 4 | Hakem reposuna `control.json` (`26c`: kill switch, bütçe durumu, `oauth_token_expires`, `loop_schedule: false`, `merge_paused`, `founder_resume`) ve `policy.json` anayasal bölümünü yaz: aylık USD ve Actions dakikası tavanları, paylar, sınıf tabanları, `required_exit_rows`, regresyon dondurma kuralı, döngü ve gün tavanları, güvenlik anahtar kelimeleri, yasaklı ifadeler, aşama sırası, bakış bütçesi, güven düzeyi, non-inferiority marjı, hayatta kalma pencereleri, prova kuralları, lisans izin listesi ve istisnaları, `operating{}` bantları (`18a`) | Operatörün tek döngü dışı kolu; hiçbir App yazamaz |
| 5 | **Okuyucu App'i, yalnız özel hedef gelince** (hakem reposu önce özel olur, madde 0): yalnız `contents:read`, `metadata:read`; özel hedeflere kur. Açık beyin ve açık hedef kimliksiz okunur; önyükleme hakeminde App yoktur | Hakem özel hedefi yazma yetkisi olmadan çeksin |
| 6 | **Yazar App'i**: `contents`, `pull_requests`, `checks` yazma, `administration:read`; `workflows` yok; yalnız hedef repolara (oyuncak ve kopya) kur, beyin ve hakem reposuna kurma | Hedefe tek yazar; oyuncunun ve hakemin reposuna yazmasın |
| 7 | Hakem reposunun sırları: yazar App anahtarı (özel hedef gelince okuyucu App anahtarı), sağlayıcı kimliği (tohum rakibi ve döngünün `llm.call`'ı için `CLAUDE_CODE_OAUTH_TOKEN`), prova gizli tohumu | Ajan konteynerine ve oyuncu kodu koşan işe hiçbiri girmez |
| 8 | **Frenler ve gerçek sınır.** Rakip, Kurucu ve `llm.call` abonelikle koşar: gerçek sınır planın kullanım penceresidir (5 saatlik ve haftalık kota); takılmak (HTTP 429) operatör uyarısı ve kesintidir, ret değildir. `06` ve aşama bütçeleri liste fiyatı tahminiyle çalışan, olağan işi durdurmayacak kadar yüksek kaçak frenleridir (`asama-0/12`). GitHub Actions harcama sınırı: dakika aşımı ücretsiz durur; Aşama 0'da önyükleme hakemi dakikayı ölçmez, fren budur; P1'den sonra Gözcü bunu bütçe dondurması sayar | Kaçak döngü dursun, olağan iş durmasın |
| 9 | Kill switch'in yolları: `control.json` bayrağı (her iş onu `main`'den canlı okur; açıkken iş başlamaz, koşan koşuda `yaz` kabul etmeyen, harcamayı yazan bir `stopped` sonucu imzalar), `gh run cancel` (iptal edilen koşu hiçbir şey imzalamaz), `gh workflow disable`, belirteç sırrını silmek ya da (App'ler kurulunca) App askıya alma. Her yolu bir kez dene | Durdurma hakkı |
| 10 | Oyuncak hedef: boş, herkese açık bir repo aç; içeriği Aşama 0 çıkışında aktarılır (`25a`) | Döngünün ilk koştuğu hedef; geri alma provası burada |
| 10a | **Kopya hedef.** Gerçek hedefin yalnız `main`'ini yeni, açık, çatal olmayan bir repoya it; **Actions kopyada tamamen kapalı** (hedefin sır kullanan iş akışları koşmaz); `main` güncellemesi yalnız operatör rolüne açık. **Aynalama:** operatörün ayrı bir işi, yalnız kopyanın içeriğine yazan ince taneli belirteçle orijinalin `main`'ini hızlı ileri sarar, `brain/*`'a dokunmaz, ileri sarılamazsa durur; (B) PASS olana kadar duraklatılır (`base_sha` sabit), sonra günde bir. Özete `targets[]` (`26c`): kimlik, repo, tür, `base_sha`, `identifiers`, `excluded_paths` (hedefin ajan yapılandırması ve kapsam dışı paketler; beyin listeyi yalnız genişletebilir), `unit_candidates` (kopyanın aday birim yolları, sırayla; ölçütler `asama-0/08`) | Aşama 0'ın iki hedefi ve birimi veri olarak adlı olsun; insan düzeltmeleri kopyaya aksın |
| 10b | **Tohum dönemi.** Özetin `seed_epochs[]`'ine `{commit, spec_tohum_sha256, seed_sha256, bootstrap_sha256}` satırı. Runbook: `snowball-mcp` `main`'i yeşil → kill switch aç → aynı commit'ten `bootstrap/`, `vectors/`, `seats/`'i hakem reposuna kopyala → döneme satır ekle → aynı `spec/tohum` ve `seed/`'i beyin `main`'ine tek commit'le it → kill switch kapat → dokunuş satırı. İlk dönem kurulumdadır | Tohum güncellemesi Kurucu'nun ihlali sayılmasın (`seed_update`, `29b`) |
| 10c | **Dürüstlük ekimi.** Kurucu başlamadan, Kurucu olmayan bir ajanla imkânsız vektörü ve bal küpünü ek; anahtarı hiçbir açık metne yazma, `sha256(canonical(anahtar))`'ı özete `honesty_commitment` olarak yaz (`asama-0/10`). Ekim kaçırıldıysa yalnız sahibin adlı istisnası (`honesty_exception`, `02` "Sahip istisnası") ve yanında taşıma hedefinin ekiminin `honesty_commitment`'ı | Kurucu'nun dürüstlüğü ölçülsün |
| 11 | **İlk koşu ve Kurucu.** Özete ilk koşu işaretini koy, önyükleme hakemini bir kez tetikle, imzalı başlangıç durumunu doğrula, işareti kaldır; sonra Kurucu'yu başlatıcıyla başlat: kapsülde ya da ayrı Windows kullanıcısında, çalışma dizini beyin reposu, hedef salt okunur klon (`24a`) | Aşama 0 inşası |

**Actions dakikası hesabı.** Açık repoda standart koşucu dakikası ücretsizdir; `monthly_cap_ci_minutes`
P1'den sonra Gözcü'nün frenidir (`18a`), önyükleme hakemi onu ölçmez: Aşama 0'da fren GitHub harcama
sınırıdır (madde 8). Repo özel olursa (satışta) Free plan ayda ~2.000 dakika verir, tavan 1.800'dür ve her
iş en az bir dakika faturalanır. Önyükleme hakeminin boştaki saatlik yoklaması tek iştir: ayda ≈ 24 × 30 =
720 dakika. Değerlendirilen bir push beş ya da altı iştir, tipik olarak 15–30 dakika. Mikro özellikler tek
tek itilir (`asama-0/14`). Dakika biterse GitHub işleri durdurur (madde 8). Rakip freni dolunca hakem iş
başlatmaz ve aynı baş politika değişince kendiliğinden yargılanır (`29b`).

**Açık repoda bir sınır.** GitHub, açık repoda 60 gün etkinlik olmazsa zamanlanmış iş akışını kapatır; hakem
uzun süre commit almazsa yoklama sessizce durur. Operatör iş akışını yeniden açar ya da bir commit atar.

**Operatörü ne uyarır.** Döngü operatöre bir şey sormaz ama onu uyarır: kırmızı bir hakem koşusu (kimlik
ya da kota kesintisi, 429, 7 günü aşan kesinti, park edilmiş commit, `request_rejected`, rakip tarafı hata
serisi, `not_learning`, push'tan sonra sonuçsuz bekleme, `reports/` bildirimi, durum yokluğu ya da ilk koşu)
GitHub'ın başarısız koşu bildirimiyle gelir. `snowball-mcp` CI'ındaki gece bekçisi iki iş akışının
(önyükleme ve döngü) son koşusunu ve zamanlayıcının yaşadığını denetler; `oauth_token_expires`'a 30 gün
kala uyarır.

**Durum kaybolursa** (`29b`). İmzalı durum yoksa, doğrulanamıyorsa ya da koşunun okuduğu durum en yeni
değilse önyükleme hakemi durur ve koşu kırmızıdır; tohumdan kendiliğinden başlamaz. Kurtarma operatörün
işidir ve insan dokunuşu sayacına yazılır: (1) kill switch'i aç ve nedeni bul (silinmiş ya da süresi
dolmuş artefakt, doğrulanmayan imza, yarışan iki koşu); (2) yarış ya da geçici hataysa kill switch'i
kapatıp yeniden koştur, karşılaştır-ve-yaz en yeni durumu okur; (3) durum gerçekten yoksa madde 11'deki
gibi ilk koşu işaretini koy: hakem son tohum döneminin commit'inden başlar, donmuş spec'ler, frenler ve ret
hafızası sıfırlanır, eski sonuçlar Rekor'da kanıt olarak kalır. Durum şeması değişirse artefakt silinmez,
sürümlü taşınır.

Bu bölümün özeti (`setup/summary.json`, `26c`: repo adları ve görünürlükleri, ruleset'ler, kurulu App'ler
ve izinleri, iş akışı varsayılan izni, vektör ve koltuk hash'leri, anayasal politika hash'i,
`seed_epochs[]`, `targets[]`, `honesty_commitment` ve yalnız ilk koşuda ilk koşu işareti) operatörce hakem
reposuna yazılır. Önyükleme hakemi her imzalı sonuca `setup/summary.json`'un, `vectors/`'ün, `seats/`'in
ve anayasal `policy.json`'un hash'lerini yazar (böylece Rekor'a girerler); vektör ya da koltuk hash'i
özetle uyuşmazsa durur. Hash'ler git blob'ları üzerinden hesaplanır, satır sonundan bağımsızdır. Aşama 0
bu özet olmadan başlamaz: önyükleme hakemi ilk durumunu, özet kopya hedefin `identifiers`'ını taşıyan `targets[]`'ı
(10a) ve `honesty_commitment`'ı (10c; sahibin istisnası varsa taşıma hedefinin ekimi) adlandırmadıkça kurmaz, durum
kaybolunca da; var olan durum buna tabi değildir.
