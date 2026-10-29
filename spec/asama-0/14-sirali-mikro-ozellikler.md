# Aşama 0 §0.14 — Sıralı mikro özellikler

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken
Çapa: beklemede: aşama 0 çıkış raporu

---

Her satır tek mekanizmadır, tek oturumda biter, kendi gerçek testiyle gelir ve önyükleme hakeminin
koşusu yeşilken kapanır; sonraki satır öncekinin koşusu yeşilken başlar. Canlı koşular oyuncak
repodadır; hedefe bu aşamada yazılmaz. Test numaraları §0.9'dandır.

1. Zincirli defter yazıcı ve `chain.verify` (`--previous` ile yalnız-ekleme); test 13.
2. `founder-ledger.jsonl`: Kurucu kendi defterini 1'in komut satırıyla yazar, zincirsiz satırları
   bağlar; test 30.
3. `control.json` okuyucu: kill switch ve bütçe tavanı, kapalıya düşer; test 26.
4. `profile.propose` (oyuncu); test 31.
5. `profile.derive` (hakem) ve fark; test 19.
6. `snapshot.make`; test 8.
7. K0 mutasyon kataloğu, `cases.build` (dev), hunk üzerinden satır eşleme; testler 2, 4.
8. `exit.sample`: gizli tohum, kural sayımı; test 27.
9. `harness.score` ve match-rule v2; testler 1, 6, 7, 12, 14, 28.
10. `harness.baseline` ve taban satırı; test 32.
11. LLM yokluğu ve genellik; testler 9, 11.
12. `spec.lint`, `required_exit_rows` denetimi dahil; test 33.
13. `run.contained`: iç içe ağsız konteyner, dışarıda hash, kırmızı kontrol; testler 20, 21.
14. `deps.fetch`: sırsız, kurulum betikleri kapalı, içerik adresli; test 34.
15. `gate.diffguard`; test 23.
16. `gate.check`; test 35.
17. `sentinel.run`; test 36.
18. `gate.revert`, geri alma provası ve prova yargıcı (`exit.drill`, `harness.drill`; `tohum/22a`, `tohum/29c`); test 25.
19. `drift.check`; test 24.
20. `llm.call`; test 37.
21. `secrets.scan`; test 38.
22. `agent.dispatch`: `tohum/24` sözleşmesi; test 22.
23. `ledger.append` (döngü başına tek commit); test 39.
24. `rekor.anchor`; test 40.
25. `gozcu.evaluate`; test 41.
26. `status.block`; test 42.
27. `brain.accept`; test 43.
28. `lock.check`; test 29.
29. `docs.index`; test 44.
30. Etkinleştirme provası: aktarım ve etkinleştirme betikleri yerel bir git uzağına ve taklit
    GitHub API'sine karşı uçtan uca; test 45.

Sonra çıkış isteği (§0.10).
