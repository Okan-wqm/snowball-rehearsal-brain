# Önyükleme Hakemi, Devam: Kurucu Kayıtları, Sır Desenli Metin, Sınav Hatası, Bütçe Durması, Genellik Okuması

Tarih: 2026-11-01 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 boyunca; Kurucu kaydı itilirken, bir `secret_in_*` reddi okunurken, bir ret sınav hatası sayılınca, bir baş rakip frenine takılınca ve bir #genellik nedeni okunurken
Çapa: `seed/bootstrap/snowball_bootstrap/` (`classify.py` `is_founder_record`, `rival.py` `secret_paths`, `config.py` `load_exam_faults`, `decide.py`, `cli.py` `rival_allowance` ve `brake_raised`, `exitchecks.py` `generality`)

---

`29b`'nin devamıdır; aynı kurallar geçerlidir.

**Kurucu kayıtları.** Kökteki `founder-ledger.jsonl` ve kökteki `reports/` altındaki dosyalar Kurucu kayıtlarıdır: ne
spec ne koddur ve push'un türünü değiştirmez; spec isteğini karışık, `exit-request.json`'un yanında çıkış isteğini yalnız
olmayan yapmaz (iç içe bir `reports/` dizini koddur). Yalnız Kurucu kayıtlarını değiştiren push değerlendirilmez: sonuç
`noop`'tur; test, vektör ve rakip koşmaz, seriler ve son kabul edilmiş SHA değişmez. Spec ve kod isteğinde defterin son
kabul edilmiş SHA'dan bu yana eklenen satırları, çıkış isteğinde defterin tamamı denetlenir (`founder_ledger_invalid`,
`asama-0/10` #kurucu-defteri). Rakip ikisini de görmez.

**Sır desenli metin.** Rakibe gidecek istekte sır desenli bir dizge bulunursa rakip çağrılmaz: ret nedeni
`rival_unresolved`, `ref`'i `secret_in_prompt:<kural>[,<kural>…]`'dır (tohum tarayıcısının kural adları); `detail`
yoktur, `detail_sha256` boş dizginin sha256'sıdır. İmzalı sonucun `rival.secret_paths` alanı, diff'te bölümü sır desenli
dizge taşıyan dosyaların yollarını diff sırasıyla verir (en çok 20); ilk dosya bölümünden önceki istek metni
`(request text)` adını alır; kendisi sır desenli olan yol adlandırılmaz; satır numarası ve değer verilmez (`30c`).
`secret_in_prompt` Kurucu'nun düzeltebildiği rettir, ret hafızasında sayılır. Rakibin kararının denemelerindeki bir metin
(iddia, kanıt yolu, yeniden üretici) sır desenli dizge taşırsa karar kullanılmaz ve hiçbir parçası yayımlanmaz: neden
`rival_unresolved`, `ref` `secret_in_verdict:<kural>[,<kural>…]`, `detail` yoktur. Bu rakibin hatasıdır, serilere
dokunmaz. Rakip tarafı hatada (`request_rejected` dışında) commit değerlendirilmemiş kalır ve sonraki koşu onu
yeniden inceler (uyarı `rival_side_retry:<n>`); üst üste üçüncü rakip tarafı hatada commit değerlendirilir ve operatör
uyarılır (`rival_side_streak:<n>`). Rakibin protokolü ona sır desenli dizgeyi kararına yazmamasını, yeniden üreticide
çalışma anında parçalardan kurmasını söyler.

**Sınav hatası** (E53). Operatör bir reddin sınavın kendi hatası olduğunu doğrularsa (yanlış vektör ya da yanlış kanıt:
Kurucu doğru kodu tuttuğu için reddedildi), reddedilen başı ve ret imzasını `control.json` `exam_faults`'a `{head,
signature}` olarak yazar. İmza "Ret hafızası"nınkidir (`29b`), imzalı durumun `reject_streaks` anahtarı: `tür:test`,
`tür:ref`, çürütmede `refutation:<anahtar>`. Girdi, son tohum döneminin commit'i (dönem yoksa kurulum tohumununki)
adlandırdığı başın atası olduğu sürece, yani o başı yargılayan sınav yürürlükteyken geçerlidir; sonraki tohum dönemi onu
kendiliğinden kapatır. Geçerli girdinin imzası serilere sayılmaz, ret o imza yokmuş gibi okunur: imzalı durumdaki seri
girdisi geri alınır, imza `repeated`, `not_learning` ve `repeat_events`'e girmez, başka nedeni olmayan ret seriler için
kabul gibidir; öbür imzalar her zamanki gibi sayılır. Ret kalır: sınav düzeltilene kadar o imza reddetmeye devam eder.
Geçerli imzalar sonucun `exam_faults`'undadır. Biçimsiz liste ya da beyinde olmayan baş koşuyu durdurur (operatörün
dosyasıdır, ret değildir). Daha önce sayılmış `repeat_events` geri alınmaz.

**Bütçe durması** (E34, E550; `asama-0/12`). Rakibin bir koşuda harcayabileceği pay, ayın tavanından
(`monthly_cap_usd`) ve açık aşamanın freninden (`stage_budgets.asama_<k>.rival_usd`, `26e`) kalanla koşu başı tavanın
(`bootstrap.json` `rival.per_run_cap_usd_micros`, CLI'nin `--max-budget-usd`'si) en küçüğüdür; onu veren fren
`month`, `stage` ya da `per_run`'dır (eşitlikte bu sırayla). Rakip isteyen başın payı sıfır ya da altındaysa ve başka
ret nedeni yoksa test ve rakip koşmaz, neden `budget`'tır; rakip çağrısı frene takılırsa neden `rival_unresolved`,
`ref` `budget`'tır ve harcadığı yazılır. Koşu Kurucu'nun bir ret nedenini de bulduysa (hâlâ üreyen kusur, çıkış
koşulu) baş o nedenle yargılanır, fren yalnız uyarıdadır; yoksa ikisinde de baş yargılanmamıştır: sonuç kesintideki
gibi `rejected` der, ama `last_evaluated_sha`, seriler, rakip hata serisi ve kesinti sayacı değişmez; sonuç
`budget_stop {brake, allowed_usd_micros}`'u (fren ve duran koşunun payı) ve `rival_budget:<fren>` uyarısını taşır.
Sonraki yoklamalar, elle tetiklenen koşu da, aynı başı payı `allowed_usd_micros`'tan (en az sıfırdan) büyük olana dek
uyarıyla geçer: ay freni ay dönünce, her fren operatör onu yükseltince aynı baş kendiliğinden yargılanır; yeni baş her
zamanki gibi okunur. Bu kuraldan önce yargılanmış sayılan baş (`last_evaluated_sha`) yeniden açılmaz.

**Genellik okuması** (`asama-0/10` #genellik; E284, E290, E291). Denetim yalnız çıkış isteğinde, beyin arşivinin
`referee/` altındaki her dosyada koşar; kod push'unda hiçbir hedef adıyla karşılaştırma yoktur. Adlar
`setup/summary.json` `targets[].identifiers`'tır: operatörün verisi, kopya hedefi ayıran adlar; liste de sayısı da
oturuma verilmez. Ad da aranan yer de aynı biçimde karşılaştırılır (NFKD, casefold, birleşen işaretler atılır, `ı` `i`
okunur) ve ad alt dizge olarak aranır. Önce dosyanın yolu (`referee/`'den sonrası) aranır, yolunda ad olan dosyanın
metni okunmaz; sonra metni. Metin, katı UTF-8 olarak çözülen ve NUL (U+0000) taşımayan dosyadır; öbür denetim
karakterleri metindir. Metin olmayan dosya okunmadan geçmez: `referee_file_not_text:<yol>`; yolunda ya da metninde ad
olan dosya `target_name_in_referee:<yol>`. Ad taşıyan yol sonuçta `sha256:` ve sha256'sının ilk 16 onaltılık
karakteridir; `why` hedefi ve adı yalnız sırasıyla söyler (`targets[<i>].identifiers[<j>]`). Kopya hedef ya da onun
adları yoksa karar yoktur, çıkış `not_checked:genellik` ile kapalı kalır. Denetimden geçmek genelliğin kanıtı değildir:
ölçüsü `21`'in ilkesidir.
