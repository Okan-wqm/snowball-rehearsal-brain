# Görev Haritası, Devam: Sahibin İpuçları II

Tarih: 2026-11-20 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: her oturumda, görev seçilirken (`00c`'nin devamı)
Çapa: elle yazılır; `00c` 80 satıra yaklaştığı için (`15` 1) ipuçları burada sürer

---

**Sahibin ipucu (2026-11-20, E654; ipucu, reçete değil). Derslerin kendiliğinden yeniden sınanması.**
- Olgu (2026-11-20): defterde 26 `lesson` satırı var. Hepsinin bir `recheck`'i var, hepsi `trust: inferred`, hiçbiri
  bağımsız olarak yeniden koşturulmadı. `26g` gereği başlatıcı ve hakem `recheck`'i koşturmaz. Bugün dersleri yeniden
  sınayan bir şey yoktur.
- Amaç: sahip ilkesi (2026-11-06) her dersin yeniden sınanan, yanlışlanabilir bir kayıt olmasıdır. Yanlış bir ders
  sessizce kalmamalı.
- İpucu: dersler otomatik ve düzenli olarak yeniden sınansın; sonucu derse geri yazılsın (hâlâ tutuyor mu, ne zaman
  tutmadı, `closes:` ile kapanma). Ne zaman koşacağı, nerede koşacağı ve sonucun nasıl kaydedileceği Kurucu'nun
  tasarımıdır. Tohumda bir değişiklik gerekiyorsa Kurucu bunu bir rapor olarak önerir.
- Ölçülür: kaç ders yeniden sınandı, kaçı tuttu, kaçı kapandı.

**Sahibin ipucu (2026-11-20, E665; ipucu, reçete değil). Partiler amaçta da yanlış olabilir.**
- Olgu: parti tabloları (`asama-1/13` ve aşama sayfaları) Aşama 1'den önce operatörce yazıldı. Bugüne kadarki her
  rapor metnin kendisiyle tutarlı olup olmadığını sordu; hiçbiri bir maddenin aşamasının amacına hizmet edip
  etmediğini sormadı.
- İpucu: bir parti maddesinin aşamasının amacına hizmet etmediğine, yanlış sırada olduğuna, başka bir maddeyi tekrar
  ettiğine ya da bir maddenin eksik olduğuna kanıtın varsa, kanıtıyla ve bir öneriyle (çıkar, yeniden sırala,
  birleştir ya da ekle) bir `spec_issue` raporu yaz (`26c`). Yanıtı operatör verir. f1677'nin dediği gibi rapor bir
  izin değildir: yanıttan önce kendi okumanı kurmazsın.

**Sahibin ipucu (2026-11-20, E666; ipucu, reçete değil). Kaybolan oturum açıklanacak bir olgudur.**
- Olgu: 20261120T011313Z oturumu 137 çıkış koduyla bitti ve işi kayboldu (56,9 dakika, push yok, defter satırı yok);
  sonraki oturumun `previous-session.json`'u bunu kaydetti.
- İpucu: nedeni okuyabildiğin kanıttan bul. Neden beynin içindeyse yeniden sınamasıyla bir ders olarak yaz (`26g`);
  dışındaysa bir rapor yaz.

**Sahibin ipucu (2026-11-20, E667; ipucu, reçete değil). Ajanlar.**
- Olgu: E643 ajan istedi (`00b`). Altı oturum sonra beynin `agents/` dizini boştur; ölçüm aynasının `delegation`
  sayısı 0'dır.
- İpucu: ya ilk ajanı tanımla (`24a` "Ajan ve skill tanımları") ya da neden henüz olmadığını, ne zaman olacağını
  söyleyen yanlışlanabilir bir koşulla kaydet.
