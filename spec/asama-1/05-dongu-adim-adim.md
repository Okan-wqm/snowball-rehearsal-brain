# Aşama 1 §1.5 — Döngü, adım adım

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 1 çalışırken
Çapa: beklemede: aşama 1 çıkış raporu

---

0. **Başlangıç.** Hakemin zamanlayıcısı yoklar. Döngü `control.json`'u okur ve `drift.check` ile
   başlar; fark varsa sert duruş (`tohum/28`). Döngü deftere başlangıç satırı yazar.
1. **Çek.** `çek`, `brain.accept`'in kabul ettiği beyin SHA'sını ve `brain/integration` başını
   okuyucu App'iyle çeker; `getir` bağımlılıkları içerik adresli getirir.
2. **Discover.** `koş`, adapter'ı snapshot üzerinde koşar: aracın tüm ihlalleri, taban borcu dahil.
   Parmak izi `tohum/07`'deki gibidir; aynı parmak izi yeniden gözlemdir. Bu tabanda `unresolved`
   olmuş parmak izleri atlanır.
3. **Execute.** `koş`ta bulgu başına worktree açılır. Dosya güvenlik yolundaysa bulgu `blocked`.
   Önce `fixer.range`. Araç düzeltemezse `fixer.llm` tipli bir istek üretir; `çağır` onu `llm.call`
   ile işler (prompt taraması, bütçe belirteci, sunulan model) ve yapılandırılmış düzenlemeyi
   döndürür; `koş` onu deterministik uygulayıcıyla yalnız o aralığa yazar.
4. **Approve.** Aynı `koş`ta araç worktree üzerinde yeniden koşar: hedef ihlal kaybolmuş, mandal
   tutmuş; etkilenen-test komutu konteynerde koşar, sıfır test kırmızıdır. Kırmızı kontrol kırmızı
   çıkar. `candidate.publish` aday paketini `candidates/<id>/` çıktısına yazar. Tutmazsa worktree
   atılır, bulgu `cause` ile `unresolved.jsonl`'a önerilir.
5. **Merge.** `yaz` sonuçları artefakt kimliğiyle alır, hash'leri doğrular; `gate.diffguard`,
   izin listesi, mandal toplamları ve `secrets.scan` geçerse `brain/c/<id>`'den `brain/integration`'a
   PR açar, zorunlu kontrolü raporlar ve merge eder. Merge'ler sıralıdır; tavanlar `policy.json`'da.
6. **Watch.** Sonraki `koş` her merge'den sonra `sentinel.run` ile etkilenen testleri yeni başta
   koşar. Kırmızıysa 3/3 kuralıyla flaky olmadığı doğrulanır; sonra `yaz` o merge'ü `gate.revert`
   ile geri alır ve `cause` yazar; regresyon vaka adayı olur (`system_regression`). Merge'ler sıralı
   olduğu için bisect gerekmez.
7. **Learn.** `yaz` defter satırlarını döngü başına tek commit'le `brain/state`'e yazar; kök hash
   `chain/root.jsonl`'a ve Rekor'a girer. `gozcu.evaluate` ve `status.block` durum bloğunu yazar;
   `docs.render`'ın `koş`taki önerileri bulgu ve organ sayfaları olur. Her geri alma ve unresolved
   satırının `cause`'u ham ders satırıdır; ders görünümü ve enjeksiyonu Aşama 2'de açılır.
8. **Discover again.** Sonraki yoklamada yeni kabul edilmiş beyin SHA'sı ya da yeni entegrasyon
   başı döngüyü başlatır. Hakemin kendi yazımları döngü tetiklemez; olay tetiği yoktur. Döngü
   bitiş satırıyla kapanır.
