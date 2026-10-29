# Hedef Sistem

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: ilk oturumda
Çapa: profile.json; status.md amaç tablosu

---

Son durumda sistem şu döngüyü kendi başına döndürür:

```
Discover → Plan → Execute → Approve → Learn → Cheapen → Discover again
```

- Birden fazla memory'si vardır; her memory'nin yazarı, okuyucusu ve okuyucunun değiştirdiği
  kararı vardır (`16-hafiza-modeli.md`).
- Yeni adapter, skill, ajan, memory ve property'yi ihtiyaç ölçüldüğünde kendisi ekler
  (`17-kas-buyutme-sinyalleri.md`, `12-genesis.md`).
- Her parçası canlı yolda ölçülmüştür. Hiçbir adımda insan onayı beklemez (Y8).
- Bulduğu her hata sınıfını bir sonraki sefer daha ucuza bulmanın yolunu dener (Y9).
- Öğrendiğini planlayıcıya ve implementer'a verir (`22-dersler.md`).
- Hedef reponun yalnız kodunu değil dokümanını da yazar ve düzeltir (K8, `03`).

Bu son durumdur, başlangıç değil.

**Öğrenmenin amacı.** Sistem hata yapmamak için öğrenir: doğruyu yanlıştan ayırmak, daha iyi ve
daha profesyonel olanı seçmek için. Repoyu haritalamak, neyin neye bağlı olduğunu çıkarmak, ders
tutmak, başka repolardan ve modelin kendi bilgisinden yararlanmak bunun araçlarıdır; ölçüsü düşen
hata oranıdır (Y5). Bir repodan öğrenilen kalıp kopyalanmaz: modelin kendi bilgisinden gelen bir
alternatifle çekiştirilir ve kazananı yürütme seçer (`10`, `21`).

**En basit döngü.** Döngü en basit hâliyle başlar. Aşama 0'da Kurucu hakemi kurar; Aşama 1'de
canlı olan yalnız şudur: profildeki lint aracını saran tek adapter, aracın `fix` aralığını
uygulayan düzeltici, aracın kendisi olan oracle, adayı çekip yeniden koşturan ve merge eden hakem
kapısı, her merge'den sonra nöbetçi, zincirli tek defter. Keşifte LLM yoktur; LLM yalnız aracın
düzeltemediği bulguyu düzeltmek için, araçsız tek bir çağrı olarak girer. Harita, itibar, dersler
ve genesis kuyruğu, okuyucularının bir kararı değiştirebildiği aşamada açılır (Y4). Sonraki her
özellik bir mikro görevdir: tek canlı koşuda test edilebilecek kadar küçük, hemen ölçülür, sonra
bir sonraki. Binlerce satırlık bir parça tek seferde gelmez.

**Amaç.** Bağlandığı repodaki her modülü altı boyutta profesyonel hâle getirmek ve orada tutmak.
Modülün notu en zayıf boyutudur, ortalaması değil. Boyutlar alan bağımsızdır; ölçüleri profilden
gelir.

| Boyut | Ölçüsü |
|---|---|
| Güvenli | Yetki sınırları kanıtlı, girdi sınırda doğrulanmış, sır sızıntısı sıfır, denetim izi tam |
| Performanslı | Ölçülmüş darboğazlar, tanımlı hedefler, kaynak sızıntısı yok |
| Sürdürülebilir | Katman kuralları ihlalsiz, her gerçeğin tek sahibi var, ölü kod sıfır |
| Test edilebilir | Her davranışın CI'da koşan gerçek bir testi var |
| Dokümante | Doküman var olanı anlatır, her iddiası koda çapalıdır, bayatlaması bir kapıyı kırmızıya boyar; sistem onu kodla birlikte yazar |
| Doğru | Sözleşmelerin iki ucu tutarlı, uçtan uca zincir kanıtlı |

**Alan doğruluğu hedef değildir.** Sistem bir iş kuralının ya da formülün "doğrusunu" yargılamaz;
yalnız reponun kendi kendisiyle tutarlı olup olmadığını sorar: aynı kavram bir yerde tanımlı öbür
yerde tanımsız mı, iki tanım birbirini tutuyor mu, test ve doküman kodla uyuşuyor mu. Öğrendiği
ve repolar arasında taşıdığı şey alan bilgisi değil mühendisliktir: güvenlik, kimlik doğrulama,
kiracı izolasyonu, altyapı, test düzeni, mimari kalıplar (`21`).

Beyin bu repoyu değil, herhangi bir repoyu hedefler; repoya özgü her şey `21-cok-repo.md`'deki
kurala tabidir.
