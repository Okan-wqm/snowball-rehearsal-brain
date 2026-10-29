# Aşama 0 §0.2 — Doğruluk özellikleri

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken
Çapa: beklemede: aşama 0 çıkış raporu

---

Harness ve hakem için korunan özellikler; her biri bir kendi-testiyle (§0.9) kanıtlanır:

1. **Determinizm:** aynı girdi, bit düzeyinde aynı rapor.
2. **Sızıntısızlık:** hiçbir snapshot cevap anahtarını, çıkış örneklemi üyeliğini ya da fix commit
   kimliğini taşımaz; bulgu-ID kalıpları her snapshot'ta temizlenir.
3. **Kendi çıktısı kanıt değil:** harness'in, bir ajanın ya da önceki koşunun çıktısına atıf
   yapan kanıt reddedilir.
4. **Çalışma zamanında LLM yok:** harness modülleri hiçbir LLM istemcisi import etmez; ağ
   kapalıyken geçer.
5. **Genellik:** beyin boş bir oyuncak repoya bağlanır ve `<state_root>` sıfırdan büyür; beyin
   koduna, `referee/`'ye ya da tohuma hedef repoya özgü ad sızmışsa kırmızı.
6. **Zincir:** her defter satırı `prev_hash`/`row_hash` taşır; tohum vektörleri V1–V3 tutar;
   bozulmuş satır yakalanır.
7. **Şema:** her artefakt `tohum/26`'daki şemaya karşı doğrulanır.
8. **Çıkış örneklemi gizliliği:** K0 çıkış örneklemini `exit.sample` gizli tohumla, yalnız sırlı
   hakem işinde ve adapter SHA'sı pinlendikten sonra çeker; aynı tohum aynı örneklemi verir.
9. **Yürütme ayrımı:** oyuncu ya da hedef kodu yalnız `koş` işinde, sırsız ve ağsız koşar; sırlı
   işler kod koşturmaz; kırmızı kontrol her koşuda kırmızı çıkar (`tohum/08`).
10. **Kapalıya düşme:** kill switch, bütçe tavanı, Rekor hatası, kayma ve rakip zaman aşımı işi
    durdurur ya da reddeder; hiçbiri sessizce geçer sayılmaz.
11. **Yalnız düz dosya:** adaylarda sembolik bağ, alt modül, `../` yolu ve ret listesindeki yollar
    reddedilir.
12. **İzolasyon:** araç kullanan ajan hedef reponun yönerge, hook ve MCP dosyalarını yüklemez;
    onları yalnız dosya olarak okuyabilir (`tohum/24`).
