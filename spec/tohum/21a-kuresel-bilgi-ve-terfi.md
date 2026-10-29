# Küresel Bilgi: Bağlam, Koşul, Sentez ve Terfi

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: ikinci repo bağlanınca, ithal bilgi kullanılırken ve bir bilgi ya da organ terfi edilirken
Çapa: beklemede: ikinci repo — `knowledge` ve `proposal` satırları (`26b`); `gate_rules.promotion`

---

Bu sayfa anayasadır: değerleri tohum verir, çünkü sistem değerlerini veriden türetemez. Mekanizma
(küresel katman, koşul araştırması, okuma organı, örüntü önerisi, sentez organı) tohumda organ
olarak yazılmaz; sinyali doğunca genesis'ten gelir (`17`).

**Bilgi bağlama bağlıdır.** Bir repoda öğrenilen başka bir repoda yanlış olabilir. Her bilgi
"doğru" etiketi değil, bağlam tablosu taşır: bağlam parmak izi (profilden: diller, çerçeveler,
test koşucu, mimari özellikler) başına doğrulama ve çürütme sayıları. Sayıları hakem kanıtlı
defterlerden hesaplar. Çelişki silinmez; geçerlilik alanını daraltır.

**İthal bilgi hipotezdir.** Başka repodan gelen bilgi yeni repoda `derivation: imported`,
`trust: inferred` taşır ve kaynak bağlamını yazar; ilk kullanımlarında SHADOW'dadır, merge
kararına kanıt olamaz (Y1). Dispatcher hangi koşuya ithal bilgi verdiğini `imported_used`'a
yazar; ithal bilgiye dayanan iş geri alınırsa `cause` `imported_assumption`'dır ve küresel tabloya
"bu bağlamda yanlış" satırı düşer. Sistem bilgiyi uygularken bile onun ithal olduğunun farkındadır:
bulgu ve organ sayfası hangi bağlamdan hangi bilgiye dayandığını ve bu repodaki durumunu yazar.

**Koşullu bilgi.** Bilginin birimi "iddia + koşul"dur. Koşul iddiası ancak yürütmeyle sınanabilen
kod-yerel bir yüklemse bilgidir; repo düzeyindeki özellikler (dil, çerçeve) sandbox'ta
değiştirilemediği için koşul değil bağlamdır. Koşul önceden kaydedilir (ya da aday koşul sayısı F
iken α/F kullanılır) ve yalnız görülmemiş bağlamlarda doğrulanır. Bunu sağlamayan çelişki
`contradicted_unexplained` olarak kalır; LLM tartışması adayları sıralayabilir, koşulu kuramaz.

**Alan bilgisi değil mühendislik bilgisi.** Küresele yalnız alan bağımsız mühendislik bilgisi
çıkar: güvenlik, kimlik doğrulama, kiracı izolasyonu, altyapı, test düzeni, mimari kalıplar,
sözleşme tutarlılığı, performans, bakım. İş alanı bilgisi (bir hesaplamanın formülü, sektöre özgü
kural) küresele hiç çıkmaz ve sistem onun doğrusunu yargılamaz; yerelde yalnız iç tutarlılığı
sorar: aynı kavram bir yerde tanımlı öbür yerde tanımsız mı, iki tanım birbirini tutuyor mu, test
ve doküman kodla uyuşuyor mu. İddiası `domain_lexicon`'a dayanan bilgi `domain_bound`'dur, yerel kalır.

**Kopyalamak değil sentez.** Bilginin üç kaynağı vardır: repolardan gelen kalıplar, modelin kendi
mühendislik bilgisi ve sistemin kendi yaptıklarının ölçülen sonuçları; hiçbiri tek başına doğru
kabul edilmez. Tek kaynaktan gelen tasarım kopyalanmaz: karşı koltuk kendi bilgisinden referanslı
en az bir alternatif önermekle yükümlüdür ve soru "hangisi doğru" değil "ikisinden daha iyisi var
mı"dır (`10`). Kazananı sandbox'ta ölçülen fayda seçer. Her öneri `origin` taşır (`repo_pattern`,
`llm_prior`, `synthesis`, `own_outcome`); hayatta kalma kaynak ve koşul başına ölçülür, böylece
sistem hangi koşulda hangi kaynağa güveneceğini de öğrenir.

**Örüntü önerisi.** Başka repoda görülen daha iyi bir kalıp (daha iyi kimlik doğrulama, daha iyi
kiracı izolasyonu) ancak üç şeyle öneri olur: kaynakta kanıt (hayatta kalmış uygulama ve
testleri), hedefte uygulanabilirlik koşulları ve sandbox'ta ölçülmüş fayda. Ölçülebilir faydası
olmayan şey görüştür. Güvenlik örüntüleri K6 kapısından geçer; kök neden kuralları geçerlidir (`23`).
Kapanmış bir güvenlik açığının deseni katalog kimliği, CWE, dedektör biçimi ve koşullarla taşınır (`30e`).
Öneri kalıbı tarif eder, kaynağın kodunu taşımaz: hedefe giren kod hedefte yeniden yazılır ve
kaynağa yalnız `evidence_refs` ile atıf yapılır. Kaynak kodun kendisi ancak lisansı
`license_allowlist`'teyse ve atfı bildirime yazılırsa alınır (`24`); lisansı bulunamayan repodan
kod alınmaz.

**Terfi: birim repodur.** Bir organ ya da bilgi beyin çekirdeğine ancak şu kuralla terfi eder
(`gate_rules.promotion`): en az 4 repo, hepsi lehte (ya da en az 5); her repoda kendi dev
vakalarında sabit δ ile non-inferiority; genel denen her bağlam alanında en az 2 farklı değer;
seçim bir-repo-dışarıda yapılır; birden çok aday Benjamini–Hochberg ile düzeltilir. Terfi kararını
hakem verir (Y6). Beyin kodundaki her değişiklik aynı kuraldan geçer. 1–3 repodan "şu bağlamda
doğru" demek bilgi vermez; o sayıda repo yalnız hipotez üretir. Terfiyi getiren aşama, koşullu
bilginin doğru hedefe gittiğini bağlam provasıyla da gösterir (`22a`).

**Seçerek sınanan çıktı.** Okuma hipotezleri ve örüntü önerileri seçilerek sınanır; isabetleri
`19`'daki tekdüze denetim örneklemiyle ölçülür, sınanamayan iddia başarısız sayılır.
