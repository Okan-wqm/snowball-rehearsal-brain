# Değişiklik Günlüğü — Tohum, 2.2'nin Yirminci Kayıtları

Tarih: 2026-11-24 · Sürüm: 2.2
Okunma: bir sayfanın geçmişi aranırken
Çapa: git geçmişi ve zincirdeki spec hash satırları

- 2.2 (2026-11-24, E744; tohum dönemi AL; kopya hedefin `census` vektörü, operatörün `29za:19-22` işi).
  **İlk iş** (`25` 10b). Teslimden itibaren önyükleme hakeminin hiçbir denetimi kırmızı olmaz: bu dönem bir vektör grubu
  ekler (`census_copy`), hiçbir tablo onu adlandırmaz ve bugün koşmaz; ne bir tablo, ne bir zorunlu politika yolu, ne
  hakemin kodu değişir. `vectors/`'ün hash'i değişir, teslim onu yeniden hesaplar (E678). Kurucu'nun bugünkü işi sürer,
  sırası `CHANGELOG-14`'ünkidir.
  Kopyanın `census` vektörü (E744): `vectors.json`'a `census_copy` grubu, 186 vaka, `census`'un biçimiyle (`python -m
  cases.build produce eslint <kural>`); kopyanın `base_sha`'sında (`4f47901`) dört birimin etkin ESLint kurallarının
  birleşimi, her vaka kuralın etkin olduğu birimleri adlandırır (operatör kararı, 2026-11-24). Arayüzü yeni `29zc`;
  `29za` sonuna tek paragraf, `29za:1-57` yer değiştirmedi; `29d` sonu `29zc`'yi gösterir. Kopyanın sayımı
  yine `29za:15-17`'nin koşuluyla geçer. Türetme `seed/bootstrap/local/census_copy.py` ve kaydı `census_copy.json`'dur.
  Yanıtlanan rapor yok. Gevşetme yok.
