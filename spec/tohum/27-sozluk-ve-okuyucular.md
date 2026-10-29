# Sözlük ve Okuyucular

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: yeni terim ya da dosya eklerken
Çapa: her yazılan dosyanın satırı bu tablodadır (spec.lint denetler)

---

## Tek anlamlı terimler

| Terim | Anlamı |
|---|---|
| Önyükleme hakemi | Tohumla gelen, kurulumda hakem reposuna kurulan Aşama 0 yargıcı (`29b`) |
| Operatör aktarımı | Hakem kodunun tek değişme yolu: pinli beyin SHA'sındaki `referee/` ağacının hash doğrulamalı kopyası (`25a`) |
| İnsan dokunuşu | Operatör aktarımları ve sert duruş kalkışlarının sayacı; `status.md` üst bloğunda |
| Kırmızı kontrol | Her `koş` işinde koşan bilinen kötü aday; kırmızı çıkmazsa o koşunun hiçbir sonucu sayılmaz |
| Yazma modu, eğitim modu | Hedefe PR ve merge yapılabilen bağlanma; yapılamayan, yalnız okuyan ve deneyen bağlanma (`21`) |
| `çek`, `getir`, `koş`, `çağır`, `yaz` | Hakemin beş işi (`08` 1) |
| Tohum vektörü | Kurucu'nun değiştiremediği sabit girdi ve beklenen çıktı çifti (`29a`) |
| İzin listesi | `accept` satırlarından kurulan, çıktısı merge kapısına gidebilen organ tanım hash'leri |
| Aday paketi | Bulgu, diff ve organ tanım hash'leri (`26a`) |
| `impact_miss` | Merge sonrası kırmızının nedeni beyan edilen etki kümesinin dışında |
| Tohum dışı organ | Tohumda adı geçmeyen ve ablasyonda katkısı kanıtlanmış organ; sistemin kendi keşfinin ölçüsü. Provaya konan (`planted`) organ sayılmaz |
| Prova | Cevabı önceden hash'le bağlanmış, oyuncak hedefte koşan çıkış testi: ders provası, geri alma ve bağlam provası (`22a`), genesis provası (`12a`); referans yargıç `29c` |
| Ret hafızası, `not_learning` | Önyükleme hakeminin ret imzası sayacı; aynı imza ardışık sınırı aşınca Kurucu oturumu durur (`29b`) |
| Lisans kapısı | Bağımlılığın lisansını tekerleğin kendisinden okuyup `license_allowlist`'e karşı denetleyen kapı (`24`) |
| Harness puanı | Hakem harness'inin bir koşuya verdiği rapor |
| Taban avcı | Hakemin property başına sabit grep kümesi; maliyeti sıfır |
| Sınıf tabanı | `policy.json` anayasal bölümündeki çıkış alt sınırı |
| Düzeltici, implementer | Bulguyu kalıcı düzeltmeye çeviren organ; K5 ve üstünde kök nedeni tasarlayan Opus organı |
| Oracle düzelticisi | Testi yeşile çeviren asgari düzeltme; kanıttır, merge edilmez |
| Kanaryalar | Snapshot (talimat gibi görünen dosya), sandbox (dışarı yazma daveti), rakip (kusurlu artefakt), puan (puan avcılığı kalıbı), dispatch (gömülü hook, MCP ve yönerge dosyası), konteyner (kaçış denemesi) |
| Hayatta kalma, ölçüm penceresi | Merge sonrası geri alınmama süresi, sınıf başına; itibar, genesis ve Gözcü kararlarının zaman dilimi |
| Harness şeridi | Hakem değişikliğinin yolu: şerit yazarı adayı, rakip ve kanarya, operatör aktarımı |
| Gözcü işareti | Dondurma dışındaki Gözcü bulgusu; okuyucusu şerit yazarı |
| Taban (repo), baseline (merge) | Bağlanırken çıkarılan mevcut ihlaller (`07`); kapının merge öncesi yeniden ölçtüğü sonuçlar |

## Okuyucular (Y4)

Bir dosya ancak okuyucusunun bir kararı değiştirebildiği aşamada açılır. Tablo durum ve denetim
dosyaları içindir; kod dizinlerinin çağıranları `24` ve `26a`'dadır.

| Dosya | Yazar | Okuyucu | Değişen karar | Açılış |
|---|---|---|---|---|
| `control.json`, hakem reposu | operatör | her iş, Kurucu oturum başı | Durmak | Kurulum |
| `policy.json` anayasal, hakem reposu | operatör | her kapı, `spec.lint` | Eşik, zorunlu çıkış satırı | Kurulum |
| `setup/summary.json`, hakem reposu | operatör | `drift.check` | Sert duruş | Kurulum |
| `vectors/`, `seats/`, hakem reposu | operatör, tohumdan | önyükleme hakemi, `agent.dispatch` | Kabul, koltuk promptu | Kurulum |
| Önyükleme koşu artefaktları, Rekor kayıtları | önyükleme hakemi | Kurucu, aktarım betiği | Neyin düzeltileceği, aktarılacak SHA | Aşama 0 |
| `founder-ledger.jsonl`, beyin reposu | Kurucu | Kurucu sonraki oturum | Neye devam edilecek | Aşama 0 |
| `spec/`, `INDEX.md`, beyin reposu | Kurucu, `docs.index` | Kurucu, `spec.lint`, `lock.check` | Aşama açma, kilit | Aşama 0 |
| `referee/`, beyin reposu | Kurucu | önyükleme hakemi, aktarım betiği | Aktarılacak hakem | Aşama 0 |
| `candidates/`, beyin reposu | Kurucu | etkinleştirme, hakem | Merge adayı | Aşama 0 |
| `snowball-tests.json`, `exit-request.json`, beyin reposu | Kurucu | önyükleme hakemi | Hangi testlerin koşacağı, pinlenecek çıkış SHA'sı | Aşama 0 |
| `profile.json` | `profile.derive` | tüm organlar, kapı | Araç ve kapsam | Etkinleştirme |
| `policy.json` performans | prosedür (`18`), `yaz` | her kapı | Dikkat ve sıra eşiği | Etkinleştirme |
| `ledger.jsonl` `events` | hakem işleri | Gözcü, kapı, `lock.check` | Dondurma, geri alma, kilit | Etkinleştirme |
| `ledger.jsonl` `cost` | `çağır`, geçit | Gözcü | Bütçe duruşu | Etkinleştirme |
| `ledger.jsonl` `freeze` | Gözcü | kapı | Merge kapanır | Etkinleştirme |
| `ledger.jsonl` `rival`, `accept` | hakem, `brain.accept` | `brain.accept`, `gate.check` | Kabul, izin listesi | Etkinleştirme |
| `ledger.jsonl` `drill` | `exit.drill` | hakem exit, `lock.check` | Yeteneğin canlıya girmesi | İlk prova |
| `chain/root.jsonl` | `yaz` | `chain.verify`, `rekor.anchor` | Sert duruş | Etkinleştirme |
| `cases/` (dev) | `cases.build` | `harness.score`, Kurucu | Adapter değişikliği | Etkinleştirme |
| `status.md` | `status.block`, `docs.render` | operatör | Kill switch | Etkinleştirme |
| `findings.jsonl` | hakem, adapter önerisinden | düzelticiler, kapı | İş kuyruğu | Etkinleştirme |
| `unresolved.jsonl` | kapı | düzeltici seçimi | Aynı tabanda yeniden denememe | Aşama 1 |
| `runs/` | `koş`, `çağır` | `gate.check`, hash ile | Merge | Etkinleştirme |
| `docs/findings/`, `docs/organs/` | `docs.render`, `yaz` | operatör | Kill switch | Aşama 1 |
| Mühürlü depo, `ledger.jsonl` `looks` | mühür App'i, hakem exit | `harness.score` exit | Verdict, bakış bütçesi | İlk held-out havuzu |
| `map/edges.jsonl` | `map.build` | düzeltici, kapı | Etki kümesi | İlk `impact_miss` sinyali ya da K2 silmesi |
| İtibar görünümü, organ yaşam döngüsü, `genesis-queue.jsonl` | puanlayıcı, hakem, sinyaller | dispatcher, genesis, Kurucu | Sıra, yeniden yazım, taslak | Bir sınıfta ≥ 2 aday organ |
| Ders görünümü | `lessons.view` | planlayıcı, düzeltici | Yaklaşım | Aşama 2 |
| `contracts/` | organlar | organlar, kapı | Arayüz | İkinci ortak arayüz |
| `prompt-ledger.jsonl`, `fp-corpus.jsonl` | dispatcher, oracle | Kurucu, şerit yazarı, rakip kanaryası | Prompt sürümü, koltuk geri dönüşü | Aşama 4 |
| Eğitim deposu dalları | `yaz` | bilgi ve koşul görünümleri | Hipotez sırası | İlk eğitim hedefi |
