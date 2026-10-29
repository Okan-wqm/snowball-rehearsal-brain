# Aşama 0 §0.2 — Doğruluk özellikleri

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken
Çapa: beklemede: aşama 0 çıkış raporu

---

Döngü hakemi için korunan özellikler; her biri bir kendi-testiyle (§0.9) kanıtlanır. Numaralar 2.2'deki
gibidir; Aşama 0'dan çıkanlar tablonun altındadır, 13 yenidir.

| # | Özellik | Test |
|---|---|---|
| 1 | **Determinizm:** aynı girdi, aynı karar; kapıda araç üç koşuda bayt bayt aynı çıktıyı verir (§0.8) | 35 |
| 6 | **Zincir:** her defter satırı `prev_hash`/`row_hash` taşır; tohum vektörleri V1–V3 tutar; bozulmuş satır yakalanır; yazımdan önce `verify --previous`; her devrin kökü imzalıdır | 13, 39, 40 |
| 7 | **Şema (daraltıldı):** döngünün yazdığı her artefakt `tohum/26`, `26b` ve `26c`'deki şemaya uyar | 14 |
| 9 | **Yürütme ayrımı:** hedef kodu yalnız `koş` işinde, sırsız ve ağsız koşar; sırlı işler kod koşturmaz; kırmızı kontrol her koşuda kırmızı çıkar (`tohum/08`) | 20, 21, 46 |
| 10 | **Kapalıya düşme (daraltıldı):** kill switch, `merge_paused`, fren tavanı ve Rekor hatası işi durdurur ya da reddeder; hiçbiri sessizce geçer sayılmaz. Abonelik penceresine takılmak kesintidir, ret değildir (§0.12) | 46, 37, 40 |
| 11 | **Yalnız düz dosya:** adaylarda sembolik bağ, alt modül, `../` yolu, güvenlik yolu, hariç yol ve ajan yapılandırması reddedilir; diff birimin `inputs`'u içinde kalır | 23 |
| 13 | **Yazım sınırı:** hedefe yalnız API ile ve yalnız `refs/heads/brain/**` altına yazılır; `main`'e yazım 0 | 49 |

**Aşama 0'dan çıkanlar** (yerleri `asama-1/13`):

- 2 sızıntısızlık, 3 kendi çıktısı kanıt değil, 4 harness'te LLM yokluğu, 5 genellik (`<state_root>`'un
  sıfırdan büyümesi) ve 8 çıkış örneklemi gizliliği P1 partisine gider; snapshot, vaka seti, harness ve
  çıkış örneklemi oradadır. 5'in ad denetimi Aşama 0'da tohumun denetimidir (§0.10 #genellik).
- 12 izolasyon (araç kullanan ajan hedefin yönerge, hook ve MCP dosyalarını yüklemez) P2 partisine gider.
  Aşama 0'da araç kullanan ajan yoktur; `llm.call` yalnız tipli girdi alır ve hedefin ajan yapılandırması
  hariç yoldur (`tohum/14`).
- 10'dan kayma (`drift.check`) P1'e, rakip zaman aşımı önyükleme hakemine gider (`tohum/29b`).
