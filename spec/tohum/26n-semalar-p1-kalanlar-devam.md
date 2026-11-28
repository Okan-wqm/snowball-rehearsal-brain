# Şemalar, Devam: Test 9 ve 11, Sürükleme Etkinliği, Ertelenenler

Tarih: 2026-11-22 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: P1 MF5 ve MF6 (`harness/offline.py`, `drift/check.py`) yazılırken ya da değiştirilirken, Aşama 1'in bütçe anahtarları adlandırılırken ve P1'in çıkış isteğinden önce
Çapa: beklemede: P1 aktarımı — testler 9 ve 11, `drift.check`'in çıktısı

---

`26m`'nin devamı (rapor masası uzlaşısı (2026-11-22), seed-092, seed-094, seed-095; operatör kararı, sahibin
yetkisiyle). Arayüz olgularıdır; kodun nasıl yazılacağı Kurucu'nundur.

**Test 9 ve test 11** (`harness/offline.py`, P1 MF5; seed-092).
- (1) Test 9 (`asama-0/09:33`) satırının iki yarısını da gösterir: `referee/harness/`'ın import kapanışında bir model
  istemcisinin (`dispatcher/llm_call` ya da başkası) importu yoktur (statik okuma) ve harness testleri ağı kapalı bir
  `koş` koşusunda geçer. Statik okuma tek başına satırı karşılamaz. Denetim kancası korkuluğu Kurucu'nun eklemesidir,
  istenmez; sayılması için bir ağ denemesi testi kırmızı yapmalıdır (denemeyi yalnız kaydetmek yetmez).
- (2) Çalışırken çevrimiçi bulunan harness: `yaz` devri reddeder ve hiçbir şey yazmaz; defter satırı yoktur (bir satır,
  çevrimiçi bir harness'in durum yazmasına izin verirdi). Ret başarısız işin kendi çıktısıdır; neden kurulduğu gibi
  benimsendi (`harness_online`).
- (3) Test 11 döngünün kurulduğu hâliyle bir testidir, `harness/offline.py`'de kod istemez. `26e`'nin tablosu MF5'e iki
  test için bir modül verir; modül var olmalıdır (`asama-0/14`'ün modül kuralı) ve test 9'un mekanizması oradadır.
- (4) P1'in test 11 satırı şu zaman bitmiş okunur: `<state_root>`'u olmayan boş bir oyuncak reposundan başlayan bir devir,
  düzeni bir sayfada verilen durum yollarını sıfırdan yaratır (`findings.jsonl` ve `unresolved.jsonl` ilk satırlarıyla,
  hiçbiri boş yaratılmaz, `26j` MF8; `cases/dev.jsonl`, `26m`) ve yalnız o koşuda bir Aşama 0 ya da P1 aracının yazdığı
  yolları bırakır; hiçbiri önceden konmaz, hiçbir şey var olmadan okunmaz.
- Test 11'in sözü gevşetilmez (`26e:78-80`); boş oyuncak fikstürü Kurucu'nundur: prova oyuncağı boş değildir.

**Sürükleme etkinliği** (`drift.check`, P1 MF6; seed-094).
- (1) Aykırı bir etkinlik girdisinin nedeni `ref_change`'tir, Gözcü satırının tetiğiyle aynı ad (`26i:32`); girdiler
  kanıtta adlandırılır, ikinci bir ad yoktur. Kurulduğu gibi benimsendi. Pencereyi başından gösteremeyen okuma
  kullanılamaz girdidir (`01c:68-69`), sürükleme değildir.
- (2) Bir girdinin zaman damgası `01c:37`'nin tek biçimidir, `YYYY-MM-DDTHH:MM:SSZ`; başka biçim kullanılamaz girdidir.
  Kurulduğu gibi benimsendi; sıkılaştırma. Canlı gözlem (2026-11-22, salt okuma): oyuncağın ve kopyanın
  `activity?per_page=100` girdilerinin hepsi bu biçimdedir.
- (3) Açık bir hedefte okuma, herkese açık okumadan başka izin ya da kimlik istemez; `drift.check`'in öbür okumalarıyla
  aynı kimliği kullanır ve tabanın `writer_app_permissions`'ının (`01c:59-60`) tutmadığı bir izni hiçbir zaman istemez.
  Aşama 1'in iki hedefi de açıktır (`25` 10, 10a).
- (4) `01c:25`'in "görünür uyarı"sı devrin kendi koşusunda, `yaz`'ın satırından önce, uyarı düzeyinde bir iş akışı
  notudur; `operator check stale` metnini ve okunan `operator_checked_at`'i taşır. Kurulduğu gibi benimsendi. O duruşta
  hiçbir şey yazılmaz (`01c:24`), kanal yalnız koşudur; ilk canlı görülüşünü Kurucu kaydeder.
- (5) Komutun kendi çıkış numarası arayüz değildir. Arayüz: iş kırmızı bitmez, hiçbir şey yazılmaz ve eski denetim
  farktan ve kullanılamaz girdiden komutun JSON satırıyla (`stale: true`, `hard_stop: false`) ayrılır, metin okunmadan.

**Aşama 1'in bulgu başı frenleri** (`asama-1/10:16`; seed-095; sahip kararı (2026-11-23), P1 çıkış dönemi). Karar
verildi (E702 kapandı): `constitutional.stage_params.fix_call_max_usd` `"0.500000"` (`01c`'nin altı ondalıklı dizgisi,
0'dan büyük) ve `constitutional.stage_params.fix_call_max_s` `300` (1 ya da daha büyük JSON tamsayısı); başka biçim
`policy_invalid:<yol>`'dur. İkisi `18a`'nın anayasal tablosunun satırlarıdır; okuyucuları P3 MF2'de `fixer.llm` adına
`llm.call`'dır (`26s`). `stage_budgets` değil: oradaki anahtarlar aşama toplamıdır, her biri `monthly_cap_usd` ile
karşılaştırılır (`18a:57`, `02:23`); bunlar `llm.call`'ın çağrı başı tavanıdır (`26a:39`). Değerler sahibin, seed-095'in
Kurucu önerisi olan 0,50 USD ve 5 dk'dır. P3'ün tablosu açılınca okunması zorunlu yollardır (`29v`), bu dönemin tesliminde değil.
**L-AF1 bitti** (bu dönemle): `02:22`'nin eşik maddesi ("her eşik ya `policy.json`'a ya da anayasal tabana atıf") bu
hücreye de uygulanır ve hiçbir `spec.lint` bu hücreyi muaf tutmaz. "Bulgu başına" ile çağrı başının farkı
`26s`'dedir.

**Açıkça ertelenenler** (rapor masası uzlaşısı; her biri adlı bir döneme ya da aşamaya, nedeniyle):
- K4'ün sayımı (seed-091 (4)) → Aşama 3: K4 orada gelir (`03:63`).
- `cases/dev.jsonl`'un hash zinciri (seed-090 (1)) → Aşama 1 çıkış partisi (P1 çıkış döneminde karar): setin bütün geçmişini okuyan ilk hüküm `exit.sample`'dır (test 27, `asama-1/13`'ün "Aşama 1 çıkışı" satırı). O zamana kadar yalnız ekleme önek kuralı (`26m:34-37`, `01b:33`) ve `28`'in beyan dışı bir aktörün `brain/*` ref değişikliğindeki sert duruşu tutar.
- Puanlayıcıda parmak izinin snapshot baytlarından yeniden türetilmesi (seed-091 (1)) → ilk LLM avcısını getiren dönem, en geç Aşama 4 partisi (`asama-1/13`'ün "Aşama 4" partisi, "ilk LLM avcısından önce"; P1 çıkış döneminde karar): bugün
  puanlanan her parmak izini hakemin kendi yazıcısı yapar (L-AH1 dışında, `26q`). L-AH1 iki dosyalı vektör komutunda kalır.
- Test 11'in tam yol listesi (seed-092 (4)) → reddedildi (P1 çıkış döneminde karar): listenin tanımı `26n:22-25`'tir (bir Aşama 0 ya da P1 aracının sıfırdan yarattığı yollar); sabit bir liste her yeni yazıcıda bir sayfa düzeltmesi isterdi ve daha güçlü olmazdı. P1'in test 11 satırı P1 çıkışında o kuralla okunur.
- Özel bir hedefin etkinlik okumasının kimliği ve izni (seed-094 (3)) → ilk özel hedefin dönemi: Aşama 1'in hedefleri açık.
  Sayfalar özel hedefe bir aşama vermez (`01a:23-25`, `25` 0 ve 5: önce hakem reposu özel olur, okuyucu App'i kurulur);
  aşama sınırının yerine kapı: bu okumanın kimliği bir sayfada adlandırılmadan hiçbir özel hedef bağlanmaz.
- Geri çekilen vaka satırının (`01b:34`) biçimi ve yazıcısı (seed-090 (3)) → Aşama 2: Aşama 1'de yazıcısı yoktur,
  geçerlilik girişte yargılanır; biçimi ne olursa olsun eklenen bir satırdır, düzenleme değildir.
- Boş olmayan `finding_id_patterns` ve yazıcısı (seed-089 (4)) → "yorum satırı"nın tanımıyla aynı dönem (`26e:65-66`),
  en geç ilk ekilmiş snapshot'tan (Aşama 4, `26h:69-70`) önce.
- Kimlik olarak bulgu kimlikleri ve başlıkları (seed-089) → `system_tp` vakası üreten ilk partinin dönemi, en geç
  Aşama 4 (`asama-4/07:29`: panelin TP'si `system_tp` vaka adayıdır; bunu o sayfa belirler): Aşama 1'in vaka
  kaynakları `human_fix` ve `mutation`dur (`asama-1/13a:11-13`).
- Bulgu başı frenlerin anahtarları (seed-095) → P1 çıkış döneminde karar verildi (yukarıda, `26s`).

**Vakanın grubu, devam** (seed-105; `26m:77-80`). Adlar vakanın aracının ekosistemininkidir; Aşama 1'in tek aracı
`eslint`'tir (`29za:25`). İkinci bir araç kendi ekosisteminin adlarını kendi sayfasında veri olarak getirir
(`31c:23-27`); adları ne profil ne Kurucu koyar. Kurulduğu gibi benimsendi: okunmayan manifest (bağ, dizin) işaretlemez,
ağacın kökü `.`'dır. Beynin `6f36fba`'sında arama birimin kökünün üstüne çıkar (`referee/cases/build.py:484-493`;
`referee/tests/test_cases.py:903-904` onu sabitler). Açık grup kalmadı: `group_undecided` ara çözümünün yerini bu yanıt
alır, reddedilmiş mutasyonlar yeniden önerilir. Yazılmış satır durur (`26m:35-36`). Vektör değişmez; gevşetme yok.
