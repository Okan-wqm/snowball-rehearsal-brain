# İş Akışı YAML Altkümesi

Tarih: 2026-11-01 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: `loop.yml` yazılırken
Çapa: `seed/bootstrap/snowball_bootstrap/wiring.py` (`parse`)

---

**Altküme** (`asama-0/10` #is-akisi'nin "tohumun sınırlı YAML altkümesi"). `wiring`
`referee/.github/workflows/loop.yml`'u yalnız bununla okur; GitHub'ın ve tohumun aynı baytı iki türlü okuyabileceği
biçimler dışındadır.

- Bayt: en çok 262144 bayt; BOM'suz UTF-8; satır sonu yalnız LF. Hiçbir yerde CR, sekme, LF dışında U+0000–U+001F,
  U+007F–U+009F, U+2028, U+2029, U+FEFF, U+FFFE, U+FFFF yoktur.
- Belge: ilk içerik satırı 0. sütundadır ve kök bir blok eşlemedir; 0. sütunda `---`, `...` ya da `%` ile başlayan
  içerik satırı yoktur; iç içelik en çok 32 düzeydir.
- Eşleme: satır `anahtar:` ve ardından bir ya da daha çok boşlukla değer ya da satır sonudur; anahtar
  `[A-Za-z_][A-Za-z0-9_-]*`'dir ve aynı eşlemede bir kez geçer. Satırı `:` ile biten anahtarın değeri altındaki daha
  içeride bloktur; blok yoksa `null`'dır.
- Dizi: öğe `- ` ya da yalnız `-` ile başlar; öğeler ait oldukları anahtardan daha içeride ve aynı sütundadır;
  `- anahtar: değer` öğesi o anahtarın sütununda bir eşleme açar.
- Skaler: her skaler dizgidir (`false`, `true`, `1` de) ve tek satırdadır. Düz skaler `&`, `*`, `!`, `|`, `>`, `%`,
  `@`, ters tırnak, `,`, `?`, `#`, `[`, `]`, `{`, `}` ile ya da `- `, `: ` ile başlamaz, yalnız `-` ya da `:` değildir,
  `: ` ya da ` #` içermez, `:` ile bitmez. Tek tırnaklıda `''` bir tırnaktır; çift tırnaklıda kaçış yalnız `\"` ve
  `\\`'dir; kapanan tırnaktan sonra satırda boşluktan başka bir şey yoktur. `{}` boş eşleme, `[]` boş dizidir.
- Sabit blok: yalnız eşleme değeri olarak, değer tam olarak `|`'dir (gösterge yok); satırları anahtarından daha
  içeridedir; ilk satırı boş değildir ve bloğun girintisini belirler; içindeki boş satır boşluk taşımaz; sondaki boş
  satırlar düşer, blok tek LF ile biter.
- Yorum: yalnız sabit blok dışında, ilk boşluk olmayan karakteri `#` olan tam satır.

Bu yüzden dışarıdadır: çapa, takma ad, etiket, birleştirme anahtarı, `>`, `|-`, `|+`, `|2` blokları, dizi öğesi olarak
`|`, boş olmayan akış koleksiyonu (ör. `[push]`), çok satırlı skaler, satır sonu yorumu, tırnaklı ya da karmaşık anahtar,
iç içe girmeyen girinti. Dışındaki dosya `workflow_unparseable:loop.yml:L<satır>:<neden>`'dir (satır 1'den, 0 dosyanın
bütünü; kök bir blok dizisiyse `L1:not_a_mapping`). Nedenler: `too_large`, `not_utf8`, `carriage_return`, `tab`,
`byte_order_mark`, `control_character`, `empty`, `document_marker`, `indentation`, `too_deep`, `not_a_key`,
`duplicate_key`, `not_an_entry`, `empty_literal`, `blank_line_with_spaces`, `unterminated_quote`, `text_after_quote`,
`escape`, `indicator`, `plain_scalar`. Bilinen cevaplı örnekler (vaka değil): `on: [push]` → `indicator`; `run: |-` →
`indicator`; `x: a # b` → `plain_scalar`; `x: "a\n"` → `escape`; CRLF satır sonu → `carriage_return`.
