# Aşama 1 §1.6 — Sıralı mikro özellikler

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 1 çalışırken
Çapa: beklemede: aşama 1 çıkış raporu

---

Her satır tek mekanizmadır, tek oturumda biter, kendi gerçek testiyle gelir, önyükleme hakeminden
geçer ve aktarılmış hakem üzerinden `brain/integration`'da bir canlı koşuyla kapanır. Partiler (§1.13)
numarasızdır; kendi MF'leri, (A)'ları ve aktarımlarıyla araya girer.

- **Önce: P1 partisi** (organ ve ölçüm): (A), aktarım, (B). 1'in canlı koşusundan önce biter.

1. `lint.discover`: profildeki lint aracını saran adapter; dev vakalarında her kural isabet alır
   (`census`), clean'de yalnız gerçek ihlaller.
2. Taban satırı ve borç listesi; güvenlik yollarındaki borç `blocked`.
3. `fixer.range`: aracın `fix` aralığını uygulayan deterministik düzeltici.
4. `fixer.llm`: prompt şablonu, yapılandırılmış düzenleme şeması ve yalnız o aralığa yazabilen
   deterministik uygulayıcı; çağrıyı hakemin `llm.call`'ı yapar.
5. `candidate.publish`: aday paketi biçimi. Canlı koşuda kapı adayı reddeder, çünkü organların
   tanım hash'leri henüz izin listesinde değildir; bu ret bu satırın kırmızı testidir.
6. Organ izin listesi girişi: önyükleme hakeminin kabul ettiği SHA'daki adapter ve düzeltici tanım
   hash'lerini döngünün `yaz`'ı `accept` satırına yazar; 5'teki aday aynı koşulda merge olur. **Organ
   çıktısının ilk canlı merge'ü budur**; hazır adayların ilk merge'ü Aşama 0'dadır.

- **Sonra: P2 partisi** (güvenlik gözlemi): (A), aktarım, (B); güvenlik avcısının ilk koşusu.

7. `docs.render`: bulgu ve organ sayfaları iki formatta, sabit şablondan; hakem yazar. Sayfaların
   dizini (`docs.index`, test 44) aynı üreticinin çıktısıdır.
8. Çıkış: (A), **Aşama 1 çıkış partisinin** aktarımı, (B) (§1.8).
