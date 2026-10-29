# Aşama 0 §0.4 — Hata seti

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken
Çapa: beklemede: aşama 0 çıkış raporu

---

**Kaynak, iki yol.** (1) Geçmişte lint kuralı ihlali düzelten commit'ler; commit türü filtresi
yoktur. (2) **Mutasyon:** aracın kural kataloğundan bilinen ihlaller temiz dosyalara
deterministik operatörlerle enjekte edilir. K0'da ana kaynak mutasyondur.

**Vaka ebeveyne sabitlenir.** Gerçek düzeltme F için `base_sha` F'nin ebeveynidir; snapshot o
ağaçtan çıkarılır, HEAD'e ters yama uygulanmaz.

**Geçerlilik.** Araç mutasyonlu ve mutasyonsuz ağaçta koşar; satırlar mutasyon hunk'ı üzerinden
eşlenir, böylece kayan satırlar yeni ihlal sayılmaz. Vaka, mutasyon bölgesinde **tam olarak bir**
yeni (kural, satır) ihlali doğuyorsa geçerlidir; birden fazla ihlal doğuran mutasyon reddedilir.
Zaten kırmızı projelerde ölçü "araç kırmızı" değil, bu farktır.

**Sınıf etiketi.** `class_level` deterministik haritayla verilir. Profildeki `rule_property_map`,
anlamsal lint kurallarını K0'a değil, ilgili K5 property'sine bağlar; böylece K5 havuzu aç kalmaz.

**Provenance.** `human_fix`, `mutation`, `system_tp`, `system_regression`. Sistemin ürettiği
vakalar aynı organ soyunun ölçümüne ve hiçbir çıkış kapısına girmez (`tohum/19`).

**İş deseni.** Aracı koşturan her adım `koş`ta, sırsız ve ağsız koşar; seçim ve puanlama hakem
kodudur (`tohum/08` 1). Kurucu `cases.build`'i yalnız dev için, oyuncak repoda çağırabilir.

**Dev seti.** Etkinleştirmede gerçek hedef için kurulur, `<state_root>/cases/`'e yazılır ve
Kurucu'ya vaka bazında açıktır. Bölme modül grubuna göredir.

**K0 çıkış örneklemi, held-out havuzu değil.** K0 için mühürlü bir havuz tutulmaz. `exit.sample`
her çıkış isteğinde, adapter SHA'sı pinlendikten sonra gizli tohumla taze bir örneklem çeker:
profildeki etkin kataloğun mutasyonla üretilebilen **her kuralı** ve her araç zinciri için en az bir
vaka, dev gruplarının dışındaki en az `stage_params.census_min_groups` (45) ya da mevcut modül grubundan. Ölçü kural sayımıdır: sıfır
kaçırma. Deterministik bir sarıcıda kaçırma örneklem gürültüsü değil, o kuralın sarma kusurudur;
CP alt sınırı raporlanır, kapılamaz (`tohum/19`). Seçici kod Aşama 0 çıkışında donar.

**Held-out havuzu.** İlk held-out havuzu ve mühürlü depo Aşama 4'ün ön koşuludur; bakış bütçesi,
ileriye dönük kesim ve üyelik testi onunla gelir (`asama-4/03`).
