# Sözlük ve Okuyucular

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: yeni terim ya da dosya eklerken
Çapa: her yazılan dosyanın satırı bu tabloda ya da `27a`'dadır (tohumun spec denetimi ve `spec.lint` denetler)

---

## Tek anlamlı terimler

| Terim | Anlamı |
|---|---|
| Önyükleme hakemi | Tohumla gelen, kurulumda hakem reposuna kurulan Aşama 0 yargıcı; Aşama 0'dan sonra da beyin reposunun itme yargıcıdır, yalnız tohum dönemiyle değişir (`29b`) |
| Döngü hakemi | Kurucu'nun `referee/` altında yazdığı, aktarımla hakem reposuna giren ve hedeflerde devirleri koşan hakem (`asama-0/01`) |
| Devir | Döngü hakeminin bir koşusu; `cycle_id` Actions koşu kimliğidir |
| Parti | Aşama ortasında (A) → aktarım → (B) ile gelen MF kümesi: P1, P2 ve çıkış partileri (`asama-1/13`) |
| Operatör aktarımı | Hakem kodunun tek değişme yolu: aşama ya da parti çıkışında pinli beyin SHA'sındaki `referee/` ağacının hash doğrulamalı kopyası; önyükleme hakemine dokunmaz (`25a`) |
| Tohum dönemi | Tohumun (`spec/tohum`, `seed/`, `bootstrap/`) değişebildiği, özetin `seed_epochs[]`'inde adlı commit (`25` 10b) |
| İnsan dokunuşu | Aktarımlar, tohum dönemleri, `stage-open`, dürüstlük anahtarı ve sert duruş kalkışlarının sayacı; `status.md` üst bloğunda |
| Kopya hedef | Gerçek hedefin açık, çatal olmayan, Actions'ı kapalı kopyası; `main`'i yalnız operatörün aynalama işi ilerletir (`25` 10a) |
| Kırmızı kontrol | Her `koş` işinde koşan bilinen kötü aday; kırmızı çıkmazsa o koşunun hiçbir sonucu sayılmaz |
| Yazma modu, eğitim modu | Hedefe PR ve merge yapılabilen bağlanma; yapılamayan, yalnız okuyan ve deneyen bağlanma (`21`) |
| `çek`, `getir`, `koş`, `çağır`, `yaz` | Hakemin beş işi (`08` 1); önyükleme hakeminde altıncısı `yeniden`, rakibin yeniden üreticilerini koşar (`29b`) |
| Tohum vektörü | Kurucu'nun değiştiremediği sabit girdi ve beklenen çıktı çifti; gruplar MF'lere bağlıdır (`29a`, `29d`) |
| Modülsüz kırmızı | Bir MF'nin testleri modül yolu silinmiş ağaçta kırmızı olmalıdır; yeşil kalırsa ret (`asama-0/14`) |
| İzin listesi | `accept` satırlarından kurulan, çıktısı merge kapısına gidebilen organ tanım hash'leri |
| Aday paketi | Bulgu, diff ve organ tanım hash'leri (`26a`); Aşama 0'da Kurucu'nun hazır adayı (`26c`) |
| `impact_miss` | Merge sonrası kırmızının nedeni beyan edilen etki kümesinin dışında |
| Tohum dışı organ | Tohumda adı geçmeyen ve ablasyonda katkısı kanıtlanmış organ; sistemin kendi keşfinin ölçüsü. Provaya konan (`planted`) organ sayılmaz |
| Prova | Cevabı önceden hash'le bağlanmış, oyuncak hedefte koşan çıkış testi: geri alma provası (Aşama 0), ders ve bağlam provası (`22a`), genesis provası (`12a`); ders provasının referans yargıcı `29c` |
| Ret hafızası, `not_learning` | Önyükleme hakeminin, Kurucu'nun düzeltebildiği retlerin imza sayacı; aynı imza ardışık sınıra ulaşınca Kurucu oturumu durur (`29b`) |
| Fren | Olağan işi durdurmayacak kadar yüksek, döngüyü kesen bütçe ya da kaynak tavanı; takılmak ret değil, uyarıdır (`asama-0/12`) |
| Lisans kapısı | Ürüne giren bağımlılığın lisansını tekerleğin kendisinden okuyup `license_allowlist`'e karşı denetleyen kapı (`24`) |
| Harness puanı | Hakem harness'inin bir koşuya verdiği rapor |
| Taban avcı | Hakemin property başına sabit grep kümesi; maliyeti sıfır; Aşama 4 partisiyle gelir |
| Sınıf tabanı | `policy.json` anayasal bölümündeki çıkış alt sınırı |
| Düzeltici, implementer | Bulguyu kalıcı düzeltmeye çeviren organ; K5 ve üstünde kök nedeni tasarlayan Opus organı |
| Oracle düzelticisi | Testi yeşile çeviren asgari düzeltme; kanıttır, merge edilmez |
| Kanaryalar | Snapshot (talimat gibi görünen dosya), sandbox (dışarı yazma daveti), rakip (kusurlu artefakt), puan (puan avcılığı kalıbı), dispatch (gömülü hook, MCP ve yönerge dosyası), konteyner (kaçış denemesi), model (`llm.call` kanaryası) |
| Hayatta kalma, ölçüm penceresi | Merge sonrası geri alınmama süresi, sınıf başına; itibar, genesis ve Gözcü kararlarının zaman dilimi |
| Harness şeridi | Hakem değişikliğinin yolu: şerit yazarı adayı, rakip ve kanarya, operatör aktarımı |
| Gözcü işareti | Dondurma dışındaki Gözcü bulgusu; okuyucusu şerit yazarı |
| Taban (repo), baseline (merge) | Bağlanırken çıkarılan mevcut ihlaller (`07`); kapının merge öncesi yeniden ölçtüğü sonuçlar |

## Okuyucular (Y4)

Bir dosya ancak okuyucusunun bir kararı değiştirebildiği aşamada açılır. Tablo durum ve denetim
dosyaları içindir; kod dizinlerinin çağıranları `24` ve `26a`'dadır. Hedefteki durum dosyaları `27a`'dadır.

| Dosya | Yazar | Okuyucu | Değişen karar | Açılış |
|---|---|---|---|---|
| `control.json`, hakem reposu | operatör | her iş (`main`'den canlı), başlatıcı, gece bekçisi | Durmak, zamanlanmış devir, merge duraklatma, Kurucu'nun devamı; belirteç süresi uyarısı | Kurulum |
| `bootstrap.json`, hakem reposu | operatör | önyükleme hakemi | İzlenen beyin dalı, imaj, rakip modeli ve tavanları | Kurulum |
| `policy.json` anayasal ve `operating{}`, hakem reposu | operatör | her kapı, tohumun spec denetimi, `limit_hit` | Eşik, zorunlu çıkış satırı, kaynak sınırı | Kurulum |
| `setup/summary.json`, hakem reposu | operatör | önyükleme hakemi, genesis, P1'den `drift.check` | Sert duruş; tohum dönemi, hedefler ve aday birimler, genellik adları, dürüstlük taahhüdü, ilk koşu | Kurulum |
| `setup/imports.jsonl`, hakem reposu | `import` | döngü hakemi D1, genesis, `status.block`, operatör | Kabul edilmiş `referee/` hash'i; insan dokunuşu sayacı | Aşama 0 çıkışı |
| `setup/stage.json`, hakem reposu | `stage-open`, operatör iter | önyükleme hakemi her `pull`'da | Sonraki aşamanın tablosu ve testleri geçerli mi | Aşama 0 PASS |
| `setup/honesty-key.json`, hakem reposu | operatör | önyükleme hakemi, çıkışta | #durustluk | Aşama 0 çıkışı |
| `vectors/`, `seats/`, `bootstrap/stages/`, hakem reposu | operatör, tohumdan | önyükleme hakemi, `agent.dispatch` | Kabul, koltuk promptu, `done_mf` ve MF testleri | Kurulum |
| Önyükleme koşu artefaktları, Rekor kayıtları, `status-stage0.md` | önyükleme hakemi | Kurucu, başlatıcı, `import`, sonraki koşu (imzalı durum), operatör | Neyin düzeltileceği, oturum başlatma, aktarılacak SHA, sonraki karar | Aşama 0 |
| `founder-ledger.jsonl`, beyin reposu | Kurucu, tohumun defter aracıyla; başlatıcı (`cost`) | Kurucu sonraki oturum, önyükleme hakemi (zincir) | Neye devam edilecek; `founder_ledger_invalid` | Aşama 0 |
| `reports/*.json`, beyin reposu | Kurucu | önyükleme hakemi, operatör | İtiraz (`disputed`), uyarı, tohum dönemi | Aşama 0 |
| `spec/`, `INDEX.md`, beyin reposu | Kurucu | Kurucu, tohumun spec denetimi, önyükleme hakemi (kilit) | Aşama açma, kilit | Aşama 0 |
| `referee/` ve `referee/.github/workflows/loop.yml`, beyin reposu | Kurucu | önyükleme hakemi (`wiring` dahil), `import` | Aktarılacak hakem ve döngü iş akışı | Aşama 0 |
| `targets/<hedef>/units.json`, beyin reposu | Kurucu | `unit.verify` | Doğrulanmış tarif | Aşama 0 |
| `candidates/<hedef>/<cid>/`, beyin reposu | Kurucu | döngü hakemi (D1, D5) | Merge ya da ret | Aşama 0 |
| `snowball-tests.json`, `exit-request.json`, beyin reposu | Kurucu | önyükleme hakemi | Hangi testlerin koşacağı, pinlenecek çıkış SHA'sı | Aşama 0 |
