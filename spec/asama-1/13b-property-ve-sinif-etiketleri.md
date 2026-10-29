# Aşama 1 §1.13b — P1: Property ve sınıf etiketleri

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: P1 partisi yazılırken ve Aşama 1 çalışırken
Çapa: beklemede: aşama 1 çıkış raporu

---

Bu sayfa Aşama 0 2.2'nin §0.5'idir; P1 partisiyle gelir (§1.13).

Her vaka tam olarak bir property ve bir sınıf taşır. Etiket hata kalıbı değil, ihlal edilen
doğruluk özelliğidir. Başlangıç kümesi alan bağımsızdır:

| Property | Sınıf | Doğruluk özelliği |
|---|---|---|
| `lint` | K0 | Aracın kural kataloğu ihlal edilmez |
| `type` | K1 | Program derlenir ve tip denetiminden geçer |
| `dead-code` | K2 | Üretim yolunda çağıranı olmayan kod yoktur |
| `contract-parity` | K3 | Bir sözleşmenin iki ucu aynı şeyi kabul eder |
| `schema-placement` | K4 | Kalıcı veri, reponun şema kurallarına göre doğru yerde durur |
| `missing-await` | K5 | Asenkron sonuç beklenmeden kullanılmaz |
| `wrong-condition` | K5 | Dallanma koşulu belgelenmiş davranışla uyuşur |
| `idempotency` | K5 | Yeniden denenen yazma iki kez etki etmez |
| `ordering` | K5 | Bağımlı işlemler doğru sırada yürür |
| `tenant-isolation` | K6 | Bir kiracının verisi başka bir kiracı bağlamından erişilemez |
| `auth-gate` | K6 | Her mutasyon ucu yetki kapısının arkasındadır |
| `input-boundary` | K6 | Sınırda doğrulanmamış girdi iş mantığına ulaşmaz |
| `stale-doc` | K8 | Doküman iddiası koda çapalıdır ve kodla uyuşur; davranışı değişen kodun dokümanı da değişir |
| `other` | — | Hiçbir aşamada kullanılmaz; `cases.build` bunları raporlar |

Etiketi `cases.build` sürümlü ve deterministik bir kuralla verir: araç ve kural kimliği, commit
scope'u, dokunulan yollar, repodaki bulgu kaydı alanları. Kural LLM içermez; karar veremediği
vaka `other` olur. Property'ler büyür (`tohum/14`); yeni property harness'te yeterli vaka
bulunca aktif olur.

`stale-doc` için kod referanstır: repodaki doküman kod hakkında bir iddiadır ve kodla çelişirse kod
kazanır (Y1). Vakası, kodu değişip dokümanı değişmeyen geçmiş commit'lerden ve çapası kırılan
doküman satırlarından gelir.

Aşama 0'ın ve Aşama 1'in sınıfı K0, property'si `lint`'tir. Aşama 4'ün property'si K5 vakaları
arasından en çok vakası olandır; K6 property'leri Aşama 5'e kadar `blocked`'dır (`tohum/05`). K6
property'lerinin açık sınıfları ve kapanış testleri güvenlik kataloğundadır (`tohum/30`–`30c`); P2 ile
Aşama 1'den test edilir ve bildirilir, düzeltilmez (`tohum/30f`).
