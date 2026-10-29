# Aşama 0 §0.9 — Hakemin kendi testleri

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken
Çapa: beklemede: aşama 0 çıkış raporu

---

Testleri Kurucu yazar; önyükleme hakemi onları her push'ta `koş`ta koşturur, tohum vektörlerini
(`tohum/29a`, `29d`) Kurucu'nun koduna karşı ayrıca uygular ve modülsüz kırmızıyı denetler (§0.14). Vektörler
tabandır, yeter değildir.

**Test bildirimi.** Kurucu kökte `snowball-tests.json` tutar (`tohum/26c`); hakem yalnız oradaki
komutları repo kökünden (vektörleri `referee/`'den) koşturur. Bitti denen (`done_mf`, sırayla 1'den)
mikro özellik k için "Ne zaman" sütununda "MF k" yazan her test numarası bir komuta bağlı değilse ya da
hiç komut yoksa sonuç kırmızıdır (`tohum/29b`). Bu eşleme §0.14'ün "Test" sütunuyla birebirdir; ikisinin
makine kopyası tohumdaki `seed/bootstrap/stages/stage0.json`'dur.

**Ne zaman.** "MF k" bu aşamanın testidir: 18 MF'ye 21 test. Başka değerler testin ilk okuyucusuyla gelen
partiyi (`asama-1/13`) ya da sınıfı adlandırır; o testler Aşama 0'da istenmez. Numaralar kalıcıdır; taşınan
test numarasını korur.

| # | Test | Ne zaman |
|---|---|---|
| 1 | Boş bulgu → recall 0, hata yok | P1 |
| 2 | Oracle bulguları → recall 1,0 | P1 |
| 3 | Doğru dosya, yanlış property → 0 | K3 ile |
| 4 | Doğru dosya, eşlenmiş satır farklı → isabet değil (K0); sembol dışı → değil (K3) | P1 |
| 5 | `required_change` boş → 0 | K3 ile |
| 6 | Manifest dışı ya da hash uyuşmayan ref → red, raporlanır | P1 |
| 7 | Determinizm: aynı girdi iki kez → aynı rapor | P1 |
| 8 | Sızıntı: `.git`, `<state_root>`, hariç dizinler yok; planted kimlikleri temizlenmiş | P1 |
| 9 | LLM yokluğu: harness modülleri istemci import etmez, ağ kapalıyken geçer | P1 |
| 10 | Maliyet: `run_meta` eksikse `invalid`; isabet sıfırken `value_per_usd` 0; maliyet sıfırken oran yok | Aşama 3 ile |
| 11 | Genellik: oyuncak repoda `<state_root>` sıfırdan büyür. Hedefe özgü ad denetimi Aşama 0'da tohumundur (§0.10 #genellik) | P1 |
| 12 | Parmak izi: aynı bulgu iki koşuda tek sayılır; satır kayması kimliği değiştirmez | P1 |
| 13 | Zincir: vektör V1–V3; bozulmuş satır ve yalnız-ekleme ihlali yakalanır | MF1 |
| 14 | Şema: döngünün yazdığı her artefakt (genesis, `events`, `cost`, `drill` satırları, kök, `status.md` bloğu) `tohum/26`, `26b` ve `26c` şemalarına uyar | MF18 |
| 15 | Held-out erişimi: held-out `harness.score` hakem exit işi dışından reddedilir | Aşama 4 ile |
| 16 | Snapshot kanaryası, clean ve planted'da | Aşama 1 çıkış partisi |
| 17 | Görünümler: `status.md` ve üretilmiş sayfalar defterden sıfırdan kurulur ve aynı çıkar | Aşama 1 ile |
| 18 | Held-out hesaplanamaz: dev grupları dışındaki adaylar arasında üyelik AUC ≤ 0,5 + ε | Aşama 4 ile |
| 19 | Profil yeniden türetme: diller, birim adayları, güvenlik yolları, hariç yollar ve test yolu kuralları türetilir; önerilen profil ya da tarif bunlardan farklıysa ya da onları daraltıyorsa reddedilir | MF4 |
| 20 | Kırmızı kontrol: bilinen kötü aday her `koş`ta kırmızı; yeşil çıkarsa koşu geçersiz | MF3 |
| 21 | Konteyner kanaryası (taklit koşucuyla; gerçeği §0.10a #kanarya): koşan kod ağa çıkmaya, konteyner dışına yazmaya, ortamdan sır okumaya çalışır; üçü de başarısız, dışarıda alınan hash'ler değişmemiş | MF3 |
| 22 | Dispatch kanaryası: oyuncak repodaki hook, `.mcp.json` sunucusu ve yönerge dosyası `agent.dispatch` oturumunda yüklenmez | P2 |
| 23 | Yalnız düz dosya: sembolik bağ, alt modül, `../`, güvenlik yolu, hariç yol, ajan yapılandırması (büyük-küçük harf duyarsız), yapılandırma, manifest, kilit ya da `.gitattributes` değiştiren ya da birimin `inputs`'u dışına çıkan aday reddedilir | MF7 |
| 24 | Kayma: kurulum özetinden farklı kural, beyan dışı App ya da `brain/**`'da sırla tetiklenen hedef iş akışı taklidi sert duruş üretir | P1 |
| 25 | Geri alma: nöbetçi kırmızısında hakem son merge'ü geri alır; geri alma commit'inin ağacı merge'ün ilk ebeveyninin ağacıdır; `cause` mekaniktir (`test_regression`, `build_break`, `lint_regression`, `impact_miss`, `unknown`). Ders provası yargıcı Aşama 2 partisindedir | MF13 |
| 26 | Kapalıya düşme: dağıtıldı. Kill switch 46'ya, fren tavanı 37'ye, Rekor hatası 40'a, kayma 24'e (P1), rakip zaman aşımı önyükleme hakemine (`tohum/29b`) | — |
| 27 | Çıkış örneklemi: aynı tohum aynı örneklem, farklı tohum farklı; mutasyonla üretilebilen her kural en az bir vaka | Aşama 1 çıkış partisi |
| 28 | İstatistik: vektörlerdeki CP, `x_eff` ve tam McNemar değerleri | P1 |
| 29 | Kilit: (aşama, spec hash, çıkış satırı) eşleşmeyen geçiş reddedilir | tohum (`setup/stage.json`, §0.10a) |
| 30 | Kurucu defteri: zincirli ve yalnız eklenmiş; `kind` kümesi | tohum (§0.10 #kurucu-defteri) |
| 31 | Profil önerisi: oyuncak repoda diller, araç zincirleri, etkilenen-test komutu ve güvenlik yolları çıkarılır ve şemaya uyar | ikinci birim ya da hedef bağlanırken |
| 32 | Taban avcı: LLM yok; aynı snapshot iki koşuda aynı bulgu dosyası | Aşama 4 partisi |
| 33 | `spec.lint`: kasıtlı bozulmuş spec'lerde eksik bölüm, anahtarsız eşik, eksik zorunlu çıkış satırı, iki mekanizmalı mikro özellik, okuyucusuz dosya ve yasaklı ifade yakalanır | Aşama 1 çıkış partisi; Aşama 0'da tohum (§0.10 #lint) |
| 34 | `deps.fetch` (npm): her tarball kilitteki `integrity` ile aynı, bir baytı değişmiş tarball reddedilir; `resolved` izinli kayıt defterinde değilse, git ya da dosya bağımlılığıysa ret; kurulum betiği isteyen paket tarifte işaretli değilse ret; aynı kilit aynı içerik adresi; lisans raporu yazılır (`tohum/24`) | MF5 |
| 35 | Kapı (`gate.check`, saf karar; fikstür `koş` çıktılarıyla): §0.8 madde 3–8'in her biri kendi nedeniyle reddeder (oracle ayırt etmiyor, araç üç koşuda farklı, `scope_violation`, mandal artışı, sıfır test, kırmızı kontrol yeşil, `merge_paused`, nöbetçisi bitmemiş merge); artefakt hash uyuşmazlığı ret | MF8 |
| 36 | Nöbetçi: merge sonrası etkilenen testler `koş`ta; kırmızıda 3/3 flaky kuralı | MF12 |
| 37 | `llm.call` (taklit `claude` CLI'siyle; API anahtarı yok): tipli girdi dışı alan prompta girmez; yerleşik araç, ayar kaynağı ve oturum kaydı yok; her çağrı `--max-budget-usd` tavanıyla gider, aşan çağrı kesilir; aşama freni doluysa çağrı yapılmaz; sunulan model farklıysa koşu geçersiz; 429 kesinti yazılır, ret değil; her çağrı `cost` satırı | MF15 |
| 38 | `secrets.scan`: diff, satır ve promptta gömülü sahte sır yakalanır; eşleşme koşuyu geçersiz kılar, prompt gönderilmez | MF2 |
| 39 | `ledger.append`: devir başına tek `brain/state` commit'i; yazımdan önce `verify --previous`; satırlar `secrets.scan`'den geçer; beyinden gelen içerik `proposed_by` taşır | MF10 |
| 40 | `rekor.anchor` (taklit imzalayıcıyla): kök bölüm uçlarının kanonik hash'i; imzalanır ve sonraki D1 doğrular; imzalanamazsa sert duruş | MF11 |
| 41 | Gözcü: `tohum/28`'deki her tetik yapay girdiyle doğru dondurmayı ya da sert duruşu üretir | P1 |
| 42 | `status.block`, en küçük: devir, son karar, taban yaşı, fren durumu ve insan dokunuşu sayısı defterden üretilir; elle düzenleme sonraki devirde yeniden üretilip `events`'e yazılır | MF16 |
| 43 | `brain.accept`: test, vektör ya da rakip satırından biri eksik ya da kırmızıysa kabul yok | tohum (önyükleme hakemi, `tohum/29b`) |
| 44 | `docs.index`: başlıklardan üretilen dizin deterministik | Aşama 1 MF7 (`docs.render` ile) |
| 45 | Etkinleştirme (taklit GitHub API'siyle, git yok): genesis satırı, `brain/integration` kesimi, mandal tabanı, hazır adaylar; iyi aday merge, kötü aday ret | MF18 |
| 46 | İş akışı (`loop.yml`): üst düzey `permissions: {}`; sırlı iş kod koşturmaz; `run:` içinde `${{ github.* }}` yok; action'lar SHA pinli; `persist-credentials: false`; `pull_request_target`, `workflow_run`, `issue_comment` yok; her işin ilk adımı `control` ve kill switch açıkken iş durur; `if: github.ref == 'refs/heads/main'` | MF17 |
| 47 | Birim türetme: birim adayları ve hariç yollar türetilir; ajan yapılandırması her yerde ve büyük-küçük harf duyarsız, operatörün `excluded_paths`'ı hariç; listeyi daraltan öneri reddedilir | MF4 |
| 48 | Tarif doğrulaması: imaj `@sha256`, `inputs`, komutlar, sınırlar; HEAD'de 3/3 yeşil, ağsız; `inputs` kapanışı yetersizse ret; sınıra takılan iş `limit_hit:<anahtar>` | MF6 |
| 49 | Hedef yazıcı: yazım yalnız REST ve Git Data API'siyle, yalnız `refs/heads/brain/**`'a; `main`'e ve `brain/` dışına yazma girişimi reddedilir; dal, PR, check, merge ve geri alma commit'i | MF9 |
| 50 | Geri alma provası (`exit.drill`, yalnız `revert`): seçim `HMAC(prova_tohumu, cycle_id)` ile önceki devrin `yaz`'ında taahhüt edilir, taahhüt zincirde; açılım eşleşmezse prova `FAIL`; ekilen kötü merge geri alınır, `cause` anahtarla aynı; `revert_drill` vektörleri, `tampered_key` dahil | MF14 |
| 51 | Organ koşucusu: kabul edilmemiş bir organın giriş noktası `koş`ta çağrılmaz | P1 |
| 52 | `operating{}` ayarı: sınıra takılma ve boşta kalma ölçümleri sınırı yalnız operatörün bandı içinde, iki yönde oynatır; bant dışı öneri reddedilir | P1 |
