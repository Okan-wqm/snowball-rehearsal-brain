# Kas Büyütme Sinyalleri: Hangi Ölçüm Hangi Organı Doğurur

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: her döngü sonunda, genesis kuyruğu kurulurken
Çapa: beklemede: aşama 1 — defterdeki `cause` ve `miss_reason` sayıları; `impact_miss` satırları

---

Tohum organ vermez, organ büyütme refleksi verir. Kurucu'ya "şu hafızayı kur", "okuyarak öğren"
ya da "şu adapter'ı yaz" denmez. Ona şu denir: bu sayı bu eşiği aşınca bu türde bir organ
taslakla, çekişme protokolünden geçir (`10`), gerekliliğini ablasyonla kanıtla (`12`). Sistem son
durum mimarisine kendi başına varır; varamıyorsa ölçüm o parçanın gerekmediğini söylüyordur.
Öğrenme organlarının ölçüsü hatadır (Y5, `16`): her satır bir hata ya da maliyet sayısına bağlıdır.

## Başlangıç sinyal tablosu

| Ölçülen sinyal | Eşik | Doğan organ adayı |
|---|---|---|
| `impact_miss`: merge sonrası kırmızının nedeni beyan edilen etki kümesi dışında | Pencerede ≥ 1 | Harita adapter'ı, katman (a); semantik hafıza (`13`) |
| Harness kaçırması, `miss_reason: map_edge_missing` | Pencerede ≥ 3 | Haritaya yeni katman ya da kenar türü |
| Geri alma, `cause: contract_counterpart` | ≥ 1 | Haritaya yeni kenar türü; oracle kapsamı genişler |
| Aynı `cause` tekrarı | ≥ 3 | Ders kümesinden skill ya da dedektör taslağı |
| Aynı tür düzeltmede ölçülmüş boşluk, en az 3 örnekle | Maliyet sınıf medyanının 2 katı ya da başarısızlık > %30 | Prosedürel skill |
| Yeniden analiz maliyeti / değişen satır | Medyanın 3 katı | Sembol düzeyi kimlik ve geçersizleştirme |
| Yargıç faz kararı ile faz 5 uyuşmazlığı | Pencerede > %30 | Yargıç yeniden yazımı ya da yeni koltuk (şerit yazarı) |
| Sınıfta vaka var, recall eşiğin altında | 2 pencere | Yeni avcı ya da adapter |
| Çözülemeyen bulgu oranı | > %30 | Oracle kası: test-yazıcı yeniden yazımı |
| `unresolved`, nedeni "test yazılamadı", birikiyor | Pencerede ≥ 5 | Okuyarak hipotez üreten organ |
| Aynı ders ya da bilgi bir bağlamda hit, öbüründe miss | ≥ 1 çelişki | Koşul araştırması organı (`21a`) |
| İkinci repo bağlandı | 1 | Küresel katman ve taşıma organı (`21a`) |
| Bir repodaki gap ile başka repoda hayatta kalmış bir organın bağlamı eşleşiyor | ≥ 1 | Örüntü önerisi (`21a`) |
| Oracle maliyeti / okuma maliyeti | Medyanın 3 katı | Okuma basamağı (maliyet merdiveni) |
| Aynı `origin`'den gelen öneriler bir sınıfta geri alınıyor | Pencerede ≥ 3 | Sentez organı (`10`, `21a`) |
| K8 bulguları birikiyor | Pencerede ≥ 5 | Doküman organı (`15`) |
| Aynı dosyalar koşular arasında yeniden okunuyor | Okumaların > %50'si | Önbellek ya da özet hafızası |
| Sınıflandırılamayan kaçırma | Pencerede ≥ 3 | Yeni `miss_reason` kategorisi ve yeni sinyal |

Eşikler başlangıç değeridir; `policy.json`'un performans bölümünde `signal_thresholds` olarak
durur ve `18`'deki prosedürle değişir. Pencere uzunlukları da oradadır (`18b`). Başarı tek başına
organ doğurmaz: bir aracın zaten yaptığı düzeltme üç kez hayatta kaldı diye skill yazılmaz;
gerekçe her zaman ölçülmüş bir maliyet ya da başarısızlık boşluğudur. Yeni `miss_reason` ya da
`cause` kategorisi şema değişikliğidir; genesis değil şerit yazarı önerir (`26`).

## Boşluk formülü

```
gap = nokta_kaçırma_oranı × normalize_şiddet × görülmemiş_dosya_payı
```

`normalize_şiddet`, `severity_map`'in en büyük değere bölünmüşüdür ve [0, 1] aralığındadır.
Nokta kaçırma oranı kullanılır, alt sınır değil: alt sınır mükemmel recall'da bile boşluk
üretirdi. Genesis, bir sınıf ve property için gap iki pencere üst üste `rules.gap_rule`'un
üstündeyse ve vaka havuzu asgari örneklemi sağlıyorsa tetiklenir (`19`). Küçük havuzda gap
hesaplanmaz; önce vaka arzı sinyali gelir.

## Kurallar

- **Sinyal tek başına organ doğurmaz, taslak doğurur.** Taslak DRAFT olarak başlar ve `12`'nin
  yaşam döngüsünden geçer. Kabul, ayarda kullanılmamış vakalarda tam tek yönlü McNemar (en az 8
  uyuşmaz çift) ya da değer / USD için eşli bootstrap alt sınırı ≥ 1,2 ister (`19`).
- **Bir sinyal, bir taslak.** Aynı sinyal için açık bir taslak varken ikincisi açılmaz.
- **Kaçırma nedeni harness'te sınıflandırılır.** Held-out kaçırmaları ajanlara vaka bazında
  gösterilmez; `miss_reason` kategorileri yalnız toplam sayı olarak görünür.
- **Tablo da büyür.** Son satır, tablonun kendini genişletme yoludur. Yeni sinyal de bir
  organdır: çekişme protokolünden geçer, ablasyonda bir şey kazandırmıyorsa emekli olur.
- **Kuyruk sınırlıdır.** `genesis-queue.jsonl` ilk okuyucusuyla açılır (`12`); derinliği
  bütçeyle sınırlıdır; taşan sinyal Gözcü'nün işaretidir.

**Keşfin ölçüsü.** Sistemin gerçekten keşfettiğinin ölçüsü "tohum dışı organ"dır (`20`): tohumda
adı geçmeyen ve ablasyonda katkısı kanıtlanmış organ sayısı. Sıfırsa sistem kendini geliştirmiyor,
yalnız verileni koşuyordur. Sinyaller doğru yere bakmayı sağlar, keşfi garanti etmez; cevabı
Aşama 5'in genesis'i verir.
