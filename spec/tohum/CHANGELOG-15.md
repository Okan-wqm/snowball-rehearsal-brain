# Değişiklik Günlüğü — Tohum, 2.2'nin On Dördüncü Kayıtları

Tarih: 2026-11-22 · Sürüm: 2.2
Okunma: bir sayfanın geçmişi aranırken
Çapa: git geçmişi ve zincirdeki spec hash satırları

- 2.2 (2026-11-22, E698–E703; tohum dönemi AF; rapor masası uzlaşısı, sahibin yetkisiyle operatör kararı).
  **İlk iş** (`25` 10b; Kurucu'nun dersi f1741). Teslimden itibaren önyükleme hakeminin hiçbir denetimi kırmızı
  olmaz: bu dönem ne bir tablo, ne bir vektör, ne bir zorunlu politika yolu değiştirir; hakemin tek yeni okuması bir
  teyidin `epoch`'unu özetin dönemlerine karşı okumaktır (`26l`), sonucu bir uyarıdır, hiçbir zaman neden değildir.
  İlk iş `CHANGELOG-14`'ün sırasıdır, değişmeden; Kurucu'nun bugünkü işi sürer:
  1. MF9, izin listesi ve `accept` yazıcısı (`26j`);
  2. birinci maddeden hemen sonra, kırmızı görev değil, sahibin ipuçları (bu kez kural esnetildi; `00e`): E693 ve E692,
     E697 uygulanarak;
  3. MF10, MF11 ve MF12 (`26j`), MF12 sözleşmeleri T1 ve T2 ile (`26k`);
  4. sonra P1'in çıkış isteği. Bu dönemin yanıtları ondan önce yerindedir: P1 MF2–MF6'nın kurulmuş satırları `26m` ve
     `26n`'ye uyar (seed-089–092, seed-094); çıkış isteği MF1–MF12'nin hepsi bitmeden geçmez.
  Raporların teyidi `26l`'nin kuralı olarak kalır, bu listenin bir maddesi değildir: aşağıdaki sekiz rapor bu dönemin
  tesliminden sonraki ilk oturumda teyit edilir; 2026-11-22'de `epoch`'suz teyit edilen dokuz rapor alanı tek push'ta
  alır (`26l:56`; değer, yanıtı getiren dönemin beyin teslim commit'idir, `26l:41-47`).
  Yeni `26m` ve `26n` (`26e` ona işaret eder): her madde iki panelin arayüz olgularının birleşimidir; Kurucu'nun yapımı
  sayfalarla uyuştuğunda "kurulduğu gibi benimsendi", uymadığında sıkılaştırma. Bir gevşetme, geçici: L-AF1 (`26n:51-53`; `02:22`'nin eşik maddesi
  `asama-1/10:16`'nın bulgu başı fren hücresine `fixer.llm`'in (MF4) dönemine kadar uygulanmaz; o dönemde sahip anahtarlara
  karar verince biter). Sıkılaştırmalar: yolda ve
  bağ hedefinde kimlik reddedilir (089); `snapshot_id` bağları ve çalıştırma bitini kapsar (089); bölge dışı ihlal
  reddedilir (090); K0–K2 isabeti yalnız birincil başvuruyla (090); parmak izini yalnız hakem kodu yapar (091); `PASS`
  katalogdan sayılan her kuralın kapsanmasını ister (091); harness'in ağ korkuluğu ancak denemeyi kırmızı yaparsa sayılır
  (092); `null` kesim satırı dal yok demektir (093); teyidin `epoch`'u özetin dönemlerinden biridir (096; hakem ve
  başlatıcı, `reportlife`). `CHANGELOG.md`'nin 80 satır sınırı için en eski dizin satırları `CHANGELOG-arsiv.md`'ye taşındı.
  Yanıtlanan raporlar; her madde raporun yazıldığı hâliyle, kendi etiketiyle bir satırdır:
  `seed-096-the-seed-epoch-commit-of-26l-is-readable-nowhere-in-a-session` → `26l:41-47`, `26c:30-31`, `27:18`:
  - soru (bir oturumun okuyabildiği tam commit): yanıtlandı (`26l:41-47`: değer beynin teslim commit'idir, oturumun
    kendi beyin geçmişinde; yeni okuma yeri gerekmez; sıkılaştırma `26l:53-56`);
  - dokuz teyide alanın eklenmesi: yanıtlandı (`26l:56`, durum değişmez).
  `seed-093-integration-comparison-point-before-the-toys-first-merge-is-open` → `13:54-56`:
  - soru (`null` `base_sha`'lı, merge'süz hedefte karşılaştırma noktası): yanıtlandı (`13:54-56`; `integration_unnamed`
    kurulduğu gibi benimsendi, `13:56`).
  `seed-089-snapshot-path-identity-manifest-form-adapter-tool-and-pattern-writer-unstated` → `26m:13-31`:
  - (1) yanıtlandı (`26m:14-17`: ret, yeniden adlandırma yok);
  - (2) yanıtlandı (`26m:18-22`: manifest düzenli dosyalar; `snapshot_id` bağları ve kipleri kapsar);
  - (3) yanıtlandı (`asama-1/13c:31`, `26m:23-24`: araç tariften `deps.fetch`'le gelir);
  - (4) yanıtlandı (`01b:36`, `27a:14`, `26m:25-27`: `profile.derive`, Aşama 1'de boş); boş olmayan liste ertelendi: "yorum satırı"nın dönemine (`26n:66-67`);
  - yer tutucu notu (`26e:64`): yanıtlandı (`26m:28`; kural değişmez, yeniden yapım Kurucu'nun);
  - vaka şeması notu: yanıtlandı (`26m:28-31`, alan eklenmez); kimlik olarak bulgu kimliği ve başlığı ertelendi:
    `system_tp` vakası üreten ilk partinin dönemine (`26n:68-70`; en geç Aşama 4, `asama-4/07:29`).
  `seed-090-dev-case-store-layout-carriage-and-two-validity-edges-unstated` → `26m:33-56`:
  - (1) yanıtlandı (`26m:34-37`: `cases/dev.jsonl`, satır başına bir vaka); hash zinciri ertelendi: P1 çıkış dönemine (`26n:57`; önek kuralı bugün yeter);
  - (2) yanıtlandı (`26m:38-40`: `yaz` yazar, `çek` okur, `pulled` taşır);
  - (3) yanıtlandı (`26m:41-43`: vaka tabanına sabit kalır); geri çekme satırının biçimi ertelendi: Aşama 2'ye
    (`26n:64-65`; Aşama 1'de yazıcısı yok);
  - (4) yanıtlandı (`26m:44-47`: vaka satırını yalnız `yaz` yazar, kapı yol kuralıyla kabul eder);
  - (5) yanıtlandı (`26m:48-50`: ret);
  - (6) yanıtlandı (`26m:51-54`: birincil başvuru hunk'ın tamamen içinde);
  - "(1)–(4) sayfaya gelene kadar" notu: yanıtlandı (`26m:55-56`: (1)–(4) artık sayfada, dev vakaları yazılabilir);
  - `build.py`'nin grubu notu: yanıtlandı (`26m:55`; grup kuralı `26e:68-69` değişmez, yeniden yapım Kurucu'nun).
  `seed-091-harness-score-fingerprint-hash-observation-verdict-and-k4-census-unstated` → `26m:58-72`:
  - (1) yanıtlandı (`26m:59-63`: yalnız hakem kodu; biçim kurulduğu gibi); puanlayıcıda yeniden türetme ertelendi: P1 çıkış dönemine (`26n:58-59`);
  - (2) yanıtlandı (`26m:64-65`: ilk gözlem);
  - (3) yanıtlandı (`26m:66-71`: hüküm kuralı; taban yalnız çıkışta);
  - (4) ertelendi: Aşama 3'e (`26m:72`, `26n:56`; K4 orada gelir).
  `seed-092-test-9-proof-online-reason-and-test-11-scope-unstated` → `26n:12-26`:
  - (1) yanıtlandı (`26n:13-16`: statik okuma ve ağsız koşu, ikisi de);
  - (2) yanıtlandı (`26n:17-19`: ret, satır yok);
  - (3) yanıtlandı (`26n:20-21`: döngünün testi; modül var olur);
  - (4) yanıtlandı (`26n:22-25`: sıfırdan yaratılan yollar); tam yol listesi ertelendi: P1 çıkış dönemine (`26n:60`);
  - boş olmayan prova oyuncağı notu: yanıtlandı (`26n:26`; söz gevşetilmez, fikstür Kurucu'nun).
  `seed-094-drift-activity-reason-time-form-permission-and-stale-check-edges-unstated` → `26n:28-43`:
  - (1) yanıtlandı (`26n:29-31`: `ref_change`);
  - (2) yanıtlandı (`26n:32-34`: `YYYY-MM-DDTHH:MM:SSZ`);
  - (3) yanıtlandı (`26n:35-37`: açık hedefte izin yok); özel hedefin kimliği ve izni ertelendi: ilk özel hedefin dönemine; aşama sınırı yerine
    kapı: kimlik bir sayfada adlandırılmadan özel hedef bağlanmaz (`26n:61-63`);
  - (4) yanıtlandı (`26n:38-40`: koşunun uyarı notu);
  - (5) yanıtlandı (`26n:41-42`: çıkış numarası arayüz değil; iş kırmızı bitmez).
  `seed-095-asama-1-per-finding-brakes-have-no-policy-key` → `26n:44-53`:
  - soru (iki anahtar adı ya da hücrenin tek evi olduğu cümlesi): ertelendi: `fixer.llm`'i getiren döneme (`26n:44-53`;
    o zamana kadar hiçbir kod okumaz, anahtarlar anayasal bütçe anahtarıdır, sahip o dönemde karar verir; önerilen
    değerler ve adlar başlangıç noktası olarak kayıtlıdır; `18a:62` işaret eder); gevşetme L-AF1 (`26n:51-53`).
