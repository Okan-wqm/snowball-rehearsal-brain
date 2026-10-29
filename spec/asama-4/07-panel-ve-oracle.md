# Aşama 4 §4.7 — Panel, oracle ve kalıcı düzeltme

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: hedef taslak · Sahibi: operatör
Okunma: Aşama 4 çalışırken
Çapa: beklemede: aşama 4 çıkış raporu

---

Clean snapshot'taki her bulgu önce panelin 1–4. fazlarından geçer (`tohum/10a`). Faz 1 mekanik ve
bedava; çoğu yanlış bulgu burada ya da faz 2'de ölür. **Oturum:** her koltuk bir bulgu için tek bir
devam eden oturum açar; her kararı yapılandırılmış çıktıdır `{decision, refs[], sentence}`;
effort `low`. **Test talebi** mühürlü bir "belirsiz" karardır; test-yazıcı testi yazar, bulgu faz
5'e atlar ve oracle maliyeti talep edenin hesabına yazılır.

**Faz 5, kanıt için.** `tohum/04a` şartlarıyla: test property ve konumdan yazılır ve önce
mühürlenir; test-yazıcı `not_derivable` derse bulgu `unresolved` olur; kırmızı, beklenen assertion
mesajıyla eşleşen başarısız assertion'dır; 3/3 kırmızı, 3/3 yeşil; hunk kapsaması; mutant öldürme.
Oracle düzelticisinin asgari düzeltmesi yalnız kanıttır ve merge edilmez.

**Güncel kod.** Clean snapshot'lar geçmiş entegrasyon başlarıdır; test önce güncel
`brain/integration` başında kırmızı olmalıdır, değilse bulgu `withdrawn`.

**Kalıcı düzeltme.** TP için implementer kök neden kuralıyla kalıcı düzeltmeyi yazar
(`required_change` dizisi, tüm çağrı yerleri). Uygulayıcı temsilcisi kendi bilgisinden en az bir
referanslı alternatif önerir; ikisi de aynı mühürlü testten geçebiliyorsa ölçüm seçer
(`tohum/10`). Aynı mühürlü test, ikinci panel (faz 2–4, diff üzerinde) ve hakem kapısı ondan
geçer; kapı etkilenen testleri `koş` işinde yeniden koşturur ve merge eder.

**Sonuçlar.** TP → vaka adayı (`provenance: system_tp`; aynı soyun held-out'una ve exit'e girmez).
FP → `fp-corpus.jsonl`; okuyucusu rakip kanaryası ve yargıç kalibrasyonu. Unresolved →
`unresolved.jsonl`. Panelin öldürdüğü bulgulardan gizli tohumla seçilen rastgele bir örnek oracle'a
gider; öldürülen gerçek bulgu oranı raporda yazar. Panel ve oracle maliyeti deftere yazılır.
