# Şemalar, Devam: Kurucu'nun Dersi ve Ders Dizini

Tarih: 2026-11-17 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: defterine ders yazarken ve `/work/logs/lessons.json` okunurken
Çapa: `seed/bootstrap/snowball_bootstrap/ledgercheck.py` `FOUNDER_KINDS`; `seed/founder/launch.py` `lesson_index`

---

`26`'nın devamıdır; aynı kurallar geçerlidir. Sahibin kararı (2026-11-17): öğrenilen bir ders kararların arasında
kaybolmaz, her oturuma ulaşır ve hâlâ tutup tutmadığı yeniden sınanabilir. Amacı `01` "Sahibin hedefi"dir.

**`lesson` satırı.** `founder` bölümünün kapalı `kind` kümesindedir (`26`). Yükü `{summary, refs[], recheck}`'tir;
`snapshot_id`, `derivation`, `trust`, `evidence_refs` ve zincir her `founder` satırınınki gibidir.

- `summary` dersin iddiasıdır, tek cümle. Kendi başına anlaşılır ve uygulanır: onu yazan oturum olmadan okunur;
  "yukarıdaki gibi", açıklanmamış satır kimliği ya da özel kısaltma taşımaz.
- `refs[]` iddianın dayandığı kanıttır (yol, `path:line`, satır kimliği, rapor); anlam için değil kanıt içindir.
- `recheck` dersin bugün hâlâ tutup tutmadığını gösteren denetimdir: beyin klonunun kökünden yazıldığı gibi koşan bir
  komut (bir testin koşusu da bir komuttur) ya da `none: <neden>`.

**Yürürlükten çıkma.** Yeni bir mekanizma yoktur. Bir ders, sonraki bir `founder` satırı `refs[]`'inde
`closes:<row_id>` taşıyınca yürürlükten çıkar: defterin bugünkü kapatma biçimidir, kapsüldeki dizinin
`unclosed --tag closes` katlaması onu okur; dersi daha önce adlandıran satır onu kapatmaz, kapatanın geçerliliği
yargılanmaz. `supersedes` yalnız `26`'nın anlam kurallarından birini bozan satırı kapatır (`13` "Kurucu defterinde
kapatma"); geçerli bir dersi adlandıran `supersedes` geçersizdir. Bir dersi değiştirmek, eskisini `closes:` ile kapatan
yeni bir `lesson` satırı yazmaktır.

**Hakem.** Hakem `lesson` satırının yalnız her `founder` satırına uyguladığı yapıyı denetler (zincir, `part`, `kind`,
`supersedes`; `asama-0/10` #kurucu-defteri). Yükü, iddiayı ve `recheck`'i yargılamaz ve koşturmaz; derslere özgü bir
hakem denetimi yoktur.

**Ad.** Tür `lesson`'dır, `learning` değil. Defterde `kind: learning` taşıyan ve `13`'e göre `supersedes` ile kapatılmış
kabul edilmiş satırlar vardır; `learning` kümeye girseydi o kapatan satırlar geçerli satırları adlandırmış olur ve
çıkışı kapalı tutardı. Hakemin sonucundaki `learning` alanı (`29b` "Ret hafızası") da başka şeydir. `26b`'nin
**lesson** şeması (Aşama 2'nin ders dosyası) bu satır türünden ayrıdır.

**Ders dizini.** Başlatıcı her oturumdan önce, oturumun açıldığı beyin başındaki defterden oturumun klasörüne
`/work/logs/lessons.json`'u yazar:

```
{ledger: {commit, bytes, sha256, rows, unreadable}, lessons, live, shown, left_out,
 rows: [{row_id, line, claim, claim_cut}]}
```

- `ledger`: okunan defterin `commit`'i, bayt sayısı (`bytes`), `sha256`'sı, okunabilen (`rows`) ve okunamayan
  (`unreadable`) satır sayısı. Zincir burada yargılanmaz.
- `lessons` defterdeki `lesson` satırlarının, `live` yürürlükte olanların sayısıdır.
- `rows` yürürlükteki derslerin en yeni 100'ü, defter sırasıyla; `shown` onların sayısı, `left_out` dışarıda kalan
  eskilerin sayısıdır (`live` − `shown`). `line` satırın defterdeki numarasıdır; `row_id`'si dizgi olmayan satır
  dizine girmez.
- `claim` satırın `summary`'sidir, 500 karakterde kesilir; kesildiyse `claim_cut` `true`'dur, `summary` yoksa `null`.

Başlatıcı yalnız okur ve listeler: `recheck`'i koşturmaz, defteri değiştirmez, dersleri sıralamaz ya da puanlamaz.
Defter okunamazsa (henüz yoksa da) dosya yoktur ve operatör uyarılır; oturum yine başlar. Dersin tamamı
(`refs[]`, `recheck`) defterdedir: `python3 -I /opt/founder/ledger_index.py show <row_id>`.
