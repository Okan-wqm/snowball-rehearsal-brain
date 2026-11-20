# Değişiklik Günlüğü — Tohum, 2.2'nin Yedinci Kayıtları

Tarih: 2026-11-18 · Sürüm: 2.2
Okunma: bir sayfanın geçmişi aranırken
Çapa: git geçmişi ve zincirdeki spec hash satırları

- 2.2 (2026-11-19, E647–E650; sahip kararı ve sahibin ipuçları): E647, ölçüm aynası: başlatıcı her oturumdan önce
  `/work/logs/mirror.json`'u yazar, kendi kayıtlarından ve hakem arşivinden sayılan olgular, öğüt yok (sayfa
  değişmedi; `seed/founder/prompt.md` "Ölçüm aynası"). Sahibin ipucu (E648; ipucu olarak işaretli): `00b`, gerçek
  ürün reposundan önce kapılar saldırgan bir test setinden (prompt injection, diff denetiminden kaçış, gizlenmiş
  secret'lar) kanıtla geçer; seti hakem koşar, tasarım Kurucu'nundur. Yeni `00c` (`00b` 80 satırı doldurdu): sahibin
  ipuçları E649 (öğrenme: ders bulunabilir olsun, eski kodu da kapsasın) ve E650 (önleme ve yapı). 41 mutant, CI 99
  parça.
- 2.2 (2026-11-17, E609–E611; sahip kararı, 2026-11-17): yeni `26g`. `founder` bölümüne `lesson` türü,
  `26g` (E609, E610): yükü `{summary, refs[], recheck}`; iddia tek cümle ve kendi başına anlaşılır,
  `refs[]` kanıttır, `recheck` beyin kökünden yazıldığı gibi koşan komut ya da `none: <neden>`. Yürürlükten
  çıkma bugünkü `closes:<row_id>` ref'i ya da `13`'ün `supersedes`'i; yeni mekanizma yok, hakem yalnız
  yapıyı denetler. Ad `learning` değil: beynin defterinde `13`'le kapatılmış altı `kind: learning` satırı
  var, tür kümeye girseydi kapatanları geçersiz olurdu (E609). Başlatıcı her oturumdan önce
  `/work/logs/lessons.json`'u yazar: yürürlükteki derslerin en yeni 100'ünün `row_id`'si ve iddiası (500
  karakter), dışarıda kalanların sayısı; `recheck`'i koşturmaz (E610). Sahibin hedefi `01`'de, `00` ona
  işaret eder: ölçü kabul edilmiş sağlam değişiklik başına maliyet, bilgi repoda, model değil (E611).
  Karmaşıklık da maliyettir (sahip kararı, 2026-11-17, `01`): sistemin kendi boyutu ölçülür ve raporlanır,
  yerini ölçülmüş ihtiyaçla hak etmeyen birleştirilir ya da kaldırılır, yeni mekanizma yalnız ölçülmüş
  ihtiyaçtan (E611). 28 mutant, CI 92 parça.
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
