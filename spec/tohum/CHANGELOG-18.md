# Değişiklik Günlüğü — Tohum, 2.2'nin On Yedinci Kayıtları

Tarih: 2026-11-23 · Sürüm: 2.2
Okunma: bir sayfanın geçmişi aranırken
Çapa: git geçmişi ve zincirdeki spec hash satırları

- 2.2 (2026-11-23, E733–E735; tohum dönemi AI, P1 çıkış dönemi; rapor masası uzlaşısı, sahibin yetkisiyle operatör
  kararı; frenler sahip kararı). **İlk iş** (`25` 10b). Teslimden itibaren önyükleme hakeminin hiçbir denetimi kırmızı
  olmaz: bu dönem ne bir tablo, ne bir zorunlu politika yolu, ne hakemin kodu değiştirir; politika fikstürleri iki fren
  anahtarını zorunlu olmadan kazanır (`29v`), gerisi sayfalardır. Kurucu'nun bugünkü işi sürer, sırası
  `CHANGELOG-14`'ünkidir. Bu dönem P1 çıkışının parçasıdır ve hiçbir yanıtı yeniden yapım istemez: seed-073'ün (a), (c),
  (d)'si ve seed-087'nin (iv)'ü kurulduğu gibi benimsendi. Raporların teyidi `26l`'nin kuralı olarak kalır, bu listenin
  bir maddesi değildir. Yeni `26r` (organın dosyası, taşınması ve imajı; `26e:63` ona işaret eder) ve `26s` (P3'ün
  sayfadaki tablosu, testler 59 ve 60, frenler; `26e`, `26h` ve `29v` işaret eder); `24a`'nın beyin kökü
  `organs/<id>.json` ve `accept.json` kazanır. `26j:35` işin sırasıdır, bir denetim değil; `26j:79-80` (iv)'ün yanıtıdır.
  **Gevşetme L-P1E** (kapsamlı; sahibe bildirilir; `26j:80`): `26j:35`'in sırasını kod reddetmez, Kurucu'nun verisi
  tutar; kapsamı P1'dir, P1'in aktarımıyla biter; görünürdür: beyin kökünde bugün `accept.json` yoktur. **L-AF1 bitti**
  (`26n:44-53`): frenlerin anahtarları `18a`'dadır ve `02:22`'nin eşik maddesi hücreye uygulanır. Başka gevşetme yok;
  sıkılaştırma yok. P3'ün makine kopyası (`stages/stage1-P3.json`) bu dönemde değildir. `26h:44` düzeltildi: K3+ dalı
  P3'te değildir, K3'ü getiren Aşama 3 partisiyle gelir.
  Yanıtlanan raporlar; her madde raporun yazıldığı hâliyle, kendi etiketiyle bir satırdır:
  `seed-073-organ-definition-layout-and-carriage-unstated` → `26r:13-53`:
  - (a) kaydın beyindeki yeri ve organın giriş noktasını adlandıran dosya: yanıtlandı (yeni, kurulduğu gibi benimsendi;
    `26r:13-33`; `24a`'nın düzeni `organs/<id>.json` ve `accept.json` kazanır);
  - (b) `definition_sha256`'nın hangi baytları hangi kuralla kapsadığı: yanıtlandı, sayfada zaten vardır (`26e:61-63`,
    `26l`'yle yargılandı; kurulan fonksiyon `runner/organs.py:15-19`); yeniden açılmadı;
  - (c) kabul edilmiş SHA'nın organlarının `koş`'a ulaşması: yanıtlandı (yeni, kurulduğu gibi benimsendi; `26r:35-43`:
    `pulled`'da `organs.json`, `organs/<oid>/entry.json`, `organs/<oid>/files/<yol>`, `accept.json`);
  - (d) giriş noktasının koştuğu imaj: yanıtlandı (yeni, kurulduğu gibi benimsendi; `26r:45-53`, dilin sonucu dahil;
    lint aracının yolu `26m:23-24`'tedir, seed-074'ün kalanı seed-089'la geldi);
  - soru (a)–(d)'nin teyidi ya da düzeltmesi: yanıtlandı (kurulduğu gibi teyit edildi, düzeltme yok);
  - soru `26b`'nin `tools[]`'u: yanıtlandı, sayfada zaten vardır (`26e:61-63`: LLM organının araçları hash'ine girer);
    LLM organının modeli ve araçları P3'ün 2. satırıyla tanımına girer (`26r:28-29`, `26s:53-54`);
  - soru `accept` satırı: yanıtlandı, sayfada zaten vardır (`26h:24-30`, `26j:37-39`); yeniden açılmadı;
  - soru öbür alanlar (`kind`, `state`, `born_from`, `derived_from`, `transition_evidence`, `reputation`): ertelendi: ilk
    okuyucularına (organın yaşam döngüsü ve itibar görünümü, bir sınıfta iki aday organ doğunca canlı, `12:20-22`,
    `03:68-70`, `asama-1/12:30,32`; `DEGRADED`/`RETIRED` `12:30`, `12a:16`); Aşama 1'de değil, sayfalar bunu zaten tutar;
  - soru başka türlü sabitlenen olursa `çek`, `pulled` ve `runner.organs` onu izler: yanıtlandı (hiçbiri başka türlü
    sabitlenmedi; yeniden yapım yok).
  `seed-087-allowlist-package-layout-accept-trigger-and-run-ids-unstated` → `26j:79-80`:
  - (a) paketin dosyası ve alanı: yanıtlandı, sayfada zaten vardır (`26j:31-32`);
  - (b) hazır adaylar: yanıtlandı, sayfada zaten vardır (`26j:33-34`);
  - (c) giriş tetiği: yanıtlandı, sayfada zaten vardır (`26j:35-36`; `26j:35` artık işin sırası olarak yazılı);
  - (d) `evidence_run_ids`: yanıtlandı, sayfada zaten vardır (`26j:37`, `26j:73-75`);
  - (e) satır türü: yanıtlandı, sayfada zaten vardır (`26j:39`, `26b:34-35`);
  - (f) çiftle anahtarlanma: yanıtlandı, sayfada zaten vardır (`26j:38`);
  - (g) listeden çıkma: yanıtlandı, sayfada zaten vardır (`26j:38-39`, `26j:78`, L1);
  - (h) kapının tanımları: yanıtlandı, sayfada zaten vardır (`26j:78`);
  - (i) giriş isteğinin yolu: yanıtlandı, sayfada zaten vardır (`26j:68-72`);
  - (ii) koşu kimliği: yanıtlandı, sayfada zaten vardır (`26j:73-75`);
  - (iii) P1'de Aşama 0 yolları: yanıtlandı, sayfada zaten vardır (`26j:76-78`);
  - update_part_1'in (b)'si, genesis devri dışında `no_organ` ile reddedilen hazır aday: yanıtlandı, sayfada zaten vardır
    (`26j:33-34`; kuruldu ve bağlandı);
  - (iv) `accept.json` için aşama koruması: yanıtlandı (koruma yok, kurulduğu gibi benimsendi; `26j:79-80`; gevşetme
    L-P1E). Nedenler: `referee/` yalnız partilerle değişir; P1'in kodu kendi aktarımından, P2 açıkken canlıdır, "P1
    açık" koruması yalnız testlerde tetiklenebilirdi; test 55 P1'de bir `accept` satırı yazar; P1'de organ yoktur
    (`accept_unknown`); çift anahtarı (`26j:38`) erken bir çiftin MF5'i kalıcı olarak engelleyemeyeceğini söyler; MF5 →
    MF6 sırasını MF5'in kırmızı testi ve kod isteğinin incelemesi (`29b`) tutar; MF9'un kendi kanıtı canlı rettir
    (`26j:40-41`), bir koruma onu engellemezdi; erken bir giriş güvenliğe değil MF5'in reddinin kanıtına mal olur:
    giren organ önyükleme hakeminin kabul ettiği bir organdır ve adayı yine diff-guard'dan, üç lint koşusundan, test
    koşusundan ve kırmızı kontrolden geçer (`26j:54-56`). Yeni test ve vektör yok (MF9'un grubu yok, `26e:26`).
  E703'ün "P1 çıkış dönemi" ertelemeleri (`26n:57-60`), bu dönemde karara bağlandı:
  - `cases/dev.jsonl`'un hash zinciri (seed-090 (1)): ertelendi: Aşama 1 çıkış partisine (setin bütün geçmişini okuyan ilk
    hüküm `exit.sample`, test 27, `asama-1/13`'ün "Aşama 1 çıkışı" satırı); o zamana kadar yalnız ekleme önek kuralı ve `28`'in sert duruşu tutar;
  - puanlayıcıda parmak izinin yeniden türetilmesi (seed-091 (1)): ertelendi: ilk LLM avcısını getiren döneme, en geç
    Aşama 4 partisi; o zamana kadar her puanlanan parmak izini hakemin tek fonksiyonu yapar, L-AH1 vektör komutunda kalır;
  - test 11'in tam yol listesi (seed-092 (4)): reddedildi (`26n:22-25` listenin tanımıdır; sabit liste her yeni yazıcıda
    bir sayfa düzeltmesi isterdi ve daha güçlü olmazdı).
