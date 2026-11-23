# Değişiklik Günlüğü — Tohum, 2.2'nin On Sekizinci Kayıtları

Tarih: 2026-11-23 · Sürüm: 2.2
Okunma: bir sayfanın geçmişi aranırken
Çapa: git geçmişi ve zincirdeki spec hash satırları

- 2.2 (2026-11-23, E736; tohum dönemi AJ; sahibin ipucu).
  **İlk iş** (`25` 10b). Teslimden itibaren önyükleme hakeminin hiçbir denetimi kırmızı olmaz: bu dönem ne bir tablo,
  ne bir vektör, ne bir zorunlu politika yolu, ne hakemin kodu değiştirir; yalnız sayfadır. Kurucu'nun bugünkü işi
  sürer, sırası `CHANGELOG-14`'ünkidir; E736 bir görevdir, kırmızı bir görev değil, ve hiçbir yeniden yapım istemez.
  Raporların teyidi `26l`'nin kuralı olarak kalır, bu listenin bir maddesi değildir.
  Yeni `00f`'ye sahibin ipucu (E736; görev, reçete değil): E697'nin sınıf kuralı (`00e:58-60`) Kurucu'nun bütün işine
  uygulanır: ret, rakibin çürütmesi, kendi denetimlerinin ya da ajanlarının yakaladığı hata ve işe yarayan kabul her
  biri yanlışlanabilir bir kaydın kaynağıdır (`22:62-63`); aynı sınıf iki kez gelince doğduğu katmanda, dönüşünü
  yakalayan bir denetimle kapanır (`23:12-15`); hiçbir şey üstü örtülerek kapanmaz (zayıflatılan, atlanan ya da silinen
  test ya da denetim, düşürülen eşik, neden satırı olmayan erteleme ya da muafiyet yok; `02:79-80` olduğu gibi kalır);
  5 oturumdan sonra aynanın pencere başına tekrar eden sınıfları (`26o:59-60`) artmaz, artarsa yaklaşım kanıtı
  adlandıran bir `decision` satırıyla yeniden yazılır. Korkuluklar: hiçbir hakem ya da denetim gevşemez, yeni hakem
  kuralı yok; teslimde yeniden yapım yok. `00e` sonunda `00f`'yi gösteren bir satır kazanır; satırlarından hiçbiri yer
  değiştirmez.
  Yanıtlanan rapor yok.
