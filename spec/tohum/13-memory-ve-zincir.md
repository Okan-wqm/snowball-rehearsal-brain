# Memory Kuralları ve Zincirli Defterler

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: yeni memory açarken ve her defter yazımında
Çapa: beklemede: aşama 0 — chain/root.jsonl; Rekor kayıtları; tohum vektörleri V1–V3

---

- Memory bir üçlüdür: **yazar, okuyucu, okuyucunun değiştirdiği karar.** Üçü aynı değişiklikte
  gelir ve dosya ancak okuyucusunun bir kararı değiştirebildiği aşamada açılır (Y4). Sekiz hafıza
  türü ve tohumda hangisinin verildiği `16-hafiza-modeli.md`'dedir.
- İlk memory, Aşama 0'daki hata seti ve önyükleme hakeminin sonuçlarıdır; ikincisi defterin
  `cost` bölümüdür. Dersler, itibar ve harita ilk okuyucularıyla açılır (`22`, `11`, aşağıda).
  Semantik ya da vektör memory ancak ölçülmüş bir geri çağırma boşluğunda eklenir.
- **Repo haritası hata yapmamak içindir:** bir yeri yaparken başka bir yeri bozmamak ve bir
  güvenlik açığı açmamak (`05`). Katmanları aşama takvimiyle değil, ilk okuyucularıyla açılır:
  (a) derleme ve import grafiği, profildeki graf aracından; ilk `impact_miss` sinyalinde ya da K2
  silmeleriyle; (b) çalışma zamanı bağları: event üretici ve tüketicileri, HTTP uçları, tablo
  sahipleri, mesaj konuları, env değişkenleri, feature flag'ler; K3 ve K4 ile; (c) güvenlik
  sınırları: yetki kapıları, kimlik bağlamının kaynağı, satır düzeyi güvenlikli tablolar, sır ve
  PII noktaları; K6 ile; (d) dış bağımlılıklar: paket → sürüm → tüketici, lockfile ve bilinen
  açıklar; K6 ile.
- Harita `map/edges.jsonl`'dadır. Her kenar `evidence_ref`, `derivation`, `trust` ve `snapshot_id`
  taşır; iki ucundan birine dokunan diff kenarı `stale` yapar. Haritayı çıkaran ajan ile kullanan
  ajan ayrı bağlamda koşar. Bir avcının yazdığı aday kenar, statik analiz ya da test onu
  `trust: verified` yapana kadar hiçbir avcıya verilmez; exit koşularından önce harita dondurulur.
- **Harita açılana kadar** etki kümesi profildeki etkilenen-test komutudur. Merge sonrası
  kırmızının nedeni bu kümenin dışındaysa `impact_miss` yazılır; bu, haritanın doğum sinyalidir
  (`17`) ve bir öğrenme organının hata ölçüsüdür (Y5).
- **Kapsama bir görünümdür:** her döngünün her dosyaya yazdığı kader (hangi basamak gördü,
  hiçbiri görmedi, kaba) defterden kurulur. Görülmeyen dosya payı birinci sınıf sayıdır; ilk
  okuyucusu boşluk formülüdür (`17`).
- Memory'de duran hiçbir şey kanıt değildir (Y1). Memory nereye bakılacağını söyler.

**Zincirli defterler.** Defter yalnız sonuna eklenen JSONL'dir: `ledger.jsonl`, bölümleri `part`
alanıyla ayrılır (`26`). Her satır `prev_hash` ve `row_hash` taşır: `row_hash =
sha256(canonical(satır − row_hash) ‖ prev_hash)`, kanonik biçim RFC 8785, küçük harf onaltılık;
ilk satırın `prev_hash`'i 64 sıfırdır. Uygulama tohum vektörleri V1–V3'ü geçer (`29a`).

- **Satırları yalnız hakem yazar.** Oyuncunun önerdiği her satır `trust: inferred` olarak saklanır;
  hakem kendi ölçümünden yazmadıkça hiçbir oyuncu iddiası durum olmaz. Hakemin `yaz` işi döngü
  başına `brain/state`'e tek commit atar (`08`, `26a`). Kurucu'nun `founder-ledger.jsonl`'ı beyin
  reposundadır, aynı zincir kuralına uyar ve hiçbir kapı kararına girmez.
- **Kök ve dış günlük.** Her döngü sonunda tüm bölümlerin son hash'lerinden bir kök hash türetilir,
  `chain/root.jsonl`'a eklenir ve `rekor.anchor` ile Sigstore Rekor'a yazılır. Kök kaydı hakem
  ağacı hash'ini, kabul edilmiş beyin SHA'sını, koltuk özetlerini, tohum hash'ini ve anayasal
  `policy.json` hash'ini bağlar. Rekor kaydı herkese açıktır; yalnız hash ve iş akışı kimliği
  taşır. Açık hedefte `brain/state` ayrıca ruleset ile korunur (`deletion`, `non_fast_forward`,
  bypass yok); özel hedefte ve eğitim deposunda bütünlüğün dış güvencesi Rekor'dur.
- **Zincir kırığı sert duruştur.** Hash uyuşmazlığı, Rekor'daki kökle uyuşmayan dal ucu ya da
  Rekor'a yazılamama kurcalama kanıtıdır: Gözcü sert duruş yazar (`28`), defter salt okunur olur,
  kırığın satırı ve commit'i raporlanır. Kırık düzeltilmez; kırığın kendisi yeni bir satırdır.
- **Geçmişe sorgu.** `chain.asof <tarih|sha>` herhangi bir an için görünümleri kurar: kabul
  edilmiş organlar, itibarları, kapsama, açık property'ler, değer / USD, eşikler. Araç ilk
  okuyucusu doğunca açılır (`status.md`'nin "geçen yıl bugün" bölümü ya da bir eşik yeniden
  oynatması); defter bu sorguyu mümkün kılan alanları ilk günden taşır.
- **Silme yoktur, emeklilik vardır.** Hiçbir organ tanımı, bulgu, ders ya da puan zincirden
  silinmez; RETIRED, `withdrawn` ya da `superseded` satırıyla kapatılır. Eski satırlar değişmez
  blob olarak arşivlenir, hash'i zincirde kalır; arşivleme de bir satırdır.
