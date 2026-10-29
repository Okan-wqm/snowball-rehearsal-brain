# Aşama 4 §4.3 — Girişler

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: hedef taslak · Sahibi: operatör
Okunma: Aşama 4 çalışırken
Çapa: beklemede: aşama 4 çıkış raporu

---

- Aşama 3 PASS raporu. **Taban, property başınadır:** hakemin o property için taban avcı grep
  kümesi ile mevcut organların en iyisinin büyüğü. K0–K4 organları property eşleşmediği için K5
  vakalarında sıfır alır; taban onlar değildir.
- **Mühürlü depo ön koşuldur:** operatör onu kurulumun mühürlü depo satırıyla açar
  (`tohum/25a`); yazarı yalnız mühür App'idir.
- Property **P**: K5 vakaları arasından en çok `human_fix` vakası olan (`asama-0/05`); anlamsal
  lint kurallarının düzeltmeleri `rule_property_map` ile K5'e sayılır. Held-out, ileriye dönük
  havuzdan ≥ 25 `human_fix` vakası ve ≥ 10 grup ister; havuz dolana kadar verdict `UNMEASURABLE`'dır
  ve bekleme süresi raporda yazar. Mutasyonlar ayrı raporlanır, kapıya girmez.
- `properties/P.md`: yalnız doğruluk tanımı. Kalıp, dosya adı, fonksiyon adı, dekoratör adı,
  regex ya da "şunu ara" cümlesi yasaktır. Örnek, `missing-await` için:

  > Bir asenkron işlemin sonucu, işlem tamamlanmadan okunamaz, kaydedilemez ya da bir karara
  > girdi olamaz; hangi çağrıların asenkron olduğunu repodan çıkarmak avcının işidir.

- Repo haritası katmanları (a) ve (b); Aşama 2'den itibaren dersler (`tohum/22`). K6 sınırını
  harita katmanı (c) gelene kadar `profile.security_paths` tanımlar.
- Aşama 2 ve 3'ten gelmesi gerekenler: planlayıcı, harita (b), K1–K4 tabanları, mekanik
  dedektörler, `main` senkronu. Bu sayfa onların spec'leri yazılınca yeniden yazılır.
