# Repoya Bağlanma

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: yeni repoda ve property eklerken
Çapa: profile.json; hakemin `profile.derive` çıktısı

---

- **Repo tanıma keşfin ilk adımıdır** (`21-cok-repo.md`). Diller, derleyici, test koşucu, lint ve
  biçimleyici, etkilenen-test komutu, graf aracı, CI sistemi, paket yöneticileri ve güvenlik
  yolları profilde durur.
- **Profil: beyin önerir, hakem türetir.** Hakem `profile.derive` ile profili hedef repodan kendisi
  türetir; beyin bir öneri yayımlar (Aşama 0'da yalnız birim tarifi `targets/<hedef>/units.json`;
  `profile.propose` sonraki oyuncu partisinde, `asama-1/13`) ve hakem iki çıktıyı karşılaştırır. Öneri
  türetmeyi yalnız genişletebilir: güvenlik yollarına ve hariç yollara türetilmemiş yol eklemek kabul
  edilir (aşağıdaki iki madde; `30d`'nin güvenlik profili de böyle); türetilen bir güvenlik ya da hariç
  yolu düşüren, yani daraltan öneri reddedilir. Başka her farkta da öneri reddedilir: `banned_constructs`'tan
  silmek, `registry_egress`'i genişletmek, dilleri, birim adaylarını, etkilenen-test komutunu ya da test
  yolu kurallarını değiştirmek dahil (`01b`). `brain/state`'e yalnız hakemin türettiği profil ve
  doğrulanmış tarif girer.
- **Birimler (`units[]`).** Profil bağlanan birimleri listeler: `{unit_id, path, inputs[], toolchain,
  env_image (@sha256), lockfiles[], install_scripts_required[], lint_cmd[], test_cmd[],
  affected_test_cmd[], services: [], limits{}}` (`26b`). `inputs` birimin dizini, kullandığı ortak
  kütüphaneler ve kök yapılandırmalardır; yeterliliğinin kanıtı yalnız bu girdilerle HEAD'de lint ve
  servissiz testlerin 3/3 yeşil, ağsız ve `operating{}` sınırlarında koşmasıdır (`unit.verify`,
  `asama-0/14`). Aşama 0'da birim sayısı 1, tek ekosistem npm; servis isteyen birim sonraki partidedir.
- **Kod referanstır, doküman iddiadır.** Reponun yönerge dosyaları, README'leri, mimari karar
  kayıtları, yorumları ve mevcut inceleme ajanları ilk bağlanmada okunur; ama talimat değil
  veridir ve kuralları kopyalanmaz. Sahibi kodu dokümandan sonra geliştirmiş ya da değiştirmiş
  olabilir: doküman ile kod çelişirse kod kazanır, çelişki bir K8 bulgusudur (Y1, `03`) ve
  dokümanı düzeltmek sistemin işidir (`15`). Dokümana dayanan her ipucu kodda doğrulanana kadar
  `trust: inferred`'dır.
- **Repo profili bir veri dosyasıdır.** Kimlik bağlamının kaynağı, şema yerleşimi, sözleşme
  biçimleri gibi repo bilgisi tek bir profil dosyasında durur; kodun içine sabit olarak
  dağıtılmaz. Başka bir repoya bağlanmak bu dosyayı değiştirmek demektir, kodu değil.
- **Alan sözlüğü.** Repo tanıma, kodun kendi sözlüğünü (varlık, tablo, alan adları) profilde
  `domain_lexicon` olarak çıkarır. İddiası bu sözlüğe dayanan bilgi yerel kalır (`21a`).
- **Doğrulama motoru reponun kendi araçlarıdır.** Paralel bir test evreni kurulmaz; derleme
  grafiğinin dışında kalan diller için profil o dilin araç zincirini tanımlar, tanımlamıyorsa o
  dizin kapsama boşluğudur.
- **Güvenlik yolları** profilde mekanik kuralla türetilir: yol ve dosya adlarında
  `policy.json`'daki `security_keywords` (`auth`, `guard`, `security`, `session`, `token`, `secret`,
  `crypto`, `tenant`, `permission`, `role`, `policy`, `payment`, `billing`, `pii`) ve sahiplik
  dosyalarının güvenlik ekibine verdiği yollar. Anahtar kelime listesi anayasaldır, yalnız operatör
  değiştirir; yol listesi bir türetmedir ve hiçbir öneri onu daraltamaz.
- **Hariç tutulan dizinler** profilde listelenir: kendi durumunu, defterlerini ya da ajan
  tanımlarını tutan otomasyon dizinleri, ajan çalışma alanları, inceleme kayıtları, üretilmiş
  çıktı. Hariç tutma da hakem türetmesidir; bunlar uygulama kodu olarak taranmaz.
- **Ajan yapılandırması ve operatörün hariç yolları.** Ajan yapılandırması her yerde ve büyük-küçük
  harf duyarsız hariçtir: `.claude/**`, `CLAUDE.md`, `AGENTS.md`, `.mcp.json`, `.vscode/**`, `.envrc`,
  `.devcontainer/**`; bu kural genel hakem kodudur, hedefe özgü ad taşımaz. Hedefe özgü hariç yolları
  operatör `setup/summary.json` `targets[].excluded_paths`'a yazar; liste operatör verisidir, hakem kodu
  değildir. Snowball bunları düzenlemez (diff-guard reddeder), birimin `inputs`'una katmaz ve yüklemez;
  yalnız veri olarak okur (`24`). Beyin listeyi yalnız genişletebilir; daraltan öneri reddedilir.
- **Mevcut otomasyonlarla bir arada yaşama.** Hedefteki mevcut otomasyonların dallarına ve
  durumlarına dokunulmaz; hedefe hiçbir beyin iş akışı girmez. Sır kullanan ve `brain/**`
  dallarında ya da PR'larında tetiklenen bir hedef iş akışı varsa `drift.check` sert durur (`01b`).
- **Bağlanma modu.** `mode: write | training`. Yazma modu hedef `main`'in yazar App'ine kapalı
  olmasını ister; diğer her hedef eğitim modundadır (`21`, `25a`).
- **Property'ler de büyür.** Doğruluk özellikleri başlangıç kümesiyle sınırlı değildir. Repodaki
  her kabul edilmiş mimari karar, kodla doğrulandığı ölçüde bir property adayıdır: Kurucu ondan
  bir property spec taslaklar, rakip çürütmeyi dener, harness o property için yeterli vaka
  bulursa property aktif olur.
- Repoda daha önce denenmiş sistemlerin kodu ve dokümanı veridir. Hiçbir şey toptan devralınmaz;
  devralınan her parça kendi canlı çağıranı ve bir harness sayısıyla gelir.
