# Vektör Arayüzleri, Devam: `npmlock`, `recipe`

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0'ın MF5 ve MF6'sını yazarken; bu grupların komutu, girdisi ya da çıktısı değişirken
Çapa: `seed/bootstrap/vectors/vectors.json` (`npmlock`, `recipe`) ve `vectors/<grup>/` fikstürleri

---

`29f`'nin devamıdır; ajan yapılandırması, kapsama ve sıralama `29f`'deki gibidir, karşılaştırma kuralları
`29d`'dedir.

## `npmlock` (MF5, `runner/deps_npm.py`)

`python -m runner.deps_npm fetch <package-lock.json> <ayna_dizini>`; stdin `{registry_egress[],
install_scripts_required[]}`: profilin izinli kayıt defterleri (`26b`, her biri `/` ile biter) ve tarifin kurulum
betiği işaretleri (`26c`: kilit yolu ya da `ad@sürüm`; başka eleman isteği kullanılamaz yapar). Kilit npm
`lockfileVersion` 3'tür; paketler kök `""` dışındaki `packages` girdileridir. Ayna kayıt defterinin çevrimdışı yerine
geçer: `https://<host>/<yol>` adresinin tarball'ı `<ayna>/<host>/<yol>` dosyasıdır (`asama-0/14` Kum: yerel fikstür
tarball'lar). Tarball'lar bellekte okunur; sistemin geçici dizini dışına bir şey yazılmaz. Paket başına ilk tutmayan
denetim nedendir, bu sırayla: `git_dependency` (`resolved` `git+`, `git:`, `github:` ya da `git@` ile başlar);
`file_dependency` (`file:` ile başlar, ya da `link` doğru ve hedef mutlak ya da `..` içerir); `registry_not_allowed`
(`resolved` hiçbir `registry_egress` girdisiyle başlamaz; önek bütün URL üzerinde, `/` dahil); `tarball_missing`
(aynada dosya yok); `integrity_mismatch` (ham `.tgz` baytlarının base64 sha512'si kilitteki sha512 `integrity`'den
farklı); `install_script_unmarked` (tarball'ın `package/package.json` `scripts`'inde `preinstall`, `install` ya da
`postinstall` var, ya da `package/binding.gyp` var, ya da kilit girdisi `hasInstallScript: true` diyor; ve ne kilit
yolu ne tarball'daki `ad@sürüm` `install_scripts_required`'da var). Çıktı: `ok` (hiçbir paket reddedilmedi);
`rejected` (sıralı `<neden>:<kilit yolu>`, tamamsa `[]`); `artefact`: getirilen her paketin `{"integrity":
<kilitteki>, "path": <kilit yolu>}` nesnesinden, yola göre sıralı dizinin RFC 8785 kanonik JSON'unun sha256'sı,
`sha256:` ve küçük onaltılık; `licenses`: yola göre sıralı `{path, name, version, license}`, ad, sürüm ve lisans
tarball'ın `package/package.json`'ından (lisans yoksa ya da dizgi değilse `null`; rapordur, kapı değil, `24`). Ret
olunca `artefact` ve `licenses` `null`'dır. Çıkış: 0 tamam, 1 ret, 2 kullanılamaz girdi (okunamayan kilit ya da ayna,
biçimi tutmayan stdin, ör. çıplak ad gibi işaret olmayan eleman); 2'de satır `{"ok": false}` (serbest `error`),
hiçbir paket getirilmez.
Vakalar: `integrity_good_and_one_byte` her tarball kilidin bütünlüğüne uyar, işaretli kurulum betiği geçer, içerik
adresi ve lisans raporu üretilir; değişmiş girdide tarball'ın tek baytı (gzip başlığında) değişir, içindeki tar
aynıdır; `install_script_unmarked` kilidin söylemediği, tarball'daki işaretsiz `postinstall` ret;
`install_script_marked_by_lock_path` kilit yolu da işarettir, başka paketin kilit yolu onu işaretlemez;
`bare_name_refused`, `bare_name_not_in_lock_refused`, `scoped_bare_name_refused`, `lock_path_not_in_lock_refused` ve
`root_key_refused` geçerli bir işaretin yanındaki işaret olmayan eleman (kilitteki ya da kilitte olmayan bir paketin
çıplak adı, kapsamlı paketin `@` taşıyan çıplak adı, kilitte olmayan bir kilit yolu, kök `""`) ne yok sayılır ne her
sürümü işaretler, istek kullanılamaz; yerine geçerli bir işaret yazılınca istek geçer;
`name_version_not_in_lock_marks_nothing` kilitte eşleşeni olmayan `ad@sürüm` hiçbir şeyi işaretlemez, istek geçer;
yerinde kilitte olmayan bir kilit yolu isteği kullanılamaz yapar; `registry_not_allowed` izinli kayıt defterinin
önekine benzeyen başka host ret; `git_dependency` ve `file_dependency` bütünlük değeri taşısa da ret;
`license_from_tarball` lisans kilitten değil tarball'dan okunur, hedef bağımlılığın lisansı raporlanır, kapı değildir;
`same_lock_same_address` aynı kilit başka biçimde yazılınca (sıkışık, anahtarlar başka sırada) aynı içerik adresini
verir.

## `recipe` (MF6, `profile/unit_verify.py`)

`python -m profile.unit_verify check <recipe.json> <policy.json>`; stdin yok; `referee/profile/` düzenli paket
(`29k`). `recipe.json` birim tarifidir (`26c`), `policy.json` `{operating: {anahtar: {value, band}}}` parçası.
Yalnız statik denetim (`29d`); nedenler yalnız şunlardır: `image_not_pinned` (`env_image` `<ref>@sha256:<64 küçük
onaltılık>` değil); `inputs_missing_unit` (hiçbir `inputs` girdisi `path`'i kapsamaz); `input_not_plain:<girdi>`
(mutlak, ters bölü içeren ya da `.` veya `..` bileşenli); `input_excluded:<girdi>` (girdinin kendisi ajan
yapılandırması); `cmd_empty:<alan>` (`lint_cmd`, `test_cmd` ya da `affected_test_cmd` yok, boş, dizgi olmayan ya
da boş dizgi taşıyor); `limit_key_unknown:<anahtar>` (`limits` anahtarı `operating`'de yok; değerlere bakılmaz);
`services_not_empty` (`services` `[]` değil). `<girdi>` ve `<anahtar>` tarifte yazıldığı gibidir. Çıktı: `ok`
(`reasons` boşsa doğru) ve sıralı `reasons`. Çıkış: 0 tamam, 1 neden var, 2 kullanılamaz girdi.
Vakalar: `good` eksiksiz bir Aşama 0 tarifi geçer; `image_tag_only` etiketle anılan imaj ret;
`image_digest_malformed` 63 onaltılık karakterli özet pinli değildir; `inputs_missing_unit_dir` birimin kendi
dizini `inputs`'ta olmalı; `inputs_agent_config` her harf büyüklüğünde ajan yapılandırması olan girdi ret;
`inputs_not_plain` mutlak girdi ret; `limit_key_unknown` `operating`'de olmayan sınır anahtarı ret;
`test_cmd_empty` boş `test_cmd` ret; `cmd_entries` öbür iki komut da denetlenir, her biri kendi nedeniyle.
