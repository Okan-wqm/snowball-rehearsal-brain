# Değişiklik Günlüğü — Tohum

Tarih: 2026-10-29 · Sürüm: 2.2
Okunma: bir sayfanın geçmişi aranırken
Çapa: git geçmişi ve zincirdeki spec hash satırları

- 2.2 (2026-11-17, E608; Kurucu raporu, olgu): yeni kural, vaka ve mutant yok. Yanıtlanan rapor:
  `seed-063-outside-brain-ruleset-covers-nested-brain-branches` → `25a:17` (iki hedefte `brain-disi`'nin hariç listesi
  2026-11-17'den beri `refs/heads/brain/**`, `refs/heads/brain/**/*`, `~DEFAULT_BRANCH`; `brain/c/good`, `brain/drill/x`,
  `brain/revert/x` için okunan kural yok). (B)'nin sekizinci ve dokuzuncu denemesi, arşiv: `CHANGELOG-7.md`. 80 satır
  için 2026-11-13 E577–E582 kaydı `CHANGELOG-7.md`'ye taşındı.
- 2.2 (2026-11-16, E606–E607; Kurucu raporları, olgu): yeni kural, vaka ve mutant yok. Yanıtlanan raporlar:
  `seed-062-genesis-vector-seed-sha256-not-setups-form` → `29o:69-76` (kurulumun özetteki biçimi; `null` olabilen yalnız
  `targets[].base_sha` ve `seed_epochs[].seed_sha256`), `29o:63-67` (`seed_epoch_seed_null`, `toy_base_empty`,
  `toy_base_absent`: `seed_epoch.seed_sha256` `null`); hakemin özetinde 23 dönem satırı, her biri dört anahtarlı, her
  `seed_sha256` `null`; `bootstrap_sha256` `null` vakası yok, `26c:30` türsüz (E606).
  `seed-061-integration-cut-needs-create-exemption` → `25a:17` (iki hedefin beş ruleset'i, olgu; `brain-integration`'da
  `do_not_enforce_on_create: true`). (B)'nin yedinci denemesi: `CHANGELOG-7.md`.
- 2.2 (2026-11-16, E600–E605; Kurucu raporları, sahibin onayı): yeni `29z`. Önyükleme hakemi çıkış isteğinde ayrı,
  sırsız ve izinsiz `kanarya` işinde beynin `python -m runner.contained run`'ını konteynerin dışında, oyuncağın birim
  tarifinin imajında bir kez koşturur; geçerli olmayan ya da kırmızı kanarya `exit.missing`'de `canary:<durum>`, iş
  başarısızsa `canary:job_<sonuç>`; sonuç `exit.canary`'de imzalanır (E600–E602). `genesis` grubuna dört vaka (E603).
  Yanıtlanan raporlar: `seed-058-no-real-container-before-b` → `29b:73`, `29z` (komut, istek, okunan, durumlar, kayıt);
  `seed-059-genesis-vector-toy-base-not-setups-form` → `29o:45-46`, `29o:69-76` (kurulumun özetteki biçimi;
  `toy_base_empty`, `toy_base_absent`, `copy_base_empty`, `seed_epoch_seed_null`: `29o:63-67`); `seed-060-app-secret-form-not-stated` → `29s:78-80` (iki sırrın
  adı ve girilişi; `WRITER_APP_ID`'nin çevresindeki boşluk bilinmiyor). (B)'nin beşinci ve altıncı denemesi: `CHANGELOG-7.md`.
- 2.2 (2026-11-15, E594–E599; Kurucu raporu ve sahibin kararı, iki uzmanlı iki turlu panel): yeni `29y`. Yanıtlanan
  rapor: `seed-055-prompt-limit-not-stated` → `29b:47-50` (istemin parçaları, Unicode kod noktası birimi,
  `bootstrap.json` `limits.max_prompt_chars`, `prompt_too_large`; sonucun `rival` kaydı her koşuda, sınır denetiminden
  önce, `prompt_chars`, `prompt_diff_chars` ve `prompt_max_chars` taşır, ölçülmeyen `null`'dır). Raporun bayt birimi
  ve `rival.prompt_max_bytes` anahtarı kodda yoktur; en büyük yollar listesi alınmadı (E595). `29b:46-54` satır sayısı
  değişmeden yazıldı; çıkan olgular `24:21`, `24:29`, `29b:44`, `29e:16` ve `25:42-44`'te kalır. Sahibin kararı
  (E596): Kurucu döngünün (`loop.yml`) en yeni üç koşusunu her oturumda `/work/logs/loop-runs.jsonl`'da görür (`29y`;
  `prompt.md`, `00b`). `policy.json`'un kopyası kaçışla yazılmış sır desenini de reddeder (E598). Yanıtlanan raporlar:
  `seed-056-kos-red-without-its-cause` → `29y:29-36` (her işin son çıktı satırları, `output`);
  `seed-057-app-read-credential-not-stated` → `29s` "GitHub kimlikleri". 80 satır için 2026-11-12/13 E569–E574 ve
  operatörün 2026-11-15 gözlem ve istisna kayıtları `CHANGELOG-7.md`'de.
- 2.2 (2026-11-14, E588–E592; Kurucu raporu ve sahibin iki kararı, iki uzmanlı iki turlu panel): yeni `29u`, `29v`.
  Sahibin kararı (E590): (A) kabul edilince sabitlenen yalnız kabul edilen SHA'dır, `main` değil; sonraki push olağan
  yargılanır, `changed_after_exit` ve `referee_changed_after_exit` kalktı, `referee/`'ye dokunan push
  `referee_ahead_of_exit` uyarısını taşır; döngünün ağaç karşılaştırması son aktarım satırının `brain_sha`'sındadır
  (`29u`; `29b:73`, `25a:22`, `25a:35`, `26c:28`, `29t:35` ona bakar; donmuş `asama-0` sayfalarının dondurma
  cümlelerinin yerini `02` 1 gereği `29u` alır). Sahibin kararı (E592): Kurucu'nun hafızası yalnız `main`'dedir,
  `wip/` dalı `main`'e merge edilir ya da kanıtla kapanır (`15:28-32`). Yanıtlanan rapor:
  `seed-053-policy-shape-unseen-before-b` → (a) `24a:34-35` (dosyanın bütünü `/work/logs/policy.json`'da), `29v:16-19`
  (bayt bayt kopya ve koşulları); (b) `29v:21-31` (`python -m policy.reads`, fikstürler `/vec/policy/`, aşamanın
  zorunlu yolları), `29v:36-47` (bulgular; Aşama 0'da uyarı); (c) `18a:12` (anahtar sütunu tam yoldur, bölümsüz ad
  o yoldur; donmuş `asama-0/12:20` için de), `18a:49-50` (`deps.fetch` okur), `29b:79` (okudukları `constitutional`
  altında), `26e:46`. 80 satır sınırı için 2026-11-05 ve 2026-11-06 kayıtları `CHANGELOG-6.md`'ye taşındı.
- 2.2 (2026-11-14, E585–E587; sahip): `29t` kendi haritası: hakem `docs/map/brain.md`'yi sınar (Aşama 0 uyarı, 1 ret).
- 2.2 (2026-11-12 – 2026-11-13, E569–E574, E577–E582): `29e` "Genellik okuması", hedeflerin `targets.json`'u, yasa
  `00` Y12 "Maliyet", başlatıcının `targets.json`'u ve `operating.json`'u: `CHANGELOG-7.md`.
- 2.2 (2026-11-05 – 2026-11-06, E550, E551, E553, E560–E566): rakibin bütçe durması, çıkış sırası ve sahip
  istisnasının #spec'i: `CHANGELOG-6.md`.
- 2.2 (2026-11-02 – 2026-11-04, E499, E506, E507, E540–E546): kırmızı bir (B)'den sonra dalların arşivi ve
  silinmesi, tohum güvenlik defteri, imzalı (A) sonucunun aktarımdaki yeri, canlı prova fikstürleri, kapsülde
  defterin salt-okur dizini ve standart kütüphaneyi gizleyen modül adı: `CHANGELOG-5.md`.
- 2.2 (2026-11-01, E411–E417, E470–E475, E478–E485, E490–E499): `26d`'nin olguları (son kökün paketi, zincirli
  satır, Rekor v1, genesis satırı), içe aktarmanın git nesneleriyle anlatımı, `stage-open`'ın bağları ve döngünün
  üç girdisi (`29s`): `CHANGELOG-5.md`.
- 2.2 (2026-10-31 – 2026-11-01, E93, E333, E342, E390–E400, E404, E405, E421–E436, E450): önyükleme hakeminin
  çıkıştan sonraki kuralı, imzalı durumun arayüzü, Kurucu raporlarının yanıtları, npm workspaces kilidi, PASS
  satırı, `stage-open`, fiziksel güvenlik ve kapsülün ajan/skill tanımları: `CHANGELOG-4.md`.
- 2.2 (2026-10-30 – 2026-10-31, E64, E65, E249, E280–E301, E308, E317–E324, E338, E339, E341, E344): ders provasının
  aileleri ve sınav tarafı, sistem haritası, Aşama 0 çıkışının karar verilemeyen koşulları, `control`'ün döngü arayüzü,
  sınıf merdiveninin varsayılanlığı, yük altında performans ve `main`'in salt okunur okunuşu: `CHANGELOG-3.md`.
- 2.2 (2026-10-28 – 2026-10-30, E246–E247 ve öncesi): üçüncü inceleme, önyükleme hakeminin yazılışı ve sonraki kararlar: `CHANGELOG-2.md`.
- 2.1 ve öncesi (2026-10-28): `CHANGELOG-1.md`.
