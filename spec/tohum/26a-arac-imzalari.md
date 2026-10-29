# Araç İmzaları: Aşama 0 ve 1

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: araç yazarken ve çağırırken
Çapa: beklemede: aşama 0 — hakem ve beyin MCP araç tanımları

---

Her araç `{input, output, side_effects, allowed_callers}` ile tanımlıdır; `allowed_callers` boş
araç yoktur. "İş" sütunu aracın hangi hakem işinde koştuğudur (`08` 1): `çek` okuyucu App'iyle
çeker, `getir` bağımlılık getirir, `koş` sırsız ve ağsızdır, `çağır` model çağrısı yapar, `yaz`
yazar App'ini tutar. Oyuncu kodu yalnız `koş`ta koşar; sırlı işler oyuncu kodu koşturmaz.

| Araç | Yer | İş | Girdi | Çıktı | Yan etki | Çağıran |
|---|---|---|---|---|---|---|
| `exit.sample` | Hakem | `çek` | sınıf, gizli tohum, profil | çıkış vakaları (kural sayımı) | yok; aşama çıkışında donar | hakem exit |
| `exit.drill` | Hakem | `çek`, `yaz` | prova türü, aile listesi, gizli tohum | oyuncak hedefte örnekler; önce taahhüt hash'i, koşudan sonra cevap anahtarı | `drill` satırları; provaya konan organlar `planted: true` | hakem exit (`22a`, `12a`) |
| `cases.build` | Hakem | `çek` | sınıf, kaynak (geçmiş, mutasyon) | dev vakaları | `cases/` önerisi | hakem; Kurucu yalnız dev |
| `snapshot.make` | Hakem | `çek` | `base_sha`, vaka listesi, tür | `snapshot_id`, manifest | kısa ömürlü dizin | hakem; Kurucu dev |
| `harness.score` | Hakem | `yaz` | bulgu dosyası, `snapshot_id` | harness raporu (`26b`) | rapor | Kurucu dev; hakem exit |
| `harness.baseline` | Hakem | `çek` | `snapshot_id`, property | bulgu dosyası | yok | hakem |
| `spec.lint` | Hakem | `koş` | spec dizini, `required_exit_rows` | ihlal listesi | yok | Kurucu, `brain.accept`, `lock.check` |
| `ledger.append` | Hakem | `yaz` | bölüm, satırlar | `row_hash`'ler | döngü başına tek `brain/state` commit'i | hakem işleri |
| `chain.verify` | Hakem | `yaz` | dal ya da commit; yalnız-ekleme için önceki sürüm (`--previous`) | geçerli / kırık satır | kırıksa sert duruş | herkes |
| `rekor.anchor` | Hakem | `yaz` | kök hash | Rekor kayıt kimliği | Rekor'a ekleme | `ledger.append` |
| `secrets.scan` | Hakem | `çağır`, `yaz` | diff, satır, prompt | eşleşmeler | koşuyu geçersiz kılar | `llm.call`, `gate.check`, `ledger.append` |
| `drift.check` | Hakem | `yaz` | kurulum özeti | fark | sert duruş | hakem döngü başı |
| `profile.derive` | Hakem | `çek` | hedef ağacı | profil | yok | etkinleştirme, `brain.accept` |
| `deps.fetch` | Hakem | `getir` | lockfile'lar, profil | içerik adresli artefakt, lisans raporu (`24`) | izinli olmayan lisans adayı kırmızı yapar | hakem |
| `run.contained` | Hakem | `koş` | komut, ağaçlar, artefaktlar | sonuçlar ve hash'leri, ölçülen `files_read` | yok | hakem |
| `llm.call` | Hakem | `çağır` | tipli girdi, şablon, model, bütçe belirteci | yapılandırılmış çıktı, sunulan model, maliyet | `cost` satırı | `fixer.llm` adına hakem |
| `agent.dispatch` | Hakem | `koş` + geçit | rol, prompt, araç listesi | çıktı, `run_meta` | yok | hakem (rakip; sonra her ajan) |
| `gate.diffguard` | Hakem | `yaz` | diff, profil, politika | ret nedenleri | yok | `gate.check` |
| `gate.check` | Hakem | `yaz` | aday, `koş` sonuçları | karar | PR, durum kontrolü, merge | hakem döngüsü |
| `sentinel.run` | Hakem | `koş` | `brain/integration` başı | etkilenen test sonuçları | yok | her merge sonrası |
| `gate.revert` | Hakem | `yaz` | merge SHA'sı, `cause` | geri alma | PR ve merge | `sentinel.run` kırmızısı |
| `gozcu.evaluate` | Hakem | `yaz` | defter görünümleri | dondurma, işaret | `freeze` satırı | hakem döngü sonu |
| `status.block` | Hakem | `yaz` | dondurma, bütçe, insan dokunuşu | `status.md` üst bloğu | `brain/state` | hakem döngü sonu |
| `lock.check` | Hakem | `yaz` | aşama, spec hash, çıkış satırı | kilit açık / kapalı | `events` satırı | aşama geçişi |
| `brain.accept` | Hakem | `yaz` | beyin SHA'sı, `koş` sonuçları, rakip satırı | kabul / ret | `accept` satırı | hakem yoklaması |
| `profile.propose` | Beyin | `koş` | hedef ağacı | profil önerisi | yok | Kurucu, etkinleştirme |
| `lint.discover` | Beyin | `koş` | `snapshot_id`, profil | bulgu dosyası | yok | hakem döngüsü |
| `fixer.range` | Beyin | `koş` | bulgu | worktree diff'i | worktree | hakem döngüsü |
| `fixer.llm` | Beyin | `koş` | bulgu, `llm.call` çıktısı | worktree diff'i | worktree | hakem döngüsü |
| `candidate.publish` | Beyin | `koş` | bulgu, diff | aday paketi | `candidates/<id>/` çıktısı | düzelticiler |
| `docs.render` | Beyin | `koş` | defter görünümleri | sayfa önerileri | yok | hakem döngü sonu |
| `docs.index` | Beyin | `koş` | spec ve `docs/` dizini | `INDEX.md` önerisi | yok | Kurucu, hakem döngü sonu |

**Aday paketi** `{finding, diff, organ_ids, definition_sha256[]}`'dir. Çalışma zamanında `koş`
işinin çıktı ağacındaki `candidates/<id>/`'ye yazılır ve hakem onu artefakt kimliğiyle okur;
beyin reposundaki `candidates/` aynı biçimde Kurucu'nun yayımladığı adayları ve etkinleştirmenin
hazır iyi ve kötü adaylarını tutar. Hakem hiçbir adaya yeniden koşturmadan güvenmez.

**İlk çağıranıyla açılanlar.** `chain.asof` (ilk zamansal sorgu okuyucusu), `map.build` (ilk
`impact_miss` sinyali ya da K2 silmeleri), `oracle.run` (Aşama 4, K5 test oracle'ı),
`reputation.score` (bir sınıfta ≥ 2 aday organ), `lessons.view` (Aşama 2 planlayıcısı),
`genesis.queue` (bir sınıfta ≥ 2 aday), `main.sync` (Aşama 2), `seal.rotate` (ilk held-out havuzu),
`exit.drill` (ilk prova: merge getiren aşamanın geri alma provası).

Beyin araçlarının yazdığı her şey bir öneri ya da worktree'dir; `brain/state`'e ve hedefe yalnız
`yaz` işi yazar.
