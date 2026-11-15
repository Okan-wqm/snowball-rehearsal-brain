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
`deps.fetch`, `run.contained` ya da `unit.verify` olan anahtarlardır; sonraki aşamanın satırı o aşamanın tohum dönemiyle
gelir.

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
hafızasında sayılır (`29b`).

**Okunuş.** `29t` "Okunuş" gibidir: bulgu yalnız testleri koşulan push'ta vardır, kırmızı push'ta da koşu yapılır;
Docker'ın kendi hatası (125) bulgu değil kesintidir (`kos:docker`). Geçmek, komutun adlandırdığı değerlerin kendi
yollarından geldiğini söyler; döngünün her okumasının komutta adlandırıldığını söylemez (E589).
