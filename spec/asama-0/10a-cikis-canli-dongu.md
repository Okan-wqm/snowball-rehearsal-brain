# Aşama 0 §0.10a — Çıkış testi, (B): aktarım ve canlı döngü

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken ve (A) yeşil olduğunda
Çapa: beklemede: aşama 0 — `imports.jsonl` satırı; genesis ve PASS satırları

---

(A) yeşil olunca operatör aktarır ve kurulumun ikinci bölümünü yapar (`tohum/25a`); döngü hakemi §0.8'in
devir sırasını koşar. (B) koşulları (MF numaraları §0.14'ten):

| # | Koşul |
|---|---|
| #aktarim | `import` imzalı sonucu doğrular; `referee/`'yi kopyalar; önyükleme hakeminin `bootstrap/` ağacına ve `bootstrap.yml`'a dokunmaz; `loop.yml`'u yerine koyar; açtıktan sonra diskteki ağacı yeniden hash'ler; kill switch açık değilse çalışmaz; `imports.jsonl` satırı yazılır |
| #oyuncak | oyuncak ağacı taze bir dizine açılır, hash'i (A)'daki `toy_tree_sha256` |
| #hedefler #drift | iki hedefte ruleset'ler (`tohum/25a`), yazar App'i yalnız ikisinde, kopyada Actions kapalı; `targets[]` özette; genesis bu gerçekleri API'den okur ve hash'ler. Bu, yazma modunun Aşama 0'daki tek denetimidir; her devirdeki `drift.check` P1'le gelir |
| #genesis | iki hedefte genesis: hakem ağacı, tohum dönemi, politika, özet, (A) sonucu ve Rekor kimlikleri, `imports.jsonl` satırı, `seed_security_ledger_sha256` ve son `row_hash`, tarif hash'i |
| #taban | mandal tabanını hakemin kendi araç koşusu genesis'te yazar; Kurucu taban veremez. K0 için taban avcı yoktur: çıta anayasal `census`'tur (`tohum/26b`) |
| #kirmizi #kanarya | her `koş`ta kırmızı kontroller kırmızı; konteyner kanaryası: ağ, dışarı yazma ve ortamdan sır okuma girişimi başarısız, dışarıdaki hash'ler aynı (test 21'in gerçeği) |
| #getir #birim | kopyada tarif HEAD'de 3/3 yeşil, ağsız, sınırların içinde; her tarball `integrity` ile aynı |
| #merge | oyuncakta ve kopyada hazır iyi aday merge olmuş |
| #ret | oyuncakta dört kötü aday ve kopyada bir kötü aday beklenen nedenle reddedilmiş |
| #oracle-ayirt #mandal #sifir-test | her merge'de §0.8 madde 3, 5, 6 |
| #kapsama-kaydi | her birleşen hunk'ta `hunk_covered` yazılı (`unmeasured` nedenli); kapılamaz |
| #nobetci #hayatta | her merge'den sonra nöbetçi yeşil; merge'ler PASS satırına kadar geri alınmamış. Anayasal hayatta kalma penceresi (`tohum/07`) Aşama 1 çıkışında ölçülür |
| #geri-alma | oyuncakta en az üç ekilmiş kötü merge (`test_regression`, `build_break`, `lint_regression`), her biri geri alınmış, `cause` anahtarla aynı; taahhüt koşudan önce zincirde, açılım eşleşiyor. Kategori başına ≥ 3 ve karışıklık matrisi Aşama 1 çıkışında (`tohum/22a`) |
| #model #belirtec #prompt | kanarya çağrısı: sunulan model istenenle aynı, `--max-budget-usd` uygulanmış, `cost` satırı yazılmış; sır desenli prompt gönderilmemiş |
| #kok | iki hedefte zinciri tohumun kodu da doğrular; her devrin kökü imzalı ve Rekor'da |
| #durum | her devirde `status.md` bloğu |
| #main #guvenlik-yolu | `main`'e, güvenlik yoluna ve hariç yollara yazım 0 |
| #pass | PASS satırını döngü hakemi oyuncak hedefin `brain/state`'ine yazar; kopyanın genesis ve merge satırlarının hash'lerini taşır. Çıkış raporu onun kopyasıdır ve `asama-0/` altına tarihli sayfa olarak girer; güven kökünü (önyükleme hakemi, tohum vektörleri, tohum rakibi, operatör aktarımı), insan dokunuşu sayısını ve kopyada ilk canlı merge'e kadar oturum ve USD'yi yazar |

**Kilidin açılışı.** Operatör `stage-open` komutunu koşar: PASS satırını okur, zinciri tohum koduyla ve
kökü Sigstore ile doğrular, `setup/stage.json`'a `{stage: 1, pass_row_sha256, toy_state_head,
copy_state_head, import_line_sha256}` yazar; operatör inceler ve iter (dokunuş). Önyükleme hakemi her
`pull`'da onu okur: Aşama 1 tablosu ve `stage: 1` testleri yalnız ondan sonra geçerlidir. Döngünün
zamanlayıcısı `control.json` `loop_schedule: true` ile açılır.

**Başarısızlık.** (A) kırmızıysa Kurucu düzeltir ve yeni SHA için yeniden ister. (B) kırmızıysa sistem
sert durur; operatör aktarım commit'ini `git revert` eder; itme yargıcı aktarımdan etkilenmediği için
Kurucu'nun yolu açık kalır; düzeltilmiş SHA'nın aktarımı yine dokunuştur. (A)'dan sonra `referee/`'ye
dokunan push `referee_changed_after_exit`'tir; yalnız `candidates/` ve `targets/` değişebilir.

PASS bir imza değil, bu koşulların makine doğrulamasıdır. PASS'ten sonra hakem kodu yalnız operatör
aktarımıyla, bir parti ya da aşama çıkışında değişir (`tohum/01a`).
