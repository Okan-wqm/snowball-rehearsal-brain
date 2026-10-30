# Mimari İlkeler VII: Karar Rehberi

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: aşağıdaki durumlardan biri ortaya çıktığında, `decision` satırı yazılmadan önce
Çapa: `founder-ledger.jsonl` `kind: decision` satırları; kaynaklar `catalog.md` "Decision guide" bölümü

---

Rehber her durum için önce düşünülecek ilkeleri ve nedenini, ödünleşimiyle verir; tek bir cevap vermez.
Seçimi Kurucu yapar, listede olmayan bir ilkeyi de seçebilir ve seçimi, bıraktığı alternatifleri ve
seçimi koruyacak kontrolü `decision` satırına yazar (`31`). Göç, bayrak, manifest ya da sır gerektiren adım
sahibinindir (Y3).

**Yeni özellik.** Önce `bounded-context` (yeni kavramın sahibi hangi model), `sor` (yeni gerçekleri hangi
modül yazar), `yagni` ve `kiss` (gerçek çağıranı olan en küçük şey), `parse-boundary`. Ödünleşim: mevcut bir
modüle koymak bugün ucuzdur ama değişme nedenlerini karıştırabilir (`srp`). Tutulacak kanıt: sınır kuralı
yeşil, yazar haritası yalnız beyan edilen yeni sahiple değişmiş.

**İki yerde bulunan hata.** Önce `dup-kind`: tek bilgi mi, iki bilgi mi? Birlikte değişme geçmişine ve iki
kopyanın aynı kuralı kodlayıp kodlamadığına bak. Tek kuralsa ikisini aynı değişiklikte düzelt (`23` kapsam
kuralı) ve `ssot`/`dry` birleştirmesini, oracle olarak farklılık testiyle düşün. Benzer görünen iki ayrı
kuralsa ayrı ayrı düzelt, birleştirme. Ödünleşim: bağlamlar arası birleştirme bağ yaratır (`shared-kernel`),
birleştirmemek bir sonraki ayrışmaya kapı bırakır. Ayrışmanın kendisi çürütme düzeyinde kanıttır.

**Aynı veriyi isteyen ikinci servis.** Önce `sor` ve `single-writer`: veri sahibinde kalır. Artan bedel
sırasıyla seçenekler: sahibin API'sini çağırmak (taze, ama çalışma zamanı bağı); olaylarını yerel okuma
modeline tüketmek (`derived`, `outbox`, `idempotency`; özerklik, ama bayatlık ve idempotency işi); salt
okunur paylaşılan replika ya da görünüm (ucuz, ama şema bağı); paylaşılan çekirdek (yalnız küçük, kararlı
tipler). İkinci yazardan ve veriyi hesaplayan kuralı kopyalamaktan kaçın. Kanıt: yazar haritasında tek yazar;
kopyanın yeniden kur ve karşılaştır kontrolü.

**Yeni ekosistem (pnpm, poetry, cargo, Go modülleri).** Önce `registry` ve `ports-adapters`: ekosistem bir
tanımlayıcı (veri) ve bir adaptör olarak gelir, mevcutların uyum vektörlerini geçer, çekirdek dosyaya
dokunmaz (`31c`). Ödünleşim: bu yalnız ikinci çeşitse küçük açık bir dal daha sade olabilir (`yagni`), ama
çekirdekte repoya özgü yama olmaz (genellik testi). Bilinmeyen ekosistem kapalıya düşer, kapsama boşluğu yazılır.

**Kaynakla çelişen rapor.** Önce `lineage`: rapor alanını sahibine kadar izle, sonra çelişkinin türünü
seç. Bayat türetilmiş veri → `data-trust`, `derived`; "aynı" metriğin iki hesabı → `svot`; rapor CQRS'in öbür
tarafını okuyor → `cqrs`; kaynağın iki yazarı var → `sor`. Ödünleşim: raporu kaynağa uyacak biçimde yamalamak
nedeni gizler (`23`: "üst akış doğru olsaydı bu kod var olmak zorunda kalır mıydı?"). Kanıt: iki hesap tek
fikstürde koşar; yeniden kur ve karşılaştır.

**Bir tablonun iki yazarı.** Önce `sor` ve `single-writer`; ikinci yazar yalnız veriyi taşımak için varsa
`outbox`. Tabloyu taşımak ve yetki vermek göçtür: sistem yazar haritasını bildirir, mümkünse bekçi testi
bağlar, sahibi karar verir. Çürütme, iki yazarın yol açtığı kayıp güncellemeyi ya da tutarsız durumu
gösteren yeniden üretici ister.

**İki yapılandırma kaynağında aynı ayar.** Önce `config` ve `parse-boundary`. Kanıt: iki varsayılanı
gösteren anahtar envanteri; etkin değerin ortama ya da başlatma yoluna göre değiştiğini gösteren test.

**Yeniden denemelerden sonra çift işleme (NATS, MQTT, HTTP).** Önce `idempotency`, üretici tarafında
`outbox`. Oracle "iki kez teslim et" testidir; bu çoğu zaman koku değil, yeniden üretilebilir kusurdur.

**Paylaşılan arayüzün değişmesi (GraphQL alanı, olay, konu).** Önce `evolve` (genişlet-daralt), şema
uyumluluğu (`schema-registry`) ve `contract-test`. Ödünleşim: monorepoda atomik değişiklik çekicidir, ama
dağıtılmış tüketiciler kendi takvimleriyle güncellenir.

**Eski bir modülün değiştirilmesi.** Önce `strangler` bir `acl` arkasında, eski ile yeni arasında
farklılık testiyle; bitiş koşulu eskinin silinmesidir (K2).

**Bağlamlar arası klon bildirimi.** Önce `dup-kind`; üretilmiş ve fikstür yollarını ayıkla; bağlama
(`bounded-context`) ve birlikte değişmeye bak. Varsayılan: kanıtıyla açık iddia; birlikte değişme ya da
ayrışma kanıtı olmadan bağlamlar arasında birleştirme yapılmaz.

**Kodla çelişen doküman.** Önce `docs-derived` ve `doc-drift`: referans koddur; bayat doküman bulgusu
çapası ve çelişen koduyla yazılır. Doküman düzeltilir (K8), yeter ki kendi oracle'ı olan ayrı bir bulgu
kodun yanlış olduğunu göstermesin. Doküman başvuru malzemesiyse ve arkasındaki harita doğrulanmışsa elle
yazılmış kopyayı üretilmiş olanla değiştirmeyi düşün (`living-docs`); ödünleşim: üretim kaymayı kaldırır
ama sahibin o sayfaya yazdığı insan inceliğini de kaldırır; gerekçe çapalı kayıtlarda kalır (`adr`).
