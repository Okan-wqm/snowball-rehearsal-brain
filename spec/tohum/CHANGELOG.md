# Değişiklik Günlüğü — Tohum

Tarih: 2026-10-29 · Sürüm: 2.2
Okunma: bir sayfanın geçmişi aranırken
Çapa: git geçmişi ve zincirdeki spec hash satırları

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
- 2.2 (2026-11-13, E577–E581; Kurucu raporları, iki uzmanlı iki turlu panelin kararı): `24a` 3: başlatıcının
  `targets.json`'u `targets[]` sırasıyla `[{id, kind, base_sha, unit_candidates}]`'dır (kimlik ya da aday ad taşırsa
  başlatıcı durur; repo, hariç yollar, güvenlik yolları ve adlar verilmez); `policy.json`'un `operating`'i her oturum
  için okunup `/work/logs/operating.json`'a yazılır (`seed/founder/prompt.md` "Hedefler"). `26c` "Birim tarifi":
  sürüm dosyası hedefin iş akışlarına ve `engines`'a karşı geçerlidir; işaret getirme iznidir, koşma buyruğu
  değildir; tarifin ölçüsü yalnız `unit.verify`'dır. Yanıtlanan raporlar:
  `seed-050-copy-target-row-unreadable-for-unit-proposal` → (a) E571, `24a:32-33`; (b), (c) `24a:32-33` (adaylar ve
  taban `/work/logs/targets.json`'da); (d) `24a:34-35` (`operating.json`; değerler operatöründür, hakem reposunun
  `policy.json`'unda bugün `operating` yoktur, E579); (e) `26c:67` (sürüm dosyası kazanır, o sürümde kırmızı koşu
  ölçümdür); `seed-051-install-marks-run-platform-foreign-scripts` → (1) `26c:71` (işaret izindir, hangi betiğin
  koşacağını hiçbir sayfa sabitlemez); (2) `29g:20-21` (platform koşulu olmadan getirilir ve denetlenir), `26c:71`
  (açılmayan paket ret nedeni değildir); (3) `26c:71` (hiçbir betiğin başarısızlığı, isteğe bağlı paketinki dahil, ret
  nedeni değildir; ölçü `unit.verify`). E576'nın yanıtı adlandırılmamıştı (E581):
  `seed-052-known-b-stop-has-no-path-before-b` → `29b:73`. seed-049 kaydının `24a:53`'ü `24a:54` oldu. 80 satır
  sınırı için `24a` "Oturumun maliyet satırı" yeniden sarıldı (içerik değişmedi) ve 2026-11-04 E499, E540–E546 kaydı
  `CHANGELOG-5.md`'ye taşındı.
  Sahibin kararı (E582): `cost` satırı modeli ve CLI'nin token toplamlarını da taşır (`24a:35`).
- 2.2 (2026-11-12 – 2026-11-13, E569–E574): `29e` "Genellik okuması", hedeflerin `targets.json`'u ve yasa `00`
  Y12 "Maliyet": `CHANGELOG-7.md`.
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
