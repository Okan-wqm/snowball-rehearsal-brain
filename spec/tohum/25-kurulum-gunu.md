# Kurulum, Birinci Bölüm: İnşadan Önce

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: ilk başlatmadan önce, bir kez
Çapa: hakem reposundaki `setup/summary.json`

---

Döngü içinde insan yoktur; döngüden önce iki kısa insan işi vardır. Hepsi listededir; listede
olmayan hiçbir şey sonradan insandan istenmez. Ön şart: tohumla gelen önyükleme hakeminin kodu
(`seed/bootstrap/`, `29b`) yazılmış ve kendi testlerinden geçmiş olmalıdır; yoksa kurulum başlamaz.

| # | İş | Neden |
|---|---|---|
| 0 | **Plan gerçeğini kaydet.** Hesap Free; özel repoda ruleset, dal koruması ve ortam sırrı yok; App izinleri kurulum genelinde; özel repolar ayda ~2.000 Actions dakikası. Bu yüzden hakem reposuna hiçbir App yazmaz, hakem kodu yalnız operatör aktarımıyla değişir (`01a`) | Tasarımın dayandığı gerçek yazılı olsun; değişirse `drift.check` görür |
| 1 | Beyin reposunu özel aç. **Kurucu kimliği**: beyin reposunda içerik yazma, `workflows` yok; hakem reposunda yalnız okuma (içerik ve Actions sonuçları) | Oyuncu kendi iş akışını ve hakemini değiştiremesin |
| 2 | Hakem reposunu özel aç. Yazma izinli hiçbir App kurulmaz, ortak çalışan eklenmez; iş akışı varsayılan izni salt okunur | Hakemi yalnız operatör yazsın |
| 3 | Önyükleme hakemini kur: `seed/bootstrap/` → hakem reposunda `bootstrap/`, `seed/bootstrap/workflow/bootstrap.yml` → `.github/workflows/`, `seed/bootstrap/vectors/` → `vectors/`, `29` → `seats/`; `bootstrap.json`'u yaz (beyin reposu ve dalı, `@sha256` ile pinli imaj, rakip modeli, `effort`, tur sayısı ve çağrı başı USD tavanı, sınırlar); değişken `READER_APP_ID`, sırlar `READER_APP_KEY` ve `CLAUDE_CODE_OAUTH_TOKEN` (operatörün `claude setup-token` çıktısı; bir yıl geçerlidir, dolunca rakip `api_error` verir: uyarı çıkar, ret hafızasına işlenmez, aynı SHA'da üçüncüsünden sonra günde bir yeniden denenir; iç kullanımda API anahtarı yoktur); hash'leri özete yaz | Aşama 0'ın yargıcı Kurucu'dan önce var olsun (Y6) |
| 4 | Hakem reposuna `control.json` (kill switch bayrağı, bütçe durumu) ve `policy.json` anayasal bölümünü yaz: aylık USD ve Actions dakikası tavanları, paylar, sınıf tabanları, `required_exit_rows`, regresyon dondurma kuralı, döngü ve gün tavanları, güvenlik anahtar kelimeleri, yasaklı ifadeler, aşama sırası, bakış bütçesi, güven düzeyi, non-inferiority marjı, hayatta kalma pencereleri, prova kuralları, lisans izin listesi ve istisnaları (`18a`) | Operatörün tek döngü dışı kolu; hiçbir App yazamaz |
| 5 | **Okuyucu App'i**: yalnız `contents:read`, `metadata:read`; beyin reposuna ve özel hedeflere kur | Hakem beyni ve hedefi yazma yetkisi olmadan çeksin |
| 6 | **Yazar App'i**: `contents`, `pull_requests`, `checks` yazma, `administration:read`; `workflows` yok; yalnız hedef repolara kur, beyin ve hakem reposuna kurma | Hedefe tek yazar; oyuncunun ve hakemin reposuna yazmasın |
| 7 | Hakem reposunun sırları: okuyucu ve yazar App anahtarları, sağlayıcı kimliği (tohum rakibi için `CLAUDE_CODE_OAUTH_TOKEN`), çıkış örneklemi ve prova gizli tohumları | Ajan konteynerine ve oyuncu kodu koşan işe hiçbiri girmez |
| 8 | Harcama tavanları: sağlayıcı harcama tavanı (tohum rakibi abonelik belirteciyle koşar: tavan planın kullanım sınırıdır, `06` bütçesi liste fiyatı tahminidir), GitHub Actions harcama sınırı (dakika aşımı ücretsiz durur, Gözcü bunu bütçe dondurması sayar) | Bütçe sert olsun |
| 9 | Kill switch'i üç yolla bir kez dene: `control.json` bayrağı, App askıya alma, sağlayıcı tavanı ya da belirteç sırrını silmek | Durdurma hakkı |
| 10 | Oyuncak hedef: boş, herkese açık bir repo aç; içeriği Aşama 0 çıkışında aktarılır (`25a`) | Etkinleştirmenin canlı provası |
| 11 | Kurucu'yu başlat: Actions dışında, çalışma dizini beyin reposu, hedef salt okunur klon (`24`) | Aşama 0 inşası |

**Actions dakikası hesabı.** Free planda özel repolar ayda ~2.000 dakika alır;
`monthly_cap_ci_minutes` 1.800'dür ve her iş en az bir dakika faturalanır. Önyükleme hakeminin
boştaki saatlik yoklaması tek iştir: ayda ≈ 24 × 30 = 720 dakika. Değerlendirilen bir push beş ya
da altı iştir, tipik olarak 15–30 dakika; kalan ~1.080 dakika ayda ~35–70 değerlendirme eder. Kurucu
bu yüzden birden çok mikro özelliği tek push'ta bitirir. Dakika biterse GitHub işleri durdurur
(madde 8) ve Gözcü bunu bütçe dondurması sayar. Tavanı genişletmek operatörün kararıdır ve plan
gerçeğini (madde 0) değiştirir: Pro planı (3.000 dakika) ya da her işten sonra sıfırlanan kendi
koşucusu. Hakem reposunu açık yapmak dakikayı bedava yapar ama imzalı sonuçlar beyin kodundan
alıntı taşır; önerilmez.

Bu bölümün özeti (`setup/summary.json`: repo adları ve görünürlükleri, kurulu App'ler ve izinleri,
iş akışı varsayılan izni, vektör ve koltuk hash'leri, anayasal politika hash'i, `seed_commit` ve
`python -m snowball_bootstrap seed-hash` ile hesaplanan `seed_tree_sha256`) operatörce hakem
reposuna yazılır; hash'i önyükleme hakeminin ilk koşusunda Rekor'a girer. Aşama 0 bu özet olmadan
başlamaz.
