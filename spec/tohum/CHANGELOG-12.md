# Değişiklik Günlüğü — Tohum, 2.2'nin On Birinci Kayıtları

Tarih: 2026-11-21 · Sürüm: 2.2
Okunma: bir sayfanın geçmişi aranırken
Çapa: git geçmişi ve zincirdeki spec hash satırları

- 2.2 (2026-11-21, E691–E693; tohum dönemi AC; bağımsız inceleme ekibi kararı, sahibin yetkisiyle operatör kararı,
  sahibin ipucu).
  **İlk iş** (`25` 10b; Kurucu'nun dersi f1741). Teslimden itibaren önyükleme hakeminin hiçbir denetimi kırmızı
  olmaz: bu dönem ne bir tablo, ne bir vektör, ne bir zorunlu politika yolu değiştirir; `done_mf` 1–8 açık P1
  tablosunun öneki kalır. İlk iş P1'in kalan MF'leridir; P1'in çıkış isteği MF1–MF12'nin hepsi bitmeden geçmez:
  1. MF9, izin listesi ve `accept` yazıcısı (`26j`);
  2. birinci maddeden hemen sonra, kırmızı görev değil, sahibin ipuçları (bu kez kural esnetildi; `00e`): E693 oturum
     içinde kapsamlı doğrulama, E689'un hızlı geçişiyle, tam koşu bir kez son prepush'ta; E692 ilk ajan olarak push'tan
     önce koşan bir uyum denetçisi, beş bağlayıcı korkulukla; ikisi de ölçülerek;
  3. MF10, organ çıktısının tutulması; MF11, çalışma-zamanı adayının yeniden koşusu (`26j`);
  4. MF12, `yaz`'ın aday okuması (`26j`), sözleşmeleri T1 ve T2 ile (`26k`): `finding_unknown` ve
     `finding_not_open` merge seçilmeden önce verilen D5 nedenleridir; hiçbir adayın içeriği devri kullanılamaz kılmaz.
  Bu sıra `CHANGELOG-11`'in E689 ve E690 yerleşiminin yerini alır: E689'un hızlı geçişi artık E693'le birlikte MF9'dan
  hemen sonradır.
  Yeni `26k` "Şemalar, Devam: Bulgu Durumlarının Yazıcıları" (`26j` ve tohumun `asama-1/13d` kopyası ona işaret eder):
  bağımsız inceleme ekibi kararı (seed-088, E691): `fixed`'i merge kararı yazar; yeniden gözlem; geri alınan merge
  bulgusunu aynı devirde yeniden açar (iki uzmanın ayrıldığı yerde daha sıkı olan); açık olmayan bulguya karar adayın
  reddidir; `verified` ve `withdrawn` Aşama 1'de yazılmaz (gevşetme L-088, sahibin yetkisiyle operatör kararı). Yeni
  `00e` "Görev Haritası, Devam: Sahibin İpuçları III" (`00d` ona işaret eder): sahibin ipucu (E692).
  Yanıtlanan rapor:
  `seed-088-finding-states-fixed-verified-withdrawn-have-no-named-writer` → `26k:12-36`, `asama-1/13d:19`.
