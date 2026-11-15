# Çıkıştan Sonra: Sabitlenen SHA ve `main`

Tarih: 2026-11-14 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0'ın (A)'sı kabul edildikten sonra; (B) sürerken, yeni çıkış isteğinde, aktarımda ve `stage-open`'da
Çapa: `seed/bootstrap/snowball_bootstrap/cli.py` (`exit_pin`), `decide.py`; `seed/bootstrap/tests/test_flow.py`

---

Sahibin kararı (2026-11-14, kesin; E590): (A) kabul edilince sabitlenen yalnız kabul edilen SHA'dır, `main` değildir.
(A)'nın kendisi `29b` "Çıkış isteği"ndedir; sonrasını bu sayfa söyler. `asama-0/01` D1, `asama-0/10a` ve
`asama-0/11`'deki dondurma cümlelerinin yerini bu sayfa alır (`02` 1: tohum geçerlidir; donmuş sayfalar değişmez).

**Sabit.** İmzalı durum (A)'nın başını `exit_accepted_sha`'da tutar. Aktarım SHA'yı imzalı sonucun
`exit.brain_sha`'sından alır; (B) o SHA'nın `referee/` ve oyuncak ağacını koşar (`25a` 1-2). Alanı yalnız (A)'dan
yeniden geçip kabul edilen bir çıkış isteği değiştirir; reddedilen istek eskisini bırakır. Kilit sonraki aşamayı açınca
ya da operatör o başı `control.json` `reverted_exits`'e yazınca (`25a` "Başarısızlık"; aktarımdan önce `29b` "Çıkıştan
sonra") sonraki sonuç alanı unutur ve liste sonradan temizlense de geri gelmez. Başka hiçbir push alanı değiştirmez.

**`main` serbesttir.** Kurucu (A)'dan sonra da `main`'e iter; her push olağan yargılanır (`29b`). Spec, test, manifest,
`docs/`, oyuncak ya da `referee/` değişikliği (A)'dan sonra ret nedeni değildir: `changed_after_exit` ve
`referee_changed_after_exit` yazılmaz. Kabul edilen push `last_accepted_sha`'yı ilerletir, `exit_accepted_sha`'ya
dokunmaz; `main`'in sabit SHA'dan ileride olması olağan durumdur. Yan dal yalnız `main`'e ait olmayan işi tutar (`15`
9).

**Hakeme ne ulaşır.** Hakemin kodu yalnız aktarımla değişir (`25a` 1-4): kabul edilen bir `referee/` değişikliği de
oyuncağın ağacı da döngüye bir sonraki aktarımla ulaşır. Sabit varken push'un kendi değişiklikleri `referee/`'ye
dokunuyorsa imzalı sonucun `warnings`'inde `referee_ahead_of_exit:<sabit SHA'nın ilk 7 hanesi>` vardır: ret nedeni
değildir, karar ve seriler değişmez; `main`'deki hakem kodunun koşan hakemden ayrıldığını söyler.

**Döngü ne okur.** `çek` `candidates/` ve `targets/`'ı kabul edilmiş SHA'da (`state.last_accepted_sha`) okur. Koşan
hakem ağacı son aktarım satırının `brain_sha`'sındaki `referee/`'dir: o SHA kabul edilmiş SHA'nın kendisi ya da atasıdır
ve oradaki `referee/` hash'i satırın `referee_tree_sha256`'sıdır. Kabul edilmiş SHA'daki `referee/`'nin aktarılandan
farklı olması durdurma nedeni değildir; `asama-0/01` D1'in son hücresindeki karşılaştırmanın yerini bu cümle alır.

**Aşama kilidi.** `stage-open` beyni okumaz: PASS satırını, hedeflerin son genesis satırını ve son aktarım satırını
bağlar (`25a` 9, `26d`). `main`'in aktarılan SHA'dan ileride olması kilidi ne engeller ne açar; kilitten sonra
yargılanan ilk push Aşama 1 tablosuyla yargılanır ve sonucu alanı unutur.

**İkinci (A).** Sabit varken kabul edilen yeni bir çıkış isteği alanı yeni başla değiştirir; aktarılmış olan değişmez,
yeni baş yalnız operatör onu aktarırsa koşar. Yerine yenisi geçmiş eski bir başı `reverted_exits`'e yazmak hiçbir şeyi
boşaltmaz; kilit (B)'nin koştuğu aktarım satırını bağlar (E377).

**Geçiş.** Kararın öncesinde imzalanmış bir (A) aynen geçerlidir: durumun şeması değişmez, alan okunur ve yeniden
yargılanmaz; kararın öncesinde `changed_after_exit` ya da `referee_changed_after_exit` ile reddedilmiş bir baş yeniden
yargılanmaz, içeriği sonraki push'la gelir.
