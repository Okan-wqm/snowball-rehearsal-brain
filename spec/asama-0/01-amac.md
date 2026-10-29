# Aşama 0 §0.1 — Amaç

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken
Çapa: beklemede: aşama 0 çıkış raporu

---

Asgari bir ölçüm zemini ve onu yöneten hakemin tamamını kurmak; fazlasını değil. Harness, herhangi
bir avcının çıktısını cevabı bilinen gerçek hatalara karşı **LLM'siz ve deterministik** biçimde
puanlar; isabetle birlikte maliyeti de ölçer. Verdict üç değerlidir: `PASS`, `FAIL`,
`UNMEASURABLE` (`tohum/19`). İlk sınıf K0'dır: profildeki lint aracının kural ihlalleri.

Hakemin tamamı bu aşamada yazılır: kapı, nöbetçi, geri alma, Gözcü, kayma denetimi, çağrı ve
dispatch, defter ve Rekor. Gerekçe: Aşama 1'in ilk merge'ü onları ister ve hakem yalnız bir
operatör aktarımıyla değişir (`tohum/01a`). Aşama 1 yalnız oyuncu organlarını kurar.

Hakemi yazan Kurucu'dur, ama onu Kurucu puanlamaz: her push'u tohumla gelen önyükleme hakemi
(`tohum/29b`), tohum vektörleri (`tohum/29a`) ve farklı modelden tohum rakibi denetler (Y6).

Bu aşamada sistemin içinde LLM avcı yoktur. İnşa zamanında Kurucu (Opus) ve tohum rakibi (Sonnet)
vardır; bu inşa-zamanı bütçesidir. Sistemin çalışma-zamanı LLM maliyeti sıfırdır: `llm.call` ve
`agent.dispatch` yazılır ve yalnız oyuncak repoda kendi testleriyle sınanır.
