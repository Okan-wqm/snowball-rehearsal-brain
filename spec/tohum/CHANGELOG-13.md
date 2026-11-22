# Değişiklik Günlüğü — Tohum, 2.2'nin On İkinci Kayıtları

Tarih: 2026-11-22 · Sürüm: 2.2
Okunma: bir sayfanın geçmişi aranırken
Çapa: git geçmişi ve zincirdeki spec hash satırları

- 2.2 (2026-11-22, E694–E696; tohum dönemi AD; rapor masası uzlaşısı, sahibin yetkisiyle operatör kararı).
  **İlk iş** (`25` 10b; Kurucu'nun dersi f1741). Teslimden itibaren önyükleme hakeminin hiçbir denetimi kırmızı
  olmaz: bu dönem ne bir tablo, ne bir vektör, ne bir zorunlu politika yolu değiştirir; yeni `reports_unconfirmed`
  bir uyarıdır, hiçbir zaman neden değildir; `done_mf` 1–8 açık P1 tablosunun öneki kalır. İlk iş `CHANGELOG-12`'nin
  sırasıdır, P1'in çıkış isteği MF1–MF12'nin hepsi bitmeden geçmez:
  1. MF9, izin listesi ve `accept` yazıcısı (`26j`; seed-087'nin kalanları sayfanın sonundadır);
  2. birinci maddeden hemen sonra, kırmızı görev değil, sahibin ipuçları (bu kez kural esnetildi; `00e`): E693 ve E692;
  3. MF10, MF11 ve MF12 (`26j`), MF12 sözleşmeleri T1 ve T2 ile (`26k`).
  Raporların teyidi bu listenin bir maddesi değildir, `26l`'nin kuralıdır: bir dönemin yanıtladığı her rapor, o dönemin
  tesliminden sonraki ilk oturumda `confirmed`, `declined` ya da eksik kalan için açılan yeni bir raporla `superseded`
  olur; bu kural bu dönemin tesliminden sonraki ilk oturumdan başlar.
  Yeni `26l` "Şemalar, Devam: Raporların Yaşam Döngüsü" (`00a` ve `26c` ona işaret eder): rapor masası uzlaşısı (E694):
  durumların kapalı kümesi (`open`, `confirmed`, `declined`, `superseded`, `withdrawn`), hepsini Kurucu yazar; okuma
  kapalıdır (bilinmeyen ya da olmayan durum, kanıtsız `confirmed` ya da `declined`, dosya adından farklı `id`, gerçek
  bir ardıla dayanmayan `superseded` `open` sayılır); operatörün tipli yanıtı `{id, changelog, kind}` tohum verisindedir
  (`seed/bootstrap/reports/answers.json`; tek kaynak); teyidin zamanı ve
  tipli kanıtı (`epoch`, `answered_by`, `check`, `check_kind`); kalan ya da yanlış yanıt `derived_from`'lu yeni
  rapordur; iki sayım: `reports_open` (operatörün borcu) ve yeni `reports_unconfirmed` (Kurucu'nun borcu). Gevşetmeler
  (operatör kararı, sahibin yetkisiyle; hiçbiri anayasal değil): L-AD1 bir teyit sayfaları okumaya dayanabilir
  (`check_kind: read`); L-AD2 beyin `6b5966a`'da teyit edilmiş 73 rapor baytları değişmedikçe yeni kanıt alanları
  olmadan kapalı kalır (`(id, sha256)` taşınır); L-AD3 `reports_open` operatörün borcuna daralır, düşen kısmı
  `reports_unconfirmed` taşır. Tohum verisinin girdileri bugün açık 16 raporun bu günlüklerdeki satırlarıdır; seed-073'ün
  `CHANGELOG-9`, seed-085'in `CHANGELOG-10` ve seed-087'nin `CHANGELOG-11` girdisi `partial`'dır. İstemindeki (d)
  görevi artık `26l`'ye işaret eden tek cümledir: istemin `prompt_sha256`'sı değişir ve bu değişiklik AD'nin teslimiyle
  tek sınırda gelir (yeniden başlatmada tek `intervention` satırı).
  `26j` "İzin listesi, MF9: seed-087'nin kalanları" (E695): `accept.json` beyin kökünde, Kurucu commit'ler, kod
  isteğidir; imzalı sonucun `run.id`'si; genesis'ten sonraki yollar ve testlerin açık kapısı; (g), (h). Ertelenen
  (E696): (iv) `accept.json` için aşama koruması ve seed-073'ün (a), (c), (d)'si P1 çıkış dönemine. `26h` ona işaret eder.
  Yanıtlanan raporlar:
  `seed-087-allowlist-package-layout-accept-trigger-and-run-ids-unstated` → `26j:67-80`;
  `seed-073-organ-definition-layout-and-carriage-unstated` → `26j:79-80` ((a), (c), (d) P1 çıkış dönemine açıkça ertelendi).
