# Ölçüm İstatistiği: PASS Ne Zaman Anlamlıdır

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: her çıkış testi tasarlanırken ve her verdict okunurken
Çapa: beklemede: aşama 0 — harness raporundaki n, x_eff, census ve verdict alanları; vektörler `29a`

---

Küçük sette eşik yazı turadır: beş vakada "3/5" kararının %95 Clopper–Pearson güven aralığı
0,15 ile 0,95 arasındadır. Bu kurallar o yüzden vardır. Sayısal örnekler `29a` vektörleridir.

**Üç verdict.** `PASS`, `FAIL`, `UNMEASURABLE`. Örneklem yetersizse sonuç `UNMEASURABLE`'dır;
nedeni yazılır ve vaka arzı bir gap sinyali olur. `UNMEASURABLE` asla `PASS` gibi davranmaz.

**Alt sınır.** Tüm alt sınırlar tek yönlü Clopper–Pearson'dur; güven düzeyi `confidence_level`.
Vakalar aynı modül grubundan geliyorsa etkin örneklem grup sayısı G'dir ve etkin başarı
`x_eff = recall · G`'dir; alt sınır gerçel argümanlı Beta ile hesaplanır: `BetaInv(α; x_eff,
G − x_eff + 1)`. Bir sınıf tabanı, o sınıfın asgari örnekleminde erişilebilecek en yüksek alt
sınırı aşamaz: 10 grupta sıfır kaçırmayla bile alt sınır 0,794'tür. Precision'da
`n = TP + FP + unresolved`; unresolved FP gibi sayılır.

| Ölçüm | Asgari | Karar kuralı |
|---|---|---|
| Deterministik sarıcı sınıflar (K0, K1, K2, K4) | Etkin katalogda mutasyonla üretilebilen her kural ve her araç zinciri için ≥ 1 çıkış vakası; ≥ min(45, mevcut) modül grubu | **Kural sayımı:** sıfır kaçırma. CP alt sınırı raporlanır, kapılamaz |
| K5, K6 held-out recall | ≥ 25 `human_fix` vakası, ≥ 10 grup | `human_fix` katmanının nokta tahmini ve alt sınırı sınıf tabanının üstünde; mutasyonlar ayrı raporlanır, kapılamaz |
| Clean precision | ≥ 40 karara bağlanmış bulgu, ≥ 5 geçmiş entegrasyon başı | Ayrı parmak izleri, modül grubu etkin n; alt sınır tabanın üstünde |
| Organ kabulü (üstünlük) | Ayarda kullanılmamış vakalarda eşli, ≥ 8 uyuşmaz çift | Tam tek yönlü McNemar, p < 0,10, yön lehte; ya da değer / USD eşli bootstrap alt sınırı ≥ 1,2 |
| Maliyet inişi (non-inferiority) | Eşli, n ≥ 45 | Sabit marj δ = 0,05, tam test; "her basamak denendi ve başarısız" FAIL'dır |

**Neden kural sayımı.** Deterministik bir sarıcıda kaçırma örneklem gürültüsü değil kural
kusurudur; ölçülecek şey her kuralın sarılıp sarılmadığıdır. 0,95'lik CP alt sınırı sıfır
kaçırmayla bile en az 45 grup ister; küçük repoyu ölçülemez kılmak yerine sayım kapılar.

Koşu bütçesi daha çok snapshot'a harcanır; aynı snapshot'ın tekrarı vaka gürültüsünü değil, koşu
gürültüsünü ölçer.

**Held-out kaynağı.** Held-out, Kurucu'nun hesaplayamayacağı bir havuzdan gelir ve ilk havuzla
mühürlü depo açılır (Aşama 4 ön koşulu); K0 çıkışı ise taze, gizli tohumlu bir örneklemdir
(`exit.sample`). Havuz kaynakları: (1) mutasyonlar, gizli tohumla çok büyük bir aday havuzundan;
(2) insan düzeltmeleri **ileriye dönük**: exit talebinde avcının `prompt_sha256`'sı mühürlenir ve
yalnız mühürden sonra merge edilen insan düzeltmeleri sayılır, çünkü canlı hedefte kesim sonrası
düzeltmeler entegrasyon başlarından görünür; (3) hiç yayımlanmayan bir yedek havuz.

**Exit'te ne sayılır.** Yalnız `human_fix` katmanı kapılar; mutasyonlar ayrı raporlanır.
Anlamsal mutasyon geçerliliği: kod derlenir, mevcut testler yeşil kalır, operatör property'ye
bağlıdır. `system_tp` ve `system_regression` aynı organ soyunun held-out'una ve hiçbir exit
kapısına girmez.

**Bakış bütçesi.** Held-out **havuzu** başına tek bütçe vardır (`look_budget`); tüm property ve
soylar onu paylaşır, rotasyonla sıfırlanmaz. Bir bakış yalnız verdict döndürür, n ve alt sınır
döndürmez (alt sınır isabet sayısını ele verir). k. bakış α/k ile karar verir. Her bakış zincirli
bir `looks` satırıdır. Bütçe bitince havuz için ölçüm `UNMEASURABLE`'dır ve yeni ileriye dönük
vakalar beklenir. Maliyet merdiveninde yalnız kazanan basamak bir bakış harcar.

**Gizlilik.** Held-out koşusunun her ham artefaktı (bulgular, `repo_model.md`, koşu çıktıları)
mühürlü depoda kalır; ajan yalnız verdict'i görür. Kendi-test 18: dev grupları dışındaki adaylar
arasında held-out üyeliğini tahmin eden bir saldırganın AUC'si ≤ 0,5 + ε (`gate_rules.membership_auc`).

**Clean tabanlar.** Clean snapshot'lar ≥ 5 geçmiş entegrasyon başından, planted snapshot'lar eski
ebeveynlerden gelir; ikisi yaşla ayırt edilemez. Kanaryalar hem clean hem planted snapshot'lara
konur. Clean'deki her bulgu precision'a sayılır; panelin öldürdüğü bulgulardan gizli tohumla
seçilen bir örnek oracle'la denetlenir. Eski ağaçta bulunan TP güncel başta yeniden kırmızı olmalıdır.

**Seçerek sınanan çıktılar.** Bir organın çıktılarından yalnız bir kısmı sınanıyorsa (hipotez,
ders, örüntü önerisi), isabeti oluşturulurken gizli tohumla seçilmiş tekdüze bir denetim
örnekleminden ölçülür; sınanamayan iddia başarısız sayılır; ≥ 40 çözülmüş denetimden önce isabet
bütçe belirlemez; ölçüm oluşturma tarihi kohortlarıyla raporlanır (`gate_rules.audit_sample`).

**Bulaşma.** dev/held-out bölmesi modül grubu bazındadır. Exit koşularında avcı ders almaz ve
harita dondurulur. Dar kapsam basamağının glob'u yalnız dev koşularından türetilir.

**Başarısız basamak.** Bir koşu hüküm değildir. Eşiği tutmayan basamak vaka havuzu yarı yarıya
büyüyünce bir kez daha denenir.
