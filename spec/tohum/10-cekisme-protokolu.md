# Çekişme Protokolü: Her Artefakt İçin

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: her artefakt üretildiğinde
Çapa: faz kararları ve oracle sonuçları defterde

---

Bu protokol tek bir yerde yazılır ve her artefakta uygulanır: spec, property tanımı, bulgu,
düzeltme, doküman, adapter, maliyet basamağı, memory türü, yeni ajan, harita kenarı, örüntü
önerisi, eşik değişikliği, harness değişikliği. Şekli her yerde aynıdır; yalnız oracle değişir.

**Şekil.** Bir üretici artefaktı yazar. Üç koltuk onu beş fazda çekiştirir: **Savcı** artefaktın
gerekli ve doğru olduğunu, **Savunma** gereksiz, yanlış ya da zararlı olduğunu, **Uygulayıcı
temsilcisi** neye mal olacağını ve neyi bozacağını kanıtlamakla yükümlüdür. Her fazda kararlar
yapılandırılmış çıktı olarak (`{decision, refs[], sentence}`) mühürlenir, sonra açılır; faz başına
en fazla iki tur. Son sözü hiçbir zaman oy değil, o artefaktın yürütme oracle'ı söyler. Üretici
koltuklardan hiçbirine oturamaz (Y6); koltuk modelleri `09a`'ya uyar.

**Tasarımda alternatif yükümlülüğü.** Artefakt bir tasarımsa (yeni organ, örüntü önerisi, kalıcı
düzeltmenin biçimi, doküman yapısı) ve tek bir kaynaktan geliyorsa (başka bir repodan kalıp ya da
bir modelin önerisi), Savunma yalnız çürütmekle kalmaz: kendi bilgisinden, referanslı en az bir
alternatif önerir. Soru "hangisi doğru" değil "ikisinden daha iyisi var mı"dır. Adaylar aynı
oracle'la yan yana koşar; kazananı yürütme seçer. Her öneri `origin` taşır (`repo_pattern`,
`llm_prior`, `synthesis`, `own_outcome`) ve hayatta kalma oranı kaynak ve koşul başına ölçülür
(`11`, `21`). Kopyalanan şey ölçülmemiş bir tercihtir.

| Faz | Soru |
|---|---|
| 1 Varlık | Artefakt iyi biçimli mi, referansları snapshot'ta var mı, kendi çıktısına mı dayanıyor. Mekanik, bedava |
| 2 Gereklilik | Bunu isteyen ölçülmüş bir boşluk ya da gerçek bir yol var mı (Y5) |
| 3 Sonuç | Kabul edilirse ne değişir, kim görür; kasıt ya da konvansiyon mu |
| 4 Etki ve maliyet | Etki kümesinde ne var, ne bozulabilir, değer / USD ne, katman iddiası tutuyor mu |
| 5 Yürütme | Oracle koşar ve karar verir |

**Artefakt başına oracle.**

| Artefakt | Faz 5 oracle'ı |
|---|---|
| Aşama spec'i, property spec'i | `spec.lint` (yapı, `required_exit_rows`, kalıp sızıntısı); sonra o aşamanın çıkış testi |
| Bulgu (K5 ve üstü) | Üreme testi: kırmızı → düzeltme → yeşil, etki kümesi yeşil (`04a`) |
| Bulgu (K0–K2, K4) | Aracın yeniden koşusu ve mandal (Y8, `03`) |
| Düzeltme, PR | Aynı test ya da araç + etkilenen-test komutu + diff-guard; K5'ten sonra ikinci panel diff üzerinde |
| Doküman (K8) | Her iddia koda çapalı; çapa çözülür; mekanik denetlenebilir iddialar koda karşı doğrulanır |
| Adapter, dedektör | Harness: deterministik sınıfta kural sayımı sıfır kaçırma; LLM sınıfında held-out recall ve clean precision alt sınırları tabanı geçer (`19`) |
| Maliyet basamağı | Aynı vakalarda eşli, tam non-inferiority, δ = 0,05, n ≥ 45; bütün maliyet daha düşük (`06`) |
| Memory türü, ders, harita katmanı | Okuyucusu ölçülmüş bir hata oranını düşürür (Y5); yoksa canlı yoldan çıkar |
| Örüntü önerisi | Sandbox deneyinde ölçülen fayda; hedefte uygulanabilirlik koşulları sınanmış (`21`) |
| Yeni ajan | Ölçülmüş boşluk pencerede küçülür |
| Repo haritası kenarı | İki ucu snapshot'ta doğrulanır; stale kenar yeniden doğrulanır |
| Eşik ve harness değişikliği | Dev arşivinde yeniden oynatma: geçmiş skoru yükseltmez, geri alınmışı geçirmez |

**İki sınır.** Oracle yoksa panel yoktur; artefakt `blocked`'dır (Y8). Araç karar veriyorsa
panel yoktur; K0–K2 ve K4'te yargıç aracın kendisidir, panel mekanik kararın bittiği yerde
başlar.

**Açık fazlar aşamaya göredir.** Aşama 0 ve 1'de yalnız faz 1 (mekanik), tek rakip (tohum rakibi)
ve faz 5 çalışır; Aşama 1 düzeltmelerinde rakip yoktur, çünkü oracle aracın kendisidir. Bir
aşamanın açık fazları onun spec'inde yazar ve genesis o fazlarla yetinir (`12`).

**Panelin maliyet merdiveni.** Faz 1 mekanik ve bedava; faz 2 repo haritası varsa çoğunlukla
mekanik; faz 3 ve 4'ün modelleri `09a`'daki ayrıklık kuralıyla belirlenir; faz 1–2 en ucuz
modelde koşabilir. Bulguların çoğu faz 1 ve 2'de sıfır maliyetle ölmelidir.
