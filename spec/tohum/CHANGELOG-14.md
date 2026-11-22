# Değişiklik Günlüğü — Tohum, 2.2'nin On Üçüncü Kayıtları

Tarih: 2026-11-22 · Sürüm: 2.2
Okunma: bir sayfanın geçmişi aranırken
Çapa: git geçmişi ve zincirdeki spec hash satırları

- 2.2 (2026-11-22, E697; tohum dönemi AE; sahibin ipucu).
  **İlk iş** (`25` 10b; Kurucu'nun dersi f1741). Teslimden itibaren önyükleme hakeminin hiçbir denetimi kırmızı
  olmaz: bu dönem ne bir tablo, ne bir vektör, ne bir zorunlu politika yolu, ne hakemin kodu değiştirir. İlk iş
  `CHANGELOG-13`'ün sırasıdır, değişmeden; P1'in çıkış isteği MF1–MF12'nin hepsi bitmeden geçmez:
  1. MF9, izin listesi ve `accept` yazıcısı (`26j`);
  2. birinci maddeden hemen sonra, kırmızı görev değil, sahibin ipuçları (bu kez kural esnetildi; `00e`): E693 ve E692,
     E697 uygulanarak: E692'nin ajanı da her ajan gibi Kurucu'nun yazdığı kurallarla kurulur ve ölçülür;
  3. MF10, MF11 ve MF12 (`26j`), MF12 sözleşmeleri T1 ve T2 ile (`26k`).
  Raporların teyidi `26l`'nin kuralı olarak kalır, bu listenin bir maddesi değildir.
  `00e`'ye sahibin ipucu (E697; görev, reçete değil): ajanlar, Kurucu'nun yazıp beyinde tuttuğu kurallarla kurulur (ne
  verildiği, dersler ve hafıza dahil; çıktının denetimi; koşu başına başarım ölçümü; yeniden tasarım ve emeklilik);
  Kurucu zaafları ölçülen başarımdan kendisi bulur ve her sınıfı kurallarda mimari bir değişiklikle kapatır; kurallar
  yanlışlanabilir kayıtlardır. Korkuluklar: E692'nin 1–3. korkulukları her ajan koşusuna uygulanır; önyükleme hakemi,
  rakip ve tam prepush değişmez; kurallarla geçen 5 oturumdan sonra ölçülen iyileşme yoksa kayıt ve yeniden tasarım.
  Yanıtlanan rapor yok.
