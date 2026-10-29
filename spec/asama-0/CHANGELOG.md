# Değişiklik Günlüğü — Aşama 0

Tarih: 2026-10-28
Okunma: bir sayfanın geçmişi aranırken
Çapa: git geçmişi ve zincirdeki spec hash satırları

- 2.2 (2026-10-28): Kurucu hakemin tamamını beyin reposunun `referee/` dizininde yazar; önyükleme hakemi ve tohum vektörleri denetler; çıkış iki parçalı: pinli SHA'da denetim, sonra operatör aktarımı ve oyuncak hedefte canlı etkinleştirme; K0 held-out havuzu yerine gizli tohumlu çıkış örneklemi ve kural sayımı; mühürlü depo Aşama 4'te; tek mekanizmalı mikro özellikler; bütçe ve takvim oturum sayısıyla. Kurucu denemesinden sonra: dört iki mekanizmalı mikro özellik bölündü (30 madde), her mikro özelliğin bir §0.9 testi var (30–45 eklendi), eşikler `stage_params` anahtarlarına bağlandı, çıkışa `lock.check` ve okuyucu tablosu satırları eklendi. Sonra: özet getirdiği yetenekleri beyan eder ve çıkış maddeleri `#kimlik` taşır; bağımlılık lisans kapısı (`deps.fetch`, test 34, çıkış); `gate.revert` mikro özelliği geri alma provasını (`exit.drill`, taahhüt ve açılım, test 25) içerir; çıkış raporu tekrarlanan ret sayısını yazar. Mikro özellik 18 prova yargıcını (`harness.drill`) da kapsar; test 25 onun prova vektörlerinde referans yargıçla aynı kararı verdiğini denetler (`tohum/29c`).
- 2.1 (2026-10-28): hakem reposu yerleşimi; tohum rakibi; hunk üzerinden satır eşleme ve tek yeni ihlal; rule_property_map; üç iş deseni; hesaplanamaz held-out; Clopper–Pearson; snapshot kanaryası kuralı; export-ignore'suz çıkarma; planted kimliklerine özgü temizleme; yeni kendi-testler 17–19; mikro özellik sırası (defter önce).
- 2.0 (2026-10-28): inceleme sonrası yeniden yazım: vaka ebeveyne sabitlenir, K0 ana kaynağı mutasyon,
  geçerlilik = fark, provenance, held-out mühürlü depoda, ID temizleme, match-rule v2 (K0 tam
  satır), UNMEASURABLE, inşa-zamanı rakip bütçesi, spec-lint ve dizin üreticisi teslimatta,
  sıralı mikro özellikler, doğruluk özellikleri bölümü.
- 1.0 (2026-10-28): tek dosya bölüm başına sayfalara bölündü.
- 0.1–0.4 (2026-10-28): tek dosya taslak dönemi.
