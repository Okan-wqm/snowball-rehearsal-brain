# Değişiklik Günlüğü — Tohum, 2.2'nin Altıncı Kayıtları

Tarih: 2026-11-13 · Sürüm: 2.2
Okunma: bir sayfanın geçmişi aranırken
Çapa: git geçmişi ve zincirdeki spec hash satırları

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
