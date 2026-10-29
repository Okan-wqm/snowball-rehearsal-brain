# Aşama 1 §1.6 — Sıralı mikro özellikler

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 1 çalışırken
Çapa: beklemede: aşama 1 çıkış raporu

---

Her satır tek mekanizmadır, tek oturumda biter, kendi gerçek testiyle gelir, `brain.accept`'ten
geçer ve donuk hakem üzerinden `brain/integration`'da bir canlı koşuyla kapanır.

1. `lint.discover`: profildeki lint aracını saran adapter; dev vakalarında recall taban avcıyı
   geçer, clean'de yalnız gerçek ihlaller.
2. Taban satırı ve borç listesi; güvenlik yollarındaki borç `blocked`.
3. `fixer.range`: aracın `fix` aralığını uygulayan deterministik düzeltici.
4. `fixer.llm`: prompt şablonu, yapılandırılmış düzenleme şeması ve yalnız o aralığa yazabilen
   deterministik uygulayıcı; çağrıyı hakemin `llm.call`'ı yapar.
5. `candidate.publish`: aday paketi biçimi. Canlı koşuda kapı adayı reddeder, çünkü organların
   tanım hash'leri henüz izin listesinde değildir; bu ret bu satırın kırmızı testidir.
6. Organ izin listesi girişi: adapter ve düzeltici tanım hash'leri `brain.accept` ile `accept`
   satırına girer; 5'teki aday aynı koşulda merge olur. **İlk canlı merge budur.**
7. `docs.render`: bulgu ve organ sayfaları iki formatta, sabit şablondan; hakem yazar.
8. Çıkış koşusu (§1.8).
