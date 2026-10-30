# Vektör Arayüzleri, Devam: `status`

Tarih: 2026-10-30 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0'ın MF16'sını yazarken; bu grubun komutu, girdisi ya da çıktısı değişirken
Çapa: `seed/bootstrap/vectors/vectors.json` (`status`) ve `vectors/status/` fikstürleri

---

`29m`'nin devamıdır (`genesis`: `29o`), kuralları onunkidir; beklenen değerler burada yok (`29a`). MF17'nin (`loop.yml`)
grubu yoktur: tohumun `wiring` denetimidir (`29d`).

## `status` (MF16, `status/block.py`)

`python -m status.block render <defter.jsonl> <imports.jsonl> <status.md>`; stdin `{"canary_cap_usd_micros": tamsayı}`
(aşama tavanı, çağıran mikroya çevirir). Defter hedefinkidir (`26`), bu devrin `status` satırından önce; imports
`setup/imports.jsonl` (`26c:37-38`); `status.md` `brain/state`'teki dosya, boş olabilir. Alanlar (test 42,
`asama-0/09:66`), `events` satırı `part: events` olandır: `cycle_id` son `cycle_start` satırının `payload.cycle_id`'si
(`01b:54` her devir başlangıç satırı yazar; tür adı seçim); `last_decision` son `decision` satırının
`payload.decision`'ı; `base_age_s` = ts(son `cycle_start`) − ts(ilk `genesis` satırı), saniye, ts `YYYY-MM-DDTHH:MM:SSZ`
(UTC); `07:12-13`'ün commit sayısını Aşama 0'da üreten yok (D1 `main`'i okumaz, `asama-0/01:37`): vektörde yok. `brake`
`{spent_usd_micros: her `part: cost` satırının `payload.usd_micros` toplamı, cap_usd_micros, engaged: spent ≥ cap}`,
`prompt`'un freni. `human_touches` `imports.jsonl`'ın satır sayısı: o dosya insan dokunuşu sayacıdır (`26c:38`, `27:56`)
ve `27:19` ile `asama-0/12:38-39` aktarım dışı dokunuşları da (tohum dönemi `25:28`, `stage-open`, dürüstlük anahtarı,
sert duruş kalkışı `25:55`) sayaca koyar: aktarım olsun olmasın her satır bir dokunuştur. Aktarım dışı satırın biçimini
ve yazanını spec vermez (`26c:37` yalnız aktarım satırını, `27:56` yalnız `import`'u adlandırır): vektörde yalnız `ts`,
`stage` ve zincir alanları, seçim. **Blok**, tam olarak `<!-- status.block -->` olan satırın LF'sinden sonraki bayttan
tam olarak `<!-- /status.block -->` olan sonraki satırın ilk baytına kadardır: işaret baytı yok, son satırı LF'siyle;
geri kalanı `docs.render`'ın (`15:42-43`). Açılış satırı yoksa `found_sha256` `null`; iki açılış ya da kapanışsız açılış
kullanılamaz. **Düzenleme** (`asama-0/14:43` yeniden üret ve `events`'e yaz der, tespiti söylemez; seçim): her devir
yazdığı bloğun `events {kind: status, payload: {block_sha256}}` satırını ekler; `recorded_sha256` son `status`
satırınınki ya da `null`; `edited` ⇔ `found_sha256 ≠ recorded_sha256` (ikisi `null`, ilk devir, düzenleme değil; silinen
blok düzenleme). `render` yazmaz: yeniden üretilen bloğu çağıran yazar, `ledger.append`'le `status_edited` (varsa) ve
yeni `status` satırını ekler. Bu türler `26`'ya girmelidir (`26:9-10`). Sert duruş yok: `asama-0` yeniden üretir;
`15:16` ve `01b:37` düzenlemeyi zincir kırığı ve ret sayar, karar sahibin. Defter ve imports zincirini `render`
doğrulamaz (`ledger.append`, `29i`). Çıktı: `cycle_id`, `last_decision`, `base_age_s` (eksikse `null`), `brake`,
`human_touches`, `edited`, `event` (`{kind: "status_edited", payload: {found_sha256, recorded_sha256}}` ya da `null`);
`block` ve `block_sha256` karşılaştırılmaz (görünüm Kurucu'nun, test 42). Çıkış: 0 düzenlenmemiş; 1 düzenlenmiş; 2
okunamayan dosya, JSON nesnesi olmayan satır, kullanılan satırda biçimsiz `ts`, tamsayı `usd_micros`'u olmayan `cost`
satırı, tamsayı olmayan tavan, işaret hatası (satır `{"edited": null}`).
Vakalar: `fields_from_ledger` alanlar yalnız defterden ve imports'tan; sonraki başka türden `events` satırı son kararı
değiştirmez, her devrin `cost`'u sayılır; blok kayıttakine eşit; `hand_edit_regenerated` blok içinde elle düzenleme iki
hash'le `status_edited` yazar; `edit_outside_block` iki işaret satırı arası bloktur, dışındaki düzenleme değil;
`deleted_block_is_edit` defter blok kaydederken silinmiş blok düzenlemedir; `brake_engaged` harcama tavana ulaşınca;
`last_status_row` her devir bir `status` satırı ekler: kayıt son satırınkidir, önceki devrinki tarihtir. İmports'un
aktarım dışı satırı da dokunuştur (`fields_from_ledger`'ın değişmiş girdisi).
