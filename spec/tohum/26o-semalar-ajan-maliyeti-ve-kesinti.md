# Şemalar, Devam: Oturumun ve Ajan Koşusunun Maliyeti, Rakip Kesintisi, Haftalık Kota

Tarih: 2026-11-22 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: bir ajan koşusunun maliyeti ya da bir `cost` satırı okunurken; `previous-session.json`, `mirror.json` ya da `cost-pending.json` okunurken
Çapa: `seed/founder/launch.py`, `seed/founder/mirror.py`, `seed/founder/prices.json`

---

`24a` 2 ve 4'ün ve `26h` "Ölçüm aynası"nın devamı (rapor masası uzlaşısı (2026-11-22), seed-097; operatör kararı,
sahibin yetkisiyle; başlatıcının üç düzeltmesini sahip onayladı). Arayüz olgularıdır; Kurucu onları okur, yazmaz.

**Oturumun maliyet satırı** (E720). CLI her tur bittiğinde bir `result` olayı yazar: `total_cost_usd` ve `modelUsage`
oturumun o ana kadarki toplamıdır, `num_turns` yalnız o turun. `kind: cost` satırının `summary`'si bütün oturumundur:
- tur sayısı bütün `result` olaylarının `num_turns` toplamıdır (birinde yoksa `unknown`);
- maliyet son olayın `total_cost_usd`'si, token toplamları son olayın `modelUsage`'ının modeller üzerinden toplamıdır;
- sonra `per model:` ile her model, adına göre sıralı: `in`, `out`, `cache_read`, `cache_write`, `costUSD` mikro
  olarak (`cost_usd_micros`) ve CLI'nin `costBasis` sözcüğü (`basis`); bilinmeyen değer `unknown`'dır.
`payload` `{summary, refs}` kalır (`26`). Bu dönemden önce yazılmış satırlar eski biçimlerindedir; defter yalnız eklenir.
Satır kabul edilmiş bir baş bekledikçe (`24a` 4) her oturumun klasöründe `/work/logs/cost-pending.json`'dadır:
`{pending: [{stamp, snapshot_id, summary, refs}], written}`, en eskisi önce, bekleyen yoksa `[]`; satır deftere
yazılınca oradan düşer. Bu dönemden önce bekletilmiş bir satır yazılmadan önce oturum günlüğünden yeniden okunur.

**Ajan koşusunun maliyeti** (E720). Başlatıcı her oturumdan önce `mirror.json` `delegation`'ının her oturumuna (en yeni
20) şunları yazar:
- `runs`: her Agent ya da Task çağrısı için bir girdi (bir alt ajanın kendi çağrısı da), çağrının `tool_use_id`'si
  `toolu_…` ile anahtarlı, çağrıların sırasıyla (oturum başına en çok 50, kalanı `runs_left_out`): `subagent_type`,
  `model` (koşunun mesajlarına hizmet eden model), `effort` (çağrınınki, yoksa `null`), `parent` (çağıran koşunun
  kimliği, oturumun kendi çağrısında `null`), `status` ve `wall_ms` (`task_notification`'dan; yoksa `unfinished`),
  `tokens` `{in, cache_read, cache_write_5m, cache_write_1h, out}`, `out_from`, `cost_usd_micros`,
  `cost_floor_usd_micros`, `cost_basis`, `not_measured`.
- Tokenlar koşunun kendi mesajlarınındır (`parent_tool_use_id`'si çağrınınki), her API mesajı kimliğiyle bir kez; iç
  içe koşu kendi girdisidir. Önde koşan bir koşunun son mesajı günlükte yoktur, kullanımı Agent çağrısının
  `tool_use_result`'ındadır ve oradan sayılır.
- Günlükteki bir mesajın `output_tokens`'ı akışın başladığı andaki sayıdır, son sayı değildir: koşunun çıktı tokenı
  günlükten okunmaz. `out`, koşu oturumda modelinin tek koşusuysa ve oturumun kendi modeli başkaysa o modelin kapanış
  `modelUsage` `outputTokens`'ıdır (`out_from: cli_model_line`), değilse `null`.
- `cost_usd_micros` türetilmiştir (`cost_basis: derived:price_table`): tokenlar çarpı operatörün fiyat tablosu
  (`seed/founder/prices.json`; `delegation.prices`'ta kaynağı ve tarihiyle, milyon token başına USD mikro), tam mikroya
  yuvarlanır; CLI'nin rakamı değildir. `cost_floor_usd_micros` aynı hesabın çıktı tokensızıdır.
- `null` değer bir `not_measured` ile gelir: `output_tokens_unlogged` (taban durur), `price_unknown:<model>` (tabloda
  satırı yok ya da oturumun kapanış `modelUsage`'ı o modele bilinen bir `costBasis` vermiyor), `no_usage`,
  `usage_unreadable`.
- `models_cli`: kapanış `modelUsage`'ı model başına (tokenlar, `costUSD` mikro olarak, `costBasis`); `session_model`
  oturumun kendi modeli. Kesinlik: model başına rakam bir koşununkine yalnız oturum o ajanı o modelde bir kez koştuysa ve
  oturumun kendi modeli başkaysa eşittir.
- Bunlar oturumun sonundaki olgulardır, sonraki oturumdan okunur; çalışan oturum yalnız kendi canlı günlüğünü okur.
  Bir satır bu değeri anarken `mirror.json`'u, oturumun damgasını ve `tool_use_id`'yi adlandırır. Değerin nasıl
  tartıldığı Kurucu'nundur (E692'nin 4. korkuluğu, E697).

**Rakip kesintisi** (E721; sayfalar onu zaten kesinti sayar: `24a` 2, `24a` "Oturumun maliyet satırı", `29b`). Her
nedeni rakibin kendi tarafındaki hatası olan sonuç (`rival_unresolved`, `ref`'i `api_error:` ile başlar ve yalıtım
hatası `api_error:isolation_…` değildir; ör. `api_error:http_429`) başı değerlendirmez: kesintidir, Kurucu'nun reddi
değildir. Kural hakeminkinden dardır: hakem bir `api_error` nedeni olan her başı değerlendirmez (`29b`), ama başka bir
nedeni de olan sonuç kesinti değil, `evaluated: false` bir rettir; başlatıcı onu her değerlendirilmemiş baş gibi yeniden
yargılatır (en çok iki kez), sonra oturum o nedenleri okur.
- Başlatıcının metrik satırı ve `previous-session.json` onu `verdict: null`, `evaluated: false`, `unjudged: {cause:
  "outage", owner: "rival"}` diye yazar. Öteki notlarda `evaluated` değerlendirilmiş baş için `true`, bilinmeyende
  `null`, `unjudged` `null`'dır. Bu dönemden önce `rejected` diye yazılmış böyle bir satır da notta kesintidir.
- `mirror.json` `per_model` onu `outages` altında sayar: hiçbir zaman bir kararda, `rejected_rows_by_reason`'da ya da
  `repeats`'te değil. Böyle bir push sonraki bir karar ancak onu değerlendirilmiş diye adlandıran bir nottan alır.
- En yeni sonuç böyle bir kesintiyken başlatıcı yeni oturum açmaz (`24a` 2): hakemi bir kez yoklar, baş
  değerlendirilince sürer, değilse 30 dakika sonra yeniden yoklar; bu bekleyiş bir döngü sayılmaz. Değerlendirilen
  başın imzalı kararı geçerlidir. Bekleyişin başını ve sonunu operatöre `pilot-log.md`'de birer satır söyler.

**Haftalık kota** (E722). Başlatıcı kotanın açılış anını "resets 3:50am (UTC)" biçiminden başka "resets Nov 25, 4pm
(UTC)" biçiminden (`<Ay> <gün>, <saat>[:dk](am|pm)`) de okur. O ana kadar bekler (tarihli açılışta en çok 8 gün);
operatörün anahtar dosyasının değişme zamanı oturumun başından beri değiştiyse (oturum sürerken konan anahtar da) bir
dakika içinde sürer (dosyanın içeriği okunmaz). Bu bir
kesintidir, Kurucu'nun boş oturumu değildir (`24a` "Oturumun maliyet satırı").

**Bağlam ve sıkıştırma** (E742, sahibin ipucu, `00g`). Başlatıcı her oturumdan önce `mirror.json`'un `context`
bölümüne en yeni 20 oturumun her biri için, transkriptin (`session-<damga>.jsonl`) oturumun kendi `compact_boundary`
olaylarından (bir alt ajanınki sayılmaz) şunları yazar: `compactions` (sayı), `first_compaction_min` (ilkinin dakikası)
ve `each`: her sıkıştırma için `minute` (oturumun damgasından, ondan önce zaman damgası taşıyan son olaya kadar, bir
ondalık), `input_tokens_before` (olayın `compact_metadata.pre_tokens`'ı; yoksa oturumun ondan önceki son kendi
mesajının giriş, önbellek okuma ve önbellek yazma tokenları) ve `tokens_from` (`pre_tokens` ya da `last_usage`);
oturum başına en çok 20, kalanı `each_left_out`. Olmayan değer `null`'dır ve nedeni `not_measured`'dadır (transkript
yok, sıkıştırma yok, zaman damgası ya da token yok). Yalnız olgudur; tanımı `seed/founder/mirror.py`'nin
`SOURCES`'undadır.
