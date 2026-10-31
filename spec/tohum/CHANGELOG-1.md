# Değişiklik Günlüğü — Tohum, 2.1 ve öncesi

Tarih: 2026-10-29 · Sürüm: 2.2
Okunma: bir sayfanın geçmişi aranırken
Çapa: git geçmişi ve zincirdeki spec hash satırları

- 2.1 (2026-10-28): ikinci beş incelemeden (istekler ve kararlar, bağlantı ve veri akışı, mantık,
  uçtan uca simülasyon, kırmızı takım) doğrulanan bulgular. Hakem reposu: oyuncu kendi hakemini
  yazamaz; kapı, kullanıcı hesabında da çalışan, yalnız hakem App'inin raporlayabildiği zorunlu
  durum kontrolüdür. Kurulum iki bölüm. Tohum koltukları, sözlük ve okuyucu tablosu, dondurma,
  araç imzaları sayfaları. Held-out hesaplanamaz havuzdan; bakış bütçesi rotasyonla sıfırlanmaz;
  Clopper–Pearson. Çıkış tabanları anayasal, prosedür yalnız sıkılaştırır. Keşif tüm ihlaller ve
  mandal; nöbetçi ve birinci ebeveyn bisect. Model kuralı iki modelle uygulanabilir hâle geldi.
  Oracle: property'den test, hunk kapsaması, kapı yeniden koşturur. Dersler: ilk okuyucu
  düzeltici, test-yazıcı okumaz, kredi rastgele saklamayla. Yasaklı ifade listesi tanımlandı.
- 2.0 (2026-10-28): beş bağımsız incelemeden (tutarlılık, istekler, uygulanabilirlik, kırmızı
  takım, ölçüm ekonomisi) sonra yeniden yazım. Yetki üç yere ayrıldı (beyin reposu, hedef repo,
  mühürlü depo) çünkü tek repoda dosya bazlı izin yok; held-out mühürlü depoya taşındı; cevap
  anahtarına `provenance` geldi; K0 oracle'ı "araç yeşil" yerine "base SHA'ya göre fark" oldu;
  SHADOW→ACTIVE kilidi çözüldü; istatistik sayfası ve UNMEASURABLE verdict'i; dinamik eşik
  prosedürü ve `policy.json`; oracle sertleştirme ve diff-guard; ikili ayrık model kuralı ve
  donmuş koltuklar; Gözcü deterministik; itibar Beta alt sınırı ve kök neden kredisi; ablasyon
  bileşik skor; zincir için CI attestation; çalışma modeli, kurulum günü ve şema sayfaları;
  hafıza modeli, kas sinyalleri, dersler, metrikler, çok repo, yama değil mimari çözüm sayfaları;
  tohumdan hedef repoya özgü adlar çıkarıldı; sistem çıktıları İngilizce ve bulgular iki formatta.
  Sonra rakip API anahtarsız çalışır oldu (iç kullanım; ticari kullanımda anahtara geçilir): `claude` CLI
  oturumuyla, hakemin kendi MCP sunucusuyla ve pinli npm kilidiyle; model SDK'sı ve fiyat tablosu kalktı,
  her koşu izolasyonunu CLI'nin `init` olayından kanıtlar (`29b`).
- 1.0 (2026-10-28): tek dosya özellik başına sayfalara bölündü.
- 0.1–0.11 (2026-10-28): tek dosya taslak dönemi; geçmişi zincirde ve git'te.
