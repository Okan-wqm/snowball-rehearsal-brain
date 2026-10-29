# Önyükleme Hakemi: Aşama 0'ın Yargıcı

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: kurulumda ve Aşama 0 boyunca
Çapa: `seed/bootstrap/` (kod, iş akışı ve testleri); hakem reposundaki kopyası

---

Aşama 0'da Kurucu hakemi yazar; o hakem henüz yoktur, Kurucu da kendi yargıcı olamaz (Y6).
Aradaki boşluğu önyükleme hakemi kapatır: tohumla gelen, küçük, deterministik bir hakem.

**Kim yazar, nerede.** Kurucu'dan önce, Kurucu olmayan bir yazarca yazılmıştır ve beyin
reposunun `seed/bootstrap/` dizinindedir: `snowball_bootstrap` paketi (yalnız standart kütüphane),
iş akışı `workflow/bootstrap.yml`, hash'e sabitlenmiş `requirements/` (Sigstore ve `claude` CLI),
makine okunur vektörler `vectors/` ve kendi testleri `tests/`. Operatör kurulumda hakem reposuna
kurar (`25` 3); Kurucu ona yazamaz (`seed/**` değiştiren push reddedilir). Aşama 0 çıkışında
aktarılan hakem onun yerini alır; aktarım betiği aynı paketin `import` komutudur (`25a` 1).

**Boru hattı.** Zamanlayıcı saatte bir, sabit bir dakikada beyin reposunun izlenen dalını
`ls-remote` ile yoklar; son kabul edilmiş ya da son değerlendirilmiş SHA'dan farklı bir SHA yoksa
hiçbir şey kurmaz ve doğrulamaz (dakika hesabı `25`'te). Yeni SHA varsa işler koşar. Kod koşturan
işin izni ve sırrı, sır taşıyan işin kod koşturması yoktur; işler arası her artefakt hash'le
doğrulanır.

| İş | Sır ya da izin | Ne yapar |
|---|---|---|
| `çek` | Okuyucu App'i; içerik ve Actions okuma | Önceki imzalı durumu Sigstore ile doğrular; SHA'yı çeker, sınıflandırır, ağacı blob blob kurar (`export-ignore` etkisizdir) |
| `getir` | Yok, ağ var | Kilit dosyalarındaki tekerlekleri `--only-binary`, `--require-hashes` ile indirir; kurulum betiği koşmaz |
| `koş` | Yok | Tekerleklerin lisans kapısı (`24`); kırmızı kontroller, bildirimdeki Aşama 0 testleri ve vektörler, her biri `--network none --cap-drop ALL --read-only --user 65534` konteynerde |
| `çağır` | `CLAUDE_CODE_OAUTH_TOKEN` | Tohum rakibi (aşağıda) |
| `yeniden` | Yok | Rakibin yeniden üreticileri, `koş` ile aynı kumda |
| `yaz` | OIDC, içerik okuma | Kararı verir, sonucu Sigstore ile imzalayıp Rekor'a bağlar, imzalı durum artefaktını yükler |

**Durum.** Hakem reposuna hiçbir iş yazamadığı için bellek, bir önceki koşunun imzalı
`bootstrap-state` artefaktıdır (`result.json` ve Sigstore paketi); her koşu onu kimlik
doğrulamasıyla açar, doğrulanamazsa durur. İlk kabul edilmiş SHA kurulum özetindeki tohum
commit'idir. Boşta geçen 7 günde bir imzalı durum aynen yeniden yüklenir.

**Üç tür push.** Yalnız `spec/asama-*/` değiştiren push **spec isteğidir**: test aranmaz, rakip
çürütmeyi dener; kabul edilirse aşama dizininin hash'i donmuş olarak duruma girer. Yalnız
`exit-request.json` değiştiren push **çıkış isteğidir** (aşağıda). Diğer her push **kod isteğidir**;
`spec/asama-0` donmadan kabul edilmez. Spec ile kodu karıştıran push reddedilir.

**Test bildirimi.** Kurucu kökte `snowball-tests.json` tutar (`26b`). Hakem yalnız oradaki
komutları, repo kökünden koşturur (vektörleri `referee/`'den); bitti denen (`done_mf`, sırayla 1'den) her mikro özelliğin `asama-0/14`'teki
test numarası bir komuta bağlı değilse ya da hiç komut yoksa sonuç kırmızıdır. Vektörler `29a`'daki
arayüzle, sahibi olan mikro özellik bitince uygulanır.

**Rakip çağrısı.** Şimdilik iç kullanımda API anahtarı yoktur, ticari kullanımda anahtara geçilir: rakip,
çağıranın oturumuyla koşan, `requirements/claude-cli/`'de sha512'yle pinli `claude` CLI'sidir. Yerleşik
araç, ayar kaynağı, slash komutu ve oturum kaydı yoktur; tek MCP sunucusu hakemin `rival_mcp.py`'sidir:
`read_file`, `grep`, `glob` yalnız çıkarılmış ağacı okur, karar `submit_verdict` ile gelir; her koşu bunu
CLI'nin `init` olayından kanıtlar (CLI ortam bilgisini ve hesap adını da ekler). API'nin döndürdüğü model
istenenden farklıysa, ret, bütçe sonu, tur sonu ya da biçimsiz karar `unresolved`'dır, yani kabul değildir;
yedek model yoktur. Kimlik, kota, ağ hatası ve zaman aşımı altyapı arızasıdır (`api_error`): ret sayılmaz,
yeniden denenir; aynı SHA'da üçüncüsünden sonra günde bir. Sır desenli metin ve karar atılır; fikstür sırları koşuda birleştirilir.

**Kabul.** Kod SHA'sı: Aşama 0 testleri yeşil; vektörler geçer ve değiştirilmiş girdiyi reddeder;
kırmızı kontroller doğru; rakip geçerli bir karar verdi ve hiçbir çürütmesi yeniden üretilmedi.
Testler kırmızıysa rakip bütçe harcanmasın diye çağrılmaz. **Ret artefaktı** tiplidir: `{sha, kind,
reasons: [{kind, test_id?, ref, detail_sha256, detail?}]}`; Kurucu nedeni oradan okur. Hakemin
kendi tekerlekleri (Sigstore) de kurulmadan önce lisans kapısından geçer; kaydı
`requirements/licenses.json`'dadır ve testi onu `sign.txt` ve `18a`'daki listeyle karşılaştırır.

**Ret hafızası.** Her değerlendirilmiş ret, nedenlerinin imzasıyla (`tür:test`, `tür:ref`; çürütmede iddianın özeti)
sayılır; kabul sayaçları sıfırlar, altyapı arızası dokunmaz. Sonuç `learning {repeated,
not_learning, repeat_events}` taşır. Aynı imza ardışık `stage_params.repeat_reject_limit` retten
geçerse `not_learning`'dir ve Kurucu oturumu durur (`22a`); çıkış bloğu `repeat_events`'i taşır.

**Çıkış isteği, Aşama 0 çıkışının (A) parçası.** `exit-request.json` son kabul edilmiş SHA'yı ve
donmuş `spec/asama-0` hash'ini adlandırır. Hakem tüm testleri ve vektörleri yeniden koşar; 30 mikro
özelliğin hepsi bitmiş, çıkış SHA'sının kendi rakip denemesi var ve ondan ayrı en az
`stage_params.rival_min_attempts` artefakt rakipten geçmiş olmalıdır. Hepsi tutarsa sonuç
"aktarılabilir" olur ve `referee/` kod ağacının hash'ini taşır (`25a` 1).

**Asla yapmadıkları.** Hedefe, beyin reposuna ve hakem reposuna yazmaz; merge etmez; Kurucu'nun
kodunu sırlı işte koşturmaz; Actions önbelleği kullanmaz; kill switch açıksa ya da bütçe bittiyse
iş başlatmaz. Okuduğu politika anahtarları: `monthly_cap_usd`, `stage_budgets.asama_0.rival_usd`,
`stage_params.rival_min_attempts`, `stage_params.repeat_reject_limit`, `license_allowlist`,
`license_exceptions`.
