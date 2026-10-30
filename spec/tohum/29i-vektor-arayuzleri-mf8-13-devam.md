# Vektör Arayüzleri, Devam: `refs`, `append`

Tarih: 2026-10-30 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0'ın MF9 ve MF10'unu yazarken; bu grupların komutu, girdisi ya da çıktısı değişirken
Çapa: `seed/bootstrap/vectors/vectors.json` (`refs`, `append`) ve `vectors/<grup>/` fikstürleri

---

`29h`'nin devamıdır (`root`, `flaky`, `cause`: `29j`); kuralları `29f` ve `29g`'ninkidir, beklenen değerler burada yok
(`29a`). Üretimde dış dünyaya dokunan mekanizma vektörde fikstür bir taklittir (`asama-0/14` Kum).

## `refs` (MF9, `target/write.py`)

`python -m target.write replay <api.json>`; stdin tek yazma isteği. `<api.json>` kaydedilmiş GitHub REST ve Git
Data API'sidir, `{"METHOD /yol": yanıt gövdesi}`, süreç içinde ağsız oynatılır: kaydı olan çağrı gövdesini, başka
her çağrı 404 alır; yazmalar yürütülmez, kayıttan yanıtlanır; kayıt yasak yazmaları da yanıtlar, onları yalnız modül
reddeder. İstek `{op, …}`; yollar `/repos/{repo}` altında: `branch {repo, ref, sha}` → `POST /git/refs {ref, sha}`;
`update {repo, ref, sha}` → `PATCH /git/refs/<ref, refs/ öneksiz> {sha, force: false}`; `pr {repo, head, base,
title}` → `POST /pulls`; `check {repo, sha, name, conclusion}` → `POST /check-runs`; `merge {repo, pr}` → `GET
/pulls/{pr}`, sonra `PUT /pulls/{pr}/merge`; `revert {repo, merge_sha, onto, ref}` → `GET /git/commits/{merge_sha}`,
`GET /git/commits/<ilk ebeveyni>`, `GET /git/ref/<onto, refs/ öneksiz>`, `POST /git/commits {message, tree: ilk
ebeveynin ağacı, parents: [onto'nun başı]}`, `POST /git/refs {ref, sha: yeni commit}`. **Ref kuralı:** yazılan her
ref `refs/heads/brain/` ile başlar, `refs/heads/`'den sonraki bileşenleri boş, `.` ya da `..` değil; büyük-küçük harf
duyarlı. Kural `branch`, `update` ve `revert`'ün `ref`'ine, `pr`'nin `head` ve `base`'ine, `merge`'ün yazdığı PR'nin
kayıttaki `head` ve `base`'ine uygulanır (merge base'i yazar); reddedilen istek yazma çağrısı yapmaz. Çıktılar
gönderilen isteklerdendir, kayıttaki yanıtlardan değil: `ok` (kuraldan geçti, her çağrı yanıtlandı); `refs` (oluşan
ya da güncellenen ref'ler, sıralı: `POST git/refs` gövdesinin `ref`'i, `PATCH git/refs` yolu `refs/<yol>`, merge
edilen PR'nin kayıttaki base'i `refs/heads/<base>`); `writes` (GET dışı her çağrının `METHOD /yol`'u, çağrı
sırasıyla; yol `/repos/` ile başlar); `commit` (`revert`'te `POST git/commits` gövdesinin `{tree, parents}`'ı, yoksa
`null`); `forced` (bir `PATCH git/refs` gövdesi `force: true` taşıdı mı; zorla itme yoktur, `07`); retle `refs` ve
`writes` `[]`, `forced` yanlış. Çıkış: 0 yazıldı; 1 ref kuralıyla ret; 2 kullanılamaz istek ya da 404.
Vakalar: `revert_first_parent_tree` geri alma commit'inin ağacı merge'ün ilk ebeveyninin ağacı (Git Data API'sinden),
ne kendi ağacı ne ikinci ebeveyninki; ebeveyni `onto`'nun başı, yazılan tek ref `brain/` altındaki dal; `refuse_main`
kaydın kabul edeceği `refs/heads/main` güncellemesi yazmadan ret; `update_never_forces` `brain/c/*` dalının
güncellemesi zorlamaz (o dalların `non_fast_forward` kuralı yok, `01b`); `refuse_prefix_lookalike` metin olarak
`refs/heads/brain` ile başlayan, `refs/heads/brain/` altında olmayan ref ret; `refuse_dotdot` `..` bileşeniyle
`brain/`'den çıkan ref ret; `refuse_merge_into_main` istek ref adlandırmasa da kayıttaki base'i `main` olan PR'nin
merge'ü, PR okunduktan sonra yazmadan ret; `refuse_pr_into_main` `brain/`'den `main`'e PR ret. `check` vakasız.

## `append` (MF10, `ledger/append.py`)

`python -m ledger.append cycle <defter.jsonl> <önceki.jsonl>`; stdin `{"rows": [satır, …]}`, devrin satırları (`26`)
`prev_hash` ve `row_hash` olmadan. Defter `brain/state` başındaki, önceki son doğrulanmış sürümdür. Sırayla: (1) stdin
okunmadan önce: defter geçerli zincirdir (`29a`) ve öncekinin yalnız eklemeli uzantısı, önceki her satır yerinde bayt
bayt aynı (`01b`; kanonik eşitlik yetmez, önceki yalnız bayt olarak karşılaştırılır); değilse hiçbir şey yazılmaz,
istek kullanılamaz olsa da hakem sert durur (`13`). JSON nesnesi olmayan satır zinciri kırar: spec bunu adlandırmaz,
defter JSONL'dir (`13`) ve tutmayan denetim sert duruştur (`01b`); seçim. (2) Her yeni satır
`secrets.scan`'in `row` anlamıyla taranır (`29f`, kaçışlar çözülmüş); eşleşme hiçbir şey yazmaz, koşuyu geçersiz
kılar (`08`), sert duruş değil. (3) `proposed_by` taşıyan satır `trust` `inferred` ile saklanır (`26`; değerin biçimi
serbest). (4) Satırlar stdin sırasıyla son satıra zincirlenir, bölümü ne olursa olsun (`13`). (5) Yazarla tek
`brain/state` commit'i; yazar commit sayan bir taklittir (`asama-0/14` Kum), diske ve ağa dokunulmaz. Çıktı: `ok`;
`row_hashes` (saklanan satırlarınki, stdin sırasıyla); `commits`; `hard_stop` (zincir kırık ya da yalnız eklemeli
değil); retle `[]`, 0. Çıkış: 0 yazıldı; 1 ret, sert duruş dahil; 2 kullanılamaz girdi: okunamayan dosya, ya da
(1) tuttuktan sonra `{rows: […]}` olmayan stdin, `prev_hash` ya da `row_hash` taşıyan ya da `row_id`'si tekrarlanan
satır. `chain`'in kendi arayüzü `python -m ledger.chain verify <dosya> --previous <dosya>` (`29a`, MF1) de bu grupta
sınanır, yalnız `valid` karşılaştırılır.
Vakalar: `cycle_one_commit` iki bölümün iki satırı tek devirde sırayla zincirlenir, devir tek commit yapar;
`chains_onto_current_tip` önceki sürümden beri büyümüş defterde yeni satır defterin son satırına zincirlenir;
`refuse_broken_tip` öncekini bayt bayt uzatan ama son satırı hash'ten sonra düzenlenmiş defter: yalnız eklemelilik
geçirirdi; `refuse_unparsable_ledger` yazılırken kesilmiş son satır: JSON Lines olmayan defter kullanılamaz girdi
değil, zincir kırığıdır; `refuse_broken_chain_first` kurcalanmış defter kullanılamaz istekle gelse de sert duruş;
`refuse_rewritten_history` hash'i yeniden hesaplanmış eski satır, kendi başına geçerli zincir;
`refuse_reserialized_row` anahtarları başka sırada yazılmış satır, kanonik biçim aynı, baytlar başka;
`refuse_secret_row` `\u` kaçışıyla yazılmış sahte belirteç çözülmüş satırda yakalanır, sert duruş değil;
`proposed_by_stored_inferred` verilen `trust` ne olursa olsun `inferred`, hash saklanan satırın; `chain_previous_rewrite`
ve `chain_previous_truncated` yeniden yazılmış ya da son satırını yitirmiş dosya öncekinin uzantısı değil.
