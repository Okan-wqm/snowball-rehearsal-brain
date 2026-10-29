# Mimari ve Yetki: Dört Yer

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: ilk oturumda ve her yeni repoya bağlanırken
Çapa: kurulum özeti (hakem reposu); her döngünün `drift.check` satırı

---

GitHub'da repo içinde dosya bazlı izin yoktur, App izinleri kurulumun tamamında geçerlidir ve Free
planda özel repoda ruleset, dal koruması ve ortam yoktur. Bu yüzden yetki dört yerde durur ve
oyuncu kendi reposu dışına hiçbir şey yazmaz: aday yayımlar, hakem çeker (çekme modeli).

| Yer | İçerik | Kim yazar |
|---|---|---|
| **Beyin reposu** (oyuncu; iç kullanımda açık; `snowball-mcp`'den ayrı, yeni repo) | MCP sunucusu, CLI, adapter'lar, düzelticiler, avcılar, planlayıcı, doküman üreticisi; `candidates/`, `targets/`, `reports/`; `founder-ledger.jsonl`; spec ve tohum; döngü hakeminin ve partilerin adayı `referee/` | Kurucu kimliği; `workflows` izni yok |
| **Hakem reposu** (iç kullanımda açık) | Önyükleme hakemi (`bootstrap/`, `bootstrap.yml`; `29b`): beyin reposunun itme yargıcı, Aşama 0'dan sonra da kalır. Aktarılmış döngü hakemi (kapı, nöbetçi, defter, `loop.yml`; partilerle harness, dispatcher, Gözcü), koltuk promptları, tohum vektörleri; anayasal `policy.json`, `control.json`, kurulum özeti | Yalnız operatör; yazma izinli App kurulu değil; iş akışı varsayılan izni salt okunur |
| **Hedef repo** | `brain/state` (yetim dal, `<state_root>`), `brain/integration`, `brain/c/<id>` aday dalları | Yazar App'i, yalnız hakemin `yaz` işinden |
| **Mühürlü depo** (özel) | Held-out havuzu, mühür, mühürlü görünümler, held-out koşularının ham çıktıları, K6 artefaktları | Yalnız mühür App'i; ilk held-out havuzuyla açılır (Aşama 4 ön koşulu) |

Eğitim modundaki hedeflerin durumu operatörün özel **eğitim deposunda**, hedef başına bir dalda
durur; yazarı yazar App'idir, bütünlüğü Rekor köküdür; ilk eğitim hedefiyle açılır (`21`).

**Açık hakem reposu.** Hakem reposu açıkken koşu günlükleri ve artefaktları da herkese açıktır. Bu
yüzden o sürece yalnız açık hedefler ve eğitim hedefi bağlanır; ilk özel hedeften ya da mühürlü depo
açılmadan önce hakem reposu özel yapılır (`25` 0).

**Beyin bir MCP sunucusudur.** Repo-bağımsız koddur; hedefe bağlanınca `<state_root>` açar:
`brain/state` yetim dalının kökündeki dizin (varsayılan `.brain/`). Her dosya ancak okuyucusu doğunca açılır, okuyucusu kalmayınca kapanır (Y4).

**Kimlikler** (`24`, `25`). Kurucu kimliği beyin reposuna yazar, hakem reposunu okur; açık beyni ve
açık hedefi kimliksiz okur. Okuyucu App'i yalnız özel hedef gelince kurulur ve yalnız okur. Yazar App'i
hedeflere ve eğitim deposuna kurulur; içerik, PR ve check yazar, `workflows` izni yoktur. Mühür
App'i yalnız mühürlü depodadır. Beyin App'i yoktur.

**İş başına haklar.** Hiçbir iş hem sır tutup hem oyuncu ya da hedef kodu koşturmaz (`08`).

| İş | Kimlik ve sır | Okur | Yazar | Kod koşturur |
|---|---|---|---|---|
| `çek` | Kimliksiz; özel hedefte okuyucu App'i | Beyin reposu, hedef | İçerik kimlikli artefakt | Hayır |
| `getir` | Sır yok; ağ var | Paket kayıt defterleri | İçerik adresli bağımlılık artefaktı | Paket yöneticisi, betikler kapalı |
| `koş` | Sır yok, `permissions: {}`; ağ yok | Artefaktlar | Sonuç dosyaları; hash'leri konteyner dışında | Evet, iç içe konteynerde |
| `çağır` | Sağlayıcı kimliği | Tipli girdi | Yanıt, sunulan model, maliyet | Hayır |
| `yaz` | Yazar App'i, Sigstore OIDC | `koş`, `çağır` çıktıları, kimlikle | `brain/state`, `brain/integration`, check, Rekor | Hayır |
| Held-out exit (Aşama 4'ten) | Mühür App'i | Mühürlü depo | Mühürlü görünüm | Hayır; oyuncu koşusu `koş`ta |

**Hakem, oyuncudan ayrıdır.** Hedefte beynin hiçbir kimliği ve iş akışı yoktur. Hakem reposunun
zamanlayıcısı beyin reposunu ve hedefi yoklar, adayı çeker, sırsız işte yeniden koşturur ve kararı
hakem koduyla verir. `brain/integration`'daki zorunlu kontrolün kaynağı yazar App'ine sabittir;
başka kimlik raporlayamaz ve bu kullanıcı hesabında da çalışır. Yazar App'i `main`'e yazamaz:
yazma modu bunu taşıyan bir `main` ruleset'i ister (`21`, `25a`).

**Hakem değişikliği ve bilinen sınır.** Hakem reposu ruleset'e dayandırılmadığı için (özel Free planda yoktur) hiçbir App
ona yazmaz. Döngü hakeminin kodu yalnız operatör aktarımıyla değişir: **aşama çıkışında ya da parti
çıkışında**, mekanik betikle. Parti çıkışı aynı (A) → aktarım → (B) protokolünün dar hâlidir: partinin
mikro özellikleri bitince (A), operatör aktarır, (B) partinin ilk okuyucusunu canlı koşar (`02`,
`asama-1/13`). Ağaç hash'i, operatör dosyaları (`policy.json`, `control.json`, `bootstrap.json`, `setup/`,
`seats/`, `vectors/`) ve önyükleme hakemi hariç, beyin reposundaki pinli SHA'nın `referee/` ağacıyla aynı
olmalıdır; aktarım önyükleme hakemine dokunmaz, o yalnız tohum dönemiyle değişir. Her aktarım insan
dokunuşu sayacına yazılır. Yeni parçaların (Aşama 0 ve partiler) adayını Kurucu `referee/` altında yazar ve
önyükleme hakemi her push'u yargılar; aktarılmış kodun değişikliğini şerit yazarı yazar (`29`): Kurucu
değildir, yalnız tipli hakem raporlarını ve kanaryaları okur, çıktısı rakipten ve kanaryadan geçer. Tek yazma anahtarı yazar
App'idir ve ortam sırları olmadığından hakem reposundaki her iş onu adlandırabilir; bunu Rekor kökü,
kırmızı kontrol ve `drift.check` tespit edilebilir kılar, imkânsız kılmaz. Hakem reposu ruleset ve
ortam taşıyabildiği gün (açık repo ya da Pro; iç kullanımdaki açık repo bugün taşır, yol operatör kararıyla ayrıca açılır) ayrı denetçi ve yazar App'leri, ortam sırları ve
aktarımsız şerit yolu açılır (`09a`).

**Genellik testi.** Beyin ve hakem, kendi testlerinde boş bir oyuncak repoya bağlanır ve
`<state_root>` sıfırdan büyür. Beyin koduna, hakem koduna ya da tohum sayfalarına hedef repoya
özgü bir yol, araç ya da karar belgesi adı sızmışsa test kırmızıdır. Aşama 0'da ad denetimini
önyükleme hakemi yapar (`asama-0/10` #genellik); `<state_root>`'un büyümesi P1 partisiyle gelir.

**Kurulum.** `25` inşadan önceki, `25a` Aşama 0 çıkışındaki operatör işidir; `25a` her yeni hedef
için tekrarlanır. Döngü içinde insan yoktur; kurulumun bozulmadığını genesis bir kez (`asama-0/10a`),
P1'den sonra her döngü `drift.check` doğrular (`01b`).
