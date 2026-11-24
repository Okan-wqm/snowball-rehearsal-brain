# Görev Haritası, Devam: Sahibin İpuçları V

Tarih: 2026-11-23 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: her oturumda, görev seçilirken (`00f`'nin devamı)
Çapa: elle yazılır; `00f`'de bu dört ipucuna yer kalmadığı için (`15` 1) ipuçları burada sürer

---

Dört ipucunun her biri bir görevdir, reçete değil: olgusu ölçülmüştür, tasarım senindir, her birini kanıtla
çürütebilirsin. Beyin olguları beynin `94517ab` commit'indendir. Sondaki korkuluklar dördü için bağlayıcıdır.

**Sahibin ipucu (bu kez kural esnetildi; 2026-11-23, E739; görev, reçete değil). Aday, onu üreten organla yargılanır.**
- Olgu (sayfalar): "Listede olmayan bir hash'in ürettiği aday, içeriği ne olursa olsun reddedilir" (`12:15-18`; ayrıca
  `01b:9-12`). Kapı paketten yalnız `organ_ids`'i okur (`26j:32`).
- Olgu (beyin): `referee/gate/allowlist.py:32` "Of the package only ``organ_ids`` is read"; `referee/loop/decide.py:252`
  kararı `AL.reasons(cand.package, ...)` ile paketin adlandırdığı organlara verir. `koş`un dizini her çağrılan organın
  saklanan çıktısının hash'ini o organın girdisinde taşır (`referee/runner/kos.py:86-89`) ve paket bu çıktılardan
  birinin dosyasıdır (`referee/runner/candidate_rerun.py:8-10`); yeniden koşu çıktıları organ kimliği olmadan alır
  (`referee/runner/kos.py:512-513`).
- Görev: kapının kararı, adayı hangi organın ürettiğine hakemin kendi bildiğiyle dayanır, adayın kendisi için
  söylediğiyle değil (`12:15-18`). Bunu, paketi listelenmiş bir organı adlandıran ama listede olmayan bir organın
  ürettiği adayın reddedildiği bir testle göster. Zaman: ilk girişten (Aşama 1 MF6, `26j:35-36`) sonra ikinci bir organ
  çağrılmadan önce; kapı P1'in MF9'udur (`26j:30`), P1 açıkken bu P1'in kodudur.

**Sahibin ipucu (bu kez kural esnetildi; 2026-11-23, E740; görev, reçete değil). Organ, sayfasının söz verdiği araca
ulaşır.**
- Olgu (sayfa): adapter birimin lint aracına snapshot'tan değil, birimin tarifinden Aşama 0'ın `deps.fetch`'iyle `koş`
  koşusunda ulaşır; snapshot'ın hariç tutmaları değişmez (`26m:23-24`).
- Olgu (beyin): `koş` organı snapshot üzerinde koşar, "no installed dependency is in it"
  (`referee/runner/kos.py:79-82`); organın çağrısına imaj, ağaç ve ortam verilir, `deps` verilmez
  (`referee/runner/kos.py:324-325`); kap ağsızdır (`referee/runner/organs.py:6`). Aynı modül adapter'ın aracına nasıl
  ulaştığını hiçbir sayfanın söylemediğini yazar (`referee/runner/kos.py:97-99`, seed-074); `26m:23-24` bunu söyler.
- Görev: Aşama 1 MF1'in ilk canlı koşusundan önce bir organın koşusunun `26m:23-24`'ün söylediğine ulaşıp ulaşmadığını
  sına. Ulaşmıyorsa boşluk `koş`'u taşıyan partide, araç ulaşılamazsa kırmızı olan bir testle kapanır.

**Sahibin ipucu (bu kez kural esnetildi; 2026-11-23, E741; görev, reçete değil). Dersler büyür: bulma ve yeniden
sınama.**
- Olgu (beyin, `founder-ledger.jsonl`): 81 `lesson` satırı; 81'inin `recheck`'i var, hiçbirinin `scope`'u yok. İlk ders
  satırı 2026-11-18'dedir (`f1503`); o günün sonunda 9 ders vardı. Dersin alanları `22:25-33`'tedir (`scope` `22:29`);
  satırın yükü `{summary, refs[], recheck}`'tir (`26g:12`); başlatıcı en yeni 100 dersi listeler (`26g:48`).
- Olgu (beyin): `tests/lesson_recheck.py` yürürlükteki her dersin `recheck`'ini koşar, birer birer, defter sırasıyla
  (`tests/lesson_recheck.py:1`, `:25`). 20261123T201159Z oturumunda bu koşu oturumun kendi 25 dakikalık sınırına
  sığmadı, `f1972`'de durdu ve yeniden koşuldu (commit `0fa9ef6`'nın mesajı; defter satırı `f2082`).
- Görev: dersler büyüdükçe onları okumanın ve yeniden sınamanın maliyeti her oturumda bütün kümeyle büyümez, ve bir ders
  ilgili olduğu işe ulaşır. Nasıl olacağını sen tasarlarsın (`22`'nin kendi alanları, `26g`); ölçersin: oturum başına
  süre ve bağlam, korudukları işin andığı dersler. Yanlışlanabilir: bu görevle geçen 5 oturumdan sonra.

**Sahibin ipucu (bu kez kural esnetildi; 2026-11-23, E742; görev, reçete değil). Bağlam ölçülen bir kaynaktır.**
- Olgu: E676 (`00d:41-50`, 2026-11-20) arama tabanlı okumayı önerdi; beyinde onu kuran bir araç ve E676'yı adlandıran
  bir defter satırı yok.
- Olgu: 20261123T125013Z oturumu 2, 20261123T152245Z oturumu 3 kez sıkıştırıldı; ilk sıkıştırma oturumun damgasından
  9,7 ve 3,6 dakika sonradır; her sıkıştırmadan önce bağlam 166.725 ile 174.293 giriş tokenı arasındaydı
  (transkriptin `compact_boundary` olayı, `compact_metadata.pre_tokens`).
- Olgu: ölçüm aynası (`26o`, `26h:50-55`) bugüne kadar hiçbir sıkıştırma ya da bağlam olgusu taşımıyordu. Bu dönemden
  itibaren `mirror.json`'un `context` bölümü onları oturum başına verir (`26o` "Bağlam ve sıkıştırma").
- Görev: bu olguları okursun ve kararı sen verirsin; hiçbir tasarım verilmez. Yanlışlanabilir: bu görevle geçen 5
  oturumdan sonra aynanın `context` sayılarıyla.

- Korkuluklar (sahibin koşulu; dördü için bağlayıcıdır):
  1. Bu ipuçları hiçbir hakemi ya da denetimi gevşetmez ve tohumdan yeni bir hakem kuralı getirmez: E739 ve E740
     senin kendi kodunu var olan sayfalarla (`12:15-18`, `26m:23-24`) hizalar.
  2. Teslimde, E739 ve E740'ın sayfaların zaten istediği işin ötesinde hiçbir yeniden yapım istenmez; işin sırası
     `CHANGELOG-14`'ünkidir.
  3. Yanlışlanabilir: E739 ve E740 kendi testleriyle; E741 ve E742 5 oturumdan sonra aynanın ve defterin sayılarıyla.
