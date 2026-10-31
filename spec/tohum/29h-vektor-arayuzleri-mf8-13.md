# Vektör Arayüzleri: `k0map`

Tarih: 2026-10-30 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0'ın MF8'ini yazarken; bu grubun komutu, girdisi ya da çıktısı değişirken
Çapa: `seed/bootstrap/vectors/vectors.json` (`k0map`) ve `vectors/k0map/` fikstürleri

---

`29f`, `29g` ve `29k`'nin devamıdır, kuralları onlarınki (`refs`, `append`: `29i`; `root`, `flaky`, `cause`: `29j`);
beklenen değerler burada yok (`29a`). Üretimde dış dünyaya dokunan mekanizma vektörde fikstür bir taklittir
(`asama-0/14` Kum).

## `k0map` (MF8, `gate/check.py`)

`python -m gate.check map <diff.patch> <yol> <satır>` (stdin yok) ve `python -m gate.check decide <aday_dizini>
<taban.jsonl> <aday_koşu_dizini> <hashes.json>` (stdin tek JSON nesnesi). Diff `29k`'deki gibi okunur (`diff --git
a/A b/B` bloğu B'yi değiştirir); yalnız `<yol>`'un hunk'ları sayılır. **Eşlenmiş satır** (`asama-0/08`): hunk
`@@ -a,b +c,d @@` (sayı yoksa 1); taban aralığı bağlam dahil `[a, a+b-1]`, aday aralığı `[c, c+d-1]`. Bir taban
aralığındaki `L` o hunk'ın aday aralığının tamamına eşlenir (`d = 0` ise `[]`); başka her `L` `[m, m]`'ye,
`m = L + Σ(d−b)`, toplam taban aralığı `L`'den önce biten hunk'lar üzerinden. `b = 0` olan hunk'ın taban aralığı
yoktur: git `a` satırından sonraki eklemeyi `-a,0` yazar; hunk `a` ile `a+1` arasındadır, `a < L` ise önce biter.
`map` → `mapped`: `[ilk, son]` ya da `[]`. `decide`: `<aday_dizini>` `finding.json` (`26c`) ve `diff.patch`
taşır; karar bulgudan yalnız `rule_id`, `path` ve `line`'ı okur: `fix` hakemin kendi taban koşusundandır,
`tool_output_sha256` okunmaz (`asama-0/08` 4, `26a`). `<taban.jsonl>` taban ağaçta, `<aday_koşu_dizini>/cand.jsonl`
aday ağaçta üç lint koşusudur, satır başına bir koşu; `<aday_koşu_dizini>/checks.json` `{tests: [{id, status:
pass|fail}], red_control: pass|fail}` (aday ağaçta etkilenen testler, aynı `koş`un bilinen-kötü adayı). Koşu satırı
normalleştirilmiş kayıttır (spec araç çıktısının biçimini vermez): `{tool, violations: [{rule_id, path, line, fix:
[ilk, son] | null}]}`, `fix` iki ucu dahil taban satırları. Üç satırı olmayan koşu dosyası kullanılamaz; koşu okuyan
her koşul dosyanın ilk satırını okur. `<hashes.json>` üç `koş` dosyasının baytlarının sha256'sı (`{"base.jsonl",
"cand.jsonl", "checks.json"}`, küçük onaltılık, kapsayıcı dışında alınır, `08`). stdin `{control: control.json
nesnesi, unfinished_sentinels: [merge sha]}`. **Nedenler, hepsi yazılır:** `artefact_hash_mismatch` (üç `koş`
dosyasından biri yok ya da sha256'sı başka; her biri denetlenir); `target_not_found` (`base.jsonl`'da bulgunun
`rule_id`, `path` ve `line`'ı olan ihlal yok; hedefsiz `not_distinguished` ve `scope_violation` değerlendirilmez);
`not_distinguished` (`cand.jsonl`'da hedefin `rule_id` ve `path`'i olan bir ihlal hedef satırın eşlenmiş aralığında);
`tool_nondeterministic` (taban ya da aday dosyanın, ikisi de denetlenir, üç satırı bayt bayt aynı değil);
`scope_violation` (diff başka yola dokunur; silinen satırın taban numarası hedefin taban `fix`'i `[s, e]` dışında;
eklenen satırın taban konumu `p`, hunk'ında sıradaki taban satırı, son taban satırından sonra `a+b`, `b = 0`
hunk'ında `a+1`, `s ≤ p ≤ e+1` dışında; ya da hedefin `fix`'i `null`; bağlam satırına bakılmaz); `ratchet_increase`
(bir araç aday dosyada tabandakinden çok ihlal sayar; araç başına, kural başına değil; olmayan araç 0); `zero_tests`
(`tests` boş); `tests_red` (bir `fail`); `red_control_green` (`red_control` `pass`); `merge_paused`
(`control.merge_paused` `false` değil: `true`, yok ya da başka değer, `26c`); `sentinel_pending`
(`unfinished_sentinels` boş değil); `secret_in_diff` (`diff.patch` `secrets.scan diff`'ten temiz geçmez; MF8 MF2'yi
çağırır). Karar yalnız neden yoksa `merge`. Çıktı `decision` (`merge` | `reject`), sıralı ve tekil `reasons`.
Çıkış: `map` 0, kullanılamaz girdide 2 (ayrıştırılamayan diff, pozitif tamsayı olmayan satır); `decide` 0 merge, 1
ret, 2 diff, koşu dosyası, `checks.json` ya da stdin anlatıldığı gibi değilse (satır `{"decision": "reject"}`).
`asama-0/08` 1'in başa uygulama denetimi bu modülündür, saf karara girişi yazılana kadar vakasız; `secret_in_diff` de.

Vakalar: `map_shift` hunk dışındaki satır yolun, önünde biten hunk'larının net sayısı kadar kayar; `map_inside_hunk`
taban aralığındaki satır hunk'ın aday aralığının tamamına eşlenir, kaymış tek satıra ya da hunk içindeki konumuna
değil; `map_insertion_point` saf eklemenin (`b = 0`) `a` satırı kaymaz, ekleme ondan sonradır; `map_deleted_line`
saf silmenin (`d = 0`) silinen satırı `[]`'ye eşlenir, boşluktan önceki aday satırına ya da ters bir aralığa değil;
`map_after_pure_hunks` iki saf hunk'ın ardındaki satır ikisinin net sayısı kadar kayar, ekleme de sayılır; `merge`
madde 3–8 tutar (hedef eşlenmiş aralıktan gitmiş, aynı kuralın kaymış eski ihlali aralık dışında, kural değişse de
araç toplamı aynı, koşular aynı, diff `fix` içinde, testler yeşil, kontrol kırmızı, duraklatma ve açık nöbetçi yok,
hash'ler tutar); `artefact_hash_mismatch` hash'i tutmayan `koş` dosyasına güvenilmez; `forged_candidate_run` `koş`ta
temiz bir koşuyla değiştirilmiş aday koşusu, manifestoda gerçeğinin hash'i: yarım düzeltme merge olmaz;
`forged_checks` hepsi geçer diye yeniden yazılmış `checks.json` da güvenilmez; `not_distinguished` bölünen satırda
kalan ihlal aday aralığında, hedef satırın kendisi, kaymışı ve hunk içindeki konumu onu kaçırır;
`insertion_not_distinguished` hiçbir şey düzeltmeyen, hedef satırın ardına yalnız yorum ekleyen aday: `b = 0` hunk'ı
hedeften önce bitmez, ihlal eşlenmiş aralıkta kalır; `target_not_found` taban koşusunun vermediği satırı adlandıran
bulguya güvenilmez; `tool_nondeterministic` JSON değeri aynı, bir boşluk baytı farklı aday koşusu;
`base_nondeterministic` aynısı taban koşusunda; `scope_violation` diff `fix` dışındaki bir satırı da yazar,
`finding.json`'ın geniş `fix_range`'i sayılmaz; `insertion_past_fix` `fix`'i düzelten diffin `e+1`'in ötesine
(`b = 0` hunk'ında `a+1`) eklediği satır; `ratchet_and_broken_test` mandal artışı ve düşen test ikisi de yazılır;
`red_control_green` bilinen-kötü kontrol yeşil; `fail_closed_controls` `merge_paused`'suz `control`, bitmemiş nöbetçi
ve sıfır test birlikte.
