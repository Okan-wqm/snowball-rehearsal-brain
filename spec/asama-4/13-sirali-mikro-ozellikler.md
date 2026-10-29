# Aşama 4 §4.13 — Sıralı mikro özellikler

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: hedef taslak · Sahibi: operatör
Okunma: Aşama 4 çalışırken
Çapa: beklemede: aşama 4 çıkış raporu

---

Hedef taslaktır; Aşama 3 PASS alınca yeniden yazılır. Her satır tek mekanizmadır.

1. Mühürlü depo, mühür ve `seal.rotate`.
2. İleriye dönük held-out: prompt hash mührü ve mühür sonrası `human_fix` toplama.
3. `looks` satırları: havuz bütçesi, α/k, yalnız verdict.
4. Property spec'i ve kalıp sızıntısı denetimi.
5. Sağlayıcı geçidi ve koşuya bağlı belirteç.
6. Kapsayıcılık özetleri (koşu öncesi ve sonrası).
7. Sandbox kanaryası.
8. Snapshot kanaryası, clean ve planted.
9. Avcı promptu ve dev döngüsü; `prompt-ledger.jsonl`.
10. Panel faz 1–2 (mekanik ve en ucuz model) ve faz kayıtları.
11. Panel faz 3–4: tek oturum, yapılandırılmış karar, mühür, tur kuralı, test talebi kararı.
12. Test-yazıcı koltuğunun kurulumu ve donması; `not_derivable`.
13. Oracle: `tohum/04a` şartlarının hepsi.
14. Implementer ve ikinci panel; kapı yeniden koşusu; merge.
15. Panel öldürmelerinin rastgele oracle denetimi.
16. Üyelik testi (kendi-test 18).
17. Exit koşusu (birinci kapı).
18. Maliyet merdiveni dev'de; kazanan basamağın tek held-out bakışı (ikinci kapı).
