# Değişiklik Günlüğü — Aşama 1

Tarih: 2026-10-29
Okunma: bir sayfanın geçmişi aranırken
Çapa: git geçmişi ve zincirdeki spec hash satırları

- 2.2 (2026-10-29, daraltma): Aşama 0'ın daraltılmasıyla (`asama-0/CHANGELOG`) hakem donuk değildir, yalnız aktarımla değişir: P1 (organ koşucusu, snapshot, vaka seti, harness, LLM yokluğu, `drift.check`, Gözcü, `operating{}` ayarı) Aşama 1 MF1'den önce, P2 (güvenlik gözlemi, `agent.dispatch`, avcı koltuğu) içeride, çıkış partisi (`exit.sample`, snapshot kanaryası, `spec.lint`) (A) ile (B) arasında (yeni §1.13; Aşama 0 2.2'nin §0.4–§0.7'si ve §0.8'in metrikleri §1.13a–§1.13e'ye taşındı). Push kabulü önyükleme hakemindedir; MF6'nın `accept` satırını döngünün `yaz`'ı yazar ve ilk organ merge'üdür. Çıkış (A) + aktarım + (B); `#kapsama-kaydi` (`hunk_covered`, `mutant_killed`) ve `#zayif-oracle` satırları; `#lint` ve `#lock` tohumun spec denetimi ve kilit çiftidir. Bütçe kaçak frenidir; oturum ve USD ölçüdür, abonelik penceresi (429) kesintidir.
- 2.2 (2026-10-29): iç kullanımda API anahtarı ve geçit yoktur (`tohum/CHANGELOG`): `llm.call` çağrısı `claude` CLI'siyle, çağrı başı tavan `--max-budget-usd`; `#belirtec` çağrı başı bütçedir, koşuya bağlı belirteç satışta gelir (§1.5, §1.8, §1.10).
- 2.2 (2026-10-28): yalnız oyuncu organları, sekiz mikro özellik; aday yayımlanır, hakem yoklar ve uygular; düzeltici araçsız tek çağrı; harita, sözleşme, itibar, ders enjeksiyonu, organ yaşam döngüsü, bisect ve `main` senkronu ilk okuyucularına taşındı; çıkışta en az bir canlı merge ve geri alma sınırının dürüst ifadesi. Sonra: özet getirdiği yetenekleri beyan eder, çıkış satırları `#kimlik` taşır; eksik zorunlu satırlar eklendi (bütçe belirteci, giden prompt taraması, lisans kapısı) ve öğrenmenin ham maddesini sınayan geri alma provası.
- 2.1 (2026-10-28): keşif tüm ihlaller ve taban; mandal; harita (a) ve kapsama; sözleşme; nöbetçi, bisect, şablonlu ders; kapı yeniden koşturur; kurulum istisnası ile hakem bileşenleri; kanarya kuralı; teslim listesi tamamlandı.
- 2.0 (2026-10-28): inceleme sonrası yeniden yazım: fark oracle'ı, `fix` aralığı, güvenlik yollarına
  dokunmama, SHADOW→ACTIVE dev sayılarıyla (N = 3), 72 saatlik pencere ve 3 haftalık takvim,
  sıralı mikro özellikler, tam teslim listesi, model ayrıklığı, üretilmiş sayfalar, doğruluk
  özellikleri bölümü, inşa-zamanı bütçesi.
- 1.0 (2026-10-28): bölüm başına sayfalar.
- 0.1–0.5 (2026-10-28): tek dosya taslak dönemi.
