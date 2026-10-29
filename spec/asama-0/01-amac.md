# Aşama 0 §0.1 — Amaç

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken
Çapa: beklemede: aşama 0 çıkış raporu

---

İlk canlı döngüyü kurmak ve koşturmak; fazlasını değil. Döngü hakemi bir hedefte bir lint bulgusunu
düzelten hazır bir adayı alır, kapıdan geçirir, `brain/integration`'a merge eder, nöbetçiyle izler,
gerekirse geri alır ve her kararı zincire yazar. Önce oyuncak hedefte, aynı (B) içinde gerçek hedefin
kopyasındaki tek birimde koşar (§0.8). Her mikro özellik bu döngünün bir adımında okunur; okuyucusu henüz
olmayan parça ilk okuyucusundan hemen önceki parti aktarımıyla gelir (`asama-1/13`, Y4).

Döngü hakemini Kurucu yazar, ama onu Kurucu puanlamaz: her push'u tohumla gelen önyükleme hakemi
(`tohum/29b`), tohum vektörleri (`tohum/29a`) ve farklı modelden tohum rakibi yargılar (Y6). Önyükleme
hakemi Aşama 0'dan sonra da beyin reposunun itme yargıcıdır; push kabulü, aşama kilidi ve rakip çağrısı
Kurucu'nun işi değildir. Sistemi LLM'ler kurar ve işletir; insan yön verir ve hesap işlemlerini yapar, her
dokunuşu sayılır.

| Parça | Nerede | Döngüdeki işi |
|---|---|---|
| Önyükleme hakemi | hakem reposu `bootstrap/` ve `bootstrap.yml` | beyin reposunun her push'unu yargılar; Aşama 0'dan sonra da kalır. `control` komutu, Sigstore pinleri ve lisans kapısı döngü iş akışına da hizmet eder |
| Döngü hakemi | beyinde `referee/`; aktarımla hakem reposunun kökünde; iş akışı `loop.yml` | hedeflerde D0–D8 |
| Oyuncak hedef | ayrı açık repo; içeriği `tests/fixtures/toy-repo/`: JavaScript, lint aracı, `node --test`, tohumlanmış düzeltilebilir lint borcu | ilk koşulan hedef; geri alma provası burada |
| Kopya hedef | gerçek hedefin açık kopyası (çatal değil), Actions kapalı (`tohum/25`) | tek birimde ilk gerçek merge |
| Yazar App'i | yalnız bu iki hedefte | `brain/*` dallarına, PR'a, check'e yazar; `main`'e yazamaz (`tohum/25a`) |
| Kurucu | yeni, ayrı beyin reposu (`tohum/24`) | `referee/`, `candidates/`, `targets/`, oyuncak fikstürü; hedef kodunu kendi makinesinde koşturmaz |

**Adımlar.** Döngü hakeminin her koşusu bir **devirdir** (`cycle_id` = Actions koşu kimliği). İş ayrımı
`tohum/08`'deki gibidir; her iş ilk adımında `main`'deki `control.json`'u canlı okur. Yargıç sütunu
§0.14'ün MF numaralarıdır.

| Adım | İş | Okur | Yazar | Yargıç | Yeşil |
|---|---|---|---|---|---|
| D0 tetik | her işin ilk adımı | `control.json` | — | tohumun `control` komutu | kill switch kapalı; zamanlanmış koşu `loop_schedule: true` değilse `paused` ile yeşil biter |
| D1 çek | `çek`: içerik ve Actions okuma | önyükleme hakeminin son imzalı sonucu; o SHA'daki `candidates/<hedef>/` ve `targets/<hedef>/units.json`; hedefin `brain/state` ve `brain/integration` başları (kimliksiz) | `pulled` | Sigstore doğrulaması; 1 `verify --previous`; 11 kök imzası; 4 profil | kabul edilmiş SHA'nın `referee/` hash'i son `imports.jsonl` satırınınkiyle aynı; zincir ve kök doğrulanır |
| D2 getir | `getir`: sırsız, ağlı | tarifteki kilit | `deps` ve lisans raporu | 5 | her tarball kilitteki `integrity` ile aynı; kayıt defteri izinli |
| D3 koş | `koş`: `permissions: {}`, ağsız | `pulled`, `deps`, tarif, aday | sonuç dosyaları; hash'leri konteyner dışında | 3 kırmızı kontroller; 6 tarif (genesis'te ve kilit değişince); 12 nöbetçi | kırmızı kontroller doğru; her komut sonuçlandı |
| D4 çağır | `çağır`: sağlayıcı kimliği, kod koşturmaz | tipli istek | yanıt, sunulan model, maliyet | 15 | yalnız (B)'deki kanarya çağrısı |
| D5 karar | `yaz`: OIDC; yazar App belirteci işte üretilir; kod koşturmaz | D3 ve D4 artefaktları, hash'le | karar | 2, 7, 8 | §0.8'in kabul kuralı |
| D6 yazım | `yaz` | karar | `brain/c/<id>`, PR, check, merge ya da geri alma commit'i; devir başına tek `brain/state` commit'i; imzalı kök; `status.md` | 9, 10, 11, 16 | yazılan her ref `refs/heads/brain/` altında; zincir yazımdan önce doğrulandı |
| D7 nöbet | sonraki devrin `koş` ve `yaz`'ı | `brain/integration`'ın yeni başı | yeşil ya da geri alma | 12, 13 | etkilenen testler yeşil; kırmızıda 3/3, sonra geri alma ve `cause` |
| D8 prova | önceki devrin `yaz`'ı taahhüt eder; bu devir uygular | tohumun prova fikstürleri, prova tohumu (hakem sırrı) | `drill` satırları | 14 | açılım taahhüde eşit; ekilen merge geri alındı; `cause` anahtarla aynı |

**Devir yeşili:** her adım yeşil, bütün artefaktlar hash'le doğrulanmış, her kararın kanıt satırı
zincirde, `status.md` yazılmış. Çalışma zamanındaki tek LLM çağrısı D4'ün kanaryasıdır; LLM avcı, yargıç
ve düzeltici yoktur.
