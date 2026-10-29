# Kurulum, İkinci Bölüm: Aşama 0 Çıkışında Aktarım ve Etkinleştirme

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çıkışının (A) parçası yeşil olduğunda, bir kez; her yeni hedefte satır 3–7
Çapa: hakem reposundaki `setup/summary.json`, ikinci bölüm; `brain/state` genesis satırı

---

Hedef repoya dokunan kurulum, Aşama 0'ın ürettiği hakemle yapılır; bu yüzden ikinci bölümdür.
Önyükleme hakemi pinli bir beyin SHA'sında Aşama 0 çıkışının (A) parçasını yeşil raporlamış
olmalıdır (`asama-0/10`).

| # | İş | Neden |
|---|---|---|
| 1 | **Operatör aktarımı:** aktarım betiğini koştur. Betik pinli SHA'daki `referee/` ağacını hakem reposuna kopyalar ve kod ağacının hash'inin, operatör dosyaları (`policy.json`, `control.json`, `setup/`, `seats/`, `vectors/`) hariç, Rekor'daki (A) kaydıyla aynı olduğunu doğrular; farklıysa durur. `referee/` bu adlarla dosya taşıyamaz. Aktarım sayacı bir artar | Hakem kodu yalnız aktarımla değişir (`01a`) |
| 2 | Aynı betik `tests/fixtures/toy-repo/`'yu oyuncak hedefin `main`'ine iter | Etkinleştirme provası için içerik |
| 3 | Hedefte ruleset'ler: `brain/state` için `deletion`, `non_fast_forward`; `brain/integration` için `deletion`, `non_fast_forward`, `pull_request` ve zorunlu kontrol (strict, `integration_id` = yazar App'i). Hiçbirinde bypass aktörü yok | Zincir ve entegrasyon dalı yazar App'ine bile yeniden yazılamasın |
| 4 | **Yazma modu şartı:** hedef `main` ruleset'inde yazar App'i bypass değildir ve `main` güncellemesi ya onaylı inceleme ister ya da güncelleme kısıtıyla yalnız operatör rolüne açıktır. Hedef bunu taşıyamıyorsa (özel repo, Free) bağlanma `mode: training`'dir | Yazar App'i `main`'e ulaşamasın (`21`) |
| 5 | Hedefe kurulu App'lerin listesini özete beyan et | Etkinlik API'sinde beyan dışı aktör sert duruştur (`01b`) |
| 6 | Hedefin mevcut iş akışlarından sır kullanan ve `brain/**` dallarında ya da PR'larında tetiklenen biri olmadığını doğrula; varsa dışla ya da bağlama | Ajan yazımlı kod sırla koşmasın; çatal çaresi yoktur |
| 7 | **Etkinleştirme koşusu:** aktarılan hakemi tetikle. Oyuncak hedefte ve gerçek hedefte `brain/state`'i genesis satırıyla açar, `brain/integration`'ı `main`'den keser, profili türetir, oyuncak hedefte canlı döngüyü koşar (`asama-0/10` (B)) | İlk durum ve canlı kanıt |

**Başarısızlık.** Satır 1 ya da 7 kırmızıysa sistem sert durur; düzeltilmiş SHA'nın aktarımı yine
operatörün işidir ve insan dokunuşu sayacında görünür.

**Her yeni hedef.** Satır 3–7 her yeni yazma modu hedefinde tekrar edilir; satır 5–6 da `drift.check`
ile her döngü yeniden doğrulanır (`21`). **Eğitim hedefi** için satır 3–4 yerine: operatörün özel
**eğitim deposunu** (ilk eğitim hedefinde) aç, yazar App'ini yalnız oraya kur, hedef başına bir dal
ayır; üçüncü kişi repolarına hiçbir App kurulmaz, hakem onları kimliksiz klonlar.

**Mühürlü depo (Aşama 4 ön koşulu).** Aşama 3 PASS'ten sonra, ilk held-out havuzundan önce:
özel mühürlü depoyu aç; **mühür App'ini** yalnız oraya kur (içerik yazma); mühür App anahtarını ve
HMAC mühür anahtarını hakem reposunun sırlarına ekle. Bu, aşama çıkışındaki aktarım gibi bir insan
dokunuşudur ve sayaçta görünür.

Bu bölümün özeti de hakem reposuna yazılır ve genesis satırına bağlanır. Bundan sonra her döngü
kurulumun bozulmadığını `drift.check` ile doğrular; bozulmuşsa sistem sert durur ve kalkış
operatörün döngü dışı işidir (`28`).
