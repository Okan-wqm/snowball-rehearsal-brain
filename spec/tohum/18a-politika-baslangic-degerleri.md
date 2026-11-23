# Politika Başlangıç Değerleri: Anayasal Bölüm

Tarih: 2026-10-30 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: kurulumda `policy.json` yazılırken ve bir eşiğin ilk değeri aranırken
Çapa: beklemede: aşama 0 — hakem reposundaki policy.json; şema `26b`

---

`policy.json`'un her anahtarı burada ya da `18b`'de bir başlangıç değeriyle durur; anahtarı olmayan eşik yoktur. Anayasal
değerleri operatör kurulumda yazar (`25`); bu tablo onun önerisidir. Performans değerleri `18b`'dedir ve `18`'deki
prosedürle değişir. Adlar `26b` şemasıyla aynıdır. Tablo kesri virgülle yazar; dosyada altı ondalıklı dizgidir (`01c`).
Anahtar sütunu her anahtarı bölümüyle, tam yoluyla yazar; başka sayfada bölümsüz geçen ad bu yoldur (`29v`).
## Anayasal (`constitutional`)

| Anahtar | Başlangıç | Okuyan |
|---|---|---|
| `constitutional.monthly_cap_usd` | 10.000 USD (sahip kararı, 2026-11-19, hakem `33c01cb`: hesaplar şirketin CLI aboneliğidir, harcama frenleri sistemi durdurmaz); kaçak freni (`06`) | `06`, Gözcü (`28`), önyükleme hakemi (`29b`) |
| `constitutional.monthly_cap_ci_minutes` | 1.800 dk (Free özel repo kotası 2.000; açık repoda kota yok, tavan fren olarak kalır; önyükleme hakemi ölçmez, Aşama 0'da fren GitHub harcama sınırıdır, `25` 8) | `01b`, `06`, `28` |
| `constitutional.session_cap_usd` | Kurucu oturumu başına 20 USD (`--max-budget-usd`); kaçak freni | `24` |
| `constitutional.shares` | Keşif ≤ %30, üretim ≤ %40, ölçüm ≤ %20, genel ≤ %10 | `06` |
| `constitutional.class_floors.K0` | `{kind: census, misses: 0}`; clean'de FP 0 | `19`, aşama çıkışları |
| `constitutional.class_floors.K1`, `K2`, `K4` | Kural sayımı, sıfır kaçırma (deterministik sarıcı, `19`) | `19` |
| `constitutional.class_floors.K5`, `K6` | `recall_lb` ≥ 0,50 (`human_fix` katmanı, ≥ 25 vaka, ≥ 10 grup); `precision_lb` ≥ 0,60 | `19`, `asama-4/08` |
| `constitutional.class_floors.K3`, `K7`, `K8` | Sınıfın aşama spec'i donmadan operatör yazar; yazılmadan aşama açılmaz | `02`, `lock.check` |
| `constitutional.required_exit_rows` | `18`'deki yetenek tablosu | tohumun spec denetimi, Aşama 1 çıkışından `spec.lint` (`02`) |
| `constitutional.noninferiority_margin` | δ = 0,05 | `06`, `19` |
| `constitutional.n_min_paired` | 45 | `06`, `19` |
| `constitutional.mcnemar_min_discordant` | 8 | `12`, `17`, `19` |
| `constitutional.confidence_level` | 0,90, tek yönlü (dosyada `"0.900000"`, `26h`) | `19` |
| `constitutional.look_budget` | Held-out havuzu başına 3 bakış; k. bakışta α/k | `19` |
| `constitutional.survival_windows` | K0, K1, K2, K4: 72 saat; K3, K7, K8: 7 gün; K5, K6: 14 gün; yalnız uzar | `07`, `11` |
| `constitutional.regression_freeze.min_merges`, `window_days`, `revert_rate`, `min_reverts` | 50, 30, `"0.020000"`, 2: ≥ 50 merge varken 30 günde geri alma > %2; < 50 iken pencerede ≥ 2 geri alma (`28a`) | `20`, `28` |
| `constitutional.cycle_caps` | Döngü başına PR ≤ 10, merge ≤ 5, CI ≤ 60 dk | `01b` |
| `constitutional.daily_caps` | Gün başına PR ≤ 30, merge ≤ 15, CI ≤ 90 dk | `01b` |
| `constitutional.security_keywords` | `14`'teki liste | `14`, `profile.derive` |
| `constitutional.banned_phrases` | `23`'teki liste | `04a` 9, `spec.lint` |
| `constitutional.stage_order` | 0 → 1 kök; sonra +1 sayaç, sınıf `03`'ün önkoşul tablosundan; 6 son | önyükleme hakeminin kilidi (`setup/stage.json`), sonra `lock.check` |
| `constitutional.class_requires` | `03`'ün sınıf önkoşulları tablosu; prosedür yalnız ekler, yalnız operatör siler (Y11) | Aşama 1'den sonraki her aşama spec isteği (`03`), `drift.check` |
| `constitutional.gate_rules.ratio_bootstrap_lb` | Değer / USD yolu: eşli bootstrap alt sınırı ≥ 1,2 | `12`, `17`, `19` |
| `constitutional.gate_rules.membership_auc` | ε = 0,05; ≥ 200 aday; α = 0,10 | `19` (kendi-test 18) |
| `constitutional.gate_rules.audit_sample` | Gizli tohumla %10 tekdüze denetim; bütçe ≥ 40 çözülmüş denetimden sonra | `19` |
| `constitutional.gate_rules.promotion` | ≥ 4 repo hepsi lehte ya da ≥ 5; repo başına δ = 0,05; BH q = 0,10 | `21a` |
| `constitutional.gate_rules.soft_freeze_limit` | Pencerede 2'den fazla yumuşak dondurma → sert duruş | `28` |
| `constitutional.gate_rules.containment_freeze` | Aynı pencerede 2 kapsayıcılık ihlali → yumuşak dondurma | `08`, `28` |
| `constitutional.gate_rules.gross_delete_cap` | Aday başına brüt silme ≤ 200 satır; sınıf istisnası yoktur | `04a` 9 |
| `constitutional.gate_rules.lesson_drill` | k = 30 eşli örnek; derssiz kol ≥ 21 kırık; ≥ 8 uyuşmaz çift; tam tek yönlü McNemar p < 0,10 · 2^-i (i: aşamada açılan provanın sırası, cevap anahtarında; toplam ≤ 0,10), yön dersten yana; etki çiftinin iki kolu aynı model, çaba, tur ve bütçeyle, ders bloğu çıkarılmış prompt hash'i aynı; kredi Newcombe %90, plasebo %99; kol ≥ 8; kapsam ailenin ≥ %80'i, başka aileden 0; aile havuza ≥ 20 derssiz koşuda ≥ %85 kırıkla girer | `22a`, `22b`, `22c`, `29c`, `29q` |
| `constitutional.gate_rules.context_drill` | İki oyuncak hedef; hedef başına ≥ 8 uygun örnek; zararlı enjeksiyon 0 | `22a` |
| `constitutional.gate_rules.genesis_drill` | Prova penceresi 20 koşu; büyüme ve yeniden yazım `12`'nin kabul yolundan; budamada iki ablasyon; sessizlikte ACTIVE 0 | `12a` |
| `constitutional.license_allowlist` | `MIT`, `MIT-0`, `BSD-2-Clause`, `BSD-3-Clause`, `0BSD`, `Apache-2.0`, `ISC`, `PSF-2.0`, `Python-2.0`, `Unlicense`, `CC0-1.0`, `Zlib`, `MPL-2.0`; GPL, LGPL, AGPL, SSPL, BUSL, ticari olmayan, tescilli ve bulunamayan lisans listede yoktur | `24`, `29b`, `deps.fetch` |
| `constitutional.license_exceptions` | Boş. Operatör tek bir `ad==sürüm` için incelediği ifadeyi kanıtıyla yazar (`{expression, evidence}`); ifade yine listeden geçer | `24`, `29b`, `deps.fetch` |
| `constitutional.stage_params.census_min_groups` | 45 modül grubu ya da mevcut olanın tamamı | `asama-1/13a`, `exit.sample` |
| `constitutional.stage_params.planted_max_cases` | Snapshot başına 5 vaka | `asama-1/13c` |
| `constitutional.stage_params.evidence_ref_max_lines` | Birincil ref (`evidence_refs[0]`, `26h`) ≤ 30 satır | `asama-1/13d` |
| `constitutional.stage_params.match_window_lines` | K3 ve üstü eşleme penceresi ±15 satır | `asama-1/13e` |
| `constitutional.stage_params.rival_min_attempts` | Aşama başına rakipten sağ çıkmış 5 ayrı artefakt, artefakt başına 1 deneme | `asama-0/10`, `29`, `29b` |
| `constitutional.stage_params.repeat_reject_limit` | Aynı imzalı 3 ardışık ret → `not_learning` | `24`, `29b` |
| `constitutional.stage_budgets` | Aşama sayfalarının bütçe tabloları; toplamdır, aylık tavan ayrıca bağlar. Değerler kaçak frenidir, kısıt değil (`06`); her anahtar tek başına `monthly_cap_usd` ile karşılaştırılır, toplamları değil (`02`). Güvenlik avcısının kendi satırı `<aşama>.security_hunter_usd`'dir; yazılmamışsa avcı koşmaz, Aşama 1'de yoktur (`30f`) | aşama bütçe sayfaları, P1'den Gözcü, önyükleme hakemi (`29b`), güvenlik avcısı (`30f`) |
| `constitutional.stage_budgets.asama_0.founder_usd` | Başlangıç fren değeri 220 USD; ölçüm ~22 oturumdur, kapı değil | başlatıcı (`24`), `asama-0/12` |
| `constitutional.stage_budgets.asama_0.rival_usd` | Başlangıç fren değeri 25 USD; 2026-11-05'ten 1000 USD (sahibin kararı: rakip `claude` CLI aboneliğiyle koşar, USD freni yalnız kaçak frenidir) | önyükleme hakemi (`29b`), `asama-0/12` |
| `constitutional.stage_budgets.asama_0.canary_usd` | Başlangıç fren değeri 1 USD; çağrı başına ayrıca `--max-budget-usd` | `llm.call`, `asama-0/12` |
| `constitutional.stage_budgets.asama_1.rival_usd`, `founder_usd`, `runtime_llm_usd` | Her biri 10.000 USD (sahip kararı, 2026-11-20: harcama frenleri sistemi hiçbir zaman durdurmaz; yalnız kaçak freni; spec-071). `rival_usd` 2026-11-19'dan beri 10.000'dir (hakem `33c01cb`; önce 1000, 2026-11-05); koşu başına rakip tavanı 3 USD kalır; harcama kilidin açılışından sayılır, kilit `rival_usd`'siz açılmaz (`26e`) | önyükleme hakemi (`29b`), `stage-open`, başlatıcı (`24`), `asama-1/10` |
| `constitutional.stage_params.fix_acceptance_min`, `live_merge_min` | 0,80 (dosyada `"0.800000"`; Aşama 1 çıkışında düzeltme adaylarının kabul oranı) ve 10 (çıkışın canlı merge sayısı min(bu değer, uygun borç)'tur); spec-071. `asama-1/10`'un bulgu başı frenlerinin anahtarları aşağıdaki satırdadır (karar verildi, `26n`, seed-095) | `asama-1/08`, Aşama 1 çıkışı |
| `constitutional.stage_params.fix_call_max_usd`, `fix_call_max_s` | Çağrı başına 0,50 USD (dosyada `"0.500000"`, 0'dan büyük) ve 300 sn (1 ya da daha büyük JSON tamsayısı); başka biçim `policy_invalid:<yol>` (sahip kararı, 2026-11-23, seed-095). `asama-1/10`'un bulgu başı frenidir, `stage_budgets` değildir; P3'ün tablosu açılınca zorunlu yoldur (`29v`, `26s`) | P3 MF2: `fixer.llm` adına `llm.call` (`26s`) |

## İşletim sınırları (`operating`)
Döngünün karşılaştırdığı her kaynak sınırı `operating{key: {value, band}}` anahtarıdır; sabit yoktur.
Başlangıç değerini ve bandı operatör yazar; değer bandın içinde iki yöne oynar (Y11), kalite eşikleri
gibi yalnız sıkılaşmaz. Aşama 0'da sınır kendini ayarlamaz; ayarı P3'le gelir (`26h`). Sınıra
takılan iş `limit_hit:<anahtar>` nedenidir, Kurucu'ya sayılmaz, `status.md`'de görünür. Okuyanlar
`run.contained`, `unit.verify` ve `deps.fetch`'tir (`asama-0/14`).

| Anahtar | Neyi sınırlar |
|---|---|
| `operating.unit_inputs_bytes` | Birimin `inputs` kapanışının boyutu |
| `operating.deps_bytes` | `getir`'in içerik adresli bağımlılık artefaktı; büyük kök kilitte ilk ölçümle bandın içine çekilir |
| `operating.worktree_bytes` | Koşu başına taze host dizini (`08`) |
| `operating.container_mem_bytes` | `koş` kapsayıcısının belleği |
| `operating.kos_wall_s` | `koş` işinin duvar saati |
| `operating.test_total_s` | Birimin testlerinin toplam süresi |
| `operating.output_bytes` | Bir komutun sonuç dosyaları |
