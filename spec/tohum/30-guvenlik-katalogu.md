# Güvenlik Kataloğu: İlkeler, Zamanlama, Ortak Kader

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: her güvenlik işinde, her bildirimde ve yeni bir hedefe bağlanırken
Çapa: `seed/security-ledger.jsonl`; beklemede: Aşama 1 — `<state_root>/security/` ve `security` satırları

---

**Neden var.** Repoyu öğrenmenin bir amacı güvenlik açığı açmamaktır (`05`); güvenlik K6 sınıfıdır
(`03`). Katalog bilinen açık sınıflarını tek yerde toplar ki her ajan neye bakacağını bilsin: Kurucu
beyin ve hakem kodunu yazarken, güvenlik avcısı (`30f`) ararken, rakip bir artefaktı çürütürken (ilgili
tohum sayfası olarak, `29`), K6 organları Aşama 5'ten düzeltirken. Test-yazıcıya katalog girdisi property
tanımının parçası olarak gider, bulgunun iddiası gitmez (`04a` 2). Katalog bir hipotez listesidir, bulgu
değildir (Y1): bir sınıfın bu kodda var olduğunu yalnız yürütme söyler.

**Bir girdi.** Her sınıf şunları taşır: kimlik (İngilizce; profil, defter ve bildirimlerde bu adla
geçer, ör. `bola`) ve bağlı olduğu property; tek satırlık tanım; **bulma** yolu (statik sinyal, araç,
test); **kapanış testi**, yani açığı yürüten ve açık varken kırmızı olan test deseni; CWE ve OWASP
karşılığı; düzeltme yolu. Etkin property'ler `tenant-isolation`, `auth-gate`, `input-boundary`'dir
(`asama-0/05`); öbür adlar (`output-encoding`, `data-exposure`, `resource-bound`, `memory-safety`,
`crypto`, `secret-hygiene`, `supply-chain`, `fail-closed`, `config`, `llm-boundary`) adaydır ve `14`'teki
yolla açılır; o güne kadar harness'te sayılmazlar ama avcının bildirimi ve testi yine koşar. Sayfalar:
`30a` erişim, kimlik, enjeksiyon, web; `30b` çok kiracılık, GraphQL, kaynak tüketimi; `30c` bellek, kripto,
sır, tedarik zinciri, yapılandırma, hata işleme ve ajan sınıfları. Hedefin tehdit modeli `30d`, defter
`30e`, avcı `30f`'dedir.

**Açık ancak yürütmeyle gerçektir.** Bir açık, onu yürüten test ya da yeniden üretici bugünkü snapshot'ta
beklenen gözlemle 3/3 kırmızıysa (`04a` 3–4) ve boş kontrol ağacında üretmiyorsa (totoloji, `29`)
doğrulanmıştır. Kapanış: aynı test düzeltmeden sonra 3/3 yeşildir, düzeltmenin en az bir mutantını
öldürür (`04a` 6) ve bekçi olarak her döngüde koşmaya devam eder. Statik sinyal, tarayıcı eşleşmesi ve
modelin görüşü "buraya bak"tır (`trust: inferred` ya da `observed`). Aracın kendisinin oracle olduğu
sınıflarda (`vulnerable-deps`, `secrets`) kapanış aracın yeniden koşusu ve mandaldır (K0 gibi, `03`).
Saldırı `koş`un ağsız konteynerinde, süreç içi istemciyle kurulur: istek ağa çıkmaz, veritabanı ve kuyruk
profildeki yerel servistir; kurulamayan test `blocked`'dır ve kapsama boşluğu sayılır (`17`).

**Zamanlama** (operatör onayı, 2026-10-29). Test eklemek ve açık bildirmek davranışı değiştirmez.

| İş | Ne zaman |
|---|---|
| Bulmak, kanıtlamak, bildirmek; `security` satırı (`30e`) | Aşama 1'den (etkinleştirme) |
| Bir kuralı bekçi testine bağlamak: bugün yeşil, ekilmiş ihlali yakalar | Aşama 1'den; test `<state_root>/security/tests/`'tedir, hedefin `main`'ine girmez (`30d`) |
| Hedefin koduna güvenlik düzeltmesi; bekçi testini hedefin test yoluna önermek | K6 canlı olunca, yalnız K6 kapısından (`05`, `04a` 10); Aşama 5 |
| Migration (ör. RLS), bağımlılık manifesti, sır döndürme, yapılandırma, iş akışı | Hiçbir zaman sistem (Y3, `04a` 9): hedefin sahibi düzeltir, sistem testi yeniden koşar ve `verification` yazar |

Katalog tablolarındaki "Düzeltme" sütunu bu satırların kısaltmasıdır: `K6` ya da `sahip` (nedeni
parantezde). Avcı hiçbir satırda düzeltmez (`30f`).

**Ortak kader.** Sistemin herhangi bir yerinde (hakemde, rakipte, beyinde, hedefte) kullanılan bir açık
bütün sistemi, dolayısıyla onu kullananı da yaralar: açığı kullanılmış bir hakemin kabulü değersizdir ve
ona dayanan itibar, ders ve merge onunla birlikte değersizleşir. Bu yüzden hiçbir ajan bir açığı
kullanmaz; gördüğü her açığı, kendi işinin dışında olsa da, kanıtıyla bildirir: Kurucu beyin reposunda
kırmızı bir testle, avcı ve rakip imzalı sonuçta. Bildirim ödüldür, açığı kullanmak hiçbir zaman
ödüllenmez; doğrulanmış her bildirim bir `security` satırı ve kalıcı bir test bırakır (`30e`).

**Kapsama haritası.** Listelerin her maddesi en az bir sınıfa düşer:

| Liste | Karşılık |
|---|---|
| OWASP Top 10:2025 (2021) | A01 `bola` `bfla` `excessive-exposure` `path-traversal` `csrf` `open-redirect` `ssrf` ve bütün `tenant-*`; A02 (A05:2021) `misconfig` `cors-headers` `gql-introspection` `xxe`; A03 (A06:2021) `vulnerable-deps` `supply-chain` `ci-supply-chain`; A04 (A02:2021) `weak-crypto` `weak-random` `secrets`; A05 (A03:2021) `sqli` `nosqli` `cmdi` `code-injection` `ldapi` `ssti` `xss` `input-validation`; A06 (A04:2021) `insecure-design`; A07 `authn` `session-jwt`; A08 `integrity` `deserialization` `mass-assignment`; A09 `logging-alerting` `pii-in-logs` `log-injection`; A10 `exceptional-conditions` (A10:2021 `ssrf`) |
| OWASP API Security Top 10:2023 | API1 `bola`; API2 `authn` `session-jwt`; API3 `mass-assignment` `excessive-exposure` `gql-field-authz`; API4 `rate-limit` `unbounded-input` `gql-depth-cost` `gql-alias-batch` `n-plus-one`; API5 `bfla`; API6 `rate-limit` `insecure-design`; API7 `ssrf`; API8 `misconfig` `cors-headers` `gql-introspection`; API9 `inventory`; API10 `unsafe-consumption` |
| CWE Top 25:2025 | 79 `xss`; 89 `sqli`; 352 `csrf`; 862, 863 `bola` `bfla` `gql-field-authz`; 787, 416, 125, 120, 476, 121, 122 `rust-unsafe` `ffi-boundary`; 22 `path-traversal`; 78, 77 `cmdi`; 94 `code-injection`; 434 `upload`; 502 `deserialization`; 20 `input-validation`; 284, 639 `bola` `tenant-*`; 200 `excessive-exposure`; 306 `authn`; 918 `ssrf`; 770 `rate-limit` `unbounded-input`. 2024'ten çıkanlar da: 287 `authn`, 269 `tenant-impersonation`, 798 `secrets`, 190 `integer-overflow`, 400 `unbounded-input`, 119 `rust-unsafe` |

**Katalog büyür, ama tohumdur.** Katalog sayfalarını yalnız operatör değiştirir. Hiçbir sınıfa uymayan
doğrulanmış bir açık önce hedefin profilinde yerel sınıf olarak doğar (`30d`, `origin`), kaçırma olarak
sayılır (`30e`), başka repolarda da doğrulanırsa terfi kuralıyla (`21a`) küresele, operatör kararıyla
tohuma girer.
