# Şemalar, Devam: Bulgu Durumlarının Yazıcıları

Tarih: 2026-11-21 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: P1 MF8'in durum geçişleri ve P1 MF12'nin karar okuması yazılırken, bir bulgu satırı okunurken
Çapa: beklemede: P1 aktarımı — `findings.jsonl`'un durum satırları

---

`26j` "Bulgu yazıcısı, MF8"in devamı (bağımsız inceleme ekibi kararı (2026-11-21), seed-088). Arayüz olgularıdır;
kodun nasıl yazılacağı Kurucu'nundur. Her bulgu satırını hakem yazar (`findings.write`); bir öneri durum taşımaz.

**`fixed`.** Kapının bulgu için verdiği merge kararı yazar: merge satırıyla aynı devirde ve aynı `brain/state`
commit'inde. Anlamı "kapı bir düzeltmeyi merge etti"dir, "düzeltme hayatta kaldı" değildir; hayatta kalma defterin
satırlarından okunur.

**Yeniden gözlem.** Son satırı `open`, `reopened` ya da `blocked` olan bulgunun yeniden gözlemi satır yazmaz. `fixed`
(ya da `verified`) bulgunun yeniden gözlemi `reopened` yazar; bulgunun üçüncü yeniden açılışını bir `blocked` satırı
izler.

**Geri alma** (operatörün seçimi, iki uzmanın ayrıldığı yerde daha sıkı olan). Bir merge geri alınınca aynı devir o
merge'ün bulgusu için `reopened` yazar; üçe sayılır, bir başarısız merge en çok bir yeniden açılıştır. Geri alma
`unresolved.jsonl` satırı yazmaz (nedeni defterin `revert` satırıdır). Bir prova ekmesinin geri alınması bulgu satırı
yazmaz.

**Açık olmayan bulguya karar.** Bilinmeyen ya da açık olmayan bir bulguyu adlandıran karar o adayın reddidir
(`finding_unknown`, `finding_not_open`); bulgu için hiçbir şey yazılmaz.

**`verified` ve `withdrawn`** Aşama 1'de yazılmaz (operatör kararı, sahibin yetkisiyle (2026-11-21)). `verified`'ın
yazıcısı hayatta kalma ve salınım ölçüsüyle sonra gelir; `withdrawn`'ın tetiği Aşama 4'ün oracle'ıdır (`asama-4/07`).
İkisi de `26`'nın kapalı kümesinde geçerli değerler olarak kalır ve okunur. `asama-1/13d:19` bunları Aşama 1 durumu
sayar; bu sayfa onu gevşetir (L-088).

**P1 MF12'nin sözleşmeleri.** MF12 (`26j`) bunları karşılar:
- T1: `finding_unknown` ve `finding_not_open` D5 nedenleridir ve merge seçilmeden önce verilir. Bir merge, kaydın
  reddettiği bir bulgunun üstüne asla düşmez.
- T2: hiçbir adayın içeriği devri kullanılamaz kılmaz. Bir bulgu için iki karar sonraki adayı reddeder, devri asla
  geçersiz kılmaz.
