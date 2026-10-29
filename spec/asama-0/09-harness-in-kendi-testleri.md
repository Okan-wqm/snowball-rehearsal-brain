# Aşama 0 §0.9 — Harness'in ve hakemin kendi testleri

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken
Çapa: beklemede: aşama 0 çıkış raporu

---

Testleri Kurucu yazar; önyükleme hakemi onları her push'ta `koş`ta koşturur ve tohum vektörlerini
(`tohum/29a`) Kurucu'nun koduna karşı ayrıca uygular. Vektörler tabandır, yeter değildir.

| # | Test | Ne zaman |
|---|---|---|
| 1 | Boş bulgu → recall 0, hata yok | Aşama 0 |
| 2 | Oracle bulguları → recall 1,0 | Aşama 0 |
| 3 | Doğru dosya, yanlış property → 0 | K3 ile |
| 4 | Doğru dosya, eşlenmiş satır farklı → isabet değil (K0); sembol dışı → değil (K3) | Aşama 0 |
| 5 | `required_change` boş → 0 | K3 ile |
| 6 | Manifest dışı ya da hash uyuşmayan ref → red, raporlanır | Aşama 0 |
| 7 | Determinizm: aynı girdi iki kez → aynı rapor | Aşama 0 |
| 8 | Sızıntı: `.git`, `<state_root>`, hariç dizinler yok; planted kimlikleri temizlenmiş | Aşama 0 |
| 9 | LLM yokluğu: harness modülleri istemci import etmez, ağ kapalıyken geçer | Aşama 0 |
| 10 | Maliyet: `run_meta` eksikse `invalid`; isabet sıfırken `value_per_usd` 0; maliyet sıfırken oran yok | Aşama 3 ile |
| 11 | Genellik: oyuncak repoda `<state_root>` sıfırdan büyür; hedef repoya özgü ad yok, tohum dahil | Aşama 0 |
| 12 | Parmak izi: aynı bulgu iki koşuda tek sayılır; satır kayması kimliği değiştirmez | Aşama 0 |
| 13 | Zincir: vektör V1–V3; bozulmuş satır ve yalnız-ekleme ihlali yakalanır | Aşama 0 |
| 14 | Şema: her artefakt `tohum/26` ve `26b` şemalarına uyar | Aşama 0 |
| 15 | Held-out erişimi: held-out `harness.score` hakem exit işi dışından reddedilir | Aşama 4 ile |
| 16 | Snapshot kanaryası, clean ve planted'da | Aşama 1 ile |
| 17 | Görünümler: `status.md` ve üretilmiş sayfalar defterden sıfırdan kurulur ve aynı çıkar | Aşama 1 ile |
| 18 | Held-out hesaplanamaz: dev grupları dışındaki adaylar arasında üyelik AUC ≤ 0,5 + ε | Aşama 4 ile |
| 19 | Profil yeniden türetme: önerilen profil hakem türetmesinden farklıysa reddedilir | Aşama 0 |
| 20 | Kırmızı kontrol: bilinen kötü aday her `koş`ta kırmızı; yeşil çıkarsa koşu geçersiz | Aşama 0 |
| 21 | Konteyner kanaryası: koşan kod ağa çıkmaya, konteyner dışına yazmaya, ortamdan sır okumaya çalışır; üçü de başarısız, dışarıda alınan hash'ler değişmemiş | Aşama 0 |
| 22 | Dispatch kanaryası: oyuncak repodaki hook, `.mcp.json` sunucusu ve yönerge dosyası `agent.dispatch` oturumunda yüklenmez | Aşama 0 |
| 23 | Yalnız düz dosya: sembolik bağ, alt modül, `../` yolu ya da ret listesindeki yol içeren aday reddedilir | Aşama 0 |
| 24 | Kayma: kurulum özetinden farklı kural, beyan dışı App ya da `brain/**`'da sırla tetiklenen hedef iş akışı taklidi sert duruş üretir | Aşama 0 |
| 25 | Geri alma: nöbetçi kırmızısında hakem son merge'ü geri alır, `cause` yazılır. `exit.drill`: cevap anahtarının hash'i koşudan önce zincirde; açılım eşleşmezse prova `FAIL`; tohumlanmış kötü merge'ün `cause`'u anahtarla aynı; `harness.drill` prova vektörlerinde referans yargıçla aynı kararı verir (`tohum/29c`) | Aşama 0 |
| 26 | Kapalıya düşme: kill switch, bütçe tavanı, Rekor hatası, kayma, rakip zaman aşımı işi durdurur ya da reddeder | Aşama 0 |
| 27 | Çıkış örneklemi: aynı tohum aynı örneklem, farklı tohum farklı; mutasyonla üretilebilen her kural en az bir vaka | Aşama 0 |
| 28 | İstatistik: vektörlerdeki CP, `x_eff` ve tam McNemar değerleri | Aşama 0 |
| 29 | Kilit: (aşama, spec hash, çıkış satırı) eşleşmeyen geçiş reddedilir | Aşama 0 |
| 30 | Kurucu defteri: zincirsizden zincirliye geçişte önceki dosyanın sha256'sı ilk zincirli satırda; `kind` kümesi; oyuncu kodu `referee/`'yi import etmez | Aşama 0 |
| 31 | Profil önerisi: oyuncak repoda diller, araç zincirleri, etkilenen-test komutu ve güvenlik yolları çıkarılır ve şemaya uyar | Aşama 0 |
| 32 | Taban avcı: LLM yok; aynı snapshot iki koşuda aynı bulgu dosyası | Aşama 0 |
| 33 | `spec.lint`: kasıtlı bozulmuş spec'lerde eksik bölüm, anahtarsız eşik, eksik zorunlu çıkış satırı, iki mekanizmalı mikro özellik, okuyucusuz dosya ve yasaklı ifade yakalanır | Aşama 0 |
| 34 | `deps.fetch`: kurulum betiği isteyen paket profilde işaretli değilse reddedilir; aynı kilit dosyası aynı içerik adresi; lisansı `license_allowlist` dışında ya da bulunamayan paket, ve lisansı söyleyen yerlerden biri izinsiz olan paket reddedilir (`tohum/24`) | Aşama 0 |
| 35 | Kapı: sıfır test, mandal artışı, izin listesi dışı tanım hash'i ve artefakt hash uyuşmazlığı reddedilir; iki aday aynı anda merge olmaz | Aşama 0 |
| 36 | Nöbetçi: merge sonrası etkilenen testler `koş`ta; kırmızıda 3/3 flaky kuralı | Aşama 0 |
| 37 | `llm.call` (taklit sağlayıcıyla): tipli girdi dışı alan prompta girmez; bütçe belirteci aşımı kesilir; sunulan model farklıysa koşu geçersiz | Aşama 0 |
| 38 | `secrets.scan`: diff, satır ve promptta gömülü sahte sır yakalanır; prompt gönderilmez | Aşama 0 |
| 39 | `ledger.append`: döngü başına tek commit; oyuncu önerisi `trust: inferred`; yazımdan önce `chain.verify` | Aşama 0 |
| 40 | `rekor.anchor` (taklit Rekor'la): kök kaydı yazılır; yazılamazsa sert duruş | Aşama 0 |
| 41 | Gözcü: `tohum/28`'deki her tetik yapay girdiyle doğru dondurmayı ya da sert duruşu üretir | Aşama 0 |
| 42 | `status.block`: dondurma, bütçe ve insan dokunuşu bloğu defterden üretilir; elle düzenleme ret | Aşama 0 |
| 43 | `brain.accept`: test, vektör ya da rakip satırından biri eksik ya da kırmızıysa kabul yok; spec ve kod isteği karışık push ret | Aşama 0 |
| 44 | `docs.index`: başlıklardan üretilen dizin deterministik | Aşama 0 |
| 45 | Etkinleştirme provası: yerel git uzağı ve taklit GitHub API'sine karşı aktarım, genesis satırı, iyi aday merge, kötü aday ret | Aşama 0 |
