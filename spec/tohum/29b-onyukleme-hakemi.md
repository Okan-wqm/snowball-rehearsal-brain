# Önyükleme Hakemi: Aşama 0'ın Yargıcı

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: kurulumda ve Aşama 0 boyunca
Çapa: `seed/bootstrap/` (kod, iş akışı ve testleri); hakem reposundaki kopyası

---

Aşama 0'da Kurucu hakemi yazar; o hakem henüz yoktur, Kurucu da kendi yargıcı olamaz (Y6). Boşluğu tohumla gelen,
Kurucu'dan önce ve Kurucu olmayan bir yazarca yazılmış küçük, deterministik önyükleme hakemi kapatır: beyin reposunun
`seed/bootstrap/` dizininde `snowball_bootstrap` paketi (yalnız standart kütüphane), `workflow/bootstrap.yml`, hash'e
sabitli `requirements/` (Sigstore, `claude` CLI), `vectors/` ve `tests/`. Operatör kurulumda hakem reposuna kurar
(`25` 3); Kurucu ona yazamaz. Her çıkıştaki aktarım bu paketin `import` komutudur (`25a` 1).

**Boru hattı.** Zamanlayıcı saatte bir, sabit bir dakikada beyin reposunun izlenen dalını `ls-remote` ile
yoklar; son kabul edilmiş ya da son değerlendirilmiş SHA'dan farklı bir SHA yoksa hiçbir şey kurmaz
(dakika hesabı `25`'te). Yeni SHA varsa işler koşar; her iş `main`'deki `control.json`'u canlı okur. Kod
koşturan işin izni ve sırrı, sır taşıyan işin kod koşturması yoktur; artefaktlar hash'le doğrulanır.

| İş | Sır ya da izin | Ne yapar |
|---|---|---|
| `çek` | Kimliksiz beyin okuma; Actions okuma | Önceki imzalı durumu Sigstore ile doğrular; SHA'yı çeker, sınıflandırır, ağacı blob blob kurar (`export-ignore` etkisizdir) |
| `getir` | Yok, ağ var | Kilit dosyalarındaki tekerlekleri `--only-binary`, `--require-hashes` ile indirir; kurulum betiği koşmaz |
| `koş` | Yok | Tekerleklerin lisans kapısı (`24`; hakemin kendi Sigstore tekerlekleri de kurulmadan önce geçer, kaydı `requirements/licenses.json`); kırmızı kontroller, `snowball-tests.json` bildirimindeki Aşama 0 testleri (`asama-0/09`) ve vektörler, her biri `--network none --cap-drop ALL --read-only --user 65534` konteynerde |
| `çağır` | `CLAUDE_CODE_OAUTH_TOKEN` | Tohum rakibi (aşağıda); sır desenli metin prompta girmez |
| `yeniden` | Yok | Rakibin ve durumdaki yeniden üreticiler, `koş` ile aynı kumda; gözleneni gösteren her biri boş kontrol ağacında da (`29`) |
| `yaz` | OIDC, içerik okuma | Kararı verir, sonucu Sigstore ile imzalayıp Rekor'a bağlar, imzalı durumu yükler; kill switch açıksa kabul etmeyen, harcamayı yazan `stopped` sonucu imzalar; iptal edilen koşu hiçbir şey imzalamaz |

**Durum.** Bellek, önceki koşunun imzalı `bootstrap-state` artefaktıdır (`result.json` ve Sigstore
paketi); her koşu onu kimlik doğrulamasıyla açar, doğrulanamaz ya da yoksa durur. Durum artefaktı, hakem reposunun `main`
dalındaki koşularının yaptığı, süresi dolmamış, adı tam `bootstrap-state` olan en yeni artefakttır (Actions okuma; iki
dosya: `result.json`, `result.json.sigstore.json`). Açılışı: `sigstore verify identity --bundle result.json.sigstore.json --cert-identity https://github.com/<hakem reposu>/.github/workflows/bootstrap.yml@refs/heads/main --cert-oidc-issuer https://token.actions.githubusercontent.com result.json`; doğrulanamazsa ya da yoksa okuyan durur (çıkış 2).
Son kabul edilmiş SHA `state.last_accepted_sha` alanıdır. Başlangıç durumunu (ilk kabul edilmiş SHA özetteki tohum
commit'i) yalnız operatörün `setup/summary.json`'daki ilk koşu işareti kurar; kurtarma `25`'tedir. Sonuç önceki sonucun
hash'ini taşır, koşu yalnız en yeni durumu okuduysa yazar (karşılaştır-ve-yaz). Boşta 7 günde bir, kill switch'ten
bağımsız bir adım durumu aynen yeniden yükler.

**Üç tür push.** Yalnız `spec/asama-*/` ve `spec/INDEX.md` değiştiren push **spec isteğidir**: test aranmaz, rakip çürütmeyi
dener; kabul edilirse dizinin hash'i donar. Yalnız sıradaki aşamanın dizini donabilir; donmuş dizine dokunan istek
`spec_already_frozen`'dır, açılması operatör kararıdır. Tohumdaki Aşama 0 spec'i düzeltme istemiyorsa Kurucu incelemesini
`spec/asama-0/CHANGELOG.md`'ye tarihli satır olarak ekleyip iter. Yalnız `exit-request.json` değiştiren push **çıkış
isteğidir**; diğer her push **kod isteğidir**, `spec/asama-0` donmadan kabul edilmez. Değişikliksiz push değerlendirilmez;
spec ile kodu karıştıran, `seed/**`, başka `spec/` yolu ya da `.github/` değiştiren, geçmişi yeniden yazan push reddedilir.
Kurucu kayıtları: `29e`.

**Rakip çağrısı.** İç kullanımda API anahtarı yoktur (satışta anahtara geçilir): rakip, operatörün
`CLAUDE_CODE_OAUTH_TOKEN`'ıyla koşan, `requirements/claude-cli/`'de sha512'yle pinli `claude` CLI'sidir; yerleşik araç,
ayar kaynağı, slash komutu ve oturum kaydı yoktur, tavan `--max-budget-usd`'dir. Artefaktı (son kabul edilmiş SHA'dan bu
yana tam diff) ve ilgili tohum sayfalarını görür, commit ağacını tek MCP sunucusu `rival_mcp.py`'nin `read_file`, `grep`,
`glob`'uyla salt okur, kararı `submit_verdict` ile verir (`init` olayından kanıtlanır); `founder-ledger.jsonl` diff'ten ve
ağaçtan çıkarılır. Sunulan model farklıysa, ret, bütçe ya da tur sonu ve biçimsiz karar kabul değil `unresolved`'dır;
yedek model yoktur. Kimlik, kota, ağ, zaman aşımı ve 5xx kesintidir (`api_error`), ret sayılmaz: aynı SHA üçüncüden sonra
günde bir, en çok 7 gün denenir, sonra görünür durur. 400/404/413/422 `request_rejected`'dır: değerlendirilmiş sayılır,
Kurucu'ya yazılmaz, operatörü uyarır. İzolasyon hatası operatör için durdurur. Sır desenli metin: `29e`.

**Kabul.** Kod SHA'sı: Aşama 0 testleri yeşil; vektörler geçer ve değiştirilmiş girdiyi reddeder; kırmızı
kontroller doğru; rakip geçerli karar verdi; ne yeni bir çürütme ne durumda tutulan kanıtlanmış kusur
yeniden üretildi (`refutation_still_reproduces`, `29`). Testler kırmızıysa rakip çağrılmaz. **Ret
artefaktı** tiplidir: `{sha, kind, reasons: [{kind, test_id?, ref, detail_sha256, detail?}]}`.

**Ret hafızası.** Kurucu'nun düzeltebildiği her ret (test, vektör, lisans, yeniden üretilmiş çürütme, `prompt_too_large`, `max_turns`,
`secret_in_prompt`) nedenlerinin imzasıyla (`tür:test`, `tür:ref`; çürütmede komut ve beklentinin hash'i) sayılır; kabul seriyi sıfırlar.
Rakibin hataları (`model_mismatch`, `malformed_verdict`, `no_verdict`, `refusal`, `rival_missing`, `secret_in_verdict`), bütçe ve altyapı
arızası serilere dokunmaz; rakip hata serisi operatörü uyarır. Sonuç `learning {repeated, not_learning, repeat_events}` taşır; aynı imza
ardışık `stage_params.repeat_reject_limit` rete ulaşınca `not_learning` olur ve Kurucu oturumu durur (`22a`). Sınav hatası: `29e`.

**Çıkış isteği, Aşama 0 çıkışının (A) parçası.** `exit-request.json` son kabul edilmiş SHA'yı ve donmuş `spec/asama-0` hash'ini
adlandırır. Hakem testleri, vektörleri, durumdaki yeniden üreticileri koşar, açık iddiaları listeler; aşama tablosunun
(`stages/stage0.json`, `asama-0/14`) her mikro özelliği bitmiş olmalı: `done_mf` 1'den tablonun sayısına kesintisiz (Aşama 0'da
18), değilse sonucun `exit.missing`'inde `not_all_micro_features_done`; `spec.lint` ve `gate.lock` (A)'da çağrılmaz, spec denetimi
ve kilit tohumun kodudur (`29a`, `asama-0/10`); çıkış SHA'sı ve ondan ayrı en az `stage_params.rival_min_attempts` artefakt
rakipten sağ çıkmış olmalı (tamamlanmış karar, yeniden üretilmiş çürütme yok); aynı başın yeniden denemesi saklı rakip
sonucunu kullanır. Sonuç "aktarılabilir"dir, `referee/` ağaç hash'ini ve `repeat_events`'i taşır (`25a` 1). **Çıkıştan sonra** imzalı durum (A)'nın başını `exit_accepted_sha`'da tutar; o andan spec, kod ya da çıkış push'unda Kurucu kayıtları dışında yalnız `candidates/` ve `targets/` değişebilir (`asama-0/10a`, `asama-0/11`, `25a` 8): `referee/` altındaki değişiklik `referee_changed_after_exit`, başka her yol `changed_after_exit:<yol>`'dur (Kurucu'nun nedeni). Dondurma Aşama 0'ındır: kilit sonraki aşamayı açınca ya da (B) kırmızı olup operatör aktarımı geri alıp o başı `control.json` `reverted_exits`'e yazınca biter, sonraki sonuç alanı boşaltır; düzeltilmiş SHA (A)'dan yeniden geçer (`25a` "Başarısızlık"). Kurucu (A)'dan sonra (B)'yi durduracak kendi kusurunu kanıtıyla bildirirse operatör, kanıtı doğruladıktan sonra o başı aktarmadan `reverted_exits`'e yazabilir; dondurma kalkar, düzeltilmiş SHA (A)'yı yeniden ister (seed-052, E576).

**Asla yapmadıkları.** Hedefe, beyin ve hakem reposuna yazmaz; merge etmez; Kurucu'nun kodunu sırlı işte
koşturmaz; Actions önbelleği kullanmaz; kill switch açıksa iş başlatmaz. Rakip freni dolunca baş tüketilmez, yoklama
uyarıyla geçer; aynı baş ay dönünce ya da fren yükselince kendiliğinden yargılanır (`29e`). Aşama 0'da Gözcü yoktur,
bütçe dondurması buradadır; `monthly_cap_ci_minutes` ölçülmez (fren GitHub harcama sınırıdır,
`25` 8). Politikadan okudukları: `monthly_cap_usd`, açık aşamanın `stage_budgets.asama_<k>.rival_usd`'si (`26e`),
`stage_params.{rival_min_attempts, repeat_reject_limit}`, `license_allowlist`, `license_exceptions`.
