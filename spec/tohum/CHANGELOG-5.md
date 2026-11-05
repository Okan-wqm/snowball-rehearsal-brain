# Değişiklik Günlüğü — Tohum, 2.2'nin Dördüncü Kayıtları

Tarih: 2026-11-04 · Sürüm: 2.2
Okunma: bir sayfanın geçmişi aranırken
Çapa: git geçmişi ve zincirdeki spec hash satırları

- 2.2 (2026-11-02, E507; Kurucu raporu): `26e`: bir modülün ilk adı Python'un standart kütüphanesinde bir modülün adı
  olamaz (`sys.stdlib_module_names`); hakem komutu `referee/` `sys.path`'te önde koşar ve o ad standart modülü gizler;
  böyle satırı olan tablo yüklenmez. Aşama 0'ın donmuş tablosundaki `profile` (MF4, MF6) kuraldan önce gelir, o tablo
  yeniden açılana kadar kalır. Yanıtlanan rapor: `spec-011-profile-shadows-stdlib` → `26e:33-37` (hakemin hiçbir
  komutu `cProfile`'ı çağırmaz; Aşama 0'ın yolu kalır). 80 satır sınırı için 2026-11-01 E421–E436 kaydı
  `CHANGELOG-4.md`'ye taşındı.
- 2.2 (2026-11-02, E506; sahibin kararı, boşluk D): `24a` "Kurucu": kapsülde defterin salt-okur dizini
  `/opt/founder/ledger_index.py` vardır (imajla gelir, beyne gelmez; tohumun ekleme aracı yine yoktur). 80 satır
  sınırı için 2026-11-01 E450 kaydı `CHANGELOG-4.md`'ye taşındı.
- 2.2 (2026-11-01, E470–E475; dördüncü şüphecinin bulgusu; sahibin yetkisiyle mimari karar): `25a` 1–2 içe aktarmayı
  git nesneleriyle anlatır: hakem reposu çıplak klonlanır, yeni `main` pinli `referee/` ağacı ile `main`'den tam adıyla
  alınan korunanlardan kurulur, her ad nesne yazılmadan denetlenir (`26c`, sonda nokta ya da boşluk, aygıt adı, `~` ve
  rakam, korunanın harf varyantı, harf duyarsız tek ad), sayaç satırı aynı commit'tedir, oyuncak ve hakem zorlamadan
  itilir; çalışma ağacı yoktur. `26d`: `stage-open` klonun commit'indeki hakem ağacını ve genesis'in ağaç ve sonuç
  hash'lerini aktarım satırına bağlar, kopyanın tabanı vardır, profil okunabilir olmalıdır, kaydın verisinin hash'i
  kökün kendisidir; `26a` `rekor.anchor` bunu söyler.
- 2.2 (2026-11-01, E411–E417; üçüncü şüphecinin bulgusu): `26d`'ye olgular: son kökün Sigstore paketi döngünündür ve
  kök satırının yanında, aynı `brain/state` commit'inde `<state_root>/chain/<kök>.sigstore.json`'dadır (`stage-open`
  oradan okur; `27a`); `<state_root>` `01a`'nın `.brain/`'idir, başka bir `state_root` tohum dönemi ister (E417, sahibin
  yetkisiyle operatör kararı); zincirli satırın kuralları (son satır da LF ile biter,
  CR yok, anahtar iki kez yok); kök Rekor v1 `hashedrekord`'dur (`sigstore` 4.5.0 `sign --rekor-version 1`; bayraksız en
  yüksek sürüm, v2). Genesis satırı `events`, `kind: genesis`, hakemin kendi satırı; (B)'nin koştuğu genesis defterin
  son genesis'idir ve kural yalnız ondan sonrakileri sayar: yeniden aktarım kilidi kapatmaz (`25a` "Başarısızlık").
  Öneri, `proposed_by`'ı boş olmayan dizgi olan satırdır. `00b`: `26c` ve `26d` üç görevde okunur. 80 satır sınırı için
  2026-10-31'in dört kaydı daha `CHANGELOG-3.md`'ye taşındı (`main`'le birleşince orada).
