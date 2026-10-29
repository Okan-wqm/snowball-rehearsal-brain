# Önyükleme Hakemi: Aşama 0'ın Yargıcı

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: kurulumda ve Aşama 0 boyunca
Çapa: `seed/bootstrap/` (kod, iş akışı ve testleri); hakem reposundaki kopyası

---

Aşama 0'da Kurucu hakemi yazar; o hakem henüz yoktur, Kurucu da kendi yargıcı olamaz (Y6). Boşluğu tohumla
gelen, Kurucu'dan önce ve Kurucu olmayan bir yazarca yazılmış küçük, deterministik önyükleme hakemi
kapatır: beyin reposunun `seed/bootstrap/` dizininde `snowball_bootstrap` paketi (yalnız standart
kütüphane), `workflow/bootstrap.yml`, hash'e sabitli `requirements/` (Sigstore, `claude` CLI), `vectors/`
ve `tests/`. Operatör kurulumda hakem reposuna kurar (`25` 3); Kurucu ona yazamaz. Aşama 0 çıkışındaki
aktarım bu paketin `import` komutudur; Kurucu'nun betiği (`asama-0/14` 30) sonraki çıkışlarda kullanılır.

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
paketi); her koşu onu kimlik doğrulamasıyla açar, doğrulanamaz ya da yoksa durur. Başlangıç durumunu (ilk
kabul edilmiş SHA özetteki tohum commit'i) yalnız operatörün `setup/summary.json`'daki ilk koşu işareti
kurar; kurtarma `25`'tedir. Sonuç önceki sonucun hash'ini taşır, koşu yalnız en yeni durumu okuduysa yazar
(karşılaştır-ve-yaz). Boşta 7 günde bir, kill switch'ten bağımsız bir adım durumu aynen yeniden yükler.

**Üç tür push.** Yalnız `spec/asama-*/` ve `spec/INDEX.md` değiştiren push **spec isteğidir**: test
aranmaz, rakip çürütmeyi dener; kabul edilirse dizinin hash'i donar. Yalnız sıradaki aşamanın dizini
donabilir; donmuş dizine dokunan istek `spec_already_frozen`'dır, açılması operatör kararıdır. Tohumdaki
Aşama 0 spec'i düzeltme istemiyorsa Kurucu incelemesini `spec/asama-0/CHANGELOG.md`'ye tarihli satır
olarak ekleyip iter. Yalnız `exit-request.json` değiştiren push **çıkış isteğidir**; diğer her push **kod
isteğidir**, `spec/asama-0` donmadan kabul edilmez. Değişikliksiz push değerlendirilmez; spec ile kodu
karıştıran, `seed/**`, başka `spec/` yolu ya da `.github/` değiştiren, geçmişi yeniden yazan push reddedilir.

**Rakip çağrısı.** İç kullanımda API anahtarı yoktur (satışta anahtara geçilir): rakip, operatörün
`CLAUDE_CODE_OAUTH_TOKEN`'ıyla koşan, `requirements/claude-cli/`'de sha512'yle pinli `claude` CLI'sidir;
yerleşik araç, ayar kaynağı, slash komutu ve oturum kaydı yoktur, tavan `--max-budget-usd`'dir. Artefaktı
(son kabul edilmiş SHA'dan bu yana tam diff) ve ilgili tohum sayfalarını görür, commit ağacını tek MCP
sunucusu `rival_mcp.py`'nin `read_file`, `grep`, `glob`'uyla salt okur, kararı `submit_verdict` ile verir
(`init` olayından kanıtlanır); `founder-ledger.jsonl` diff'ten ve ağaçtan çıkarılır. Sunulan model
farklıysa, ret, bütçe ya da tur sonu ve biçimsiz karar kabul değil `unresolved`'dır; yedek model yoktur.
Kimlik, kota, ağ, zaman aşımı ve 5xx kesintidir (`api_error`), ret sayılmaz: aynı SHA üçüncüden sonra
günde bir, en çok 7 gün denenir, sonra görünür durur. 400/404/413/422 `request_rejected`'dır:
değerlendirilmiş sayılır, Kurucu'ya yazılmaz, operatörü uyarır. İzolasyon hatası operatör için durdurur.

**Kabul.** Kod SHA'sı: Aşama 0 testleri yeşil; vektörler geçer ve değiştirilmiş girdiyi reddeder; kırmızı
kontroller doğru; rakip geçerli karar verdi; ne yeni bir çürütme ne durumda tutulan kanıtlanmış kusur
yeniden üretildi (`refutation_still_reproduces`, `29`). Testler kırmızıysa rakip çağrılmaz. **Ret
artefaktı** tiplidir: `{sha, kind, reasons: [{kind, test_id?, ref, detail_sha256, detail?}]}`.

**Ret hafızası.** Kurucu'nun düzeltebildiği her ret (test, vektör, lisans, yeniden üretilmiş çürütme,
`prompt_too_large`, `max_turns`) nedenlerinin imzasıyla (`tür:test`, `tür:ref`; çürütmede komut ve
beklentinin hash'i) sayılır; kabul seriyi sıfırlar. Rakibin hataları (`model_mismatch`, `malformed_verdict`,
`no_verdict`, `refusal`, `rival_missing`), bütçe ve altyapı arızası serilere dokunmaz; rakip hata serisi
operatörü uyarır. Sonuç `learning {repeated, not_learning, repeat_events}` taşır; aynı imza ardışık
`stage_params.repeat_reject_limit` rete ulaşınca `not_learning` olur ve Kurucu oturumu durur (`22a`).

**Çıkış isteği, Aşama 0 çıkışının (A) parçası.** `exit-request.json` son kabul edilmiş SHA'yı ve donmuş
`spec/asama-0` hash'ini adlandırır. Hakem testleri, vektörleri, durumdaki yeniden üreticileri koşar, açık
iddiaları listeler; `referee/`'den `python -m spec.lint spec/asama-0` boş `violations`,
`python -m gate.lock check 0 <spec_sha256> exit-request.json` `{"open": true}` vermeli (`29a`). 30 mikro
özellik bitmiş; çıkış SHA'sı ve ondan ayrı en az `stage_params.rival_min_attempts` artefakt rakipten sağ
çıkmış olmalı (tamamlanmış karar, yeniden üretilmiş çürütme yok); aynı başın yeniden denemesi saklı rakip
sonucunu kullanır. Sonuç "aktarılabilir"dir, `referee/` ağaç hash'ini ve `repeat_events`'i taşır (`25a` 1).

**Asla yapmadıkları.** Hedefe, beyin ve hakem reposuna yazmaz; merge etmez; Kurucu'nun kodunu sırlı işte
koşturmaz; Actions önbelleği kullanmaz; kill switch açıksa iş başlatmaz. Rakip bütçesi bittiyse yoklama
uyarıyla geçer; aynı baş ay dönünce ya da politika değişince kendiliğinden yargılanır. Aşama 0'da Gözcü
yoktur, bütçe dondurması buradadır; `monthly_cap_ci_minutes` ölçülmez (fren GitHub harcama sınırıdır,
`25` 8). Politikadan okudukları: `monthly_cap_usd`, `stage_budgets.asama_0.rival_usd`,
`stage_params.{rival_min_attempts, repeat_reject_limit}`, `license_allowlist`, `license_exceptions`.
