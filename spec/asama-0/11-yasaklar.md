# Aşama 0 §0.11 — Yasaklar

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken
Çapa: beklemede: aşama 0 çıkış raporu

---

- Çalışma zamanında hiçbir LLM çağrısı: harness'te, vaka üretiminde, snapshot üretiminde, taban
  avcıda. `llm.call` ve `agent.dispatch` yalnız oyuncak repoda, kendi testleriyle koşar.
- LLM avcı, yargıç, dedektör, düzeltici; defter, zincir ve vaka seti dışında hafıza.
- Hedefe yazmak. Aşama 0'da hedefe hiçbir şey girmez; ilk yazım etkinleştirme koşusudur ve yalnız
  `brain/state` ile `brain/integration`'a. Hedefe iş akışı ya da kimlik eklenmez.
- Hakem kodunun yeri: Aşama 0 boyunca beyin reposunun `referee/` dizini, aktarımdan sonra yalnız
  hakem reposu. Oyuncu kodu `referee/`'yi, `referee/` oyuncu kodunu import etmez.
- Hakem reposuna yazmak; önyükleme hakemini, tohum vektörlerini, tohum koltuklarını, `control.json`'u
  ya da anayasal politikayı değiştirmek. Kurucu hakem reposunu okur, yazamaz.
- Vektöre ya da önyükleme hakemine özgü dal yazmak; testin koştuğunu algılayıp başka davranmak.
- Çıkış örneklemini çıkış isteğinden ve adapter SHA'sının pinlenmesinden önce çekmek; gizli tohumu
  sırlı hakem işi dışında kullanmak.
- Sırlı bir işte oyuncu ya da hedef kodu koşturmak; Actions önbelleği kullanmak.
- Aşama 0 kapandıktan sonra hakemi değiştirmek; tek yol aşama çıkışındaki operatör aktarımıdır.
