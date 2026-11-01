# Önyükleme Hakemi, Devam: Kurucu Kayıtları, Sır Desenli Metin

Tarih: 2026-11-01 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 boyunca; Kurucu kaydı itilirken ve bir `secret_in_*` reddi okunurken
Çapa: `seed/bootstrap/snowball_bootstrap/` (`classify.py` `is_founder_record`, `rival.py` `secret_paths`, `decide.py`)

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
dokunmaz. Rakip tarafı hatada (bütçe ve `request_rejected` dışında) commit değerlendirilmemiş kalır ve sonraki koşu onu
yeniden inceler (uyarı `rival_side_retry:<n>`); üst üste üçüncü rakip tarafı hatada commit değerlendirilir ve operatör
uyarılır (`rival_side_streak:<n>`). Rakibin protokolü ona sır desenli dizgeyi kararına yazmamasını, yeniden üreticide
çalışma anında parçalardan kurmasını söyler.
