# Değişiklik Günlüğü — Tohum, 2.2'nin Üçüncü Kayıtları

Tarih: 2026-11-01 · Sürüm: 2.2
Okunma: bir sayfanın geçmişi aranırken
Çapa: git geçmişi ve zincirdeki spec hash satırları

- 2.2 (2026-11-01, E404, E405; ikinci şüphecinin bulgusu): PASS satırı ve `stage-open`'ın kuralı yeni `26d`'de: `events`
  satırı, `payload` `{stage: 0, verdict: "PASS", import_line_sha256, copy_genesis_row_hash, copy_merge_row_hashes[],
  owner_exception?}`, hakemin kendi satırı (`trust` `verified` ya da `observed`); merge satırı `kind: merge`; önerilmiş
  kopyası sayılmaz; oyuncağın merge'ünden sonra gelir, son aktarımı adlandırır. Alanlar `26` ve `26b`–`26d`'de (`25a` 9).
- 2.2 (2026-11-01, E390–E399; Kurucu raporları; E156, E158, E159, E234, E235, E281 kapandı): bu dönemin yanıtladığı ve
  reddettiği raporlar: `seed-002-29b-stale-after-narrowing` → `29b:13` (giriş), `29b:67-73` "Çıkış isteği";
  `seed-003-toy-repo-no-reader` → `27:67` (`tests/fixtures/toy-repo/`); `seed-005-push-class-ledger` → `29e:11-16`
  "Kurucu kayıtları", `29b:44`; `seed-006-ledger-kind-set` → Kurucu talimatı "Görevlerin" (d): eksik yetenek
  `missing_capability:` önekli `seed_issue`'dur, tür kümeleri kapalı (`26` `founder` satırı, `26c` `reports/*.json`);
  `seed-007-chain-cli-exit-and-broken-row` → `29d:24-28` "Genel koşucu"; `seed-009-secret-in-prompt-no-location` →
  `29e:18-29` "Sır desenli metin", `29b:54`, `29b:61-65` "Ret hafızası"; declined: satır numarası (yalnız yol verilir)
  ve tarayıcının kural kümesi (MF2'nin tabanı `29f:26-29`, fazlası tarayıcının kendisidir);
  `seed-010-verdict-withheld-no-claim` → `29e:18-29` "Sır desenli metin", `29b:61-65`; declined: kararın eşleşen
  kısmını hash'leyip kalanını geçirmek (`08:71-72`: eşleşme koşuyu geçersiz kılar; kaybolan bulguyu yeniden inceleme
  geri getirir); `seed-017-diffguard-config-list` → `29k:53-55` `diffguard`; `seed-022-k0map-mismatched-file-rules` →
  `29h:31-34` `artefact_hash_mismatch`, `29h:59-60` vaka `mismatched_file_not_read`;
  `seed-024-revert-parent-is-onto-head` → `29i:21-22`, `29i:32-33` `refs` `revert`, `29i:36` vaka
  `refuse_revert_not_head`; `seed-025-append-choices` → `29i:54-61` `append` (çıkış 2, (5)), `29i:73-74` vakalar
  `refuse_known_row_id`, `refuse_empty_rows`; `seed-029-flaky-choices` → `29j:36-39` `flaky`, `29j:48-49` vakalar
  `unread_run_not_checked`, `empty_runs_rerun` ((d) `29j:39-41` aynen; kimlik biçimi ve sonuçların üreticisi
  Kurucu'nun); `seed-035-loop-control-and-yaml-subset` → `29p` (denetim komutu, 3b), `29p:55`, `29r` (YAML altkümesi);
  `spec-004-calls-17-18`
  → `26c:19-22`, `02:13-14` (3a): 17 1–16'yı, 18 1–17'yi çağırır, donmuş `asama-0/14:48` değişmez;
  `spec-013-lint-green-vs-violation` → `26c:64-66` "Birim tarifi" (lint yeşili, 3b);
  `spec-014-toolchain-form-and-calls-6-4` → `26c:66-67` "Birim tarifi" (`toolchain`, 3b), `26a:15-21` (`calls` yalnız
  sırayı bağlar); `spec-019-calls-7-8-3-8` → `26a:15-21` (`calls` ve "Çağıran"), `26c:21`, `29h:18`;
  `spec-021-target-write-callers` → `26a:33` "Çağıran", `25a:17` (kontrol adı);
  `spec-026-append-writes-through-target-write` → `26a:33` "Girdi"; `spec-028-anchor-calls-append` → `26a:35`
  "Çağıran", `01a:27-28` (`<state_root>`); `spec-032-drill-calls-9-14` → `26a:33` "Çağıran", `29m:27-29`;
  `spec-038-expect-reason-comparison` → `26c:55-59` "Hazır aday". Yeni sayfalar `29e` ve `29r` (`INDEX`, `00b`); 80
  satır sınırı için 2026-10-30 ve 2026-10-31'in dört kaydı `CHANGELOG-3.md`'ye taşındı.
- 2.2 (2026-11-01, E400; Kurucu raporu spec-015 -> `29g`, `29d`, `24`, `30c`): npm workspaces kilidi. Kök, çalışma alanı bağı (`link` doğru, `resolved` depo içi göreli yol) ve böyle bir bağın adlandırdığı çalışma alanı dizini getirilmez ve denetlenmez; iç içe `<çalışma alanı>/node_modules/<paket>` dahil başka her girdi pakettir, getirilir ve denetlenir (`29g`; vakalar `workspaces_lock`, `workspace_folder_needs_its_link`, `nested_registry_not_allowed`). Hangi girdinin getirilip denetlendiği yalnız `29g`'dedir; `29d`, `24` ve `30c` oraya bakar.
- 2.2 (2026-10-31, E333; uzman tartışması ve hakem, ikinci tur 2026-11-01): önyükleme hakemi `asama-0/10a`'nın kuralını
  uygular: kabul edilmiş çıkıştan ((A)) sonra spec, kod ya da çıkış push'unda Kurucu kayıtları dışında yalnız `candidates/`
  ve `targets/` değişebilir: `referee/` `referee_changed_after_exit`, başka yol `changed_after_exit:<yol>` (`29b` "Çıkıştan
  sonra"). Dondurma Aşama 0'ındır: kilit sonraki aşamayı açınca ya da (B) kırmızıyken operatör aktarımı geri alıp başı
  `control.json` `reverted_exits`'e yazınca biter (`26c`, `25a` "Başarısızlık"). İmzalı durum çıkışın başını taşır
  (`snowball-bootstrap-state/4`; `/3` aynen taşınır, taşıdığı sonuç aktarılabilir bir çıkışsa onun başıyla).
- 2.2 (2026-10-31, E342, E93; Kurucu raporu seed-040, uzman tartışması ve hakem): önyükleme hakeminin imzalı durumunun
  arayüzü `29b` "Durum"dadır: artefakt, hakem reposunun `main`'indeki koşuların süresi dolmamış en yeni `bootstrap-state`'i
  (iki dosya); açılışı `sigstore verify identity` (`bootstrap.yml`'in `main` kimliği, GitHub OIDC yayıncısı), doğrulanamazsa
  ya da yoksa çıkış 2; son kabul `state.last_accepted_sha`. `26c` `referee_tree_sha256`'nın kuralını, kodun her retini
  (arşivin her yerindeki bağ, özel dosya ve güvensiz ad dahil) ve bilinen cevaplı örneğini (`/vec/treehash/three-files.tar`;
  vektör vakası değil) verir; D1'in nasıl kurulacağı Kurucu'nundur. Raporların okuyucusu (E93): `pull` beynin
  `reports/*.json`'unu okur; imzalı sonuç `reports[]` `{id, kind, ref, state, sha256}` ve açık rapor varsa `reports_open:<n>`
  uyarısını taşır; rakibin isteği `reports/`'u yine dışarıda tutar (`26c`); `disputed` kuralı E53'te kalır. Her dönemin
  günlük satırı yanıtladığı ya da reddettiği rapor kimliklerini adlandırır; bu dönem: `seed-040-d1-bootstrap-state-read` →
  `29b:30-34`, `26c:39-45`.
