# Aşama 1 §1.1 — Amaç

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 1 çalışırken
Çapa: beklemede: aşama 1 çıkış raporu

---

Döngüyü en basit hâliyle, en basit hata sınıfında, uçtan uca ve canlıda kapatmak:

```
lint adapter → düzeltici → aday paketi → hakem: çek, koş, çağır, yaz → kapı
  → brain/integration → nöbetçi → defter ve Rekor → sayfalar
```

Bu aşama yalnız **oyuncu organlarını** kurar. Hakem Aşama 0'da kuruldu, aktarıldı ve bu aşama
boyunca değişmez.

Keşifte LLM yoktur. LLM yalnız aracın kendi başına düzeltemediği bulguyu düzeltmek için girer ve
Sonnet'tir. Bu çağrı araçsızdır: hakemin `llm.call`'ı tek bir yapılandırılmış çıktı ister,
beynin deterministik uygulayıcısı onu yalnız hedef aralığa yazar. Bu yolda sandbox kaçışı yapısal
olarak imkânsızdır (katman 1, `tohum/23`).

Aşama 1'in sorusu "LLM bulur mu" değil, şudur: döngü kapanıyor mu, her dosyanın okuyucusu bir
kararı değiştiriyor mu, kapı ajan sözüne değil yeniden koşuya mı bakıyor.
