# Değişiklik Günlüğü — Tohum, 2.2'nin Sekizinci Kayıtları

Tarih: 2026-11-20 · Sürüm: 2.2
Okunma: bir sayfanın geçmişi aranırken
Çapa: git geçmişi ve zincirdeki spec hash satırları

- 2.2 (2026-11-20, E655–E664; bağımsız inceleme ekibinin kararları, sahibin devrettiği bir operatör kararı ve sahip
  kararları): Kurucu'nun on açık raporu yanıtlandı; yalnız arayüz olguları, kodun nasıl yazılacağı Kurucu'nundur.
  Yanıtlanan raporlar:
  `seed-070-red-b-on-the-copy-base-lint-cause-not-on-the-line` → `29y:43-45` (birim dizedir; çok satırlı içerik
  ayrı dizeler olarak yazılır; E655);
  `seed-072-p2-hunter-tool-using-runtime-agent` → `30f:9-13`, `03:46-49`, `08:60-61`, `09:35-36`, `26e:39`, `26e:54-56`
  (sahibin devrettiği operatör kararı: Aşama 1'de araç kullanan çalışma-zamanı güvenlik avcısı yok, araç kullanan ilk
  ajanla en geç Aşama 4'te gelir; P2 MF2 `agent.dispatch` düştü, MF1 kalır; E656);
  `seed-073-organ-definition-layout-and-carriage-unstated` → `26e:61-63` (tanım hash'i, tek fonksiyon; E657);
  `seed-074-snapshot-case-list-and-comment-lines-unstated` → `26e:64-66` (yer tutucu türü ele vermez; vaka
  şeması `26`; boş `finding_id_patterns` geçerli; yorum satırı ertelendi; E658);
  `seed-075-dev-case-store-group-and-validity-edges-unstated` → `26e:67-70` (`<state_root>/cases/` yalnız ekleme;
  modül grubu; operatörün kuralı; döngü başına sayı Kurucu'nun, muhalefet kayıtlı; E659);
  `seed-076-harness-score-inputs-identity-and-policy-keys-unstated` → `26e:71-77`, `26a:44`, `29a:67-72`,
  `29v:29-33` (test 6, `rules_total`, yarım yukarı yuvarlama, imza, beş anahtar ve `required.json`'un Aşama 1
  satırı; E660);
  `seed-077-harness-offline-client-network-and-state-growth-unstated` → `26e:78-80` (test 9; test 11 gevşemez;
  E661);
  `seed-078-revert-row-does-not-name-its-commit-and-stage-0-has-no-watcher` → `13:51-58`, `26f:17-18`, `26f:78-79`, `26d:35`,
  `29m:30` (geri alma `head_sha`, merge `merge_sha`, kesim `base_sha`; Gözcü öncesi `hard_stop`; E662);
  `seed-079-three-sign-calls-per-yaz-job-or-per-root` → `13:59-62` (sahip kararı: sayaç iş başına, `verify`
  sayılmaz; E663);
  `spec-071-asama-1-thresholds-without-policy-keys` → `18a:17`, `18a:57`, `18a:61-62`, `02:23` (anahtarlar
  ve değerler; sahip kararı: harcama frenleri sistemi durdurmaz; anahtar başına aylık tavan; E664).
  Tohum teslimi `spec/asama-*`'yı taşımaz (E180): tohumdaki `asama-1` kopyası (01 dışında 04, 06, 08, 10, 12, 13) aynı
  kararlarla hizalandı; canlı beyindeki kopyayı Kurucu `02`'nin öncelik kuralıyla uzlaştırır. Yerleşmeyen:
  `asama-1/10`'un bulgu başına 0,50 USD ve 5 dakikası için anahtar adı verilmedi. 14 mutant, CI 100 parça.
- 2.2 (2026-11-20, E665–E667; sahibin ipuçları, "zayıf noktaları kapatalım"; ipucu olarak işaretli): `00d`. Partiler
  amaçta da yanlış olabilir: amaca hizmet etmeyen, yanlış sıradaki, tekrar eden ya da eksik madde için kanıt ve
  öneriyle (çıkar, yeniden sırala, birleştir, ekle) `spec_issue`; yanıt operatörün, rapor izin değildir (E665).
  Kaybolan oturum (20261120T011313Z, çıkış 137) kanıtla açıklanır: beyindeyse yeniden sınamalı ders, dışındaysa rapor
  (E666). Ajanlar: ilk ajan tanımlanır ya da yanlışlanabilir bir koşulla neden henüz olmadığı kaydedilir (E667). 3
  mutant.
- 2.2 (2026-11-20, E668; bağımsız inceleme ekibi kararı): yeni `01c`, `drift.check`'in taban çizgisi; `01b` ve `26c`
  ona işaret eder. Yanıtlanan rapor:
  `seed-080-drift-check-has-no-recorded-baseline-in-the-summary` → `01c:9-46`, `01b:67-69`, `26c:36` (döngünün
  ve operatörün okumaları, `drift` nesnesi, etkinlik API'si, hedef türü). Operatör `drift` tabanını bu dönemin
  teslimiyle hakem reposunun `setup/summary.json`'una yazar. 2 mutant.
- 2.2 (2026-11-20, E669; sahip kararı, anayasal): yeni `29za`. oyuncak hedefte K0 sayımının paydası hakemin tarafında
  sabittir: tohumun `census` vektörü, oyuncağın etkin yedi ESLint kuralı; her kuralın en az bir geçerli `13a` vakası;
  kopyanın vektörü operatörün açık işi (E671); kuralı düşüren katalog kırmızıdır; `exit.sample` ve `cases.build` tek
  mutasyon kütüphanesini paylaşır; test 27 böyle okunur. 2 mutant.
- 2.2 (2026-11-20, E670; sahip kararı, anayasal): `29za` "Saldırgan set": E648'in kapı seti Aşama 1 çıkış partisinin
  `exit.adversarial` satırıdır (test 54; düzeltici istemine prompt injection, kaçan diff, gizlenmiş sır); Aşama 1
  çıkışı onsuz geçmez; snapshot kanaryası (test 16) Aşama 4'e taşındı. 1 mutant.
- 2.2 (2026-11-20, E654; sahibin ipucu): yeni `00d` (`00c` 80 satıra yaklaştı), "Derslerin kendiliğinden yeniden
  sınanması" (ipucu olarak işaretli): dersler otomatik ve düzenli yeniden sınansın, sonuç derse geri yazılsın;
  ne zaman, nerede ve nasıl kaydedileceği Kurucu'nundur, tohum değişikliği rapor olarak önerilir. 1 mutant.
- 2.2 (2026-11-20, E672–E678; tohum dönemi Z): yeni `26h` "Şemalar, Devam: Aşama 1'in İlk Dilimi" (`26e` ona işaret
  eder). Sahip kararı (O1, E672): ilk dilim deterministiktir, ilk düzeltme yolunda LLM yoktur (`lint.discover` →
  taban → `fixer.range` → `candidate.publish` → izin listesi ve `accept`); P1 MF8 bulgu yazıcısı `findings.write`
  (test 12 MF4'ten taşındı), P1 MF9 izin listesi ve `accept` yazıcısı `gate.allowlist` (yeni test 55; karşılaştırılan
  hash hakemin kendi hesapladığıdır); Gözcü (MF7) önlerinde; eski MF8 (`operating{}`), düzeltme gidiş-dönüşü ve
  `fixer.llm` ilk organ merge'ünden sonraki P3'te (tablosu bir tohum döneminde gelir); `mcnemar` MF4'le kabul edildiği
  için kalır, K3+ dalı K3'le.
  `stages/stage1-P1.json` 9 MF (MF1–MF7'nin numaraları değişmedi); `26e`, `26a`, `26`, `18a`, `26c`, `24`, `27` hizalandı. Sahip kararı
  (O3, E673): H1, H2, H3 dış göz incelemesinin bulduğu tablo düzeltmeleridir. Bağımsız inceleme ekibi kararı (F13, E675): `09` "Kökenin yeri": köken gövdede, yükleyicinin kuralı
  değişmez, tanım hash'i dosyanın dışındaki kayıttır. Sahibin ipucu (E676): `00d` "Arama ile okuma". Operatör
  kararları: ölçüm aynasına `session_time` ve `path` (E677; `organ_merges_copy` türetilemez, `null` ve nedeni);
  `25` "Karşılaştırmanın tabanı" ve `01c`: önyükleme hakemi `operator_hashes`'i her sonuca yazar, `drift.hashes`'e
  karşı fark koşuyu durdurur (`vectors_hash_mismatch`, `seats_hash_mismatch`), `drift`'siz özet çalışır; teslim aracı `drift.hashes`'i sahnelenen kopyadan yeniden hesaplar (E678).
  Yanıtlanan rapor: `seed-081-the-time-limit-of-a-manifest-command-is-on-no-page` → `29b:24` (bildirim komutunun
  süresi `bootstrap.json` `limits.test_timeout_s`, bugün 600, komut başına; yerel koşucu okur, varsaymaz; E674).
  41 mutant, CI 104 parça.
