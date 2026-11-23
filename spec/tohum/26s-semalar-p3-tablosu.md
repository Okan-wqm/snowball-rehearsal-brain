# Şemalar, Devam: P3'ün Tablosu

Tarih: 2026-11-23 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 1'de P3 seçilirken ya da yazılırken, P3'ün çıkış isteğinden önce ve `fixer.llm`'in çağrı başı frenleri okunurken
Çapa: beklemede: P3'ün makine kopyası (`seed/bootstrap/stages/stage1-P3.json`, sonraki bir tohum döneminde)

---

`26h` "İlk organ merge'ünden sonraya ertelenenler"in devamı (rapor masası uzlaşısı (2026-11-23), P1 çıkış dönemi;
operatör kararı, sahibin yetkisiyle; frenler sahip kararı (2026-11-23)). Arayüz olgularıdır; kodun nasıl yazılacağı
Kurucu'nundur. Tablo `26e`'ninkinin biçimindedir.

**Yeri.** P3 `asama-1/13`'ün "P3 ertelenenler" satırının sırasıyla P2'den sonradır: (A)'sı Aşama 1 MF6'dan ve P2'den sonra, MF4 `fixer.llm`'in
canlı koşusundan öncedir (`26h:34-36`). Tablo P2'den sonra açılır. Bu tohum onun makine kopyasını taşımaz:
`stages/stage1-P3.json` yoktur ve `P3` önyükleme hakeminin parti listesine o kopyayla girer; o zamana kadar P1 ve P2
aktarılınca açık tablo boştur (`26e:41-44`).

| Parti (`batch`) | MF | Test | Vektör grubu | Modül (`referee/` altında) | `calls` |
|---|---|---|---|---|---|
| `P3` | 1 | 52 | — | sayfada yok | — |
| `P3` | 2 | 59 | — | sayfada yok | sayfada yok |
| `P3` | 3 | 60 | — | sayfada yok | — |

- Hiçbir sayfa modülleri adlandırmaz: tablo yüklenirken `26e:34-37`'nin kuralıyla adlandırılır (aracı olmayan
  mekanizmada mekanizmanın adından; ilk ad standart kütüphanenin bir modülünün adı olamaz, `26j:62-66`). Hiçbir satırın
  vektör grubu yoktur. MF2'nin `calls`'u da hiçbir sayfada yoktur.
- Testler §0.9'un numaralarının devamıdır (`26e:32-33`; 58'den sonra 59 ve 60). Önyükleme hakemi testi olmayan bir
  satırı taşıyan tabloyu yüklemez; bu yüzden testler tablodan önce sayfadadır.
- **MF1, `operating{}` sınırlarının bant içinde ayarı** (eski P1 MF8, `26h:37`; `18a`, `26c:76`). Test 52
  (`asama-0/09:76`): sınıra takılma ve boşta kalma ölçümleri sınırı yalnız operatörün bandı içinde, iki yönde oynatır;
  bant dışı öneri reddedilir. §0.9'un donmuş tablosu 52'nin partisini `P1` yazar; bu sayfa ondan üstündür (`02`).
- **MF2, düzeltme gidiş-dönüşü** `koş` → `çağır` → `koş` (`26h:38-41`, `asama-1/05:18-27`). `fixer.llm` (Aşama 1 MF4,
  oyuncu MF'si, `26e:14`) bu satırla gelir, satırın kendisi değildir. Test 59: tipli bir `fixer.llm` isteği `çağır`'dan
  geçer; yanıt yalnız bulgunun aralığına uygulanır, aralığın dışındaki bir yanıt uygulanmaz; iki tavandan birini aşan
  çağrı düzenleme vermez; tutmayan yolda worktree atılır ve bulgu `cause` ile `unresolved.jsonl`'a önerilir.
- **MF3, sonda döngüsü ve kalkışı** (L3, `28a:54-55`; kural `28:28-31`, anahtar `performance.rules.probe_cycle`,
  `18b:34`). Test 60: üst üste iki temiz sonda döngüsü dondurmayı kaldırır ve kalkış bir satırdır (`26i`'nin `lift`
  satırı); temiz olmayan bir sonda döngüsü kaldırmaz. Bu satıra kadar regresyon ve kapsayıcılık dondurması Aşama 1'de
  kalkmaz (`28a:31-33`).

**`fixer.llm`'in çağrı başı frenleri** (sahip kararı (2026-11-23); seed-095; `asama-1/10:16`). Karar verildi:
`constitutional.stage_params.fix_call_max_usd` `"0.500000"` (`01c`'nin altı ondalıklı dizgisi, 0'dan büyük) ve
`constitutional.stage_params.fix_call_max_s` `300` (1 ya da daha büyük JSON tamsayısı); başka biçim
`policy_invalid:<yol>`'dur. İkisi `18a`'nın anayasal tablosunun satırlarıdır, `stage_budgets` değildir (oradakiler
aşama toplamıdır). Okuyucuları P3 MF2'de `fixer.llm` adına `llm.call`'dır (`26a:39`). Gevşetme L-AF1 bu dönemle biter
(`26n:44-53`).
- Anahtarlar çağrı başınadır; `asama-1/10:16`'nın "bulgu başına"sı ancak bir bulgu tek çağrı aldıkça onlarla aynıdır
  (`08:60`: düzeltici araçsız tek bir çağrıdır; `26h:38-40`). 300 saniyelik tavanı kimin uyguladığını P3 MF2 adlandırır:
  `26a:39` yalnız USD tavanını adlandırır.
- Zaman: iki fren anahtarı ve `performance.rules.probe_cycle` P3'ün tablosu açılınca okunması zorunlu yollar olur
  (`29v`), bu dönemin tesliminde değil; o zamana kadar hiçbiri `policy_reads_required_absent` kırmızısı vermez. Fikstürler
  (`29v`) ve hakemin `policy.json`'u iki fren anahtarını teslimden taşır: erken bir okuma `policy_reads_unknown` değildir.
- LLM organının prompt'u, modeli ve araçları (`26e:62-63`) P3'ün 2. satırıyla tanımına girer (`26r`). Tanımın dışındaki
  bir isteğin neden adı Kurucu'nundur.

**P3'te olmayanlar** (adlı; hiçbiri sessiz değil).
- McNemar ve match-rule v2'nin K3+ dalı: testleri 3 ve 5 "K3 ile"dir ve K3 Aşama 3'tedir; K3'ü getiren Aşama 3
  partisiyle gelir ve P1 MF4'ün modülünde kalır (`26h:42-44`).
- L1, salınım birikimi (`28a:48-50`), ve L2, Actions dakikasının kaynağı (`28a:51-53`): kendi sayfalarının adlandırdığı
  dönemlerle gelir, P3'le değil. Test 22 ve `agent.dispatch`: `30f`, en geç Aşama 4.
- `cases/dev.jsonl`'un hash zinciri Aşama 1 çıkış partisiyle, puanlayıcıda parmak izinin yeniden türetilmesi ilk LLM
  avcısını getiren dönemle gelir (`26n:57-59`).
