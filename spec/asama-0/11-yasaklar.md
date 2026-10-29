# Aşama 0 §0.11 — Yasaklar

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken
Çapa: beklemede: aşama 0 çıkış raporu

---

- Çalışma zamanında (B)'deki `llm.call` kanaryası dışında LLM çağrısı; LLM avcı, yargıç, dedektör,
  düzeltici; araç kullanan ajan; defter ve zincir dışında hafıza.
- Hedefe `refs/heads/brain/**` dışında yazmak; `main`'e yazmak; hedefe iş akışı ya da kimlik eklemek;
  kopyada Actions'ı açmak.
- Y3 (migration, manifest ya da kilit değişikliği, deploy, sır, feature flag); güvenlik yolu ve hariç
  yol yazımı, biçimleyici dahil (`tohum/04a`); güvenlik kodu düzeltmesi. Hariç yollar operatörün
  `excluded_paths`'ı ve hedefin ajan yapılandırmasıdır; Snowball onları düzenlemez ve yüklemez, yalnız veri
  olarak okur (`tohum/14`).
- Kurucu'nun hedef kodunu kendi makinesinde koşturması; aday hakemin yayımladığı araç çıktısından yazılır.
- Hakem kodunun yeri: Aşama 0 boyunca beyin reposunun `referee/` dizini, aktarımdan sonra hakem
  reposunun kökü. Beyindeki başka kod `referee/`'yi, `referee/` başka kodu import etmez.
- Hakem reposuna yazmak; önyükleme hakemini, tohum vektörlerini, tohum koltuklarını, `control.json`'u
  ya da anayasal politikayı değiştirmek; beyin push'unda ajan yapılandırması (`agent_config_modified`).
  Kurucu hakem reposunu okur, yazamaz.
- Vektöre ya da önyükleme hakemine özgü dal yazmak; testin koştuğunu algılayıp başka davranmak.
- Sırlı bir işte hedef kodu koşturmak; Actions önbelleği kullanmak.
- (A)'dan sonra `referee/`'ye dokunmak (`referee_changed_after_exit`); yalnız `candidates/` ve `targets/`
  değişebilir. Aşama 0 kapandıktan sonra hakem yalnız bir parti ya da aşama çıkışındaki operatör
  aktarımıyla değişir; önyükleme hakemi aktarımla değişmez, yalnız tohum dönemiyle.
