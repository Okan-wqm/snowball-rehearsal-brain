# Aşama 0 §0.3 — Roller

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken
Çapa: beklemede: aşama 0 çıkış raporu

---

| Rol | Var mı | Ne yapar |
|---|---|---|
| Operatör | Döngü dışı | Kurulumun birinci bölümü (`tohum/25`); çıkışta aktarım ve ikinci bölüm (`tohum/25a`); bütçe, kill switch. Onay vermez |
| Kurucu, Opus | Evet, inşa zamanı | Beyin reposunda `referee/` altında hakemin tamamını, oyuncu iskeletini (`snowball init`, `profile.propose`, `docs.index`, oyuncak repo) ve kendi testlerini yazar. Puanlayamaz, aktaramaz, hakem reposuna yazamaz |
| Önyükleme hakemi | Evet, tohumla | Hakem reposunda; her push'ta Kurucu'nun testlerini ve tohum vektörlerini `koş`ta, tohum rakibini `çağır`da koşar; sonuçları koşu artefaktlarına ve Rekor'a yazar (`tohum/29b`) |
| Tohum rakibi, Sonnet, ayrı bağlam | Evet, inşa zamanı | Promptu tohumla gelir (`tohum/29`); son kabul edilmiş SHA'dan bu yana tam diff'i görür, girdisini Kurucu seçmez; yalnız hakemin `read_file`, `grep`, `glob` ve `submit_verdict` araçları (`tohum/29b`); çürütmesi ancak hakemin yeniden koşturduğu bir yeniden üreticiyle sayılır |
| Taban avcı | Evet, mekanik | `referee/` içinde, puanlama kodundan ayrı modül; maliyeti sıfır |
| Aktarılan hakem | Çıkışta | Etkinleştirme koşusunu yapar ve PASS satırını yazar (§0.10) |
| LLM avcı, yargıç, düzeltici | Yok | |
