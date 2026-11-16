# Döngünün Koşuları: Kurucu'nun Gördüğü Son Koşular

Tarih: 2026-11-15 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: döngünün koşuları ve `/work/logs/loop-runs.jsonl` okunurken
Çapa: `seed/founder/launch.py` (`loop_runs`, `loop_note`, `strict_object`); `seed/bootstrap/tests/test_loop_runs.py`

---

Sahibin kararı (2026-11-15, E596): Kurucu döngünün koşularını operatörün gözlemini beklemeden görür. Dosya `24a` 3'ün
oturum dosyalarının (`targets.json`, `operating.json`, `policy.json`) yanındadır; hakem onu okumaz, ret nedeni ya da
kapı değildir, yetkili kayıt GitHub'daki koşu ve imzalı sonuçtur.

**Dosya.** Başlatıcı her oturumdan önce, operatörün kendi `gh` girişiyle, hakem reposundaki `loop.yml` iş akışının
`main`'deki en yeni üç koşusunu okur ve `/work/logs/loop-runs.jsonl`'a yazar; kapsüle belirteç girmez, hakem reposuna
bir şey yazılmaz. Dosya her oturumda vardır; o oturumun kopyasıdır ve başlatıcı onu geri okumaz. Satır başına bir JSON
nesnesi vardır, `kind`'ı `read`, `run` ya da `job`'dur: önce `read`, sonra en yeni koşudan başlayarak her `run` satırı
ve onun `job` satırları.

**`read`.** `read_at` (UTC), `state`, `why`, `workflow_state` (iş akışı kaydının GitHub'daki durumu: `active`,
`deleted`, ...). `state` üç değerdir: `runs` (okundu; koşu yoksa `run` satırı da yoktur), `no_loop` (`loop.yml` hakem
reposuna hiç girmedi: aktarım olmadı), `unavailable` (okunamadı; başka satır yoktur, `why` söyler: `timeout`, `gh`,
`bad_reply`, `launcher_error`). Kaydı `deleted` olan iş akışının koşuları da yazılır: geri alınmış bir aktarımın
koşuları görünür kalır.

**`run`.** `id`, `created_at`, `event`, `status`, `conclusion` (GitHub'ın değerleri; bitmemiş koşuda `conclusion`
`null`'dır), `attempt` (son deneme; `job` satırları onunkilerdir) ve `jobs_total` (GitHub'ın saydığı iş sayısı; koşu
başına en çok sekiz `job` satırı yazılır; işler okunamadıysa `null`'dır ve `job` satırı yoktur).

**`job`.** `run`, `name`, `status`, `conclusion`, `summary`, `summary_why`, `output`, `output_why`. `summary`, işin
günlüğünde `job` alanı işin adına eşit olan son JSON nesnesidir: döngü işi onu tek satırda yazar, anahtarlar sıralı
olduğundan `job` ilk anahtar olmayabilir. Değer işin yazdığıdır; başlatıcı yorum eklemez, neden yazmaz. Özet yoksa
`summary` `null`'dır ve `summary_why` söyler: `none` (günlük okundu, böyle satır yok), `unread` (günlük okunamadı ya da
iş bitmedi), `not_run` (iş koşmadı; günlüğü istenmez) ya da bir dışarıda tutma sınıfı. `output` yalnız başarısız olup
`summary_why`'ı `none` olan işte doludur: başarısız adımın kendi yazdığı son en çok beş satır (her biri en çok 300
karakter); başka işte `null`'dır. Başarısız işin satırları okunamadıysa `output` `null`'dır ve `output_why` `unread` ya
da `secret_shape`'tir.

**Dışarıda tutma.** `29v` "Oturumun kopyası" gibi sınıf yazılır, metin yazılmaz; sınıf yalnız o özeti dışarıda tutar,
satırın geri kalanı yerindedir: `too_large` (özet satırı ya da yazılmış hâli 16 KiB'tan büyük), `too_deep` (32 düzeyden
derin iç içe yapı), `duplicate_key` (bir anahtar iki kez), `non_finite` (`NaN`, sonsuz), `secret_shape` (tohum
tarayıcısının, `30c`, bir deseni; kaçışla yazılmış olsa da). Özette, `output` satırlarında, iş adında ve her alanda
hedef adı taşıyan dize `sha256:` ve ilk 16 onaltılık karakteriyle yazılır (`29e` "Genellik okuması"), dizenin dışı
yerindedir; sır deseni taşıyan iş adı `null`'dır.

**Okunamayan ve sınırlar.** Okunamayan değer `null`'dır; okunup boş çıkan değer boştur, biri ötekinin yerine yazılmaz.
En çok üç koşu ve koşu başına sekiz iş okunur; bir çağrı 30 saniyeyi, okumanın tamamı 90 saniyeyi aşmaz ve hiçbir çağrı
yinelenmez: yetişmeyen çağrının alanı okunamamıştır, sonraki oturum yeniden okur. Dosya o oturumun başındaki durumdur;
`read_at` ve `created_at` yaşını söyler. Yapıtlar (`results/`, `response/`) kopyalanmaz.

**Ne değildir.** Dosya bir karar değildir, ret nedeni üretmez, imzalı sonucun yerini tutmaz; özetin anlamı onu yazan
döngü kodunundur.
