# Politika Okuması: Anahtarın Yolu ve Döngünün Okumaları

Tarih: 2026-11-14 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: `policy.json`'dan değer okuyan kod ya da test yazılırken ve bir `policy_reads_*` bulgusu okunurken
Çapa: `seed/bootstrap/snowball_bootstrap/policyreads.py`; `seed/bootstrap/vectors/policy/`; `parts.py`; `decide.py`

---

`29b`'nin `koş` işinde, `29t`'nin yanında koşan bir denetimdir; aynı kurallar geçerlidir (Kurucu raporu seed-053, E588).

**Yol.** `policy.json`'un kökünde yalnız `constitutional`, `operating` ve `performance` vardır (`26b`). Her anahtarın
tam yolu bölümüyle başlar; `18a` ve `18b`'nin anahtar sütunu onu böyle yazar
(`constitutional.stage_budgets.asama_0.canary_usd`, `operating.kos_wall_s`), başka sayfada bölümsüz geçen ad o yoldur.
Kökte ya da başka bölümde aynı adı taşıyan anahtar o anahtar değildir ve onun yerini tutmaz.

**Oturumun kopyası.** Hakem reposunun `policy.json`'u eşik ve frenleri taşır, sır taşımaz. Her oturum onu bayt bayt
`/work/logs/policy.json`'da görür (`24a` 3): katı JSON nesnesi (aynı anahtar iki kez geçmez, `NaN` yok), en çok 256 KiB,
sır deseni ve hedef adı taşımayan dosya. Başka bir dosyanın kopyası yoktur; başlatıcı operatörü uyarır ve uyarı nedenin
sınıfını adlandırır, metni yazmaz.

**Komut.** `python -m policy.reads <dosya>`, `referee/` dizininde. Son standart çıktı satırı tek JSON nesnesidir: alan
adları döngünün `policy.json`'dan okuduğu her değerin tam yoludur, değerleri döngünün o yolda okuduğu JSON değeridir
(alt ağaç olabilir), türüyle. Dosyada olmayan yol `null`'dır; yerine başka yerdeki bir değer verilmez. Komut adı tohumun
seçimidir (`29f`'nin komutları gibi).

**Fikstürler** (`seed/bootstrap/vectors/policy/`; oturumda ve hakemin kumunda `/vec/policy/`). `policy.json`: `26b`
biçiminde, `18a` ve `18b`'nin her anahtarı kendi yolunda. `policy_hoisted.json`: aynı dosya, aşamanın zorunlu yolları
bölümlerinden çıkarılmış ve köke, bölümsüz yollarına başka değerlerle konmuş. `required.json`: aşama başına zorunlu
yollar; bir aşama önceki aşamalarınkini de okur. Aşama 0'ın on bir yolu `18a`'da okuyanı `llm.call`, `profile.derive`,
`deps.fetch`, `run.contained` ya da `unit.verify` olan anahtarlardır (P3 MF2'nin okuduğu iki fren anahtarı dışında,
aşağıda). Aşama 1'in satırı (bağımsız inceleme ekibi kararı, 2026-11-20, seed-076) harness'in beş yoludur:
`constitutional.confidence_level` ve `constitutional.stage_params`'ın `census_min_groups`, `planted_max_cases`,
`evidence_ref_max_lines`, `match_window_lines`'ı; sonraki aşamanın satırı o aşamanın tohum dönemiyle gelir.

**Koşu.** Testleri koşulan her push'ta komut `29t`'nin kumunda iki kez koşar: `policy.json` ve `policy_hoisted.json`
ile.

**Bulgular.** Ad `<ad>:<yol>` biçimindedir; komut cevap vermediyse yol `referee/policy/reads.py`'dir.

- `policy_reads_failed`: ilk koşu sıfırla bitmedi, süre doldu ya da son satır tek JSON nesnesi değil.
- `policy_reads_unsectioned`: yolun ilk anahtarı üç bölümden biri değil.
- `policy_reads_unknown`: yol `policy.json`'da yok (sayfası olmayan anahtar).
- `policy_reads_wrong_value`: değer `policy.json`'un o yoldaki değeri değil.
- `policy_reads_required_absent`: zorunlu bir yol ne kendisi ne nokta sınırında bir atasıyla adlandırılmış.
- `policy_reads_root_fallback`: ikinci koşu zorunlu bir yolu kökteki değerle verdi.

**Aşama.** Aşama 0'da bulgu imzalı sonucun `warnings`'ine yazılır; karar, ret nedenleri, seriler ve imzalı çıkış
değişmez. Kilit Aşama 1'i açınca aynı ad ret nedenidir, `ref`'i yoldur; Kurucu'nun düzeltebildiği rettir ve ret
hafızasında sayılır (`29b`). Y döneminin tesliminden Aşama 1'in beş yolu okunması zorunlu yollardır: beynin politika
okuması onları adlandırana kadar üzerlerindeki `policy_reads_required_absent` kırmızıdır (seed-076).

**Gözcü'nün yolları** (bağımsız inceleme ekibi kararı (2026-11-21), seed-084). AA döneminden Aşama 1'in satırında
Gözcü'nün yedi yolu da vardır: `constitutional.monthly_cap_usd`, `constitutional.regression_freeze`'in `min_merges`,
`window_days`, `revert_rate` ve `min_reverts`'ü, `constitutional.gate_rules.soft_freeze_limit` ve
`performance.windows.measure` (`28a`); teslimden itibaren onlar da okunması zorunlu yollardır. Fikstürlerin kesirleri
`01c`'nin altı ondalıklı dizgileridir (seed-082).

**Döngüde eksik anahtar** (bağımsız inceleme ekibi kararı (2026-11-21), seed-083, seed-084). Aşama 1'in satırındaki
bir yol döngünün okuduğu `policy.json`'da yoksa ya da biçim dışıysa politika kullanılamaz: döngü ilk yazımından önce
temiz durur, yolu adlandırır ve hiçbir şey yazmaz. Olmayan yol tüketicisine asla `None` ya da varsayılan olarak
verilmez; asla "yargılanmadı, devam" değildir (`18a`: anahtarı olmayan eşik yoktur).

**Okunuş.** `29t` "Okunuş" gibidir: bulgu yalnız testleri koşulan push'ta vardır, kırmızı push'ta da koşu yapılır;
Docker'ın kendi hatası (125) bulgu değil kesintidir (`kos:docker`). Geçmek, komutun adlandırdığı değerlerin kendi
yollarından geldiğini söyler; döngünün her okumasının komutta adlandırıldığını söylemez (E589).

**P3'ün yolları** (rapor masası uzlaşısı (2026-11-23), P1 çıkış dönemi). `constitutional.stage_params.fix_call_max_usd`,
`constitutional.stage_params.fix_call_max_s` ve `performance.rules.probe_cycle` P3'ün tablosu açılınca okunması zorunlu
yollar olur, bu dönemin tesliminde değil: o zamana kadar `required.json`'da değildir ve hiçbiri
`policy_reads_required_absent` kırmızısı vermez. Fikstürler iki fren anahtarını teslimden taşır (`26s`).
