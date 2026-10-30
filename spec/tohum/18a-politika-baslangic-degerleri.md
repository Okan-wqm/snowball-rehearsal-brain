# Politika Başlangıç Değerleri: Anayasal Bölüm

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: kurulumda `policy.json` yazılırken ve bir eşiğin ilk değeri aranırken
Çapa: beklemede: aşama 0 — hakem reposundaki policy.json; şema `26b`

---

`policy.json`'un her anahtarı burada ya da `18b`'de bir başlangıç değeriyle durur; anahtarı
olmayan eşik yoktur. Anayasal değerleri operatör kurulumda yazar (`25`); bu tablo onun önerisidir.
Performans değerleri `18b`'dedir ve `18`'deki prosedürle değişir. Adlar `26b` şemasıyla aynıdır.

## Anayasal (`constitutional`)

| Anahtar | Başlangıç | Okuyan |
|---|---|---|
| `monthly_cap_usd` | Operatör yazar; öneri 300 USD; kaçak freni (`06`) | `06`, Gözcü (`28`), önyükleme hakemi (`29b`) |
| `monthly_cap_ci_minutes` | 1.800 dk (Free özel repo kotası 2.000; açık repoda kota yok, tavan fren olarak kalır; önyükleme hakemi ölçmez, Aşama 0'da fren GitHub harcama sınırıdır, `25` 8) | `01b`, `06`, `28` |
| `session_cap_usd` | Kurucu oturumu başına 20 USD (`--max-budget-usd`); kaçak freni | `24` |
| `shares` | Keşif ≤ %30, üretim ≤ %40, ölçüm ≤ %20, genel ≤ %10 | `06` |
| `class_floors.K0` | `{kind: census, misses: 0}`; clean'de FP 0 | `19`, aşama çıkışları |
| `class_floors.K1`, `K2`, `K4` | Kural sayımı, sıfır kaçırma (deterministik sarıcı, `19`) | `19` |
| `class_floors.K5`, `K6` | `recall_lb` ≥ 0,50 (`human_fix` katmanı, ≥ 25 vaka, ≥ 10 grup); `precision_lb` ≥ 0,60 | `19`, `asama-4/08` |
| `class_floors.K3`, `K7`, `K8` | Sınıfın aşama spec'i donmadan operatör yazar; yazılmadan aşama açılmaz | `02`, `lock.check` |
| `required_exit_rows` | `18`'deki yetenek tablosu | tohumun spec denetimi, Aşama 1 çıkışından `spec.lint` (`02`) |
| `noninferiority_margin` | δ = 0,05 | `06`, `19` |
| `n_min_paired` | 45 | `06`, `19` |
| `mcnemar_min_discordant` | 8 | `12`, `17`, `19` |
| `confidence_level` | 0,90, tek yönlü | `19` |
| `look_budget` | Held-out havuzu başına 3 bakış; k. bakışta α/k | `19` |
| `survival_windows` | K0, K1, K2, K4: 72 saat; K3, K7, K8: 7 gün; K5, K6: 14 gün; yalnız uzar | `07`, `11` |
| `regression_freeze` | ≥ 50 merge varken 30 günde geri alma > %2; < 50 iken pencerede ≥ 2 geri alma | `20`, `28` |
| `cycle_caps` | Döngü başına PR ≤ 10, merge ≤ 5, CI ≤ 60 dk | `01b` |
| `daily_caps` | Gün başına PR ≤ 30, merge ≤ 15, CI ≤ 90 dk | `01b` |
| `security_keywords` | `14`'teki liste | `14`, `profile.derive` |
| `banned_phrases` | `23`'teki liste | `04a` 9, `spec.lint` |
| `stage_order` | 0 → 1 → 2 → 3 → 4 → 5 → 6 (`03`) | önyükleme hakeminin kilidi (`setup/stage.json`), sonra `lock.check` |
| `gate_rules.ratio_bootstrap_lb` | Değer / USD yolu: eşli bootstrap alt sınırı ≥ 1,2 | `12`, `17`, `19` |
| `gate_rules.membership_auc` | ε = 0,05; ≥ 200 aday; α = 0,10 | `19` (kendi-test 18) |
| `gate_rules.audit_sample` | Gizli tohumla %10 tekdüze denetim; bütçe ≥ 40 çözülmüş denetimden sonra | `19` |
| `gate_rules.promotion` | ≥ 4 repo hepsi lehte ya da ≥ 5; repo başına δ = 0,05; BH q = 0,10 | `21a` |
| `gate_rules.soft_freeze_limit` | Pencerede 2'den fazla yumuşak dondurma → sert duruş | `28` |
| `gate_rules.containment_freeze` | Aynı pencerede 2 kapsayıcılık ihlali → yumuşak dondurma | `08`, `28` |
| `gate_rules.gross_delete_cap` | Aday başına brüt silme ≤ 200 satır; sınıf istisnası yoktur | `04a` 9 |
| `gate_rules.lesson_drill` | k = 20 eşli örnek; derssiz kol ≥ 14 kırık; ≥ 8 uyuşmaz çift; tam tek yönlü McNemar p < 0,10, yön dersten yana; kredi Newcombe %90, plasebo %99; kol ≥ 8 | `22a`, `29c` |
| `gate_rules.context_drill` | İki oyuncak hedef; hedef başına ≥ 8 uygun örnek; zararlı enjeksiyon 0 | `22a` |
| `gate_rules.genesis_drill` | Prova penceresi 20 koşu; büyüme ve yeniden yazım `12`'nin kabul yolundan; budamada iki ablasyon; sessizlikte ACTIVE 0 | `12a` |
| `license_allowlist` | `MIT`, `MIT-0`, `BSD-2-Clause`, `BSD-3-Clause`, `0BSD`, `Apache-2.0`, `ISC`, `PSF-2.0`, `Python-2.0`, `Unlicense`, `CC0-1.0`, `Zlib`, `MPL-2.0`; GPL, LGPL, AGPL, SSPL, BUSL, ticari olmayan, tescilli ve bulunamayan lisans listede yoktur | `24`, `29b` |
| `license_exceptions` | Boş. Operatör tek bir `ad==sürüm` için incelediği ifadeyi kanıtıyla yazar (`{expression, evidence}`); ifade yine listeden geçer | `24`, `29b` |
| `stage_params.census_min_groups` | 45 modül grubu ya da mevcut olanın tamamı | `asama-1/13a`, `exit.sample` |
| `stage_params.planted_max_cases` | Snapshot başına 5 vaka | `asama-1/13c` |
| `stage_params.evidence_ref_max_lines` | Birincil ref ≤ 30 satır | `asama-1/13d` |
| `stage_params.match_window_lines` | K3 ve üstü eşleme penceresi ±15 satır | `asama-1/13e` |
| `stage_params.rival_min_attempts` | Aşama başına rakipten sağ çıkmış 5 ayrı artefakt, artefakt başına 1 deneme | `asama-0/10`, `29`, `29b` |
| `stage_params.repeat_reject_limit` | Aynı imzalı 3 ardışık ret → `not_learning` | `24`, `29b` |
| `stage_budgets` | Aşama sayfalarının bütçe tabloları; toplamdır, aylık tavan ayrıca bağlar. Değerler kaçak frenidir, kısıt değil (`06`). Güvenlik avcısının kendi satırı `<aşama>.security_hunter_usd`'dir; yazılmamışsa avcı koşmaz | aşama bütçe sayfaları, P1'den Gözcü, önyükleme hakemi (`29b`), güvenlik avcısı (`30f`) |
| `stage_budgets.asama_0.founder_usd` | Başlangıç fren değeri 220 USD; ölçüm ~22 oturumdur, kapı değil | başlatıcı (`24`), `asama-0/12` |
| `stage_budgets.asama_0.rival_usd` | Başlangıç fren değeri 25 USD | önyükleme hakemi (`29b`), `asama-0/12` |
| `stage_budgets.asama_0.canary_usd` | Başlangıç fren değeri 1 USD; çağrı başına ayrıca `--max-budget-usd` | `llm.call`, `asama-0/12` |

## İşletim sınırları (`operating`)

Döngünün karşılaştırdığı her kaynak sınırı `operating{key: {value, band}}` anahtarıdır; sabit yoktur.
Başlangıç değerini ve bandı operatör yazar; değer bandın içinde iki yöne oynar (Y11), kalite eşikleri
gibi yalnız sıkılaşmaz. Aşama 0'da sınır kendini ayarlamaz; ayarı P1'le gelir (`asama-1/13`). Sınıra
takılan iş `limit_hit:<anahtar>` nedenidir, Kurucu'ya sayılmaz, `status.md`'de görünür. Okuyanlar
`run.contained`, `unit.verify` ve `deps.fetch`'tir (`asama-0/14`).

| Anahtar | Neyi sınırlar |
|---|---|
| `unit_inputs_bytes` | Birimin `inputs` kapanışının boyutu |
| `deps_bytes` | `getir`'in içerik adresli bağımlılık artefaktı; büyük kök kilitte ilk ölçümle bandın içine çekilir |
| `worktree_bytes` | Koşu başına taze host dizini (`08`) |
| `container_mem_bytes` | `koş` kapsayıcısının belleği |
| `kos_wall_s` | `koş` işinin duvar saati |
| `test_total_s` | Birimin testlerinin toplam süresi |
| `output_bytes` | Bir komutun sonuç dosyaları |
