# Aşama 0 §0.3 — Roller

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken
Çapa: beklemede: aşama 0 çıkış raporu

---

| Rol | Var mı | Ne yapar |
|---|---|---|
| Operatör | Döngü dışı | Kurulumun birinci bölümü (`tohum/25`): beyin, hakem, oyuncak ve kopya repoları, tohum dönemleri, `targets[]`; çıkışta aktarım ve ikinci bölüm (`tohum/25a`), (B)'nin devirlerini elle tetikleme, `stage-open`; kill switch. Onay vermez; her dokunuşu sayılır |
| Kurucu, Opus | Evet, inşa zamanı | Beyin reposunda `referee/` altında 18 mikro özelliği ve testlerini, `targets/<hedef>/units.json` tarif önerisini, `candidates/<hedef>/` hazır adaylarını ve oyuncak fikstürünü yazar; defterini tohumun aracıyla zincirli tutar, bildirimlerini `reports/`'a yazar. Puanlayamaz, aktaramaz, hakem reposuna yazamaz, hedef kodunu kendi makinesinde koşturmaz |
| Önyükleme hakemi | Evet, tohumla; Aşama 0'dan sonra da | Hakem reposunda; her push'ta Kurucu'nun testlerini, tohum vektörlerini ve modülsüz kırmızıyı `koş`ta, tohum rakibini `çağır`da koşar; tohum denetimlerini (`wiring`, Kurucu defteri, genellik, spec) uygular; sonucu imzalayıp Rekor'a yazar (`tohum/29b`) |
| Tohum rakibi, Sonnet, ayrı bağlam | Evet, inşa zamanı | Promptu tohumla gelir (`tohum/29`); son kabul edilmiş SHA'dan bu yana tam diff'i ve commit ağacını görür (`founder-ledger.jsonl` ve `reports/` hariç), girdisini Kurucu seçmez; yalnız hakemin `read_file`, `grep`, `glob` ve `submit_verdict` araçları; çürütmesi ancak hakemin yeniden koşturduğu bir yeniden üreticiyle sayılır |
| Döngü hakemi, aktarılmış | (B)'de | Devirleri koşar, kapıyı uygular, merge eder, geri alır; PASS satırını yazar (§0.10a) |
| Ekici ajan, Kurucu değil | Kurulumda, bir kez | Operatörün yönettiği ayrı bir ajan; dürüstlük provasının imkânsız vektörünü ve bal küpünü eker; anahtar mühürlüdür (§0.10) |
| LLM avcı, yargıç, düzeltici; taban avcı | Yok | Çalışma zamanında tek LLM çağrısı (B)'deki kanaryadır; taban avcı Aşama 4 partisindedir (`asama-1/13`) |
