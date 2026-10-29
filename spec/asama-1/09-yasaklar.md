# Aşama 1 §1.9 — Yasaklar

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 1 çalışırken
Çapa: beklemede: aşama 1 çıkış raporu

---

- Keşifte LLM. Yeni lint kuralı yazmak. Birden fazla sınıf.
- Düzelticinin bulgu dosyası, `fix` aralığı ya da test yolları dışına yazması.
- Tek PR'da birden fazla bulgu.
- Araç yapılandırmasını gevşetmek, kural kapatmak, bastırma yorumu eklemek; `gate.diffguard`
  reddeder ve ret `events` bölümüne yazılır.
- Güvenlik yollarına dokunmak, `--fix` dahil.
- `main`'e dokunmak; `main`'i `brain/integration`'a senkronlamak.
- **Hakeme yazmak.** Bu aşamada hakem reposu, `referee/` aday alanı, tohum vektörleri, tohum
  koltukları, `control.json` ve anayasal politika değişmez. Hakem değişikliği gerektiren her bulgu
  `blocked` olur ve bir sonraki aşama çıkışının aktarım listesine yazılır.
- Çalışma zamanında araç kullanan ajan. Sonnet düzelticisi araçsızdır.
- Sırlı bir işte oyuncu ya da hedef kodu koşturmak.
- §1.12'de açılış tetiği yazan parçaları tetik doğmadan kurmak (Y4).
