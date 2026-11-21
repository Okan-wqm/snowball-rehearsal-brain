# Değişiklik Günlüğü — Tohum, 2.2'nin Dokuzuncu Kayıtları

Tarih: 2026-11-21 · Sürüm: 2.2
Okunma: bir sayfanın geçmişi aranırken
Çapa: git geçmişi ve zincirdeki spec hash satırları

- 2.2 (2026-11-21, E680–E684; tohum dönemi AA; bağımsız inceleme ekibi kararı, sahibin yetkisiyle operatör kararı).
  **İlk iş** (`25` 10b; Kurucu'nun dersi f1741). Teslimden itibaren önyükleme hakeminin hiçbir denetimi kırmızı
  olmaz: `required.json`'un Aşama 1 satırı on iki yoldur (Aşama 0 ile yirmi üç) ve beynin 7757204'teki politika
  okuması iki fikstürde de hepsini adlandırır. Bu dönemin cümleleri kabul edilmiş kodun
  (7757204) şu okumalarından ayrılır; her biri ilk iştir:
  1. `policy.json`'un kesirleri altı ondalıklı dizgidir ve kayan nokta `policy_invalid:<yol>`'dur; bugün dört kesir
     okuması JSON kayan noktası okur: `constitutional.confidence_level`, `constitutional.regression_freeze.revert_rate`,
     `performance.rules.drift_bound` ve `performance.rules.seat_similarity` (`01c:48-51`, `26h:56-72`).
  2. Birincil ref `evidence_refs[0]`'dır ve yalnız o sınırlıdır; bugün bulgu ancak her ref uzunsa reddedilir
     (`26h:58-60`).
  3. Dev raporunun grup tabanı yoktur, `census_min_groups` `exit.sample`'ındır; bugün dev raporunun tabanıdır
     (`26h:67-68`).
  `freeze` ve `lift` satırının biçimi Kurucu'nun MF7'de kurduğu biçimdir ve değişmez (`26i:13-23`).
  Yeni `26i` "Şemalar, Devam: Gözcü'nün Satırları ve Görünümleri" ve `28a` "Dondurma, Devam: Aşama 1'de Gözcü"
  (`26`, `26a`, `28` onlara işaret eder); `01c` "Politikanın sayıları" ve "Okumalar ve nedenler"; `26h` "Harness'in
  politika değerleri ve birincil ref"; `29v` "Döngüde eksik anahtar" ve Aşama 1'in yedi Gözcü yolu; `18a`
  `regression_freeze`'in dört yaprağı, `18b` `genesis_drafts`'ın iki yaprağı; `25` 10b "İlk iş" kuralı; `25`,
  `26c`, `26e`, `asama-1/13d` hizalandı. Ertelenenler (operatör kararı, sahibin yetkisiyle): L1 salınım birikimi,
  L2 Actions dakikasının kaynağı, L3 sonda döngüsü (`28a:47-55`). Politika fikstürlerinin kesirleri dizgidir.
  Yanıtlanan raporlar:
  `seed-082-drift-baseline-fields-without-a-read-or-a-computable-recipe` → `01c:27-63`, `01c:65-76`;
  `seed-083-primary-evidence-ref-and-harness-policy-value-forms-unstated` → `26h:56-72`, `29v:58-61`;
  `seed-084-gozcu-triggers-thresholds-and-row-shapes-unstated` → `26i`, `28a`, `18a:32`, `18b:37`, `29v:52-56`;
  `seed-085-gozcu-wiring-what-a-freeze-closes-and-what-a-cycle-measures` → (a) `26i:13-23` (kurulan biçim), (d)
  `28a:51-53`, (e) `26i:45-47`, (g) `28a:54-55`, (h) `26i:24-30` (satır; operatörün yeniden başlatma kaydı yanıtsız),
  (i) `26i:38-40`, (k) `29v:58-61`; (b) bütçe dondurmasının harcamadan önce okunduğu adım, (c) birden çok hedefte
  ayın harcamasının nerede toplandığı, (f) merge satırında sınıf ve (j) kapanmış kapının `cause`'u yanıtsızdır, sonraki rapor masasında.
