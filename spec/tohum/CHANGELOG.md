# Değişiklik Günlüğü — Tohum

Tarih: 2026-10-29 · Sürüm: 2.2
Okunma: bir sayfanın geçmişi aranırken
Çapa: git geçmişi ve zincirdeki spec hash satırları

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
- 2.2 (2026-11-06, E561–E566; sahibin kararı): `02` "Sahip istisnası": #spec de istisna edilir (E286), Aşama 1'in
  (A)'sına taşınır; `26c`: `spec_exception` ve yanında tohumun taşıma kaydının (`stages/carry-spec.json`) hash'i
  `spec_commitment`. Arayüz olgusu (E563): `exit.owner_exception` ve PASS satırının `owner_exception`'ı `anchor`'a göre
  sıralı bir dizidir (`26d:45-47`, denetim 7); çıkış isteği olmayan push'un sonucu değişmez.
- 2.2 (2026-11-06, E560; üç uzmanlı iki turlu çıkış panelinin kararı): `seed/founder/prompt.md` "Çıkış sırası": bir
  aşamanın ya da partinin mikro özellikleri bitince sıradaki iş çıkış isteğidir, koşulların tutup tutmadığını isteğe
  verilen hakem kararı söyler; istekten önce ancak `referee/` kodunun yanlış karar verdiği gerçek bir girdiyi (girdi,
  beklenen, gözlenen) gösteren iş gelir, ölçülmemiş ya da sınanmamış olmak bu kanıt değildir. Kural tek yerdedir,
  tohum sayfaları onu yinelemez. Önceden yanıtlanmış: `seed-046-pass-row-unnamed`'in sonraki düzenlemesi bir ilerleme
  notudur; `26d:36-47`, `10a:44` ve `seed-048-copy-gate-record-and-a-result-bytes`'ın yanıtı (`26d:47`) onu karşılar.
  80 satır sınırı için 2026-11-01 E478–E485 kaydı `CHANGELOG-5.md`'ye taşındı.
- 2.2 (2026-11-05, E550, E551, E553; Kurucu raporları, sahibin kararı): yeni `29e` "Bütçe durması": rakibin bir koşudaki
  payı ayın tavanından ve aşamanın freninden kalanla koşu başı tavanın en küçüğüdür; payı biten ya da çağrısı frene
  takılan baş yargılanmaz (`last_evaluated_sha`, seriler ve rakip hata serisi değişmez), sonuç `budget_stop` ile freni
  ve payı adlandırır, yoklama aynı başı pay büyüyene dek uyarıyla geçer; `29e:26`'nın bütçe istisnası kalktı, `29b`
  oraya bakar. `18a`: rakip freni 2026-11-05'ten Aşama 0'da da Aşama 1'de de 1000 USD'dir (rakip `claude` CLI
  aboneliğiyle koşar, fren yalnız kaçak frenidir; `asama-1/10`), `26e` sayıyı yinelemez. Yanıtlanan raporlar:
  `referee-049-rival-budget-consumes-commit` → `29e:42-53` (bütçe durması; çağrı başı tavan da fren, `per_run`),
  `29e:26` (bütçe rakip tarafı hata değildir), `29b:76-77` (baş tüketilmez), `18a:59` (politika: 1000 USD),
  `29e:53` (bu kuraldan önce yargılanmış sayılan baş yeniden açılmaz); declined (11-03 güncellemesi):
  `seed-044-revert-facts-producers`: ret geçerli (2026-11-01 kaydındaki `declined: seed-044-revert-facts-producers`
  satırı; `29j:53-60`); `asama-0/10a:26` `#geri-alma` Aşama 0'da değişmedi. 80 satır sınırı için 2026-11-02 E506 ve
  E507 kayıtları `CHANGELOG-5.md`'ye taşındı.
- 2.2 (2026-11-04, E499, E540–E546): kırmızı bir (B)'den sonra dalların arşivi ve silinmesi, tohum güvenlik
  defteri, imzalı (A) sonucunun aktarımdaki yeri ve canlı prova fikstürleri: `CHANGELOG-5.md`.
- 2.2 (2026-11-02, E506, E507): kapsülde defterin salt-okur dizini ve standart kütüphaneyi gizleyen modül adı:
  `CHANGELOG-5.md`.
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
