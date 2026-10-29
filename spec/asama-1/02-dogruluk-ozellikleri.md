# Aşama 1 §1.2 — Doğruluk özellikleri

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 1 çalışırken
Çapa: beklemede: aşama 1 çıkış raporu

---

1. **Mandal:** hiçbir merge bir aracın toplam ihlal sayısını artırmaz; hedef ihlal kaybolur.
2. **Davranış korunur:** düzeltme yalnız hedef mesajın `fix` aralığına dokunur; kapı etkilenen
   testleri `koş`ta yeniden koşturur; sıfır test kırmızıdır.
3. **Güvenlik yollarına dokunulmaz:** K6 canlı olana kadar, biçimleyici ve `--fix` dahil.
4. **Her dosyanın okuyucusu bir kararı değiştirir:** `tohum/27` tablosu (Y4).
5. **Kapı yeniden koşturur:** sonuçları artefakt kimliğiyle okur, hash'leri doğrular; ajanın
   "düzelttim" demesi kanıt değildir (`tohum/01b`).
6. **Yürütme ayrımı:** oyuncu ve hedef kodu yalnız `koş`ta, sırsız ve ağsız koşar; kırmızı kontrol
   her koşuda kırmızı çıkar.
7. **İzin listesi:** merge kapısına yalnız tanım hash'i `accept` satırında olan organın çıktısı gider.
8. **Satırı hakem yazar:** oyuncunun önerdiği her içerik `trust: inferred` ve `proposed_by` ile
   saklanır.
9. **Zincir ve Rekor:** her döngü kök hash yazar ve Rekor'a bağlar; `status.md` ve üretilmiş
   sayfalar defterden yeniden kurulabilir.
10. **Hakem yalnız aktarımla değişir:** canlı hakem ağacının hash'i son `imports.jsonl` satırınınkiyle
    aynıdır; aktarımlar yalnız §1.13'ün partileri ve aşama çıkışıdır.
