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
| `koş` | Yok | Tekerleklerin lisans kapısı (`24`; hakemin kendi Sigstore tekerlekleri de kurulmadan önce geçer, kaydı `requirements/licenses.json`); kırmızı kontroller, `snowball-tests.json` bildirimindeki Aşama 0 testleri (`asama-0/09`), vektörler ve kendi haritasının üreticisi (`29t`), her biri `--network none --cap-drop ALL --read-only --user 65534` konteynerde. **Bildirim komutunun süresi** (operatör yanıtı, arayüz olgusu, seed-081): `snowball-tests.json`'un her komutu ayrı ayrı, paylaşmadan en çok hakem reposunun operatör dosyası `bootstrap.json`'un `limits.test_timeout_s` saniyesi koşar (bugün 600; dosya operatörün ve herkese açıktır); aşan komut öldürülür, satırı `exit` 124 ve `timed_out: true` taşır ve test kırmızıdır; sonucun her test satırı `duration_ms`'i ve `timed_out`'u yazar. Komutlar yere göre dört parçaya bölünür, her parçanın işi en çok 60 dakikadır (`workflow/bootstrap.yml`). Yerel bir koşucu bu sınırı dosyadan okur, varsaymaz |
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

**Rakip çağrısı.** Rakip `requirements/claude-cli/`'de pinli `claude` CLI'sidir; yerleşik araç, ayar kaynağı, slash
komutu ve oturum kaydı yoktur, tavan `--max-budget-usd`'dir. İstem: koltuk metni, protokol, değişen yollar, ilgili
sayfalar, açık iddialar, son kabulden bu yana `--binary` diff. İstemin Unicode kod noktası sayısı `bootstrap.json`
`limits.max_prompt_chars`'ı aşarsa rakip çağrılmaz (`prompt_too_large`); sonucun `rival` kaydı her koşuda
`prompt_chars`, `prompt_diff_chars` ve `prompt_max_chars` taşır. Commit ağacını yalnız `rival_mcp.py`'nin `read_file`,
`grep`, `glob`'uyla salt okur, kararı `submit_verdict` ile verir (`init` olayından kanıtlanır). Sunulan model farklıysa,
ret, bütçe ya da tur sonu ve biçimsiz karar `unresolved`'dır; yedek model yoktur. Kesinti (`api_error`, `24`) aynı
SHA'da üçüncüden sonra günde bir, en çok 7 gün denenir, sonra görünür durur. 400/404/413/422 `request_rejected`'dır:
değerlendirilmiş sayılır, Kurucu'ya yazılmaz. İzolasyon hatası operatör için durdurur. Sır desenli metin: `29e`.

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
sonucunu kullanır. **Kanarya** (seed-058): hakem çıkış isteğinde ayrı, sırsız ve izinsiz `kanarya` işinde beynin `referee/` ağacından `python -m runner.contained run`'ı konteynerin dışında, oyuncağın birim tarifinin imajında bir kez koşturur (kanarya komutu: ağ, dışarı yazma, ortam okuma girişimi; kırmızı kontrolle); koşu geçerli değilse ya da kanarya kırmızıysa istek `exit.missing`'de `canary:<durum>` taşır, koşu yine imzalar (`29z`). Sonuç "aktarılabilir"dir, `referee/` ağaç hash'ini ve `repeat_events`'i taşır (`25a` 1). **Çıkıştan sonra** sabitlenen yalnız (A)'nın kabul edilen SHA'sıdır, `main` değil; sonrası `29u`'dadır (sahibin kararı 2026-11-14, E590). Kurucu (A)'dan sonra (B)'yi durduracak kendi kusurunu kanıtıyla bildirirse operatör, kanıtı doğruladıktan sonra o başı aktarmadan `reverted_exits`'e yazabilir; düzeltilmiş SHA (A)'yı yeniden ister (seed-052, E576). **Kendi başını adlandıran istek** (E630): bir commit kendi SHA'sını taşıyamaz; istek başın atası olan ve ondan başa yalnız `exit-request.json`'un değiştiği (Kurucu'nun defteri ve raporları hariç) bir commit'i de adlandırabilir ve son kabul edilmiş SHA'dan başa gelen değişiklik kod ise. Push önce kod push'u olarak yargılanır; isteğin kendi nedenleri kodu durdurmaz. Kod kabul edilmezse çıkış yargılanmaz ve sonucun `exit.not_judged`'ı `code_not_accepted`'dır. Kod kabul edilirse (A) aynı koşuda aynı baş için yargılanır: çıkış SHA'sı baştır, rakibin bu koşudaki artefaktı onundur, modülsüz kırmızı her MF içindir, kanarya koşar; isteğin kendi nedenleri, kodun sormadığı modülsüz kırmızı ve (A)'nın eksikleri `exit.reasons`'tadır, karar kodunkidir. Hiçbiri yoksa sabitlenen bu baştır (`exit_accepted_sha`, `exit.brain_sha`; `exit.pinned_sha` isteğin `sha`'sıdır); kabul edilmeyen istek reddedilmiş istek gibi hatırlanır. Son kabul edilmiş SHA'yı adlandıran istek eskisi gibidir; kodla gelen başka her istek `exit_request_not_alone`'dur.

**Asla yapmadıkları.** Hedefe, beyin ve hakem reposuna yazmaz; merge etmez; Kurucu'nun kodunu sırlı işte koşturmaz;
Actions önbelleği kullanmaz; kill switch açıksa iş başlatmaz. Rakip freni dolunca baş tüketilmez, yoklama uyarıyla
geçer; aynı baş ay dönünce ya da fren yükselince kendiliğinden yargılanır (`29e`). Aşama 0'da Gözcü yoktur, bütçe
dondurması buradadır; `monthly_cap_ci_minutes` ölçülmez (fren GitHub harcama sınırıdır, `25` 8). Politikadan okudukları,
hepsi `constitutional` altında (`29v`): `monthly_cap_usd`, açık aşamanın `stage_budgets.asama_<k>.rival_usd`'si (`26e`),
`stage_params.{rival_min_attempts, repeat_reject_limit}`, `license_allowlist`, `license_exceptions`.
