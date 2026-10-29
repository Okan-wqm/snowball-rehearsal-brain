# Okuyucular, Devam: Hedefteki Durum Dosyaları

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: yeni durum dosyası, bölüm ya da görünüm eklerken
Çapa: her yazılan dosyanın satırı bu tabloda ya da `27`'dedir (tohumun spec denetimi ve `spec.lint` denetler)

---

`27`'nin okuyucu tablosunun devamıdır; aynı kural geçerlidir (Y4). Bu dosyalar hedefin `brain/state` ve
`brain/integration` dallarında ya da sonraki aşamaların depolarındadır. "Etkinleştirme" Aşama 0 (B)'dir.

| Dosya | Yazar | Okuyucu | Değişen karar | Açılış |
|---|---|---|---|---|
| `profile.json` (`units[]` dahil) | `profile.derive`, `unit.verify` | kapı, `run.contained`, tüm organlar | Araç, kapsam, birim tarifi | Etkinleştirme |
| `policy.json` performans | prosedür (`18`), `yaz` | her kapı | Dikkat ve sıra eşiği | P1 |
| `ledger.jsonl` `events` | hakem işleri | kapı, `stage-open`, P1'den Gözcü | Merge ya da ret, geri alma, kilit açılışı | Etkinleştirme |
| `ledger.jsonl` `cost` | `llm.call`, geçit | frenler, P1'den Gözcü | Fren duruşu | Etkinleştirme |
| `ledger.jsonl` `drill` | `exit.drill` | hakem, `stage-open` | Geri alma provasının kararı; yeteneğin canlıya girmesi | Etkinleştirme (geri alma provası) |
| `ledger.jsonl` `freeze` | Gözcü | kapı | Merge kapanır | P1 |
| `ledger.jsonl` `rival`, `accept` | döngünün `yaz`'ı, önyükleme hakeminin imzalı sonucundan | `gate.check` | İzin listesi | Aşama 1 (MF6) |
| `ledger.jsonl` `security`; hakem ve beyin kapsamı tohumda `seed/security-ledger.jsonl` | `yaz` (`security.run`, doğrulanmış bildirim); tohum satırlarını operatör oturumu `ledger.chain` ile | `gate.check`, güvenlik avcısı, Kurucu oturum başı, `status.block`, ders görünümü | Bekçi testi kırmızıysa ret; yeniden açma; avcının kapsamı; operatör uyarısı | P2; tohum dosyası 2026-10-29 (`30e`) |
| `security/profile.json` | `security.derive`, doğrulanmış bildirim | `security.run`, `security.scan`, güvenlik avcısı, `gate.check` | Hangi sınıf ve test koşar; hangi aday K6 | P2 (`30d`) |
| `security/tests/` | `yaz`, doğrulanmış bildirimden | `security.run` (`koş`) | Merge reddi; açığın kapanışı | P2 (`30d`) |
| `chain/root.jsonl` | `yaz` | `chain.verify`, `rekor.anchor`, sonraki D1 | Sert duruş | Etkinleştirme |
| `cases/` (dev) | `cases.build` | `harness.score`, Kurucu | Adapter değişikliği | P1 |
| `status.md` | `status.block`, `docs.render` | operatör | Kill switch | Etkinleştirme |
| `findings.jsonl` | hakem, adapter önerisinden | düzelticiler, kapı | İş kuyruğu | Aşama 1 |
| `unresolved.jsonl` | kapı | düzeltici seçimi | Aynı tabanda yeniden denememe | Aşama 1 |
| `runs/` | `koş`, `çağır` | `gate.check`, hash ile | Merge | Etkinleştirme |
| `docs/findings/`, `docs/organs/` | `docs.render`, `yaz` | operatör | Kill switch | Aşama 1 |
| Mühürlü depo, `ledger.jsonl` `looks` | mühür App'i, hakem exit | `harness.score` exit | Verdict, bakış bütçesi | İlk held-out havuzu |
| `map/edges.jsonl` | `map.build` | düzeltici, kapı | Etki kümesi | İlk `impact_miss` sinyali ya da K2 silmesi |
| İtibar görünümü, organ yaşam döngüsü, `genesis-queue.jsonl` | puanlayıcı, hakem, sinyaller | dispatcher, genesis, Kurucu | Sıra, yeniden yazım, taslak | Bir sınıfta ≥ 2 aday organ |
| Ders görünümü | `lessons.view` | planlayıcı, düzeltici | Yaklaşım | Aşama 2 |
| `contracts/` | organlar | organlar, kapı | Arayüz | İkinci ortak arayüz |
| `prompt-ledger.jsonl`, `fp-corpus.jsonl` | dispatcher, oracle | Kurucu, şerit yazarı, rakip kanaryası | Prompt sürümü, koltuk geri dönüşü | Aşama 4 |
| Eğitim deposu dalları | `yaz` | bilgi ve koşul görünümleri | Hipotez sırası | İlk eğitim hedefi |
