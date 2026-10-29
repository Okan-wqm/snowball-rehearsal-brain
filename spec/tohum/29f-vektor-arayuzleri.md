# Vektör Arayüzleri: `secrets`, `contained`, `profile`

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0'ın MF2, MF3 ve MF4'ünü yazarken; bu grupların komutu, girdisi ya da çıktısı değişirken
Çapa: `seed/bootstrap/vectors/vectors.json` (`secrets`, `contained`, `profile`) ve `vectors/<grup>/` fikstürleri

---

`29d`'nin veri gruplarının Kurucu'ya dönük arayüzü; devamı (`npmlock`, `recipe`, `diffguard`) `29g`'dedir. Her
grubun komutu, girdisi, karşılaştırılan alanları, çıkış kodları ve vakalarının neyi yakaladığı burada; beklenen
değerler burada değildir (`29a`: vektörler tabandır, yeter değildir). Karşılaştırma kuralları `29d`'dedir.

- **Ajan yapılandırması** (`14`): büyük-küçük harf gözetmeden bir bileşeni `.claude`, `.vscode` ya da
  `.devcontainer`, ya da son bileşeni `CLAUDE.md`, `AGENTS.md`, `.mcp.json` ya da `.envrc` olan yol.
- **Kapsama:** `e` girdisi `p` yolunu kapsar ⇔ `p == e.rstrip('/')` ya da `p`, `e.rstrip('/') + '/'` ile başlar;
  büyük-küçük harf duyarlı, yol yazıldığı gibi. Sıralı listeler kod noktası sırasındadır.

## `secrets` (MF2, `gate/secrets.py`)

`python -m gate.secrets scan <diff|row|prompt> <dosya>`; stdin yok. Dosya UTF-8 okunur (değilse girdi
kullanılamaz); satırlar LF ile ayrılır, 1'den sayılır, son LF'den sonraki boş parça satır değildir. `diff`:
birleşik git diff'inin bütün metni (başlık, bağlam, silinen ve eklenen satırlar). `row`: JSON Lines, satır başına
bir defter satırı (`26`); her satır JSON nesnesi olarak çözülür, şemaya bakılmaz (`row_hash` henüz olmayabilir),
içindeki her dizgi (anahtar ve değer, kaçışlar çözülmüş) ayrı taranır; nesne olmayan ya da boş satır girdiyi
kullanılamaz yapar. `prompt`: metnin bütünü. **Biçimler, MF2'nin tabanı:** GitHub klasik belirteci, `gh[pousr]_`
ve ardından 36 `[A-Za-z0-9]`, iki yanında sınır aranmaz (kelimeye yapışık olan da eşleşir); AWS erişim anahtarı
kimliği, `AKIA` ya da `ASIA` ve ardından 16 `[A-Z0-9]`, iki yanında başka `[A-Za-z0-9]` yok (`_` harf değildir).
Uyan her değer sayılır, entropisi ve FAKE ya da EXAMPLE işareti ne olursa olsun; Kurucu fazlasını yakalayabilir.
Çıktı: `clean` (girdi kullanılabilir ve hiçbir yerde eşleşme yok), `lines` (eşleşmenin başladığı satırlar,
`row`'da satırın JSONL satırı; sıralı, tekil; temizse `[]`); eşleşen metin ve desen adı yazılmaz (`30c`). Çıkış: 0
temiz; 1 eşleşme (koşu geçersiz, prompt gönderilmez); 2 kullanılamaz girdi, satır yine `{"clean": false}`.
Vakalar: `diff_added_line` eklenen satırdaki sahte belirteç yakalanır, satırı yazılır, değeri yazılmaz;
`diff_context_line` bağlam satırındaki anahtar kimliği de koşuyu geçersiz kılar; `row_json_escape` defter satırı
çözüldükten sonra taranır, `\u` kaçışıyla yazılmış kimlik kaçmaz; `prompt` giden prompttaki belirteç yakalanır;
`prompt_clean` temiz prompt geçer; `glued_token` `_` ile kelimeye yapışık belirteç ve kimlik yakalanır;
`clean_near_miss` yakın ıskalar (`ghq_`, 15 karakterlik kimlik) ve FAKE kelimesi eşleşme değildir;
`row_unusable_fails_closed` çözülemeyen satır temiz sayılamaz.

## `contained` (MF3, `runner/contained.py`)

`python -m runner.contained argv`; stdin tek koşu isteği `{image, cmd[], uid, worktree, outdir, artefacts[],
env{}, services[], operating}` (`operating` `26c`'nin `{anahtar: {value, band}}` biçiminde). Komut koşacağı
`docker run` argv'sini kurar, docker'ı koşmaz, isteğin host yollarına bakmaz, diskte bir şey yaratmaz. Zorunlu:
`--network none`, `--cap-drop ALL`, `--read-only`, `--user <uid>`, bellek sınırı
`operating.container_mem_bytes.value` (`08`; `26c`: sabit yoktur); `--privileged` ve `--cap-add` yok; yazılabilir
yalnız worktree ve çıktı dizini, artefaktlar salt okunur, başka bağlama ve tmpfs yok; kapsayıcı ortamı tam olarak
isteğin `env`'i. Ret (sessizce düzeltmek değil): imaj `<ref>@sha256:<64 küçük onaltılık>` değil; `ACTIONS_*`
değişkeni; docker soketi; `services` boş değil (Aşama 0 birimleri servissizdir); `container_mem_bytes` yok. Çıktı
argv'nin izdüşümüdür: `ok`; `network` (son `--network`/`--net` değeri, yoksa `default`); `cap_drop`, `cap_add`
(sıralı); `privileged`, `read_only`; `uid` (`--user`'ın `:` öncesi, sayı); `memory_bytes` (bayt); `mounts`
(bağlama başına `[kaynak, "ro"|"rw"]`, kaynağa göre sıralı; tmpfs `["tmpfs:" + hedef, "rw"]`); `env_names`
(sıralı); `image`; `argv` (karşılaştırılmaz). Çıkış: 0 argv kuruldu; 1 ret; 2 kullanılamaz girdi; 1 ve 2'de satır
`{"ok": false}` (serbest `reason`).
Vakalar: `argv_baseline` geçerli istek zorunlu bayrakları, istekten okunan bellek sınırını, yalnız iki yazılabilir
dizini, salt okunur artefaktı, isteğin ortamını ve pinli imajı taşır; `argv_second_request` başka bir istek kendi
izdüşümünü verir, sabit bir argv ikisini tutamaz; `refuse_unpinned_image`, `refuse_actions_env`,
`refuse_docker_socket`, `refuse_services` ve `refuse_missing_mem_limit` adlarındaki istekler reddedilir.

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
`differs:unit_candidates` (listeler farklı), `narrows:security_paths`, `narrows:excluded_paths` (türetilen bir yol
öneride yok). Yalnız genişleten önerinin vakası yok: `14`'ün genel cümlesi farklı her öneriyi reddeder, özel kuralı
genişletmeye izin verir; ikisi hizalanana kadar her okuma geçer. Çıkış: `derive` 0, okunamayan girdide 2; `check` 0
kabul, 1 ret, 2 kullanılamaz girdi. Vakalar: `agent_config_case_insensitive` ajan yapılandırması her derinlikte ve
harf büyüklüğünde hariç; `operator_excluded_paths` operatörün hariç yolu dil eklemez, adayını düşürür;
`security_keyword_substring` anahtar kelime yol ve dosya adlarında alt dizgi olarak aranır;
`unit_candidates_order_and_filter` adaylar operatörün sırasını korur, olmayan, ajan yapılandırması ve hariç aday
düşer; `reject_narrowed_excluded` hariç listesini daraltan öneri ret; `reject_different_languages` dilleri farklı
öneri ret.
