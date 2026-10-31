# Vektör Arayüzleri, Devam: `root`, `flaky`, `cause`

Tarih: 2026-10-30 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0'ın MF11, MF12 ve MF13'ünü yazarken; bu grupların komutu, girdisi ya da çıktısı değişirken
Çapa: `seed/bootstrap/vectors/vectors.json` (`root`, `flaky`, `cause`) ve `vectors/root/` fikstürleri

---

`29i`'nin devamıdır; kuralları `29f`, `29g` ve `29k`'ninkidir, beklenen değerler burada yok (`29a`). Üretimde dış
dünyaya dokunan mekanizma vektörde fikstür bir taklittir (`asama-0/14` Kum).

## `root` (MF11, `ledger/anchor.py`)

`python -m ledger.anchor root <defter.jsonl>`; `python -m ledger.anchor anchor <signer.json>` (stdin `{"root": <64
küçük onaltılık>}`); `python -m ledger.anchor verify <defter.jsonl> <root.jsonl> <rekor.json>` (stdin `{"identity":
<pin>}`). `root` → `tips` (var olan her bölüm için son satırının saklı `row_hash`'i) ve `root` (`tips`'in RFC 8785
baytlarının sha256'sı, `13`). `anchor`: `<signer.json>` taklit imzalayıcı `{available, identity, uuid}`, doğrulanmış
bir Sigstore paketinin yerine (sahte kriptografi yok); erişilebilirse `entry` `{uuid, hash: kök, identity}`, değilse
`null` ve sert duruş (`28`); çıktı `ok`, `hard_stop`, `entry`. `verify` (sonraki devrin D1'i) `<root.jsonl>`'ın
(zincirli `{row_id, ts, root, rekor_uuid, prev_hash, row_hash}` satırları, `27a`) yalnız son satırını ve kaydedilmiş
`<rekor.json>`'ı `{entries: {uuid: {hash, identity}}}` (`13`) okur; çıktı `valid` ve sıralı `reasons`: `root_mismatch`
(defterin kökü kayıttakinden farklı); `entry_missing` (`rekor_uuid` defterde yok; o zaman öbür ikisi değerlendirilmez);
`entry_root_mismatch` (girdinin `hash`'i kayıttaki kök değil); `identity_mismatch` (girdinin kimliği pin değil).
Çıkış: `root` 0; `anchor` 0, imzalanamazsa 1; `verify` 0 geçerli, 1 geçersiz; hepsinde 2 kullanılamaz girdi.
Vakalar: `part_tips` iç içe bölümlerde uç ne dosyanın son satırı ne bölümün ilk satırı; `anchor_signs_root` imzalayıcı
kökü yük olarak imzalar, girdinin uuid'i, hash ve kimlik döner; `unsignable_hard_stop` imzalanamayan kök sessizce
geçmez; `verify_good` defterin kökü son kayıttaki kök ve adlandırılan girdi onu pinli kimlikle imzalar;
`verify_tip_moved` çapadan sonra uç ilerlemiş; `verify_identity_pin` girdiyi pinli olmayan bir iş akışı kimliği yapmış;
`verify_entry_other_root` kayıt doğru kökle başka kökü imzalayan girdiyi adlandırır; `verify_entry_missing` defterde
olmayan girdi: çapalanmamış kök denetlenmemiş değil, geçersiz.

## `flaky` (MF12, `gate/sentinel.py`)

`python -m gate.sentinel decide`; stdin `{"runs": [{"results": [{id, status: pass|fail}]}, …]}`: merge'den sonra
`brain/integration`'ın yeni başında etkilenen testlerin ilk koşusu, sonra taze kapsayıcıda yeniden koşuları. En az bir
sonucu olan, `fail`'siz ilk koşu yeşildir, sonrakiler okunmaz. Değilse (bir `fail` ya da sıfır test, `04`) 3/3 kuralı
uygulanır (`07:27`); `04a:24`'ün üç koşusuna ilk koşunun girip girmediğini spec söylemez. Seçim: 3/3 ilk koşu artı üç
yeniden koşudur, çünkü `07` doğrulamayı kırmızı koşudan sonraya koyar: ilk dördü değerlendirilir; dörtten azsa karar
`rerun`. Dördüyle `red` her koşuda, `flaky` bazılarında düşüp hepsinde düşmeyen kimlikler; koşuda olmayan test orada
düşmemiştir. `red` boş değilse (ya da hiçbir koşunun sonucu yoksa) karar `red`, değilse `flaky`; `revert` yalnız
`red`'de doğru. Çıktı `verdict` (`green` | `red` | `flaky` | `rerun`), sıralı `red` ve `flaky` (`green` ve `rerun`'da
`[]`), `revert`. Çıkış: 0 yeşil, 1 değil, 2 kullanılamaz girdi.
Vakalar: `green_first_run` testli ve hepsi geçen ilk koşu yeşil; `one_red_run_never_reverts` tek kırmızı koşu karar
değil, test adlandırılmaz; `two_reruns_rerun` ilk koşu ve iki yeniden koşu yetmez, hepsinde düşen test henüz
adlandırılmaz; `red_three_reruns` ilk koşuda ve üç yeniden koşuda düşen test kırmızı, merge geri alınır;
`per_test_rule` kural test başına: her koşuda düşen kırmızı, yalnız ilkinde düşen flaky, ikisi de adlandırılır.

## `cause` (MF13, `gate/revert.py`)

`python -m gate.revert cause`; stdin `{"red_tests": […], "impact": […], "build_ok": bool, "lint": {araç: {"before":
int, "after": int}}}`: doğrulanmış kırmızı testler (MF12'nin `red`), merge'de bildirilen etki kümesi (Aşama 0'da
birimin servissiz testleri), kodun kırmızı başta derlenip yüklendiği, her aracın merge'ün ilk ebeveynindeki ve
baştaki toplamı. Tutan ilk kural: `build_break` (`build_ok` yanlış); `lint_regression` (bir aracın `after`'ı
`before`'undan büyük; araç başına, `asama-0/08` 5); `test_regression` (bir kırmızı test kümede); `impact_miss`
(kırmızı test var, hiçbiri kümede değil); değilse `unknown`. Çıktı `cause` (`26`); çıkış 0, kullanılamaz girdide 2.
Geri almanın kendisi `refs`'in `revert` işlemidir; girdileri grubun dışında üretilir (spec `build_ok`'un üreticisini
ve nöbetçinin lint toplamını henüz adlandırmaz). Vakalar: `test_regression` kırmızı test kümede; `impact_miss` kümenin
dışında; `build_break_first` derlenmeyen kodda kırmızı testler onun sonucudur; `lint_regression` test ve derleme temiz,
araç toplamı arttı; `lint_per_tool` bir aracın düşüşü başkasının artışını kapatmaz; `unknown` mekanik açıklama yok.
