# Mimari ve Yetki: Dört Yer

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: ilk oturumda ve her yeni repoya bağlanırken
Çapa: kurulum özeti (hakem reposu); her döngünün `drift.check` satırı

---

GitHub'da repo içinde dosya bazlı izin yoktur, App izinleri kurulumun tamamında geçerlidir ve Free
planda özel repoda ruleset, dal koruması ve ortam yoktur. Bu yüzden yetki dört yerde durur ve
oyuncu kendi reposu dışına hiçbir şey yazmaz: aday yayımlar, hakem çeker (çekme modeli).

| Yer | İçerik | Kim yazar |
|---|---|---|
| **Beyin reposu** (özel, oyuncu) | MCP sunucusu, CLI, adapter'lar, düzelticiler, avcılar, planlayıcı, doküman üreticisi; `candidates/`; `founder-ledger.jsonl`; spec; Aşama 0'da hakem adayı `referee/` | Kurucu kimliği; `workflows` izni yok |
| **Hakem reposu** (özel) | Kabul edilmiş hakem (kapı, harness, oracle koşucusu, dispatcher, Gözcü, koltuk promptları, tohum vektörleri); anayasal `policy.json`, `control.json`, kurulum özeti. Aşama 0 çıkışına kadar önyükleme hakemi (`29b`) | Yalnız operatör; yazma izinli App kurulu değil; iş akışı varsayılan izni salt okunur |
| **Hedef repo** | `brain/state` (yetim dal, `<state_root>`), `brain/integration`, `brain/c/<id>` aday dalları | Yazar App'i, yalnız hakemin `yaz` işinden |
| **Mühürlü depo** (özel) | Held-out havuzu, mühür, mühürlü görünümler, held-out koşularının ham çıktıları, K6 artefaktları | Yalnız mühür App'i; ilk held-out havuzuyla açılır (Aşama 4 ön koşulu) |

Eğitim modundaki hedeflerin durumu operatörün özel **eğitim deposunda**, hedef başına bir dalda
durur; yazarı yazar App'idir, bütünlüğü Rekor köküdür; ilk eğitim hedefiyle açılır (`21`).

**Beyin bir MCP sunucusudur.** Repo-bağımsız koddur; hedefe bağlanınca `<state_root>` açar:
`brain/state` yetim dalının kökündeki dizin (varsayılan `.brain/`). Her dosya ancak okuyucusu doğunca açılır, okuyucusu kalmayınca kapanır (Y4).

**Kimlikler** (`24`, `25`). Kurucu kimliği beyin reposuna yazar, hakem reposunu okur, açık hedefi
kimliksiz okur. Okuyucu App'i yalnız okur; beyin reposuna ve özel hedeflere kurulur. Yazar App'i
hedeflere ve eğitim deposuna kurulur; içerik, PR ve check yazar, `workflows` izni yoktur. Mühür
App'i yalnız mühürlü depodadır. Beyin App'i yoktur.

**İş başına haklar.** Hiçbir iş hem sır tutup hem oyuncu ya da hedef kodu koşturmaz (`08`).

| İş | Kimlik ve sır | Okur | Yazar | Kod koşturur |
|---|---|---|---|---|
| `çek` | Okuyucu App'i | Beyin reposu, hedef | İçerik kimlikli artefakt | Hayır |
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

**Hakem değişikliği ve bilinen sınır.** Hakem reposu Free özel planda korunamadığı için hiçbir App
ona yazmaz. Hakem kodu yalnız operatör aktarımıyla değişir: aşama çıkışında, mekanik betikle; ağaç
hash'i, operatör dosyaları (`policy.json`, `control.json`, `setup/`, `seats/`, `vectors/`) hariç,
beyin reposundaki pinli SHA'nın `referee/` ağacıyla aynı olmalıdır ve aktarım insan
dokunuşu sayacına yazılır. Adayı şerit yazarı yazar (`29`): Kurucu değildir, yalnız tipli hakem
raporlarını ve kanaryaları okur, çıktısı rakipten ve kanaryadan geçer. Tek yazma anahtarı yazar
App'idir ve ortam sırları olmadığından hakem reposundaki her iş onu adlandırabilir; bunu Rekor kökü,
kırmızı kontrol ve `drift.check` tespit edilebilir kılar, imkânsız kılmaz. Hakem reposu ruleset ve
ortam taşıyabildiği gün (açık repo ya da Pro) ayrı denetçi ve yazar App'leri, ortam sırları ve
aktarımsız şerit yolu açılır (`09a`).

**Genellik testi.** Beyin ve hakem, kendi testlerinde boş bir oyuncak repoya bağlanır ve
`<state_root>` sıfırdan büyür. Beyin koduna, hakem koduna ya da tohum sayfalarına hedef repoya
özgü bir yol, araç ya da karar belgesi adı sızmışsa test kırmızıdır.

**Kurulum.** `25` inşadan önceki, `25a` Aşama 0 çıkışındaki operatör işidir; `25a` her yeni hedef
için tekrarlanır. Döngü içinde insan yoktur; kurulumun bozulmadığını her döngü `drift.check`
doğrular (`01b`).
