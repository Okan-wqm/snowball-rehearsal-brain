# Kurulum, İkinci Bölüm: Aşama 0 Çıkışında Aktarım ve Etkinleştirme

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çıkışının (A) parçası yeşil olduğunda, bir kez; her parti ve aşama çıkışında satır 1; her yeni hedefte satır 3–7
Çapa: hakem reposundaki `setup/summary.json`, ikinci bölüm; `setup/imports.jsonl`; `brain/state` genesis satırı

---

Hedef repoya dokunan kurulum, Aşama 0'ın ürettiği döngü hakemiyle yapılır; bu yüzden ikinci bölümdür.
Önyükleme hakemi pinli bir beyin SHA'sında Aşama 0 çıkışının (A) parçasını yeşil raporlamış olmalıdır
(`asama-0/10`); bu bölüm (B)'nin parçasıdır (`asama-0/10a`).

| # | İş | Neden |
|---|---|---|
| 1 | **Operatör aktarımı:** kill switch'i aç, sonra önyükleme paketinin `import` komutunu koştur (Aşama 0 çıkışında ve her parti çıkışında aynı komut; `29b`). Komut imzalı sonucu doğrular; pinli SHA'daki `referee/` ağacını hakem reposunun yerel klonunun köküne, `referee/.github/workflows/loop.yml`'u `.github/workflows/loop.yml`'a koyar; **önyükleme hakeminin `bootstrap/` ağacına ve `bootstrap.yml`'a dokunmaz** (itme yargıcı kalır). Ağacı önce kardeş bir geçici dizine açar, diskteki ağacı yeniden hash'ler ve operatör dosyaları (`policy.json`, `control.json`, `bootstrap.json`, `setup/`, `seats/`, `vectors/`, `bootstrap/`) hariç Rekor'daki (A) kaydıyla aynı olduğunu doğrular; farklıysa durur. `referee/` bu adları ve ajan yapılandırmasını büyük-küçük harf duyarsız taşıyamaz. Kill switch açık değilse çalışmaz. Betik hiçbir şey itmez: operatör `git status`'u inceler ve iter. Aktarım `setup/imports.jsonl`'a bir satır yazar, sayaç bir artar | Hakem kodu yalnız aktarımla değişir (`01a`); yargıç aktarılanla değişmez |
| 2 | Aynı komut `tests/fixtures/toy-repo/`'yu taze bir dizine açar; hash'i (A)'daki `toy_tree_sha256` ile aynı olmalıdır. Operatör onu oyuncak hedefin `main`'ine iter | Oyuncak hedefin içeriği (A)'da yargılanan olsun |
| 3 | İki hedefte (oyuncak ve kopya) ruleset'ler: `brain/state` için `deletion`, `non_fast_forward`; `brain/integration` için `deletion`, `non_fast_forward`, `pull_request` ve zorunlu kontrol (strict, `integration_id` = yazar App'i). Hiçbirinde bypass aktörü yok | Zincir ve entegrasyon dalı yazar App'ine bile yeniden yazılamasın |
| 4 | **Yazma modu şartı:** hedef `main` ruleset'inde yazar App'i bypass değildir ve `main` güncellemesi ya onaylı inceleme ister ya da güncelleme kısıtıyla yalnız operatör rolüne açıktır (kopyada aynalama işi bu roldedir, `25` 10a). Hedef bunu taşıyamıyorsa (özel repo, Free) bağlanma `mode: training`'dir | Yazar App'i `main`'e ulaşamasın (`21`) |
| 5 | Hedefe kurulu App'lerin listesini özete beyan et | Etkinlik API'sinde beyan dışı aktör sert duruştur (`01b`) |
| 6 | Hedefin mevcut iş akışlarından sır kullanan ve `brain/**` dallarında ya da PR'larında tetiklenen biri olmadığını doğrula; kopyada Actions tamamen kapalıdır; oyuncakta iş akışı yoktur | Ajan yazımlı kod sırla koşmasın; çatal çaresi yoktur |
| 7 | **Etkinleştirme:** kill switch'i kapat; `loop_schedule` kapalı kalır, operatör devirleri elle tetikler. Döngü hakemi önce oyuncak hedefte `brain/state`'i genesis satırıyla açar, `brain/integration`'ı `main`'den keser, profili ve birim tarifini türetir, mandal tabanını kendi araç koşusuyla yazar ve `asama-0/08`'in devir sırasını koşar; oyuncağın 1–5. devirleri yeşil olunca aynı (B) içinde kopyada `targets[].base_sha`'dan genesis yapar. Güvenlik avcısının koltuğu ve güvenlik profili (`30d`, `30f`) P2 aktarımıyla gelir | İlk durum ve canlı kanıt |
| 8 | **Kopyanın adayları:** Kurucu yalnız `candidates/<kopya>/`'yı değiştiren bir push yapar (yayımlanan bir `fix`'i aynen uygulayan iyi aday ve bir birim testini kıran kötü aday); önyükleme hakemi kod isteği gibi yargılar, `referee/` ağacı değişmemiş olmalıdır. Operatör kopyanın devirlerini tetikler | Kopyada ilk gerçek merge |
| 9 | **Kilidin açılışı:** PASS satırından sonra `stage-open` komutunu koştur; PASS satırını okur, zinciri tohum koduyla ve kökü Sigstore ile doğrular, `setup/stage.json`'u yazar (`asama-0/10a`, `26c`); incele ve it. Sonra `control.json` `loop_schedule: true`; kopyanın aynalaması günlük açılır (`25` 10a) | Aşama 1 ancak PASS'ten sonra açılsın |

**Başarısızlık.** Satır 1, 7 ya da 8 kırmızıysa sistem sert durur; operatör aktarım commit'ini `git revert`
eder; itme yargıcı aktarımdan etkilenmediği için Kurucu'nun yolu açık kalır. Düzeltilmiş SHA'nın aktarımı
yine operatörün işidir ve insan dokunuşu sayacında görünür.

**Her yeni hedef.** Satır 3–7 her yeni yazma modu hedefinde tekrar edilir; satır 5–6 P1 aktarımından sonra
`drift.check` ile her döngü yeniden doğrulanır (`21`); ondan önce yalnız genesis'te. **Eğitim hedefi** için
satır 3–4 yerine: operatörün özel **eğitim deposunu** (ilk eğitim hedefinde) aç, yazar App'ini yalnız oraya
kur, hedef başına bir dal ayır; üçüncü kişi repolarına hiçbir App kurulmaz, hakem onları kimliksiz klonlar.

**Mühürlü depo (Aşama 4 ön koşulu).** Aşama 3 PASS'ten sonra, ilk held-out havuzundan önce:
özel mühürlü depoyu aç; **mühür App'ini** yalnız oraya kur (içerik yazma); mühür App anahtarını ve
HMAC mühür anahtarını hakem reposunun sırlarına ekle. Bu, aşama çıkışındaki aktarım gibi bir insan
dokunuşudur ve sayaçta görünür.

Bu bölümün özeti de hakem reposuna yazılır ve genesis satırına bağlanır. P1 aktarımından sonra her döngü
kurulumun bozulmadığını `drift.check` ile doğrular; bozulmuşsa sistem sert durur ve kalkış operatörün
döngü dışı işidir (`28`).
