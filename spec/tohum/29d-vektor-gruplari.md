# Tohum Vektörleri, Devam: Aşama 0'ın Grupları ve Genel Koşucu

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0'ın her mikro özelliğini yazarken ve önyükleme hakeminin vektör koşucusu değişirken
Çapa: `seed/bootstrap/vectors/` (`vectors.json` ve grup fikstürleri); `seed/bootstrap/stages/stage0.json`

---

`29a`'nın devamıdır; aynı kurallar geçerlidir. Aşama 0'ın her mikro özelliği bir gruba bağlıdır
(`asama-0/14`); grubun koşacağı an aşama tablosundan okunur (`26c`).

**Veri biçimi.** Her vektör veridir: `{cmd, stdin?, fixture, expect, changed: {…, expect_not}}`. `cmd`
`referee/` kökünden koşan komut, `fixture` `vectors/` altındaki girdi ağacı ya da dosyası, `expect`
stdout'taki tek satır JSON'un beklenen alanları; `changed` aynı vektörün bir bayt ya da bir alan
değiştirilmiş girdisidir ve `expect_not` onun **vermemesi** gereken sonuçtur. Biri tutmazsa vektör
kırmızıdır (`29a`). Beklenen değerler tohum yazılırken iki bağımsız hesapla doğrulanır.

**Genel koşucu.** Önyükleme hakemi bütün grupları tek bir veri koşucusuyla, Kurucu'nun koduna `koş`un
kumunda uygular (python imajı; git, docker, node yok). Gruba özgü kod yoktur; yeni grup veridir ve tohum
dönemiyle gelir. Komutun son denemesi 125 ile biterse sonuç `runner_fault`'tur, Kurucu'ya yazılmaz.
Hakem stdout'un son satırını okur ve yalnız `expect`'in adlandırdığı alanlara bakar; satırdaki başka alanlar
komutundur. Değerler JSON olarak karşılaştırılır: `true` `1` değildir, `1` `1.0` değildir. `changed` aynı
alanları vermeli ve `expect_not`'u vermemelidir; cevap vermeyen ya da alanı eksik bırakan da kırmızıdır.
`chain`, P1'in ve provanın grupları kendi yargıçlarıyla koşar (`29a`, `29c`). `secrets`'tan `diffguard`'a
grupların komutları, girdileri, çıktı alanları ve vakaları `29f` ve `29g`'dedir.

| Grup | MF | Bağladığı |
|---|---|---|
| `chain` | 1, 10 | V1–V3 (`29a`); `hash`, `verify --previous` |
| `secrets` | 2 | diff, defter satırı ve promptta gömülü sahte sır yakalanır; temiz girdi geçer |
| `contained` | 3 | üretilen `docker run` argv'si zorunlu bayrakları (`--network none`, `--cap-drop ALL`, `--read-only`, kullanıcı) taşır, yasaklıları taşımaz |
| `profile` | 4 | fikstür ağaçlarda diller, birim adayları, güvenlik ve hariç yollar; ajan yapılandırması büyük-küçük harf duyarsız hariç; daraltan öneri ret |
| `npmlock` | 5 | `integrity` eşleşmesi; bir baytı değişmiş tarball, izinsiz `resolved`, git ve dosya bağımlılığı ret |
| `recipe` | 6 | statik tarif denetimi: imaj `@sha256`, `inputs`, komutlar, sınırların `operating{}` anahtarları |
| `diffguard` | 7 | `asama-0/08` madde 1'in her ret nedeni |
| `k0map` | 8 | eşlenmiş satır kuralı (`asama-0/08`) ve madde 3–8'in kararları, fikstür `koş` çıktılarıyla; arayüz `29h` |
| `refs` | 9 | yazılan her ref `refs/heads/brain/` altında; `main`'e ve `brain/` dışına yazma ret; geri alma ağacı ilk ebeveynin ağacı; arayüz `29i` |
| `append` | 10 | devir başına tek commit; yazımdan önce `verify --previous`; arayüz `29i` |
| `root` | 11 | kök = bölüm uçlarının kanonik hash'i; imza doğrulaması; arayüz `29j` |
| `flaky` | 12 | 3/3 kuralı (`07`); arayüz `29j` |
| `cause` | 13 | mekanik `cause` (`test_regression`, `build_break`, `lint_regression`, `impact_miss`, `unknown`); arayüz `29j` |
| `revert_drill` | 14 | taahhüt `HMAC(prova_tohumu, cycle_id)`; açılım eşleşmesi; `tampered_key` reddi; arayüz `29m` |
| `prompt` | 15 | tipli girdi → prompt sha256; tip dışı alan girmez; arayüz `29m` |
| `status` | 16 | defterden üretilen blok; elle düzenlenmiş blok yeniden üretilir; arayüz `29n` |
| — (`wiring`) | 17 | vektör değil: tohumun iş akışı denetimi, her push'ta ve (A)'da (`29b`) |
| `genesis` | 18 | genesis satırının alanları ve hash'leri; ruleset, bypass, `main` ve iş akışı olguları; arayüz `29o` |

`chain` dışındaki on altı grup Aşama 0'la gelir. `drill` grubunun sahibi Aşama 2 partisidir (`29c`);
`cp_lower`, `mcnemar` ve `match` P1'indir (`29a`). Sahibi olmayan grup Aşama 0'da koşmaz ve çıkışta
sayılmaz.
