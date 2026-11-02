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
| 1 | **Operatör aktarımı:** kill switch'i aç, sonra önyükleme paketinin `import` komutunu koştur (Aşama 0 çıkışında ve her parti çıkışında aynı komut; `29b`). Komut hiçbir çalışma ağacını okumaz ve yazmaz: hakem reposunu kendi geçici dizinine çıplak klonlar (yalnız `main`'i; oyuncaktan da yalnız `main` getirilir), pinli beyin commit'ini oraya git'in nesne denetimiyle (`fetch.fsckObjects`) getirir ve yalnız git nesneleriyle çalışır; yerel yol olarak verilen bir repo çağıranın dizininden okunur (sürücüye göreli yol o sürücünün dizininden), boş repo adı durdurur. Kill switch o `main`'in `control.json`'ıdır (tam `true`); açık değilse çalışmaz. İmzalı sonucu doğrular. Yeni `main`'in ağacı pinli SHA'daki `referee/` ağacı ve `main`'den tam adıyla alınan korunanlardır: operatör dosyaları (`policy.json`, `control.json`, `bootstrap.json`, `setup/`, `seats/`, `vectors/`) ve **önyükleme hakeminin `bootstrap/` ağacı ile `bootstrap.yml`'ı** (itme yargıcı kalır); `referee/.github/workflows/loop.yml` `.github/workflows/loop.yml`'a düşer, `main`'in başka hiçbir şeyi kalmaz. Hiçbir nesne yazılmadan önce `referee/`'nin her adı denetlenir; `26c`'nin reddettiği ad (denetim karakteri, ters bölü, iki nokta, `..`, harf duyarsız `.git`), bir dosya sisteminin başka ad okuduğu ad (sonda nokta ya da boşluk, aygıt adı, `~` ve rakam), Windows'un tutamadığı ad (`\|?*"<>`, 260 karakterden uzun yol; komut hangi sistemde koşarsa koşsun), 255 bayttan uzun tek ad (ext4'ün sınırı; NTFS'nin 255 UTF-16 birimi hiç daha çok bayt değildir), git'in kendisi için okuduğu ad (`.git`, checkout'un baytlarını değiştiren `.gitattributes`, başka yerden getiren `.gitmodules`; her derinlikte, harf duyarsız ve HFS+'ın yok saydığı kod noktaları olmadan), harf duyarsız olarak korunan bir girdi olan, onu tutan ya da ona giden ad, harf duyarsız tek ad olan iki ad, bağ ya da alt modül durdurur. `referee/`'nin blob'larından `26c` hash'i Rekor'daki (A) kaydıyla aynıdır; birleşik ağaçta her korunan girdi `main`'inkidir ve geri kalanı imzalı ağaçtır. Aktarım aynı commit'te `setup/imports.jsonl`'a bir satır ekler, sayaç bir artar. Hiçbir şey itilmeden önce git'in nesne denetimi (`receive.fsckObjects`) her itmenin göndereceğini denetler: yeni commit'in eriştiği, o uzak deponun okunan `main`'inin erişmediği nesneleri; başka bir daldaki ya da `main`'in zaten tuttuğu nesne durdurmaz. Aldığını denetleyen bir uzak deponun reddedeceği, oyuncak itildikten sonra değil, burada durdurur. Commit `main`'in üstüne, okunan `main`'e kirayla (`--force-with-lease=refs/heads/main:<sha>`) zorlamadan itilir: `main` arada ilerlediyse ya da geri alındıysa itme reddedilir, hakemde hiçbir şey değişmez ve ret uzak `main`'in o anki başını adlandırır. Operatör sonra `main`'i yerel klonuna çeker | Hakem kodu yalnız aktarımla değişir (`01a`); yargıç aktarılanla değişmez |
| 2 | Aynı komut oyuncak hedefin reposunun `main`'ine ağacı pinli SHA'daki `tests/fixtures/toy-repo/` olan bir commit iter (aynı ad kuralları ve hiçbir derinlikte `.github` yok: oyuncakta iş akışı yoktur, satır 6; hash'i (A)'daki `toy_tree_sha256`); oyuncak önce, hakem sonra itilir, her biri okunan `main`'ine kirayla. Parti aktarımı oyuncağa dokunmaz | Oyuncak hedefin içeriği (A)'da yargılanan olsun |
| 3 | İki hedefte (oyuncak ve kopya) ruleset'ler: `brain/state` için `deletion`, `non_fast_forward`; `brain/integration` için `deletion`, `non_fast_forward`, `pull_request` ve zorunlu kontrol (adı `snowball-gate`, strict, `integration_id` = yazar App'i). Hiçbirinde bypass aktörü yok | Zincir ve entegrasyon dalı yazar App'ine bile yeniden yazılamasın |
| 4 | **Yazma modu şartı:** hedef `main` ruleset'inde yazar App'i bypass değildir ve `main` güncellemesi ya onaylı inceleme ister ya da güncelleme kısıtıyla yalnız operatör rolüne açıktır (kopyada aynalama işi bu roldedir, `25` 10a). Hedef bunu taşıyamıyorsa (özel repo, Free) bağlanma `mode: training`'dir | Yazar App'i `main`'e ulaşamasın (`21`) |
| 5 | Hedefe kurulu App'lerin listesini özete beyan et | Etkinlik API'sinde beyan dışı aktör sert duruştur (`01b`) |
| 6 | Hedefin mevcut iş akışlarından sır kullanan ve `brain/**` dallarında ya da PR'larında tetiklenen biri olmadığını doğrula; kopyada Actions tamamen kapalıdır; oyuncakta iş akışı yoktur | Ajan yazımlı kod sırla koşmasın; çatal çaresi yoktur |
| 7 | **Etkinleştirme:** kill switch'i kapat; `loop_schedule` kapalı kalır, operatör devirleri elle tetikler. Döngü hakemi önce oyuncak hedefte `brain/state`'i genesis satırıyla açar, `brain/integration`'ı `main`'den keser, profili ve birim tarifini türetir, mandal tabanını kendi araç koşusuyla yazar ve `asama-0/08`'in devir sırasını koşar; oyuncağın 1–5. devirleri yeşil olunca aynı (B) içinde kopyada `targets[].base_sha`'dan genesis yapar. Güvenlik avcısının koltuğu ve güvenlik profili (`30d`, `30f`) P2 aktarımıyla gelir | İlk durum ve canlı kanıt |
| 8 | **Kopyanın adayları:** Kurucu yalnız `candidates/<kopya>/`'yı değiştiren bir push yapar (yayımlanan bir `fix`'i aynen uygulayan iyi aday ve bir birim testini kıran kötü aday); önyükleme hakemi kod isteği gibi yargılar, `referee/` ağacı değişmemiş olmalıdır. Operatör kopyanın devirlerini tetikler | Kopyada ilk gerçek merge |
| 9 | **Kilidin açılışı:** PASS satırından sonra `stage-open` komutunu koştur; PASS satırını okur, zinciri tohum koduyla ve kökü Sigstore ile doğrular, `setup/stage.json`'u yazar (`asama-0/10a`, `26c`; PASS satırının alanları ve komutun kuralı `26d`); incele ve it. Sonra `control.json` `loop_schedule: true`; kopyanın aynalaması günlük açılır (`25` 10a) | Aşama 1 ancak PASS'ten sonra açılsın |

**Başarısızlık.** Satır 1, 7 ya da 8 kırmızıysa sistem sert durur; operatör aktarım commit'ini `git revert`
eder ve çıkışın imzalı sonuçtaki başını `control.json` `reverted_exits`'e ekler (`26c`): (A)'nın dondurması kalkar
(`29b` "Çıkıştan sonra"), itme yargıcı aktarımdan etkilenmediği için Kurucu'nun yolu açık kalır. Düzeltilmiş SHA (A)'dan
yeniden geçer; aktarımı yine operatörün işidir ve insan dokunuşu sayacında görünür. Hedeflerin `brain/state`'i silinmezse
(satır 3) (B) iki hedefte yeni aktarımı adlandıran yeni bir genesis satırından yeniden koşar; `stage-open` son genesis'i
okur (`26d`).

**Her yeni hedef.** Satır 3–7 her yeni yazma modu hedefinde tekrar edilir; satır 5–6 P1 aktarımından sonra
`drift.check` ile her döngü yeniden doğrulanır (`21`); ondan önce yalnız genesis'te. **Eğitim hedefi** için
satır 3–4 yerine: operatörün özel **eğitim deposunu** (ilk eğitim hedefinde) aç, yazar App'ini yalnız oraya
kur, hedef başına bir dal ayır; üçüncü kişi repolarına hiçbir App kurulmaz, hakem onları kimliksiz klonlar.

**Mühürlü depo (K5 ön koşulu, `03`).** Held-out havuzunu getiren aşama açılınca, ilk held-out havuzundan önce:
özel mühürlü depoyu aç; **mühür App'ini** yalnız oraya kur (içerik yazma); mühür App anahtarını ve
HMAC mühür anahtarını hakem reposunun sırlarına ekle. Bu, aşama çıkışındaki aktarım gibi bir insan
dokunuşudur ve sayaçta görünür.

Bu bölümün özeti de hakem reposuna yazılır ve genesis satırına bağlanır. P1 aktarımından sonra her döngü
kurulumun bozulmadığını `drift.check` ile doğrular; bozulmuşsa sistem sert durur ve kalkış operatörün
döngü dışı işidir (`28`).
