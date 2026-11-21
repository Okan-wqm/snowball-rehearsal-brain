# Değişiklik Günlüğü — Tohum, 2.2'nin Onuncu Kayıtları

Tarih: 2026-11-21 · Sürüm: 2.2
Okunma: bir sayfanın geçmişi aranırken
Çapa: git geçmişi ve zincirdeki spec hash satırları

- 2.2 (2026-11-21, E685–E690; tohum dönemi AB; bağımsız inceleme ekibi kararı, operatör ve sahip kararları).
  **İlk iş** (`25` 10b; Kurucu'nun dersi f1741). Teslimden itibaren önyükleme hakeminin hiçbir denetimi kırmızı
  olmaz: `done_mf` 1–7 açık P1 tablosunun öneki kalır, yeni `root_files` grubu yalnız MF8 bitince koşar. İlk iş P1'in
  üç yeni satırıdır (`26j:48-59`); `done_mf` önek kaldığı için MF8 ve MF9'dan sonra kurulur, P1'in çıkış isteği
  MF1–MF12'nin hepsi bitmeden geçmez:
  1. MF10, organ çıktısının tutulması (`runner/organ_output.py`, test 56);
  2. MF11, çalışma-zamanı adayının yeniden koşusu (`runner/candidate_rerun.py`, test 57);
  3. MF12, `yaz`'ın aday okuması (`loop/candidates.py`, test 58).
  Kırmızı görev olmayan iki sahip ipucu (bu kez kural esnetildi; `00d`) İlk iş'in birinci maddesinden sonra gelir,
  bütün P1'i beklemez: E689 Kurucu'nun kendi önerisi (f1766), prepush'ın hızlı geçişi; E690 bellekten yazılan adı
  defter satırı eklenmeden önce ağaca karşı denetlemek; ikisi de ölçülerek.
  Yeni `26j` "Şemalar, Devam: P1'in Bulgu Yazıcısı, İzin Listesi ve Aday Yolu" (`26e`, `26h`, `26a` ona işaret eder).
  Bağımsız inceleme ekibi kararı (seed-086, E685): kök satırı olan her durum dosyasına adıyla bir anahtar ekler,
  vektörü MF8'in `root_files` grubu (yeni `29zb`, `29d`); Kurucu'nun kurduğu biçimler benimsendi; kararın tabanı, yeni
  tabanda yeniden açılış, eşit satırlar, bilinmeyen bulgu; kap ve `proposed_by`; MF8'in bitti tanımı. Bağımsız
  inceleme ekibi kararı (seed-087, E686): `candidates/<id>/package.json`, hazır adayların sonu, giriş tetiği veridir,
  `evidence_run_ids`, `(organ_id, definition_sha256)` anahtarı, gevşetme L1 (çıkaran satır yok), MF9'un bitti tanımı.
  Operatör kararı, sahip kararıyla gevşetmeler L-b, L-c, L-j (seed-085, E687): `çağır` dondurmada çağrı yapmaz, `koş`
  sürer; ayın harcaması sunulan bütün hedeflerin defterinden; K0; yeniden başlatma satırı `setup/imports.jsonl`'da;
  kapalı kapının reddi `cause`'suz (`28a:57-67`, `26i`, `26j:43-46`). Operatörün tablo düzeltmesi, sahip onayı (E688):
  P1 MF10–MF12; `stages/stage1-P1.json` 12 MF, `26e`, tohumun `asama-1/13` ve `06` kopyası hizalandı.
  Yanıtlanan raporlar:
  `seed-085-gozcu-wiring-what-a-freeze-closes-and-what-a-cycle-measures` → (b), (c), (f), (h), (j) `28a:57-67`, `26i:27-29`, `26i:36-37`, `26i:45-46`, `26j:43-46`;
  `seed-086-findings-write-root-coverage-row-shapes-and-triggers-unstated` → `26j:12-28`, `29zb:11-17`;
  `seed-087-allowlist-package-layout-accept-trigger-and-run-ids-unstated` → `26j:30-41`.
