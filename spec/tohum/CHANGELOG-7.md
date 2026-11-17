# Değişiklik Günlüğü — Tohum, 2.2'nin Altıncı Kayıtları

Tarih: 2026-11-13 · Sürüm: 2.2
Okunma: bir sayfanın geçmişi aranırken
Çapa: git geçmişi ve zincirdeki spec hash satırları

- 2.2 (2026-11-17; gözlem): (B)'nin sekizinci denemesi, hakem koşusu 44021027967, `cek`'te `head_missing:brain/state` ile
  durdu (`brain/integration` yedinci denemeden oyuncakta duruyordu). Dokuzuncusu kırmızı. Hakem koşusu 44021409653: `yaz`
  oyuncakta `refs/heads/brain/integration`'ı yazdı, sonraki `POST /repos/Okan-wqm/snowball-rehearsal-toy/git/refs` 422
  aldı, GitHub'ın metni `Reference update failed` (`hard_stop`). Operatör sonra `25a`'nın arşiv ve silme adımını yaptı:
  oyuncakta `refs/tags/arsiv/<row_hash>/brain/integration` etiketleri (ikisi de de5b57c'de) var, dalı yalnız `main`.
- 2.2 (2026-11-16; gözlem): (B)'nin yedinci denemesi kırmızı. Hakem koşusu 43926970052: `cek`, `cagir`, `getir`,
  `kos` yeşil; `yaz` oyuncakta `refs/heads/brain/integration`'ı yazdı (dal oyuncakta duruyor, başı de5b57c), sonraki
  `POST /repos/Okan-wqm/snowball-rehearsal-toy/git/refs` 422 aldı (`hard_stop`).
- 2.2 (2026-11-16; gözlem): (B)'nin altıncı denemesi kırmızı. Hakem koşusu 43886515914: `cek`, `cagir`, `getir`,
  `kos` yeşil; `yaz` App kimliğinden geçti, sonra `genesis payload: payload.seed_epoch.seed_sha256: not 64 lowercase
  hex` ile reddetti. Hakem reposunun `setup/summary.json`'unda `seed_epochs[]` satırlarının `seed_sha256`'sı `null`'dır;
  kurulumun özetteki biçimi `29o:69-76`'da.
- 2.2 (2026-11-16; gözlem): (B)'nin beşinci denemesi kırmızı. Hakem koşusu 43853494127: `cek`, `cagir`, `getir`,
  `kos` yeşil; `yaz` `App id: not an App id or a client id` ile reddetti; aynı işin `create-github-app-token` adımı aynı
  `WRITER_APP_ID` sırrıyla başarılı oldu. Sırların adı ve girilişi `29s:78-80`'de.
- 2.2 (2026-11-15; gözlem ve sahibin istisnası, olgu): (B)'nin üçüncü denemesi kırmızı. Aktarılan 1b0a1e4; iki devir
  (43721580137, 43721876896) aynı: `kos` oyuncakta `base` `no_verdict` [`unreadable_output`], her aday
  `base_unavailable`; `yaz` `activation_refused` [`base_run_missing`]; geri alındı, 1b0a1e4 `reverted_exits`'te. Olgu:
  `loop.yml`'un işleri koşucunun kullanıcısıyla (`ubuntu-24.04`'te uid 1001) koşar; `contained` konteyneri `--user
  65534:65534` ile başlatır; `unreadable_output` yalnız koşudan sonra `work/` ya da `out/` altında host kullanıcısının
  açamadığı bir girdi varken çıkar. 80 satır için E583 gözlemi `CHANGELOG-6.md`'de.
- 2.2 (2026-11-15; sahibin istisnası, olgu): operatörün (B) ön denetimi, iki GitHub API olgusu. (1) `GET /app`
  yalnız App'in JWT'siyle okunur; kurulum belirteci 401 alır (canlı deneme: `A JSON web token could not be
  decoded`). (2) `GET /repos/{repo}/actions/permissions` belirteçte `administration: read` ister; yazar App'inde
  Administration Read-only vardır (sahip doğruladı), bir belirteç yalnız basılırken istenen izinleri taşır.
- 2.2 (2026-11-15; gözlem): (B)'nin ikinci denemesi kırmızı. Aktarılan 4dc2c69; iki devir (koşu 43685908138,
  43686181570) aynı: `cek`, `cagir`, `getir`, `kos` yeşil; `kos` oyuncakta `base` `no_verdict` [`red_control_fault`,
  `runner_fault`], işin süresi 3 sn, her aday `base_unavailable`; `yaz` `activation_refused` [`base_run_missing`]. İlk
  denemenin `kos`'u (43534260172) aynı satırı vermişti. Aktarım geri alındı, 4dc2c69 `reverted_exits`'te.
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
- 2.2 (2026-11-13, E574; sahibin kararı): yeni yasa `00` Y12 "Maliyet" (metni yalnız orada); `06`, `24`, `24a`
  ona işaret eder; `24a`'daki "Kurucu kendi maliyetini ölçemez" cümlesi Y12 ile çeliştiği için kalktı; `00` 80 satır
  sınırı için yeniden sarıldı, başka içerik değişmedi.
- 2.2 (2026-11-12, E569–E573; Kurucu raporu, iki uzmanlı iki turlu panelin kararı): yeni `29e` "Genellik okuması":
  #genellik'in metin saydığı baytlar (katı UTF-8 ve NUL yok; öbür denetim karakterleri metindir), aradığı yer (yol,
  `referee/`'den sonrası, ve metin; karşılaştırmanın biçimi), iki nedenin adı ve listenin oturuma verilmediği; `26c:32`
  kuralı için oraya bakar, `00b`'nin aşama satırı `29e`'yi okutur; donmuş `asama-0/10` değişmedi. `24a` 3: başlatıcı her
  oturumun klasörüne `targets.json` yazar, `targets[]` sırasıyla `[{id, kind}]`, adsız (`seed/founder/prompt.md`
  "Hedefler"). Yanıtlanan rapor: `seed-049-genellik-text-rule-and-names-unreadable` → (a) `29e:60-62` (metin kuralı ve
  iki nedenin adı), `29e:58-60` (biçim; önce yol, sonra metin); (b) `29e:57-58` (liste de sayısı da oturuma verilmez),
  `29e:64-65` (denetimden geçmek genelliğin kanıtı değildir); `26c:32` listeyi adlandırır, kimin okuduğunu söylemez; (c)
  `24a:32-33` (hedeflerin kimliği ve türü `/work/logs/targets.json`'da), `24a:54` (`targets/<hedef>/`);
  `targets/names.json`'u okuyan ya da reddeden denetim yoktur. 80 satır sınırı için 2026-11-01 E490–E499 kaydı
  `CHANGELOG-5.md`'ye taşındı.
