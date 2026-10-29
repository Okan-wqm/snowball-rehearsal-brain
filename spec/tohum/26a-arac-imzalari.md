# Araç İmzaları: Aşama 0 ve 1

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: araç yazarken ve çağırırken
Çapa: beklemede: aşama 0 — hakem ve beyin MCP araç tanımları

---

Her araç `{input, output, side_effects, allowed_callers}` ile tanımlıdır; `allowed_callers` boş
araç yoktur. "İş" sütunu aracın hangi hakem işinde koştuğudur (`08` 1): `çek` kimliksiz (özel
hedefte okuyucu App'iyle) çeker, `getir` bağımlılık getirir, `koş` sırsız ve ağsızdır, `çağır` model
çağrısı yapar ve iç kullanımda araç kullanan ajanı yalnız hakemin MCP araçlarıyla koşar (`08` 5), `yaz`
yazar App'ini tutar. Oyuncu kodu yalnız `koş`ta koşar; sırlı işler oyuncu kodu koşturmaz. "Gelir"
sütunu aracı getiren mikro özelliği (`asama-0/14`) ya da partiyi (`asama-1/13`) adlandırır; taşınan araç
ilk okuyucusundan hemen önceki partiyle gelir, Aşama 0'da çağrılmaz.

| Araç | Yer | İş | Girdi | Çıktı | Yan etki | Çağıran | Gelir |
|---|---|---|---|---|---|---|---|
| `ledger.chain`, `chain.verify` | Hakem | `çek`, `yaz` | satır; dal ya da commit, yalnız-ekleme için önceki sürüm (`--previous`) | `row_hash`; geçerli / kırık satır | kırıksa sert duruş | herkes | Aşama 0 MF1 |
| `secrets.scan` | Hakem | `çağır`, `yaz` | diff, satır, prompt | eşleşmeler | koşuyu geçersiz kılar | `llm.call`, `gate.check`, `ledger.append` | MF2 |
| `run.contained` | Hakem | `koş` | komut, ağaçlar, artefaktlar, birim imajı ve sınırları | sonuçlar ve hash'leri, ölçülen `files_read` | koşu başına taze host dizini | hakem | MF3 |
| `profile.derive` | Hakem | `çek` | hedef ağacı, `targets[]` | profil, `units[]` adayları, hariç yollar | yok | etkinleştirme, `unit.verify` | MF4 |
| `deps.fetch` | Hakem | `getir` | tarifteki kilitler (Aşama 0'da npm) | içerik adresli artefakt, lisans raporu (`24`) | ürüne giren bağımlılıkta izinsiz lisans kırmızı | hakem | MF5 |
| `unit.verify` | Hakem | `koş` | tarif (`26c`), ağaç, `deps` | doğrulanmış tarif ya da ret; 3/3 sonuçları | `limit_hit:<anahtar>` | genesis; kilit değişince | MF6 |
| `gate.diffguard` | Hakem | `yaz` | diff, profil, tarif, politika | ret nedenleri | yok | `gate.check` | MF7 |
| `gate.check` | Hakem | `yaz` | aday, `koş` sonuçları, `control.json` | karar (`asama-0/08`) | `events` satırı | hakem döngüsü | MF8 |
| `target.write` | Hakem | `yaz` | dal, PR, check, merge ya da geri alma isteği | ref'ler | yalnız `refs/heads/brain/**`, GitHub REST ve Git Data API | `gate.check`, `gate.revert`, `ledger.append`, etkinleştirme | MF9 |
| `ledger.append` | Hakem | `yaz` | bölüm, satırlar | `row_hash`'ler | devir başına tek `brain/state` commit'i | hakem işleri | MF10 |
| `rekor.anchor` | Hakem | `yaz` | kök hash | Rekor kayıt kimliği | Rekor'a ekleme | `ledger.append` | MF11 |
| `sentinel.run` | Hakem | `koş` | `brain/integration` başı | etkilenen test sonuçları | yok | her merge sonrası | MF12 |
| `gate.revert` | Hakem | `yaz` | merge SHA'sı, `cause` | geri alma | `target.write` ile commit | `sentinel.run` kırmızısı | MF13 |
| `exit.drill` | Hakem | `yaz` | prova türü, aile listesi, gizli tohum | önceki devirde taahhüt hash'i, koşudan sonra cevap anahtarı | `drill` satırları; provaya konan organlar `planted: true` | hakem (`22a`, `12a`) | MF14 (yalnız `revert`); ders provası Aşama 2 |
| `llm.call` | Hakem | `çağır` | tipli girdi, şablon, model, çağrı başı tavan (iç kullanımda `--max-budget-usd`; satışta API anahtarı ve bütçe belirteci) | yapılandırılmış çıktı, sunulan model, maliyet | `cost` satırı | (B) kanaryası; Aşama 1'den `fixer.llm` adına hakem | MF15 |
| `status.block` | Hakem | `yaz` | defter (devir, son karar, taban yaşı, fren, insan dokunuşu) | `status.md` üst bloğu | `brain/state` | hakem devir sonu | MF16 |
| `activate` | Hakem | `koş`, `yaz` | hedef, `targets[]`, hazır adaylar | genesis satırı, `brain/integration` kesimi, mandal tabanı | `brain/state` | operatörün ilk devri | MF18 |
| `snapshot.make` | Hakem | `çek` | `base_sha`, vaka listesi, tür | `snapshot_id`, manifest | kısa ömürlü dizin | hakem; Kurucu dev | P1 |
| `cases.build` | Hakem | `çek` | sınıf, kaynak (geçmiş, mutasyon) | dev vakaları | `cases/` önerisi | hakem; Kurucu yalnız dev | P1 |
| `harness.score` | Hakem | `yaz` | bulgu dosyası, `snapshot_id` | harness raporu (`26b`) | rapor | Kurucu dev; hakem exit | P1 |
| `drift.check` | Hakem | `yaz` | kurulum özeti | fark | sert duruş | hakem döngü başı | P1 (Aşama 0'da genesis'te bir kez) |
| `gozcu.evaluate` | Hakem | `yaz` | defter görünümleri | dondurma, işaret | `freeze` satırı | hakem döngü sonu | P1 |
| `agent.dispatch` | Hakem | `çağır` (iç kullanımda `claude` CLI'si; satışta `koş` + geçit, `08` 5) | rol, prompt, hakemin MCP araç listesi | çıktı, `run_meta` | yok | hakem (güvenlik avcısı; sonra her ajan) | P2 |
| `security.derive` | Hakem | `çek`, `koş` | hedef ağacı, `profile.json`, göç uygulanmış test veritabanı | güvenlik profili (`30d`); öneri yalnız ekler | `security/profile.json` | her döngü | P2 |
| `security.scan` | Hakem | `getir`, `koş` | kilit dosyaları, profil, danışma veritabanları | tarayıcı eşleşmeleri ve dedektör isabetleri (`trust: observed`) | yok | her push, süpürme (`30f`) | P2 |
| `security.run` | Hakem | `koş` | profilin testleri, avcının kanıtları, ağaçlar | kural durumları, doğrulanmış ve reddedilmiş bildirimler | `security` satırları `yaz`'da | her döngü (`30d`, `30f`) | P2 |
| `exit.sample` | Hakem | `çek` | sınıf, gizli tohum, profil | çıkış vakaları (kural sayımı) | yok; aktarımında donar | hakem exit | Aşama 1 çıkışı |
| `spec.lint` | Hakem | `koş` | spec dizini, `required_exit_rows` | ihlal listesi | yok | Kurucu, aşama kilidi | Aşama 1 çıkışı (Aşama 0'da tohumun spec denetimi) |
| `harness.baseline` | Hakem | `çek` | `snapshot_id`, property | bulgu dosyası | yok | hakem | Aşama 4 |
| `lock.check`, `brain.accept` | Önyükleme hakemi | `çek`, `yaz` | aşama, spec hash, `setup/stage.json`; beyin SHA'sı, testler, rakip | kilit; kabul / ret | imzalı sonuç | her push (`29b`) | tohum; Kurucu yazmaz |
| `profile.propose` | Beyin | `koş` | hedef ağacı | profil önerisi | yok | Kurucu | Aşama 1+ oyuncu |
| `lint.discover` | Beyin | `koş` | `snapshot_id`, profil | bulgu dosyası | yok | hakem döngüsü | Aşama 1 |
| `fixer.range` | Beyin | `koş` | bulgu | worktree diff'i | worktree | hakem döngüsü | Aşama 1 |
| `fixer.llm` | Beyin | `koş` | bulgu, `llm.call` çıktısı | worktree diff'i | worktree | hakem döngüsü | Aşama 1 |
| `candidate.publish` | Beyin | `koş` | bulgu, diff | aday paketi | `candidates/<id>/` çıktısı | düzelticiler | Aşama 1 |
| `docs.render` | Beyin | `koş` | defter görünümleri | sayfa önerileri | yok | hakem döngü sonu | Aşama 1 |
| `docs.index` | Beyin | `koş` | spec ve `docs/` dizini | `INDEX.md` önerisi | yok | Kurucu, hakem döngü sonu | Aşama 1 |

**Aday paketi** `{finding, diff, organ_ids, definition_sha256[]}`'dir. Çalışma zamanında `koş`
işinin çıktı ağacındaki `candidates/<id>/`'ye yazılır ve hakem onu artefakt kimliğiyle okur. Aşama
0'da adaylar Kurucu'nun beyin reposundaki hazır adaylarıdır (`candidates/<hedef>/<cid>/`, `26c`). Hakem
hiçbir adaya yeniden koşturmadan güvenmez.

**İlk çağıranıyla açılanlar.** `chain.asof` (ilk zamansal sorgu okuyucusu), `map.build` (ilk
`impact_miss` sinyali ya da K2 silmeleri), `oracle.run` (Aşama 4, K5 test oracle'ı),
`reputation.score` (bir sınıfta ≥ 2 aday organ), `lessons.view` (Aşama 2 planlayıcısı),
`genesis.queue` (bir sınıfta ≥ 2 aday), `main.sync` (Aşama 2), `seal.rotate` (ilk held-out havuzu),
`harness.drill` (ders provası, Aşama 2 partisi), `security.*` ve güvenlik avcısının `agent.dispatch`'i
(P2; Aşama 1'den bildirir, düzeltmez, `30f`). Yukarıda "Gelir" sütununda parti adı taşıyan her araç da
böyledir.

Beyin araçlarının yazdığı her şey bir öneri ya da worktree'dir; `brain/state`'e ve hedefe yalnız
`yaz` işi, `target.write` ile yazar.
