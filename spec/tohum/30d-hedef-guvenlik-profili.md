# Hedef Güvenlik Profili: Tehdit Modeli ve Kural–Test Bağı

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: yeni bir hedefe bağlanırken, her güvenlik testi bağlanırken ve her K6 işinde
Çapa: beklemede: P2 aktarımı — `<state_root>/security/profile.json`; `security.derive` ve `security.run` çıktıları

---

**Ne zaman.** Hedefin güvenlik gözlemi P2 partisiyle, Aşama 1 içinde açılır (`asama-1/13`):
`security.derive`, `security.run` ve güvenlik avcısı (`30f`) o aktarımla gelir. Aşama 0'da hedef güvenlik
profili yoktur; güvenlik mikro özelliği `secrets.scan`'dir ve güvenlik yolları ile hariç yollar yalnız
yazım yasağı olarak uygulanır (`asama-0/08`). Hakemin ve beynin profili tohumla başından geçerlidir.

**Ne ve nerede.** Her hedefin tehdit modeli `<state_root>/security/profile.json`'da, kurallarını bağlayan
testler `<state_root>/security/tests/<rule_id>/` altındadır; ikisi de `brain/state`'tedir, `main`'e
girmez (Y2). Yazarı yalnız hakemdir (`yaz`): mekanik kısmı `security.derive` türetir (`26a`), gerisi
doğrulanmış bildirimlerden gelir. Beyin ve güvenlik avcısı (`30f`) önerir; öneri sınıf, kural, giriş
noktası ve güvenlik yolu **ekleyebilir**, hiçbirini silemez ya da daraltamaz (`14`'teki profil kuralı).
Güvenlik yolları `profile.json`'daki `security_paths`'tir (`14`); bu dosya onlara bağlanır, yeniden tanımlamaz.

**Türetme.** Kimlik ve yetki modeli bağımlılıklardan (JWT, oturum, OAuth kütüphaneleri) ve koruma
sembollerinden; giriş noktası envanteri çerçeveye özgü statik çıkarımdan (HTTP yönlendiricileri,
GraphQL SDL'i ve çözücü haritası, abonelikler, kuyruk tüketicileri, zamanlanmış işler, FFI dışa
açılımları); veri depoları bağımlılık ve ayarlardan; kiracılık, göç uygulanmış test veritabanının
kataloğundan (kiracı sütunlu tablolar, RLS bayrakları ve politikaları), `domain_lexicon`'dan ve kiracı
bağlamını kuran koddan. Model önerisi, bir test doğrulayana kadar `trust: inferred`'dır. Katalogdaki her
kimlik `classes[]`'ta bir kez görünür: "uygulanmaz" da kanıt ister (ör. bağımlılıklarda XML ayrıştırıcı
yok); kanıtsız sınıf uygulanır sayılır (kapalıya düşer).

**Her kural bir teste bağlıdır.** Kural bir katalog sınıfına ve en az bir teste bağlıdır; durumu
`security.run`'un her döngüdeki koşusundan gelir:

| Durum | Anlamı |
|---|---|
| `guarded` | Test bugün yeşil ve kum havuzundaki kopyaya mekanik olarak ekilen ihlali (kiracı yüklemini silmek, korumayı kaldırmak, sınırı açmak) yakalıyor; ekilen ihlali yakalamayan test test değildir (`04a` 6) |
| `violated` | Test bugün beklenen gözlemle 3/3 kırmızı; doğrulanmış açık, `finding` satırı (`30e`) |
| `blocked` | Test sandbox'ta kurulamıyor (servis yok, ağ gerekiyor); kapsama boşluğu |
| `unbound` | Kuralın testi yok; kapsama boşluğu, avcının ilk işi |

Testler hedefin kendi dilinde ve test koşucusuyla yazılır (`14`), `koş`ta atılacak bir worktree'ye
bindirilip ağsız koşar. Durum değişimi bir `security` satırıdır; `guarded` bir testi kırmızıya çeviren
aday, hangi sınıftan olursa olsun reddedilir (`gate.check`, `cause: test_regression`). K6 canlı olunca
`guarded` testler K6 kapısından hedefin kendi test yoluna önerilebilir; sahibin CI'ı da koşturur.

**Örnek.** TypeScript API'si ve Apollo GraphQL sunucusu, Python servisleri ve işçileri, Rust bileşenleri,
PL/pgSQL fonksiyonlu Postgres taşıyan çok kiracılı bir platform:
- `tenancy`: `shared_schema`, `tenant_key: tenant_id`, `context_source: token_claim`; RLS'li ve RLS'siz
  kiracı tabloları ayrı listelenir. `entrypoints`: her HTTP ucu, SDL'deki her Query, Mutation ve
  Subscription alanı, her kuyruk tüketicisi ve zamanlanmış iş, her FFI dışa açılımı.
- Uygulanan sınıflar: bütün `tenant-*` ve `gql-*`, `n-plus-one`, PL/pgSQL `EXECUTE` dahil `sqli`,
  `prototype-pollution`, `deserialization`, `unsafe` varsa `rust-unsafe` ve `ffi-boundary`, üç ekosistemde
  `vulnerable-deps`.
- Kurallar: R1 "A kiracısının hiçbir rolü B'nin verisini hiçbir giriş noktasından okuyamaz ve
  değiştiremez" → çapraz kiracı matrisi, bütün envanter (`30b`). R2 kiracı yalnız belirteçten. R3 RLS
  katalog ve rol testleri (düzeltme sahip, migration). R4 havuzda oturum sızıntısı. R5 `limits{}`'teki
  derinlik, maliyet, takma ad sınırları. R6 her liste alanında sorgu sayısı sabit. R7 Python işçisinde
  iş başına kiracı bağlamı.

**Hakem ve beyin de hedeftir.** Profilleri tohumla sabittir: kiracılık yok; kimlik GitHub kimlikleri,
App belirteçleri ve Sigstore OIDC; veri depoları git dalları, iş artefaktları ve Rekor; güvenlik yolu
hakem kodu, iş akışı, koltuklar ve vektörlerin tamamı. Uygulanan sınıflar `path-traversal`,
`prompt-injection`, `agent-escape`, `ci-supply-chain`, `exceptional-conditions`, `integrity`, `secrets`,
`deserialization`, `unbounded-input`, `cmdi`, `supply-chain`, `vulnerable-deps`; kuralların testleri
hakemin kendi testleridir, defteri `seed/security-ledger.jsonl`'dır (`30e`).

**Şema** (`26` ve `26b` dolu olduğu için burada; alan adları İngilizce). **security profile**:
`schema_version`, `snapshot_id`, `derived_by`, `tenancy` `{model: none|single|shared_schema|
schema_per_tenant|db_per_tenant, tenant_key?, tenant_tables[], context_source {kind: token_claim|subdomain|
header|path|none, name?}, db_enforcement {rls_tables[], setting?, scope: local|session|none}}`, `auth`
`{mechanisms[], roles[], guard_symbols[], public_routes[]}`, `data_stores[]` `{kind, name, tenant_scoping:
rls|column|prefix|index|none}`, `entrypoints[]` `{entry_id, kind: http|graphql|subscription|queue|cron|ws|
ffi|cli, file, symbol, auth, tenant_scoped}`, `security_paths_sha256`, `sensitive_fields[]`, `limits{}`
(`graphql_max_depth`, `graphql_max_cost`, `page_size_max`, `body_max_bytes`, `min_group_size`, …),
`classes[]` `{catalogue_id, applies, origin?}`, `rules[]` `{rule_id, catalogue_id, property, statement,
entrypoints: all|[entry_id], tests[], state: guarded|violated|blocked|unbound, fix_path: k6|owner}`,
`detectors[]` `{detector_id, catalogue_id, kind: grep|ast|sql_catalog, pattern, path_glob, born_from,
validated {fires_on, silent_on}}`. Analizden gelen her öğe `derivation`, `trust` ve `evidence_refs` taşır.
