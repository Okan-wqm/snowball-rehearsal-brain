# Vektör Arayüzleri, Yol Kuralları: `profile`, `diffguard`

Tarih: 2026-10-30 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0'ın MF4 ve MF7'sini yazarken; bu grupların komutu, girdisi ya da çıktısı değişirken
Çapa: `seed/bootstrap/vectors/vectors.json` (`profile`, `diffguard`) ve `vectors/<grup>/` fikstürleri

---

`29f`'nin devamıdır; ajan yapılandırması, kapsama ve sıralama `29f`'deki gibidir, karşılaştırma kuralları
`29d`'dedir.

## `profile` (MF4, `profile/derive.py`)

`python -m profile.derive derive <ağaç.tar.gz> <operator.json>` ve `python -m profile.derive check <ağaç.tar.gz>
<operator.json> <öneri.json>`; stdin yok. `referee/profile/` düzenli pakettir (`__init__.py`; yoksa standart
kütüphanenin `profile` modülü kazanır). Ağaç, üyeleri göreli POSIX adlı dosyalar olan gzip tar'dır (dizin üyeleri
yok sayılır), bellekte okunur. `operator.json`: `{security_keywords[], excluded_paths[], unit_candidates[]}`
(`18a`, `26c` `targets[]`). Dosya ajan yapılandırmasıysa ya da bir `excluded_paths` girdisinin kapsamındaysa
hariçtir. Diller hariç olmayan dosyaların uzantısından: `.py` python; `.js .mjs .cjs` javascript; `.ts .tsx .mts
.cts` typescript; başkası yok. Güvenlik dosyası: küçük harfli göreli yolu küçük harfli bir anahtar kelimeyi alt
dizgi olarak içeren, hariç olmayan dosya. Birim adayı operatörün sırasıyla kalır, kendisi (dosya kuralıyla) hariç
değilse ve ağaçta bir dosyayı (hariç olsa da) kapsıyorsa. `derive`: `languages`, `security_paths`,
`excluded_paths` (sıralı), `unit_candidates`. `check` aynı dört listeli öneriyi türetimle karşılaştırır:
`accepted` (`reasons` boşsa doğru), sıralı `reasons`: `differs:languages` (kümeler farklı),
`differs:unit_candidates` (listeler farklı: başka sıra da, eklenen aday da), `narrows:security_paths`,
`narrows:excluded_paths` (türetilen bir yol öneride yok). Öneri yalnız iki yol listesini genişletebilir (`14`):
türetilmemiş bir yol eklemek, ağaçta olmasa da, neden değildir.
Çıkış: `derive` 0, okunamayan girdide 2; `check` 0 kabul, 1 ret, 2 kullanılamaz girdi. Vakalar:
`agent_config_case_insensitive` ajan yapılandırması her derinlikte ve harf büyüklüğünde hariç;
`operator_excluded_paths` operatörün hariç yolu dil eklemez, adayını düşürür; `security_keyword_substring` anahtar
kelime yol ve dosya adlarında alt dizgi olarak aranır; `unit_candidates_order_and_filter` adaylar operatörün
sırasını korur, olmayan, ajan yapılandırması ve hariç aday düşer; `reject_narrowed_excluded` hariç listesini
daraltan öneri ret; `reject_narrowed_security` iki listeyi genişletip türetilen bir güvenlik yolunu düşüren öneri
yalnız güvenlik yollarını daralttığı için ret; `accept_widened` güvenlik ve hariç yollara birer türetilmemiş yol
ekleyen, yalnız genişleten öneri kabul, türetilen bir güvenlik yolunu da düşüren değişmiş girdisi ret;
`accept_widened_outside_tree` eklenen yolun ağaçta olması gerekmez; `reject_different_languages` dilleri farklı
öneri ret; `reject_reordered_unit_candidates` türetilen adayları başka sırayla yazan öneri ret;
`reject_added_unit_candidate` aday ekleyen öneri ret: yalnız iki yol listesi genişler.

## `diffguard` (MF7, `gate/diffguard.py`)

`python -m gate.diffguard check <diff.patch> <profile.json> <recipe.json>`; stdin yok. Diff birleşik git diff'idir;
her `diff --git a/A b/B` bloğu B yolunu değiştirir (silmede A, yeniden adlandırmada ikisini). `profile.json`
`{security_paths[], excluded_dirs[]}` (`26b`; `excluded_dirs` operatörün hariç yollarını taşır), `recipe.json`
`{unit_id, path, inputs[]}`. Değişen her yolun geçerli her nedeni, yol diff'te yazıldığı gibi (normalleştirme yok):
`symlink` (blokta `new file mode`, `new mode` ya da `index` satırında 120000); `submodule` (160000); `path_escape`
(mutlak ya da `..` bileşenli); `security_path`, `excluded_path` (bir `security_paths`, `excluded_dirs` girdisinin
kapsamında); `agent_config`; `config` (temel adı `.eslintrc`, `.eslintrc.json`, `.eslintrc.js`, `.eslintrc.cjs`,
`.eslintrc.yml`, `.eslintrc.yaml`, `eslint.config.js`, `eslint.config.mjs`, `eslint.config.cjs`, `tsconfig.json`,
`tsconfig.*.json`, `jest.config.js`, `jest.config.ts`, `vitest.config.js`, `vitest.config.ts`, `.prettierrc`,
`.prettierrc.json` ya da `biome.json`; ya da kökteki `.github/` altında); `manifest` (temel adı `package.json`);
`lockfile` (`package-lock.json`, `npm-shrinkwrap.json`, `yarn.lock`, `pnpm-lock.yaml`); `gitattributes`
(`.gitattributes`); `outside_inputs` (hiçbir `inputs` girdisi kapsamaz). Çıktı: `ok` (`reasons` boşsa doğru) ve
sıralı `reasons` (`<neden>:<yol>`). Çıkış: 0 tamam, 1 neden var, 2 kullanılamaz girdi (ayrıştırılamayan diff,
okunamayan profil ya da tarif). Diff'in `brain/integration` başına uygulanması (`asama-0/08` madde 1) bu grubun
değil, `gate.check`'in işidir (MF8; `gate.diffguard` ağaç almaz, `26a`).
Vakalar: `inside_inputs` `inputs` içindeki düz düzenleme geçer; `symlink` ve `submodule` git kipiyle tanınır,
içerikle değil; `dotdot_path` birime geri normalleşse de `../` bileşenli yol ret; `agent_config_case_insensitive`
her harf büyüklüğünde ajan yapılandırması ret; `security_path` anahtar kelime taşımasa da profilin güvenlik yolu
ret; `config_manifest_lock_gitattributes` manifest, kilit, lint yapılandırması ve `.gitattributes` her biri kendi
nedeniyle ret; `excluded_path` profilin hariç yolu ret; `every_reason` bir yolun geçerli her nedeni yazılır, yalnız
ilki değil.
