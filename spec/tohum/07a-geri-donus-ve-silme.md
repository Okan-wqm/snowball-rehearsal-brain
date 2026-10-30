# Geri Dönüş ve Silme: Kimsenin İşi Kaybolmaz

Tarih: 2026-10-30 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: koda, dokümana ya da veriye dokunan her adayda; silen, birleştiren ya da veriyi yok eden adayda baştan sona
Çapa: beklemede: aşama 2 — silme adaylarının kapı kararları, sahibin onay kayıtları, geri almalar

---

**Sahibin kararı (2026-10-30).** Biri bir şeye başlamış, işe yaramadığı için duraklatmış olabilir;
Snowball onu silmez. Gerçekten aynı işi yapan parçaları mimari olarak birleştirip kopyaları
silebilir; ama biri bir şey geliştiriyorsa o silinmez. Bu sayfa bu kararı ve Y2'nin geri dönüş
yasasının hedefteki biçimini, kapının adaydan denetlediği kısıtlar olarak tutar. Kısıt neyin tutması
ve kimin onaylaması gerektiğini söyler; yarım işi artıktan ayırmanın, kullanımı ölçmenin ve
kanıtlamanın yolunu sistem tasarlar. Kurallar hedefin kodu, dokümanı ve verisi içindir.

**Geri dönüşün biçimi.** Kodda ve dokümanda geri dönüş, hakemin merge'ü geri almasıdır (`07`);
geçmiş yeniden yazılmadığı için bu yol kapanmaz (`01b`). Geri almanın geri getiremediği her etkinin
(veri, ayrı dağıtılan bir tüketici) geri dönüşünü aday adlandırır ve kanıtlar; kapı onu adaydan
denetler. Kodu geri almak da geri migration da kayıtları geri getirmez: veride geri dönüş arşiv ve
yedektir.

**Kullanılmıyor olmak ölü olmak değildir.** Çağıranı ya da okuyucusu olmayan birim yarım kalmış ya
da duraklatılmış bir iş olabilir; K2'nin aracı kullanılmayanı bulur, silmeye karar vermez. Bir
birimi (modül, dosya, sembol, test hedefi, uç, doküman ya da bölümü) kaldıran her değişiklik, hangi
sınıftan gelirse gelsin, silmedir ve yalnız şu kurallarla olur:

1. **Yarım ya da duraklatılmış iş silinmez,** yalnız kanıtıyla bildirilir; onu anlatan plan ya da
   tasarım dokümanı o işin parçasıdır ve bir doküman düzeltmesi onun anlattığını da silemez. Kanıt
   yükü silendedir: kimsenin geliştirmediği kanıtlanmamış her birim yarım iş sayılır.
2. **Gerçekten aynı işi yapan parçalar birleştirilebilir.** Aynılık benzerlikle değil yürütmeyle
   kanıtlanır (Y8, `31`); kaldırılan kopya için 1'in kanıtı da gerekir: geliştirilen bir
   uygulama, işi bir başkasınınkiyle aynı olsa da kopya sayılmaz.
3. **Eskimiş artık yalnız sahibin onayladığı adayla silinir.** Artık, kimsenin geliştirmediği ve
   bir işin kopyası olmayan birimdir; 1'in kanıtı ile sahibin onayı birlikte gerekir.
4. **Emin olunamıyorsa tutulur ve bildirilir.** Kanıt eksik ya da çelişkiliyse silme yoktur.

Her silme adayı, silinen her birimin 2 ya da 3'ten hangisiyle silindiğini ve kanıtını taşır.

**Sahibin onayı.** Hedefin sahibinin, adayın son hâline bağlı, kalıcı ve kurcalamaya dayanıklı
kaydıdır; hiçbir ajanın, rakibin ya da kapının kararı onun yerine geçmez. Onay beklenmez (Y8):
onay gerektiren aday sahibe bırakılır, döngü başka işle sürer; onaysız aday hiçbir zaman geçmez.

**Veriyi yok eden adım.** Kalıcı veriyi silen, üzerine yazan ya da bilgi kaybettirerek dönüştüren
her adım (temizleme işi dahil; sınıflaması `05`) sahibin onayını ve şu iki şartı taşır; kapı
ikisini de adaydan denetler:

- **Önce geri getirilebilir.** Yok edilecek veri, daha önceki ayrı bir adımda yerinde geri
  getirilebilir kılınmıştır (arşiv ya da yumuşak silme).
- **Süresiz, denenmiş yedek.** Adımı kapsayan, geri yüklemesi provayla denenmiş ve saklama süresi
  sınırsız bir yedek vardır; ona yalnız sahip, sistemin dışında son verebilir. Sistem yedeği
  göremez: aday onu önkoşul olarak adlandırır, sahip doğrular.

**Bildirmek silmek değildir.** Silinmeyen her birim, nedeni (1, birleştirilmeyi bekleyen 2, onay
bekleyen 3 ya da 4) ve kanıtıyla bulgu olarak kalır (`15`).
