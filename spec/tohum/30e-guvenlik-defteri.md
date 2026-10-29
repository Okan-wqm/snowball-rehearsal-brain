# Güvenlik Defteri: Zincirli Kayıt, Yaşam Döngüsü, Öğrenme

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: her güvenlik bulgusunda, düzeltmesinde, testinde ve feragatinde; yeni bir hedefe bağlanırken
Çapa: `seed/security-ledger.jsonl` (`python -m ledger.chain verify`); beklemede: etkinleştirme — `ledger.jsonl` `part: security`

---

**Bölüm.** Güvenlik defteri `ledger.jsonl`'ın `security` bölümüdür (`26`) ve öbür bölümlerle aynı
zinciri taşır: kanonik biçim RFC 8785, `row_hash = sha256(canonical(satır − row_hash) ‖ prev_hash)`, ilk
satırın `prev_hash`'i 64 sıfır, vektörler V1–V3 (`29a`); her döngünün kök hash'i `chain/root.jsonl`'a ve
Rekor'a girer (`13`). Yalnız sonuna eklenir; satırı yalnız hakem yazar. Avcının, rakibin, Kurucu'nun ve
hedef sahibinin bildirimi `proposed_by` ve `trust: inferred` ile girer (`26`). Silme yoktur: kapanış,
feragat ve geri çekme de birer satırdır.

| `kind` | Ne zaman | `trust` |
|---|---|---|
| `report` | Bildirim geldi, henüz yürütülmedi | `inferred` |
| `finding` | Kanıt bugünkü kodda 3/3 kırmızı, totolojik değil (`30`) | `verified` |
| `test_added` | Bir kural bekçi testine bağlandı: yeşil ve ekilen ihlali yakalıyor (`30d`) | `verified` |
| `fix` | Düzeltme girdi (K6 kapısı ya da sahibin commit'i); kanıt testi yeşil, düzeltmenin mutantı ölü | `verified` |
| `verification` | Bildiren kendi testini yeni koda karşı yeniden koştu ya da bağımsız bir koşu (CI) teyit etti; `state: closed` kapanıştır | `verified` |
| `reopen` | Kapanmış açığın testi yeniden kırmızı; kırmızıya çeviren aday reddedilir | `verified` |
| `waiver` | Yalnız operatör: neden, kapsam, son tarih; süresi dolan feragat açık sayılır; ajan feragat yazamaz | `observed` |
| `miss` | Bulunması gerekirken bulunmayan açık: ekilmiş kanarya ya da avcının taradığı kapsamda başka yoldan bulunan açık; `miss_reason` (`26`) | `verified` |
| `detector` | Kapanan açıktan doğan dedektör doğrulandı | `verified` |

**Satır.** `26`'daki defter satırıdır (`part: "security"`); `derivation` `test_verified` yalnız yürütülmüş
kanıtta, `snapshot_id` kanıtın koştuğu SHA, `evidence_refs` `[{path, line_start, line_end}]`. **security
payload**: `{state: open|validated|fixed|confirmed|closed|reopened|waived, gap?, catalogue_id, class` (CWE
kimliği, ör. `"CWE-639"`)`, scope: referee|brain|target, target?, finding, fix?, tests[], mutants[],
commit?, merged_as?, ci_run?, agent {role, run_id?, model?}, found_by[]?, refs_rows[]?, detail_sha256?,
waiver? {reason, expires}, miss_reason?}`. Yaşam döngüsü bildirim kanalınınkidir: açık → doğrulandı → düzeltildi → teyit
edildi → kapandı. Sır değeri hiçbir satıra girmez; her satır `secrets.scan`'den geçer (`08` 11).

**Ayrıntı açık yüzeye düzeltmeden önce çıkmaz.** Doğrulanmış ama düzeltilmemiş açığın ayrıntısı (iddia,
kanıt testi, yeniden üretici) açık bir dala, açık repodaki koşu artefaktına ya da Rekor'a yazılmaz;
oradaki satır katalog kimliği, CWE, durum ve ayrıntının hash'ini (`detail_sha256`) taşır. Ayrıntı özel
hedefin `brain/state`'inde ya da mühürlü depodadır (`01a`, K6 artefaktları) ve düzeltme yayımlanınca
açılır; hash taahhüdü provadaki gibidir (`22a`). Hakem reposu açıkken (`01a`) avcı, ayrıntısı açık
yüzeye düşecek bir hedefe bakmaz; açık olan hakem ve beyin bu kuralın bilinen istisnasıdır.

**Okuyucular** (`27`): `gate.check` (bekçi testi kırmızıysa ret; açık `finding`'li yola dokunan aday K6'dır,
`05`); güvenlik avcısı (açık kayıtları yeniden bildirmez, kapanışı denetler, kaçırmalarını görür);
Kurucu oturum başında (açık kayıtlar); `status.block` (açık, doğrulanmış, kapanmış sayıları, en eski açık,
süresi dolan feragat); Aşama 2'den ders görünümü.

**Kapanan her açık üç şey bırakır.** (1) **Dedektör:** profilde bir `detectors[]` satırı (veri, kod değil);
hakem düzeltme öncesi snapshot'ta ateşlediğini, sonrasında sustuğunu doğrular; `security.scan` her push'ta
değişen kapsamda koşar ve onu ateşleyen aday K6'dır. (2) **Regresyon testi:** kanıt testi bekçi olarak
`security/tests/`'te kalır ve her döngü koşar. (1) ve (2) birlikte aynı sınıfın o repoda yeniden
girmesini engeller. (3) **Ders** (`22`): sabit şablondan `claim`, `scope {class_level: K6, property,
path_glob, conditions}`, `origin: own_outcome`; okuyucusu planlayıcı ve düzelticidir, test-yazıcı ve
oracle okumaz. **Repolar arası** (`21a`): desen tipli alanlarla taşınır (katalog kimliği, CWE, dedektör
biçimi, koşullar); kaynağın kodu, yolları, işaretleri ve sır parmak izleri taşınmaz. Yeni repoda
`imported`, `inferred`'dır, oradaki test doğrulayana kadar karar taşımaz; terfi `gate_rules.promotion`.
Kaçırmalar `17`'nin sinyallerine girer.

**Kendimize uygulamak.** `seed/security-ledger.jsonl` hakemin ve beynin güvenlik defteridir, aynı zincirle.
İlk satırları bu repoda 2026-10-29'da kapanan açıklardır (`docs/eksik-kaydi.md`): E01 komutun 125 çıkışı
altyapı sinyalini taklit ediyordu (CWE-345); E02 ve E41 içerik `pull`'u ve `decide`'ı çökertip hakemi
saatlik kilitliyordu (CWE-248, CWE-1287); E03 dosya adındaki denetim karakteri rakibin isteğine sahte bölüm
ekliyordu (CWE-1427); E04 içe aktarma `.git/hooks`'u operatörün checkout'una yazıyordu (CWE-22); E05
koşmayan yeniden üretici kabulü açıyordu (CWE-636); E17 iş akışında şablon enjeksiyonu ve `main`'e sabit
olmayan imza kimliği (CWE-94): yedi `fix` satırı. Sekizincisi E26'nın `verification` satırıdır: CI hepsini
her push'ta yeniden doğrular, kendisi salt okunur, sırsız ve SHA'yla pinlidir (CWE-829). Satırları başvuru
uygulaması `ledger.chain`'in `append`'i yazar, `python -m ledger.chain verify` doğrular. Etkinleştirmede
hakemin kendi kapsamındaki `security` satırları bu dosyanın son `row_hash`'inden devam eder; kökü
`rekor.anchor` canlı olunca Rekor'a yazılır, o güne kadar yalnız-ekleme `verify --previous` ve git
geçmişiyle denetlenir.
