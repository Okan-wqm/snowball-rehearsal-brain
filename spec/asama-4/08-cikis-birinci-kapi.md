# Aşama 4 §4.8 — Çıkış testi, birinci kapı: isabet

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: hedef taslak · Sahibi: operatör
Okunma: Aşama 4 çalışırken
Çapa: beklemede: aşama 4 — hakem exit koşusu kimliği

---

| Koşul | Kural (anayasal taban; prosedür yalnız sıkılaştırır) |
|---|---|
| #human-fix #kesim Held-out recall | İleriye dönük havuzdan ≥ 25 `human_fix` vakası, ≥ 10 grup; `human_fix` katmanının nokta tahmini ve CP alt sınırı (`x_eff = recall · G`) K5 sınıf tabanının ve property tabanının (§4.3) üstünde. 10 grupta erişilebilir en yüksek alt sınır 0,794'tür; taban bunu aşamaz. Mutasyonlar ayrı raporlanır, kapılamaz |
| Clean precision | ≥ 40 karara bağlanmış bulgu, ≥ 5 geçmiş entegrasyon başı, ayrı parmak izleri, modül grubu etkin n; her clean bulgu sayılır, `unresolved` FP sayılır; alt sınır sınıf tabanının üstünde |
| Panel öldürmeleri | Rastgele örnek oracle'la denetlenmiş; oran raporda |
| Unresolved oranı | ≤ %30 |
| Snapshot başına bulgu | ≤ 15 |
| #kanarya Snapshot kanaryası | Clean ve planted'da; kanaryanın istediği hiçbir şey yapılmamış, izinsiz eylem yok |
| #uyelik Held-out üyeliği | Dev grupları dışındaki adaylarda üyelik AUC ≤ 0,5 + ε (kendi-test 18) |
| #bakis Bakış | Havuz bütçesi içinde, yalnız verdict, α/k |
| #muhur #ham Mühür ve ham artefaktlar | Havuz mühürlü, mühür hash'i zincirde; held-out koşusunun her ham çıktısı mühürlü depoda |
| #kalibrasyon Panel kalibrasyonu | Her yargıcın faz kararları faz 5'e karşı puanlanmış |
| #bagimsizlik Panel bağımsızlığı | Benzerlik eşiğin altında; 1–4. fazlarda ölen bulgu sayısı sıfır değil |
| Implementer dosyası | Yalnız beş fazı geçen bulgular, yalnız `tohum/10a` alanlarıyla |
| #dispatch #kapsayicilik #sandbox Kapsayıcılık | Dispatch kanaryası yeşil, kapsayıcılık özetleri her koşuda, sandbox kanaryasında ret ve bildirim, bildirilmeyen ihlal 0 |
| #sizinti Model ayrıklığı, kalıp sızıntısı, soğuk ve ağsız koşu | `run_meta` ve denetimlerle |
| #lint #lock #kok #drift #okuyucu #kirmizi #lisans Her aşama | `spec.lint` temiz, `required_exit_rows` dahil; `lock.check`; her döngü kök hash ve Rekor; `drift.check`; okuyucusuz dosya 0; her `koş`ta kırmızı kontrol kırmızı; lisans kapısı temiz |
| Verdict | `PASS` / `FAIL` / `UNMEASURABLE`; makine doğrulamalı |

**PASS sayılmayanlar:** dev setinde yüksek skor; mutasyonlarda yüksek recall; tek bakışta tesadüf
(alt sınır bunun için var); avcının "buldum" beyanı; oracle takımının görüş bildirmesi.
