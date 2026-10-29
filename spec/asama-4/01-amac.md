# Aşama 4 §4.1 — Amaç

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: hedef taslak · Sahibi: operatör
Okunma: Aşama 4 çalışırken
Çapa: beklemede: aşama 4 çıkış raporu

---

Elinde hata kalıbı olmayan, yalnız bir doğruluk özelliğinin tanımını bilen tek bir LLM avcısının,
bu repoda o özelliğin ihlallerini bulabildiğini harness ile kanıtlamak; sonra aynı isabeti daha
ucuza tutan en düşük basamağı bulmak. Sınıf K5: mantık hataları.

Aşama 4 iki sorunun ölçülmüş cevabıdır: "LLM kalıpsız gerçek hata bulur mu" ve "bulduğunu ne
kadar ucuza tekrar bulur". Bu sayfa hedef taslaktır; Aşama 3 PASS alınca yeniden yazılır ve donar.

Aşama 4 üç şeyi ilk kez canlıya alır, çünkü ilk okuyucuları buradadır:

- **İlk held-out havuzu ve mühürlü depo.** Önceki sınıflar deterministik sarıcıdır ve kural
  sayımıyla ölçülür; LLM avcı örneklemle ölçülür ve gizli bir havuz ister (`tohum/19`).
- **Çalışma zamanında araç kullanan ilk ajan.** Sağlayıcı geçidi, kapsayıcılık özetleri ve
  sandbox kanaryası burada zorunlu olur (`tohum/08`, `tohum/24`).
- **İlk panel ve test-yazıcı.** Savunma ve Uygulayıcı temsilcisi koltukları şerit yazarının
  taslağıyla doğar; test-yazıcı tohum koltuğu ilk çağıranında kurulur ve donar (`tohum/09a`).
