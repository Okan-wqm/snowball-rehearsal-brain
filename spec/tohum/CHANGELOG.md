# Değişiklik Günlüğü — Tohum

Tarih: 2026-10-29 · Sürüm: 2.2
Okunma: bir sayfanın geçmişi aranırken
Çapa: git geçmişi ve zincirdeki spec hash satırları

- 2.2 (2026-11-22, E697; tohum dönemi AE, sahibin ipucu: ajanlar Kurucu'nun kurallarıyla, `00e`): `CHANGELOG-14.md`; başında **İlk iş**.
- 2.2 (2026-11-22, E694–E696; tohum dönemi AD, raporların yaşam döngüsü, seed-087'nin kalanları, yeni `26l`): `CHANGELOG-13.md`; başında **İlk iş**.
- 2.2 (2026-11-21, E685–E690; tohum dönemi AB, seed-085–087, yeni `26j`): `CHANGELOG-11.md`; başında **İlk iş**.
- 2.2 (2026-11-21, E691–E693; tohum dönemi AC, seed-088, yeni `26k` ve `00e`): `CHANGELOG-12.md`; başında **İlk iş**.
- 2.2 (2026-11-21, E680–E684; dönem AA, yeni `26i`, `28a`): `CHANGELOG-10.md`; girdinin başında **İlk iş** listesi vardır.
- 2.2 (2026-11-20, E655–E678; Y ve Z dönemleri, yeni `01c`, `29za` ve `26h`, Aşama 1'in ilk dilimi): `CHANGELOG-9.md`.
- 2.2 (2026-11-20, E654; sahibin ipucu): yeni `00d`, derslerin kendiliğinden yeniden sınanması: `CHANGELOG-9.md`.
- 2.2 (2026-11-19, E647–E653): ölçüm aynası, sahibin ilkesi ve beş ipucu, yeni `00c`: `CHANGELOG-8.md`.
- 2.2 (2026-11-18 – 2026-11-19, E634–E645; bağımsız inceleme ekibi kararı, sahip kararları ve Kurucu raporları): Kurucu'nun dört
  raporunu iki bağımsız inceleyici (Opus ve Sonnet) ayrı ayrı yargıladı; bu yolla karara bağlanan ilk dönem. Sahip
  kararları: `13` "Rekor'a yazılamama" (E636; `28:36`): imzalama programının başarısız tek çağrısı yazılamama değildir,
  bir `yaz` işinde en çok 3 çağrı, her birinin sonucu `yaz`'ın çıktısında; tekrarın aynı köke bıraktığı ikinci Rekor
  girdisi kırık değildir (`root` grubuna `verify_second_entry_same_root`); `25a` "Dış kesinti" (E638;
  `ETKINLESTIRME.md` 7. adım): yeniden tetik yalnız hiçbir hedef ref'i yazmamış kırmızı koşuya; hedefe yazdıktan sonra
  kırmızı koşu Başarısızlık'a gider. Sıkılaşan: `13` zincir kırığı, son imzalı durum satırının commit'inden başka bir
  `brain/integration` başı, (B)'de onu yalnız Başarısızlık onarır (E637); `29g` gömülü paketler tarball'ın parçasıdır,
  kurulum betikleri gömenin işaretini ister, `npmlock`'a iki vaka (E639). Bağımsız inceleme ekibi kararı (E641,
  E544 (2) kapandı): `26f` "Taahhüdün kataloğu": geri alma provasının taahhüdü en az ekilmiş nedenin örneklerinden
  çeker; anahtar, taahhüt, `judge` ve #geri-alma kapısı değişmez. Sahip kararı: `01` "Geçici yapılar" (E642): iş
  bitince geçici kurulanlar silinir; kanıt, arşiv ve başkasının işi kalır. Sahibin ipucu (E643; beslememe kuralının
  istisnası, ipucu olarak işaretli): `00b`, `01` ona işaret eder. Sahip ilkesi (E644, 2026-11-19): `00b` "Model
  seçimi amaçla ve ölçümle": model amaç başına, kabul edilmiş sonuç başına toplam maliyetle seçilir. Sahibin ipucu
  (E645): `çek` aktarılan beyin SHA'sının sonucunu okusun, (B) sırasında `STOP` gerekmesin (`00b`). Yanıtlanan raporlar:
  `seed-066-cek-running-tree-unexercised` → declined: `29u:30-33` ve E591 zaten yanıtlar (koşan hakem ağacı son
  aktarım satırının `brain_sha`'sındadır; kabul edilmiş SHA'daki farklı `referee/` durdurma nedeni değildir); vektör
  yok, sayfa değişmedi (E634);
  `seed-067-loop-outage-and-red-condition-not-separated` → `25a:41-49` ("Dış kesinti"; kesintiden gelmeyen
  kullanılamaz girdi beynin mantığıdır, okumaları yinelemek Kurucu'nun seçimidir, tohum ne ister ne yasaklar, E635);
  `seed-068-one-failed-sign-call-and-the-target-written-before-it` → `13:56-64` (üç çağrı, ikinci girdi,
  `brain/integration` başı), `25a:41-49` (hedefe yazmış koşu yeniden tetiklenmez), `29j:30` (E636–E638);
  `seed-069-bundled-packages-in-a-lock-and-in-a-tarball` → `29g:31-37` (F1 kabul, E639; F2: `inBundle: true` satırı
  bugün `registry_not_allowed`, kabulü onu isteyen bir hedef kilidini bekler, E640), `29g:60-62`. 80 satır için
  2026-11-14/17 E585–E599 ve E609–E611 kayıtları `CHANGELOG-8.md`'ye taşındı. 33 mutant, CI 96 parça.
- 2.2 (2026-11-17, E630–E633; sahibin onayı, sahip kararı ve Kurucu raporları): tek turda çıkış (E630).
  `exit-request.json` başın atası olan ve ondan başa yalnız isteğin değiştiği commit'i de adlandırabilir: push önce kod
  olarak yargılanır; kod kabul edilirse (A) aynı koşuda aynı başta yargılanır ve geçerse o baş sabitlenir, edilmezse
  çıkış yargılanmaz (`exit.not_judged`: `code_not_accepted`); son kabul edilmiş SHA'yı adlandıran istek değişmedi
  (`29b:73`, `26c:14-16`). Yanıtlanan raporlar: `seed-064-capsule-stdlib-has-no-bytecode` → `24a:19` (kapsülün imajı,
  tabanın sildiği `*.pyc`'ler, hakemin konteyneri; imaj artık standart kütüphaneyi derler, E632);
  `seed-065-revert-trigger-without-red-test-unstated` → `07:35-39` (geri almayı `29j`'nin `unknown` dışı nedeni başlatır,
  kırmızı testsiz `build_break` ve `lint_regression` da; flaky test doğrulanmış kırmızı değildir, `rerun` geri almaz,
  E631), `29j:59-60` (`build_ok`'un ve lint toplamının üreticisi Kurucu'nun hakem kodudur). Sahip kararı:
  `25a` "Dış kesinti" (E633; `ETKINLESTIRME.md` 7. adım): yalnız adı konmuş dış kesintiden kırmızı (B) koşusu o devir
  için bir kez yeniden tetiklenir, insan dokunuşu olarak kaydedilir; yeni kod denetimi yok.
- 2.2 (2026-11-16 – 2026-11-17, E606–E611; Kurucu raporları, olgu, sahip kararı): `seed-061`, `seed-062`, `seed-063`:
  `CHANGELOG-7.md`; yeni `26g`, Kurucu'nun dersi, başlatıcının ders dizini ve sahibin hedefi: `CHANGELOG-8.md`.
- 2.2 (2026-11-16, E600–E605; Kurucu raporları, sahibin onayı): yeni `29z`. Önyükleme hakemi çıkış isteğinde ayrı,
  sırsız ve izinsiz `kanarya` işinde beynin `python -m runner.contained run`'ını konteynerin dışında, oyuncağın birim
  tarifinin imajında bir kez koşturur; geçerli olmayan ya da kırmızı kanarya `exit.missing`'de `canary:<durum>`, iş
  başarısızsa `canary:job_<sonuç>`; sonuç `exit.canary`'de imzalanır (E600–E602). `genesis` grubuna dört vaka (E603).
  Yanıtlanan raporlar: `seed-058-no-real-container-before-b` → `29b:73`, `29z` (komut, istek, okunan, durumlar, kayıt);
  `seed-059-genesis-vector-toy-base-not-setups-form` → `29o:45-46`, `29o:69-76` (kurulumun özetteki biçimi;
  `toy_base_empty`, `toy_base_absent`, `copy_base_empty`, `seed_epoch_seed_null`: `29o:63-67`); `seed-060-app-secret-form-not-stated` → `29s:78-80` (iki sırrın
  adı ve girilişi; `WRITER_APP_ID`'nin çevresindeki boşluk bilinmiyor). (B)'nin beşinci ve altıncı denemesi: `CHANGELOG-7.md`.
- 2.2 (2026-11-14 – 2026-11-15, E585–E599): `29t` kendi haritası, `29u` çıkıştan sonra, `29v` politika okuması,
  `29y` döngü koşuları ve Kurucu'nun hafızasının yeri: `CHANGELOG-8.md`.
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
