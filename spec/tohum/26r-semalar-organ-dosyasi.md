# Şemalar, Devam: Organın Dosyası, Taşınması ve İmajı

Tarih: 2026-11-23 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: P1 MF1 ve MF9 (`runner/organs.py`, `gate/allowlist.py`) ve `çek`'in organ okuması yazılırken ya da değiştirilirken, bir organ dosyası, `pulled`'ın organları ya da `accept.json` okunurken
Çapa: beklemede: P1 aktarımı — beyin kökündeki `organs/<id>.json` ve `accept.json`, `pulled`'ın `organs.json`'u

---

`26e` "Organ tanımının hash'i"nin devamı (rapor masası uzlaşısı (2026-11-23), seed-073 (a), (c), (d); operatör kararı,
sahibin yetkisiyle). Arayüz olgularıdır; kodun nasıl yazılacağı Kurucu'nundur. "Kurulduğu gibi benimsendi" Kurucu'nun
yapımını arayüz yapar (`26j:17`'nin emsali); bu sayfanın hiçbir maddesi yeni bir sıkılaştırma değildir.

**Organın dosyası** (seed-073 (a); kurulduğu gibi benimsendi).
- Organ, önyükleme hakeminin kabul ettiği beyin SHA'sında beyin kökündeki `organs/<organ_id>.json` dosyasıdır.
  `<organ_id>` tek bir yol bileşenidir, `runner.kos.CANDIDATE_ID`'nin biçiminde: `[A-Za-z0-9][A-Za-z0-9._-]{0,127}`
  (nokta olabilir). Bir paketin `organ_ids`'inde, bir `accept` satırında ve `proposed_by`'da duran kimlik budur.
  `26p:38`'in noktasız kuralı yalnız çalışma-zamanı aday kimlikleri içindir, organ kimliği için değil.
- Dosya tam olarak `entry` ve `files` taşıyan bir JSON nesnesidir. `entry` boş olmayan dizgilerden boş olmayan bir
  dizidir: kapsayıcının yazıldığı gibi koştuğu komut, sonuna bir şey eklenmez. `files` farklı beyin yollarından bir
  dizidir: her biri göreli ve normal, o commit'in düzenli bir dosyası (bağ ya da dizin değil), yalnız ağaçlardan
  geçerek ulaşılan; hiçbiri bir başkasının yolundaki dizin değildir. Dosyalar commit'lendiği gibi bloblardır (checkout
  ve `.gitattributes` yoktur).
- Tanım `{entry, files: {yol: blobun baytları}}`'dır. Hash'i `runner.organs.definition_sha256`'dır, `26e:61-63`'ün tek
  fonksiyonu: `entry`'yi ve adlandırılan her dosyanın yolunu ve baytlarını kapsar; çalıştırma biti ve `files`'ın sırası
  hash'e girmez.
- `organs/`'un her girdisi alınır: böyle bir dosya olmayan girdi `organ_invalid:<ad>`, ağaç olmayan `organs`
  `organs_not_directory` ile çekmeyi reddeder; hiçbir girdi atlanmaz. O SHA'da `organs` girdisi yoksa organ yoktur.
- Aşama 1'de dosyada başka alan yoktur. LLM organının modeli ve araçları (`26e:62-63`) P3'ün 2. satırıyla tanımına
  girer (`26s`).
- Oyuncu kodu `24a`'nın koyduğu yerde kalır (`adapters/`, `fixers/`, ...); organın dosyası onları beyin yollarıyla
  adlandırır. `organs/` tanımların dizinidir, kod değildir.
- `24a`'nın beyin kökü düzeni `organs/<id>.json`'u (organ tanımları) ve `accept.json`'u (giriş isteği, `26j:68-72`)
  taşır: ikisi de veridir ve ikisinden birine dokunan push kod isteğidir (`29b:42`).

**Taşınma** (seed-073 (c); kurulduğu gibi benimsendi).
- `çek` kabul edilmiş SHA'nın git nesnelerinden `organs/`'u ve `accept.json`'u okur. Organlar `koş`'a ve `yaz`'a yalnız
  `pulled`'da ulaşır: `organs.json` (`{organ_id: definition_sha256}`, hakemin okuduğu dosyalardan kendi hesapladığı),
  her organ için `organs/<organ_id>/entry.json` ve `organs/<organ_id>/files/<yol>`, ve `accept.json` (`null` ya da
  `{brain_sha, run_id, organ_ids}`). `koş` bir organı yalnız `runner.organs` üzerinden çağırır (P1 MF1, test 51).
- "Kabul edilmiş" ile "listelenmiş" iki ayrı listedir. Çağrı listesi: `koş`'un çağırdığı organlar kabul edilmiş SHA'daki
  her organdır (`asama-1/05:14-16`). Merge listesi: kapının listesi `accept` satırlarıdır (`26b:34-35`, `26j:37-38`).
  Listede henüz olmayan bir organ çağrılır ve adayı `organ_not_listed:<id>` ile reddedilir: bu ret Aşama 1 MF5'in
  kırmızı testidir (`asama-1/06:21-22`).

**İmaj** (seed-073 (d); kurulduğu gibi benimsendi).
- Organın giriş noktası her `koş` koşusu gibi kapsanmış koşar (`08:25-35`): birim tarifinin `@sha256` ile pinli
  `env_image`'ında (`26c:62`, `08:33-34`), devrin temiz snapshot'ı ağacı olarak, tanımın dosyaları `/in/<beyin yolu>`
  altında salt okunur, çıktısı `/out` altında (`26p:16`), ağsız, yanında işin kırmızı kontrolüyle (`08` 3).
- Aşama 1'de organa özgü imaj yoktur; tanımda imaj anahtarı yoktur. Giriş noktası birimin imajında koşabilmelidir:
  dili o imajda olmayan organın koşusu geçerli değildir, nedeni koşununkidir. Organ başına ikinci bir imaj, `services[]`
  gibi (`08:35`), hiçbir sayfada yoktur.
- Birimin lint aracı bir adaptere `26m:23-24`'ün söylediği gibi ulaşır (tariften `deps.fetch`'le, `koş` koşusunda); bu
  sayfa onu değiştirmez.
