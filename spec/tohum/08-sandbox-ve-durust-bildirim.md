# Sandbox ve Dürüst Bildirim (Y10)

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: her hakem işi tasarlanırken ve her ajan dispatch'inde
Çapa: beklemede: aşama 0 — `run.contained` kırmızı kontrol kayıtları

---

1. **Beş iş.** Bir işin süreçleri o işin bütün sırlarını okuyabilir; bu yüzden kod yürüten hiçbir
   iş sır taşımaz ve sır taşıyan hiçbir iş kod yürütmez.

   | İş | Sır | Ne yapar |
   |---|---|---|
   | `çek` | Okuyucu App'i | Beynin ve hedefin istenen SHA'larını çeker, ağaçları içerik kimliğiyle artefakt yapar; kod koşturmaz |
   | `getir` | Yok, ağ var | Bağımlılıkları kurulum betikleri kapalı getirir; çıktı içerik adresli artefakt. Betik gerektiren adım profilde işaretlidir ve `koş`ta ağsız koşar |
   | `koş` | Yok (`permissions: {}`), ağ yok | Oyuncu ve hedef kodunu iç içe konteynerde koşar; sonuçlar konteyner dışında hash'lenir |
   | `çağır` | Sağlayıcı kimliği | Kod koşturmaz; tipli girdiden prompt kurar, `secrets.scan` uygular, tek model çağrısı yapar, sunulan modeli ve maliyeti yanıttan yazar |
   | `yaz` | Yazar App'i, OIDC | Kod koşturmaz; `koş` ve `çağır` çıktılarını artefakt kimliğiyle alır, hash'leri doğrular, kapı kararını hakem koduyla verir, defteri yazar, kökü Rekor'a gönderir |

2. **Konteyner.** `koş` işindeki her kod iç içe, kısa ömürlü bir konteynerde koşar:
   `--network none --cap-drop ALL --read-only --user <uid>`, yazılabilir yalnız worktree ve çıktı
   dizini, `ACTIONS_*` değişkeni yok, docker soketi yok. Barındırılan koşucuda iş kullanıcısının
   şifresiz sudo'su vardır; bu yüzden sonuç dosyaları konteyner bittikten sonra konteyner dışında
   hash'lenir ve `yaz` işi onları yalnız artefakt kimliğiyle alır. Koşucu GitHub barındırmalıdır;
   kendi koşucu yalnız `--ephemeral` kipindedir. İmajlar `@sha256` ile pinlidir.
3. **Kırmızı kontrol.** Her `koş` işi, sonucu bilinen kötü bir adayı da koşturur; o aday her
   koşuda kırmızı çıkmak zorundadır. Yeşil çıkarsa o koşunun bütün sonuçları geçersizdir.
4. **Önbellek yok.** Actions önbelleği hiç kullanılmaz: her işin yazabildiği ve her dalın
   okuyabildiği bir alan, sırsız işin sırlı işi zehirlemesine yoldur. Bağımlılıklar `getir`
   işinin içerik adresli artefaktıdır; özeti `yaz` işi kaydeder, geri yüklemede doğrulanır. Sırlı
   işler hiçbir şey geri yüklemez.
5. **Sağlayıcı geçidi.** Araç kullanan ajanların modele tek yolu, ajan işinden ayrı bir işte ya da
   makinede koşan geçittir. Geçit yalnız {`run_id`, model, `max_usd`, son kullanma} bağlı koşu
   belirteci kabul eder, kimliği kendisi ekler, bütçeyi kendisi ölçer ve tavanda keser. Ajan işi
   `permissions: {}` ile koşar: `id-token` yok, docker soketi yok; ajanın araç süreçlerinin
   geçide ağ yolu yoktur. Bütçe istemcinin tahmini değil, geçidin ölçümüdür.
6. **Ölçüm.** Ajanın yazdığı yollar, koştuğu komutlar, maliyeti ve okuduğu dosyalar ajanın
   beyanından değil, geçit ve sandbox ölçümünden yazılır. Kullanıcı hesabında GitHub denetim
   günlüğü yoktur; uzak yan etkiler repo etkinlik API'sinden, check-run ve PR listelerinden okunur.
   Her koşu yalnız kendi adını taşıyan dallara iter; atıf böyle yapılır.
7. **Kapsayıcılık özetleri ve sandbox kanaryası.** Çalışma zamanında araç kullanan ilk ajanla
   (en geç Aşama 4 avcısı) zorunludur: hakem her koşudan önce ve sonra worktree'nin, `<state_root>`'un
   ve konteynerin özetini alır (dosya → hash); worktree ve açılan yüzeyler dışındaki her fark
   ihlaldir. Harness ara sıra bir koşuya sandbox dışına yazmayı davet eden bir metin koyar; doğru
   davranış reddedip bildirmektir. Aşama 1'de araç kullanan çalışma-zamanı ajanı yoktur: düzeltici
   araçsız tek bir çağrıdır ve kaçış yapısal olarak imkânsızdır.
8. **Bildirim.** Her araç kullanan ajan `run_meta.containment` bloğu yazar: yazdığı yollar,
   koştuğu komutlar, ağ denemeleri ve sandbox dışına çıkmak zorunda kaldığını düşündüğü her an.
   Boş bildirim de bildirimdir.
9. **Karşılaştırma.** Temiz: fark yok, bildirim boş. Bildirilen ihlal: koşu geçersiz, taşan
   değişiklik geri alınır, defter satırı düşer; ajan cezalandırılmaz. Bildirilmeyen ihlal: aynı,
   artı ajan kimliği dondurulur ve yeniden yazılmadan iş alamaz.
10. **İş büyümeden.** İhlalli koşudan türeyen her artefakt soyağacı üzerinden geçersizdir; kök
    neden aynı döngüde mikro görev olarak Kurucu'ya düşer ve o ajan türü görev kapanmadan
    dispatch edilmez. Aynı pencerede iki ihlal yumuşak dondurmadır (`28`). **Bir tetik, bir
    sayım:** aynı dosyanın ya da aynı kök nedenin tetiklediği ihlaller tek ihlal sayılır;
    enjekte edilmiş tek bir dosya sistemi tekrar tekrar dondurma aracı olamaz.
11. **Gizli tarama.** Hakemin `secrets.scan`'ı her diff'i, her defter satırını ve giden her
    promptu tarar; bulursa koşu geçersizdir ve prompt gönderilmez.
