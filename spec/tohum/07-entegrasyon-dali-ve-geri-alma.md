# Entegrasyon Dalı, Nöbetçi, Geri Alma, Bulgu Kimliği

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: her döngü başında ve her merge'de
Çapa: beklemede: aşama 1 — `ledger.jsonl` merge ve geri alma satırları

---

**Entegrasyon dalı.** `brain/integration`, etkinleştirmede (`25a`) hedefin `main`'inden kesilir.
Aşama 0 ve 1'de `main` ona senkronlanmaz: senkron, hedefin iş akışı dosyalarını da taşıdığı için
yazar App'ine `workflows` izni gerektirir ve bu izin, uzlaşmış bir hakem işinin sırlı iş akışlarını
yeniden yazabilmesi demektir. Taban yaşı (dalın kesildiği `main` SHA'sından bu yana geçen süre ve
commit sayısı) `status.md`'dedir. Senkron, ölçülmüş ihtiyaçla (eskimiş bulgu oranı sinyali, `17`)
ve kendi güvenlik kararıyla Aşama 2 spec'inde açılır; açıldığında senkron PR'ının başı tam olarak
bir `main` SHA'sı olmalı ve `git merge-tree` sonucuna eşit olmalıdır. Çakışma çözülmez: çakışan
beyin değişikliği geri alınır, `blocked` yazılır ve yeni bir mikro görev olur. Zorla itme yoktur.

**Taban ve mandal.** Beyin bir repoya bağlandığında her aracın mevcut ihlallerinden bir taban
çıkarır; hakem bunu kendi koşusuyla doğrular ve deftere yazar. Keşif tabandaki ve sonradan doğan
tüm ihlalleri bulgu sayar; mevcut borç kapsam içindedir. Mandal kuralı: hiçbir merge bir aracın
toplam ihlal sayısını artıramaz; kapı bunu kendisi yeniden sayar.

**Merge'ler sıralıdır.** Kapı bir anda tek bir adayı merge eder; bir sonraki aday, öncekinin
nöbetçi koşusu bitince sıraya girer. Böylece her kırmızının tek bir şüphelisi vardır.

**Nöbetçi.** Her merge'den sonra hakemin nöbetçi işi (`sentinel.run`) `brain/integration` başında
etkilenen testleri `koş` işinde koşar. Kırmızı çıkarsa önce 3/3 kuralıyla flaky olmadığı
doğrulanır; sonra hakemin `gate.revert` işi o merge'ü geri alır. Bisect yalnız merge'ler sıralı
olmadığında gerekir (örneğin `main` senkronu açıldığında); o zaman `git bisect --first-parent`
yalnız son yeşilden bu yana beynin merge commit'leri üzerinde yürür, insan commit'leri bölünmez,
adım süresi ve sayısı `policy.json`'dadır. Bisect bir insan commit'ini gösterirse geri alınmaz;
raporlanır.

**Geri almayı hakem yapar.** Geri alma, merge kadar sıradan bir işlemdir; kapıdan geçer ve hakem
işiyle yapılır, beyin kendi merge'ünü geri almaz. Geri alma `cause` ile yazılır (`26`'daki kapalı
küme): kırmızı test beyan edilen etki kümesinin dışındaysa `impact_miss`, içindeyse
`test_regression` ve diğerleri. Regresyon vaka adayıdır (`provenance: system_regression`).
**Atıf puanlama olayıdır:** bir merge'ün kırmızıya atfedildiği an, geri alma işi gecikse bile
merge'ün sonucu "geri alındı" olarak sayılır; geciken geri alma pencereyi doldurup merge'ü
hayatta kalmış gösteremez.

**Hayatta kalma penceresi.** Hiçbir merge pencere dolmadan sayılmaz ya da puanlanmaz. Pencere
sınıfa göredir ve `policy.json`'un anayasal bölümündedir, çünkü çıkış satırlarını kapılar ve yalnız
uzayabilir: başlangıç K0 ve K1 için 72 saat, K5 ve K6 için 14 gün. Pencerede geri alınan iş
artısını almadan eksisini alır.

**Bulgu kimliği.** Parmak izi `property + dosya + sembol + normalize(iddia)`'dan türetilir.
Sembol yoksa, örneğin dosya düzeyindeki lint ihlallerinde, `kural + kapsayan sembol ya da dosya
+ normalize(satır içeriği)` kullanılır; satır numarası hiçbir parmak izine girmez. Aynı parmak
izi ikinci kez bulunursa yeni bulgu değil, yeniden gözlemdir. Yaşam döngüsü
`open → fixed → verified → reopened`; ayrıca `blocked` ve `unresolved` (`26`). Üç kez `reopened`
olan bulgu salınımdır; `blocked`'a düşer ve ikisini birlikte ele alan tek bir mikro görev olmadan
yeniden denenmez. Kredi kök neden başınadır (çakışan hunk ya da aynı sembol).
