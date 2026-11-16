# Vektör Arayüzleri, Son: `genesis`

Tarih: 2026-10-30 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0'ın MF18'ini yazarken; bu grubun komutu, girdisi ya da çıktısı değişirken
Çapa: `seed/bootstrap/vectors/vectors.json` (`genesis`) ve `vectors/genesis/` fikstürleri

---

`29n`'nin devamıdır; kuralları `29m`'ninkidir, beklenen değerler burada yok (`29a`).

## `genesis` (MF18, `activate.py`)

`python -m activate genesis <api.json> <summary.json> <imports.jsonl> <policy.json> <güvenlik.jsonl> <tarif.json>`;
stdin `{"target": "<targets[].id>"}`. Kuru koşu: `api.json` kaydedilmiş GitHub REST'tir, `29i`'deki gibi (kaydı olan
çağrı gövdesini, başkası 404 alır); hiçbir şey yazılmaz, kesim MF9'undur (`refs`). Girdiler `setup/summary.json`
(`26c:31-35`), `26c:37-38` satırları, hakem politikası, tohum güvenlik defteri (`30e`; hakem reposunda
`setup/security-ledger.jsonl`, `26c`, `29s`), doğrulanmış tarif (`26c:53-58`).

**Okunanlar**, iki türde: `GET /app` (yazar App'i), `GET /installation/repositories`, `GET
/repos/{repo}/rules/branches/brain/state`, `.../brain/integration` ve `.../main`; bu üç gövdenin kurallarındaki her
`ruleset_id` için bir kez `GET /repos/{repo}/rulesets/{ruleset_id}` (yazar App'inin `current_user_can_bypass`'ı;
`ruleset_id`'siz kural biçimsizdir); `toy`'da `GET /repos/{repo}/git/ref/heads/main` (oyuncak `main`'den kesilir,
`25a:21`) ve `GET /repos/{repo}/actions/workflows`; `copy`'de `GET /repos/{repo}/actions/permissions` (`main`'in ref'i
okunmaz). `rules/branches` ve `current_user_can_bypass` `01b:59-60`'ındır, öbür uçlar seçim. Bunlar genesis'in API'den
okuyup hash'lediği olgulardır (`asama-0/10a:16`): `25a`'nın 3. ve 6. satırı (`25a` "Her yeni hedef": P1'e kadar yalnız
genesis'te) ve yazma modu şartı (4. satır; seçim: `asama-0/10a:16` onu yazma modunun Aşama 0'daki tek denetimi sayar).
**Liste kapalıdır**: kayıtlı API başka GET'i 404'le cevaplar ve 404 alan GET kullanılamaz girdidir, yani grup okumada
tavandır, taban değil; spec'in genesis'e okuttuğu bir olgu buraya girmeden okunamaz. `bypass_actors` okunmaz: GitHub onu
yalnız ruleset'e yazma erişimi olan çağırana verir, yazar App'i `administration:read`'dir (`25:22`); `25a:17`'nin öbür
aktörleri kurulumda operatörün işidir.

**Nedenler** (adlar seçim; her biri sert duruş, `28:37`): `app_scope` (kurulum repolarının `full_name` kümesi
`targets[].repo` kümesi değil); `state_rules_missing` (`deletion`, `non_fast_forward` yok); `integration_rules_missing`
(`deletion`, `non_fast_forward`, `pull_request`, `required_status_checks`'ten biri yok, `25a:17`);
`integration_check_not_writer` (bir `required_status_checks` kuralında `strict_required_status_checks_policy` doğru
değil, kontrol yok ya da `integration_id` `/app`'in `id`'si değil; kural yoksa yalnız öncekisi); `rules_bypassable`
(`brain/state` ya da `brain/integration` kuralının geldiği bir ruleset'te `current_user_can_bypass` `never` değil:
`exempt` ve `pull_requests_only` de, `25a:17`, `01b:40`); `main_writable` (`main` kuralının geldiği bir ruleset'te
`current_user_can_bypass` `never` değil, ya da `main`'de ne `update` kuralı ne `required_approving_review_count`'u en az
1 tamsayı olan `pull_request` kuralı var, `25a:18`); `toy_workflows` (oyuncağın `workflows` listesi boş değil,
`25a:20`); `copy_actions_enabled` (`enabled` `false` değil, `25a:20`); `security_ledger_broken` (tohum güvenlik defteri
boş ya da geçerli zincir değil).

**Yük**, neden yoksa, on iki anahtar (`asama-0/10a:17`'nin bağladıkları; `26`'da genesis yükü yok, adlar seçim ve
`26`'ya girmeli): `target`; `base_sha` (`toy`: API'deki `main`'in `object.sha`'sı, özettekini okumaz, oyuncak kurulumda
boştur (`null`), `25:26`, `25a:16`; `copy`: `targets[].base_sha`); son aktarım satırından (`referee_tree_sha256` taşıyan son
imports satırı; sayacın aktarım dışı dokunuşları atlanır, `29n`) `referee_tree_sha256`, `result_sha256`;
`import_line_sha256` (o satırın LF'siz baytları, `26c:39`); `seed_epoch` (son `seed_epochs[]`); dosya baytlarının
sha256'sı `policy_sha256`, `summary_sha256`, `seed_security_ledger_sha256` (LF checkout'ta git blob'u, `25:64`);
`seed_security_last_row_hash` (`30e:67-69`); `recipe_sha256` (RFC 8785; evi `profile.json` `units[]`); `facts_sha256`
(türün okuduğu GET'lerin `{istek satırı: gövde}`'sinin RFC 8785'i). Grupta yok: (A)'nın Rekor kimlikleri (onları
taşıyan dosya spec'te yok), `25a` 5. satırın App beyanı (P1'le gelir; özette alanı yok, `26c:31-35`), mandal tabanı,
hazır adaylar. Çıktı `ok`, `hard_stop`, sıralı `reasons`, `payload` (sert duruşta `null`). Çıkış: 0 planlandı; 1 sert
duruş; 2 hedef `targets[]`'ta yok, okunamayan ya da biçimsiz dosya, aktarım satırı yok, gereken GET kayıtlı değil
(satır `{"ok": false, "hard_stop": true, "payload": null}`).
Vakalar: `toy_genesis_row` her ön koşul tutar (oyuncağın `main`'ini onaylı inceleme korur); oyuncağın tabanı API'deki
`main`, özettekinden farklı; imports'un son satırı aktarım değil; satır her baytı ve hash'i bağlar; `copy_genesis_row`
kopyanın tabanı özettekidir, `main`'ini güncelleme kısıtı korur, Actions izni olgu hash'ine girer; `recipe_canonical`
aynı tarif başka anahtar sırası ve girintiyle aynı yükü verir; `copy_actions_enabled` Actions açık kopya sert duruş;
`every_fault_named` altı olgu birden düşer, her biri adlanır (onaysız inceleme `main`'i korumaz, oyuncakta iş akışı
var), oyuncağın kayan `main`'i hata değil; `bypass_named` kopyada yazar App'i `brain/state`'in ruleset'ini atlayabilir
ve `main`'inkinden muaftır, `main` güncelleme kısıtlı olsa da: ikisi adlanır; `security_ledger_broken` hash'ten sonra
bir baytı düzenlenmiş tohum güvenlik defteri etkinleştirmeyi durdurur; `toy_base_empty` kurulumun yazdığı özette (oyuncağın
`base_sha`'sı ve her `seed_sha256` `null`), `toy_base_absent` oyuncağın satırında anahtar yok: yük `toy_genesis_row`'unkidir,
yalnız `seed_epoch.seed_sha256` `null` ve `summary_sha256` fikstürün kendi baytlarınındır; `copy_base_empty` kopyanın
`base_sha`'sı `null` iken kopya istenir: kullanılamaz girdi (çıkış 2); `seed_epoch_seed_null` kurulumun özetinde kopya:
`seed_epoch` son satırdır, `seed_sha256`'sı `null`.

**Kurulumun özetteki biçimi** (seed-059). Önyükleme hakemi `setup/summary.json`'u şu biçimde okur, başkasında her işi durur
(`seed/bootstrap/snowball_bootstrap/config.py` `summary_of`, `target`, `_epoch`). Zorunlu: `seed_commit` (40 küçük onaltılık
hane), `seed_tree_sha256` (64), her `targets[]` satırında yedi anahtar. `null` olabilen: `targets[].base_sha` (commit'i
henüz olmayan hedef; oyuncak kurulumda boştur, yazılan `null`'dır; boş dize ya da eksik anahtar okunmaz) ve
`seed_epochs[].seed_sha256` (beyinde `seed/` yoksa; `25` 10b gereği beyne yalnız `spec/tohum` gider, her teslim satırında
`null`'dır). Yazılmayabilen: `seed_epochs`, `targets`, `honesty_commitment`, `honesty_exception`, `spec_commitment`,
`spec_exception`, `targets[].safety_paths`. Başlatıcının `/work/logs/targets.json`'u `base_sha`'yı olduğu gibi taşır
(`24a:32-33`). Genesis oyuncağın tabanını okumaz; `seed_epoch` son satırı olduğu gibi taşır.
