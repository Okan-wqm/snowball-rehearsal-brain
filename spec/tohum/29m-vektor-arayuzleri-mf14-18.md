# Vektör Arayüzleri: `revert_drill`, `prompt`

Tarih: 2026-10-30 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0'ın MF14 ve MF15'ini yazarken; bu grupların komutu, girdisi ya da çıktısı değişirken
Çapa: `seed/bootstrap/vectors/vectors.json` (`revert_drill`, `prompt`) ve `vectors/<grup>/` fikstürleri

---

`29j`'nin devamıdır (`status`: `29n`, `genesis`: `29o`); kuralları `29f` ve `29g`'ninkidir, beklenen değerler burada yok
(`29a`). Üretimde dış dünyaya dokunan mekanizma vektörde fikstür bir taklit ya da yalnız bir plandır (`asama-0/14` Kum);
spec'in sessiz kaldığı kural "seçim" diye yazılıdır.

## `revert_drill` (MF14, `harness/revert_drill.py`)

`python -m harness.revert_drill commit <katalog.json> <tohum.json>` ve `python -m harness.revert_drill reveal` (aynı
argümanlar), stdin `{"cycle_id": "<ondalık rakamlar>"}`; `python -m harness.revert_drill judge <defter.jsonl>
<anahtar.json>`, stdin yok. Katalog tohumun ekilecek kötü merge'leri, `{instances: [{id, cause, …}]}` (kimlik boş
olmayan tekil dizgi, `cause` dizgi, başka alan okunmaz; `22a:51` biçim vermez, seçim); tohum dosyası `{seed: dizgi}`,
üretimde hakem sırrı (`25:23`), vektörde sahte. `cycle_id` taahhüdü yazan önceki devrin Actions koşu kimliğidir
(`asama-0/01:30,44`, `27:15`), ondalık rakamlardan JSON dizgisi. **Seçim** (spec yalnız "HMAC" der; SHA-256, yön ve
eşleme seçim): `selection` = HMAC-SHA256 (anahtar tohumun, ileti `cycle_id`'nin UTF-8 baytları), 64 küçük onaltılık;
örnek, kimliğe göre kod noktası sırasında dizilmiş kataloğun `int(selection, 16) mod N`'inci elemanı (seçim tek
büyük-sonlu sayı, N örnek sayısı; dosya sırası önemsiz). **Anahtar** `{cycle_id, selection, instance_id, cause}`;
taahhüt RFC 8785 baytlarının sha256'sı (`29c:25`); gizli seçim içinde olduğu için taahhüt denenerek bulunamaz.
`commit` anahtarı asla yazmaz: hakem reposunun koşu günlükleri açıktır (`25:15`, `01a`), anahtar ekilecek merge'ü
koşudan önce adlandırırdı (veri koşucusu bunu sabitleyemez). `reveal` geri almadan sonra anahtarı yeniden hesaplar.
`judge` tohumu almaz, seçimi yeniden türetmez; defter satırları (`26`): taahhüt `part: drill`, `kind: commit`,
`payload {drill: revert, family: revert, commitment_sha256}`; ekme `part: drill`, `kind: plant`, `payload {drill:
revert, family: revert, instance_id, merge_sha}`; geri alma `part: events`, `kind: revert`, üst düzey `cause`
(`26:41-44`), `payload {merge_sha}`. Sözcükler seçimdir: `26:74-75`'in drill yükü koşudan önce yazılamayacak
`instance_id`'yi ister ve alan adını yalnız `26`, `26b`, `30d`, `30e` tanımlar (`26:9-10`); `26`'ya girmelidirler.
Sıra: (1) dosya geçerli zincir değilse (`29a`; JSON nesnesi olmayan satır zinciri kırar, `29i`'nin seçimi) yalnız
`chain_broken`; (2) P = `drill`/`plant`, `payload.drill: revert` olan son satır; yoksa yalnız `not_planted`; (3) C =
dosya sırasında P'den önceki aynı biçimli son `commit`: yoksa `commitment_not_before_run`, anahtarın sha256'sı
`C.payload.commitment_sha256` değilse `commitment_mismatch`; (4) P'nin `instance_id`'si anahtarınki değilse
`instance_mismatch`; (5) R = P'den sonra `merge_sha`'sı P'ninki olan ilk `events`/`revert`: yoksa `not_reverted`,
`cause`'u anahtarınki değilse `cause_mismatch`. (3)–(5)'in her nedeni yazılır; adlar seçim, `FAIL` spec
(`asama-0/09:74`, `26:76`). "Önceki devir" yalnız zincir sırasıdır, satır devir kimliği taşımaz (`26:26-28`). Çıktı:
`commitment_sha256`; `key`, `revealed_sha256` (aynı girdide taahhüde eşit); `verdict` (`PASS` ⇔ `reasons` boş),
sıralı, tekil `reasons`. Çıkış: `commit`, `reveal` 0; 2 okunamayan ya da biçimsiz katalog ya da tohum, boş katalog,
tekrarlanan kimlik, rakam dizgisi olmayan `cycle_id` (satır `{"commitment_sha256": null}`, `{"key": null,
"revealed_sha256": null}`); `judge` 0 PASS, 1 FAIL, 2 okunamayan dosya ya da dört dizgi alanı olmayan anahtar
(satır `{"verdict": "FAIL"}`).
Vakalar: `commit_hmac_selection` taahhüdün seçimi; bu `cycle_id`'de dosya sırası, seçimin ilk ya da son baytı, ilk ya da
son 32 biti, ilk 64 biti ve yer değiştirmiş anahtar ile ileti başka örnek seçer; `reveal_selects_by_hmac` prova tohumu
HMAC anahtarı, `cycle_id` ileti, açılımın hash'i taahhüde eşit; `judge_pass` geçerli zincirde taahhüt ekmeden önce,
anahtarın örneği ondan sonra anahtarın nedeniyle geri alınmış; `tampered_key` neden yanlıştı, anahtar koşudan sonra ona
uydurulmuş: taahhütte düşer, neden artık tutar; `commitment_after_plant` (3)–(5)'ten birer neden: ekmeden sonra yazılmış
taahhüt (anahtarla karşılaştırılmaz), başka örnek ekilmiş, yanlış neden, üçü de yazılır; `other_merge_reverted`
anahtarın nedeniyle başka merge geri alınmış, ekilen değil; `rewritten_commitment` taahhüt satırı düzenlenmiş anahtara
göre yeniden yazılmış: zincir kırılır, başka hiçbir şey yargılanmaz; `last_of_several_drills` iki prova (#geri-alma üç
ister): P son ekme, C ondan önceki son taahhüt, ilk prova tarih. `not_planted` vakasızdır.

## `prompt` (MF15, `dispatcher/llm_call.py`)

`python -m dispatcher.llm_call plan <şablon.json>`; stdin `{model: dizgi, input: {…}, budget: {stage_cap_usd_micros,
spent_usd_micros, call_cap_usd_micros}}` (negatif olmayan tamsayılar; harcamayı ve `canary_usd`'yi çağıran mikroya
çevirir, seçim). Şablon `{fields: {ad: "string" | "integer"}, text: dizgi}` (`asama-0/14:42`, `26a:33` yalnız "tipli
girdi, şablon" der; seçim). Bildirilen her alan `input`'ta tipiyle bulunur (JSON dizgisi; JSON tamsayısı, boolean
değil); bildirilmeyen alan prompta girmez, `dropped`'da adlanır (`asama-0/09:61`; reddetmek yerine düşürmek seçim).
Prompt `text`'tir; her `{{ad}}` (`[A-Za-z_][A-Za-z0-9_]*`) soldan sağa tek geçişte `input[ad]`'ın RFC 8785 JSON'uyla
değişir (dizgi tırnaklı ve kaçışlı, tamsayı rakamla); yerine konan metin yeniden taranmaz; bildirilmemiş alanı
adlandıran yer tutucu isteği kullanılamaz yapar. `prompt_sha256` yalnız kurulan metnin UTF-8 baytlarınındır (`26:63`
sistem metnini söylemez; seçim). Prompt MF2'nin `prompt` kuralıyla taranır (`29f`, `08:22`, `08:71-72`): eşleşme
`secret_in_prompt`. Kalan = `stage_cap − spent`; kalan ≤ 0 ise `stage_brake` (`asama-0/12:20`), değilse çağrı tavanı
`min(call_cap, kalan)`, tohum rakibi gibi (`24:53-55`). `plan` hiçbir şey koşturmaz: promptu kurar, tarar, pinli
araçsız `claude -p`'nin argv'sini kurar (prompt stdin'de, `--model`, yerleşik araç, ayar kaynağı, slash komutu, oturum
kaydı yok, `--max-budget-usd`; `29b:44-46`); hiçbir model çağrılmaz. Sunulan model, 429 ve `cost` satırı (test 37) CLI
sonucunun spec'te olmayan biçimini okur: grupta değil, Kurucu'nun PATH'teki taklit `claude`'lu testindedir. Çıktı:
`send` (kullanılabilir ve `reasons` boş); sıralı, tekil `reasons` (`secret_in_prompt`, `stage_brake`; adlar seçim,
desen adı yazılmaz); `prompt_sha256` (gönderilmese de); sıralı `dropped`; `max_budget_usd` (mikrolardan
`"<birim>.<6 hane>"` USD dizgisi, kayan nokta yok, `26:31-33`; gönderilmezse `null`); `argv` karşılaştırılmaz. Çıkış:
0 gönderilir; 1 gönderilmez (duruş, ret değil); 2 kullanılamaz istek (okunamayan şablon, bozuk yer tutucu, eksik ya da
yanlış tipli alan, tamsayı olmayan bütçe, dizgi olmayan model), satır `{"send": false}`.
Vakalar: `prompt_from_typed_input` tipli değerler JSON olarak yerleşir; çağrı başı tavan bağlar;
`undeclared_field_dropped` bildirilmeyen alan girmez, prompt ve hash'i yalnız tipli girdininki, ad yazılır; aşamanın
bıraktığı tavanı bağlar; `value_is_data` iki değerdeki yer tutucu biçimli metin, tırnak ve satır sonu JSON dizgisi
kalır: alan alan değiştirme hangi sırayla olursa olsun birini açar; `wrong_type_unusable` tamsayı yerine `true`
kullanılamaz; `secret_never_sent` istekte `p` kaçışıyla yazılmış, değerde çözülen sahte belirteç kurulan promptta
yakalanır, tavan konmaz (ham isteği tarayan kaçırır); `stage_brake` harcama tavana ulaşınca çağrı planlanmaz.
