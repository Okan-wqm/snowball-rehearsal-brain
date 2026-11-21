# Şemalar, Devam: Aşama 1'in İlk Dilimi

Tarih: 2026-11-20 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 1'de sıradaki MF ya da parti seçilirken, P1'in MF8'i ve MF9'u yazılırken ve Aşama 1'in çıkış satırları okunurken
Çapa: `seed/bootstrap/stages/stage1-P1.json`; `asama-1/06` ve `asama-1/13`'ün sırası

---

`26e`'nin devamı. Arayüz olgularıdır; kodun nasıl yazılacağı Kurucu'nundur. Aşama sayfası bu sayfayla çelişirse bu
sayfa geçerlidir (`02`).

**İlk dilim deterministiktir** (sahip kararı (2026-11-20)). İlk düzeltme yolunda LLM yoktur. Sıra: P1 partisi (MF9'a
kadar), (A), aktarım, (B); sonra Aşama 1'in kendi MF1'i `lint.discover`, MF2'si taban, MF3'ü `fixer.range`, MF5'i
`candidate.publish` ve MF6'sı izin listesi girişi: kapı izin listesini ve `accept` satırını okur, organ çıktısının ilk
canlı merge'ü budur. Aşama 1'in MF'leri numaralarını korur; MF4 `fixer.llm` ilk organ merge'ünden sonradır.

**P1'in iki yeni satırı** (sahip kararı (2026-11-20)). İkisi de hakem kodudur, bu yüzden oyuncu MF'si değil parti
satırıdır: `referee/` yalnız partilerin MF'leriyle değişir (`asama-1/09`). Gözcü (P1 MF7) önlerinde kalır; üçü de ilk
organ merge'ünden öncedir. Eski MF8 aşağıda ertelenmiştir; MF1–MF7'nin numaraları değişmez.
- **MF8, bulgu yazıcısı** (`findings.write`; modül `findings/write.py`; test 12). `<state_root>/findings.jsonl`'u
  adapter önerisinden, `<state_root>/unresolved.jsonl`'u kapı kararından hakem yazar (`26`). Parmak izi `asama-1/13d`
  ve `07`'deki gibidir, satır girmez; aynı parmak izi yeniden gözlemdir. Durumlar `13d`'nin listesidir. Oyuncunun
  önerdiği içerik `proposed_by` taşır. Test 12 MF4'ten buraya taşındı; numarası korunur (`asama-0/09`).
- **MF9, izin listesi ve `accept` yazıcısı** (`gate.allowlist`; modül `gate/allowlist.py`; test 55). `accept` satırını
  döngünün `yaz`'ı önyükleme hakeminin imzalı sonucundan yazar (`26`, `26b`). Kapı, tanım hash'i hiçbir `accept`
  satırında olmayan organın adayını reddeder (`01b`, `09`). Karşılaştırılan hash, hakemin kabul edilmiş SHA'daki organ
  dosyalarından tek hash fonksiyonuyla kendi hesapladığıdır (`26e` "Organ tanımının hash'i"), aday paketinin
  `definition_sha256[]` beyanı değildir. Test 55 §0.9'un numaralarının devamıdır (53 `30d`'nin, 54 `29za`'nınkidir):
  tanım hash'i hiçbir `accept` satırında olmayan organın adayı kapıda reddedilir; o hash için `accept` satırı
  yazılınca aynı aday aynı koşulda geçer; adayın beyan ettiği hash kararı değiştirmez.
`26e`'nin tablosu ve `stages/stage1-P1.json` bu iki satırı taşır. §0.9'un donmuş tablosunda 52'nin partisi `P1`
yazılı kalır; bu sayfa ondan üstündür (`02`).

**İlk organ merge'ünden sonraya ertelenenler** (sahip kararı (2026-11-20)). Ertelenenler P3 partisidir: Aşama 1
MF6'dan ve P2'den sonra, MF4 `fixer.llm`'in canlı koşusundan önce. P3'ün tablosu bir tohum döneminde gelir; bu tohum
onu taşımaz (`stages/`'te tablosu yoktur, `26e` "Çıkış partisi" gibi).
- **Eski P1 MF8**, `operating{}` sınırlarının bant içinde ayarı (test 52): sahip kararıyla ertelendi.
- **Düzeltme gidiş-dönüşü** `koş` → `çağır` → `koş`: `koş`un ürettiği tipli `fixer.llm` isteğini `çağır` işler, `koş`
  yanıtı deterministik uygulayıcıyla yalnız o aralığa yazar (`asama-1/05` 3). Bugün `çağır` yalnız (B)'nin kanaryasını
  çağırır (`asama-0/01`), `loop.yml` hakem kodudur. `fixer.llm` (MF4) bu satırla birlikte gelir. Testi P3'ün tablosuyla
  gelir.
- **McNemar ve match-rule v2'nin K3+ dalı.** P1 K0 dalını uygular: `match` vektörleri K0'dır, testler 3 ve 5 "K3
  ile"dir (`asama-0/09`). `mcnemar` grubu MF4'le kabul edildi ve MF4'ün satırında kalır: kabul edilmiş bir MF geri
  çekilmez, grubu her push'ta koşar. İlk organ merge'ünden önce McNemar'ın yeni bir işi ya da okuyucusu yoktur.

**Bırakma** (sahip kararı (2026-11-20)). P1 MF8 (H1), P1 MF9 (H2) ve düzeltme gidiş-dönüşü (H3), dış göz
incelemesinin (2026-11-20, iki inceleyicinin uzlaşısı) bulduğu tablo düzeltmeleridir; Kurucu'nun bir raporundan
gelmezler.

**Ölçüm aynası** (operatör kararı, 2026-11-20). `/work/logs/mirror.json`'un `session_time` bölümü oturum başına
`wall_s`, `api_s`, `blocked_on_own_checks_s` ve kotanın başı ve sonunu kova adıyla (`quota_start`, `quota_end`),
`path` bölümü bu dilimin henüz kabul edilmemiş MF'lerini (`path_mfs_left`) ve `organ_merges_copy`'yi verir. Yalnız
olgudur; tanımları `seed/founder/mirror.py`'nin `SOURCES`'undadır. Türetilemeyen değer `null`'dır ve nedeni
yazılıdır.
