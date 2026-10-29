# Çalışma Modeli: Beyin, Hakem ve Kurucu Nasıl Koşar

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 inşasından önce ve her dispatch değişikliğinde
Çapa: beklemede: aşama 0 — beyin ve hakem reposu README'leri; run_meta

---

| Karar | Değer |
|---|---|
| Beyin reposu | Ayrı, özel repo; MCP sunucusu adı `snowball`; hedef repoda aynı adlı sunucu varsa profil çakışmayı raporlar |
| Hakem reposu | Ayrı, özel repo (`01a`); yalnız operatör yazar; kabul edilmiş hakem kodu, anayasal `policy.json`, `control.json`, kurulum özeti, tohum vektörleri ve koltuk promptları |
| Dil ve paket | İkisi de Python paketi; `pyproject` ile kurulur; bağımlılıklar hash'le pinlidir |
| İki yüzey | **CLI** deterministik, CI'nın çağırdığı yüzey. **MCP** ajanlara açılan yüzey; CI bir MCP sunucusunu doğrudan çağıramaz |
| Tetik | Hakem reposunun zamanlayıcısı beyin reposunu ve hedefi okuyucu App'iyle yoklar; hedefte beynin iş akışı ve kimliği yoktur (`01b`) |
| İşler | `çek`, `getir`, `koş`, `çağır`, `yaz` (`08` 1); oyuncu kodu yalnız `koş`ta, iç içe ağsız konteynerde |
| Kimlikler | Kurucu kimliği, okuyucu App'i, yazar App'i, Aşama 4'ten mühür App'i (`25`). Beyin App'i yoktur |
| Model kimlikleri | Yüksek: `claude-opus-5-5`. Düşük: `claude-sonnet-5-5`. En ucuz: `policy.json`'da adlandırılır. Effort rol başına `policy.json`'da |
| Model kaydı | Sunulan model ve maliyeti ajan değil `çağır` işi ya da sağlayıcı geçidi yanıttan yazar; istenenden farklıysa koşu geçersizdir |
| Sağlayıcı kimliği | Hakem reposunun sırlarında; yalnız `çağır` işinde ve sağlayıcı geçidinde. Oyuncu kodu koşan hiçbir işte yoktur |
| Durum dalı | `<state_root>` hedef repoda yetim `brain/state` dalında; uygulama kodunun CI'ını kirletmez |
| Entegrasyon dalı | `brain/integration`; etkinleştirmede `main`'den kesilir, Aşama 0–1'de senkronlanmaz (`07`) |
| Snapshot | Git ağacından dosya listesiyle çıkarılır, `export-ignore` dikkate alınmaz; `.git` yoktur. Keşif "tümünü koş", "etkilenen" yalnız worktree'de |
| Bağımlılık | `getir` işinde, kurulum betikleri kapalı, içerik adresli artefakt; Actions önbelleği kullanılmaz (`08` 5) |
| Lisans | Ürüne giren her bağımlılık ticari kullanıma açık, `license_allowlist`'teki bir lisanstadır (`18a`). Lisans tekerleğin kendisinden okunur (`License-Expression`, `License`, sınıflandırıcılar, `dist-info` lisans dosyaları) ve lisansı söyleyen her yer izinli olmalıdır; lisansı bulunamayan paket reddedilir; istisna yalnız operatörün `license_exceptions`'ıdır. MPL-2.0 dosyaları değiştirilmez. Dağıtılan sürüm lisans raporundan üretilen üçüncü taraf bildirimini taşır. Konteyner imajı, git ve docker ürünü koşturur, ürüne girmez; model sağlayıcı, Sigstore ve GitHub ticari şartlarıyla kullanılan servislerdir; rakibin `claude` CLI'si (tescilli, `LICENSE.md`) tekerlek değildir, dağıtılmaz ve lisans kapısına girmez: hakemin aracıdır, sürümü ve sha512 bütünlüğü `requirements/claude-cli/package-lock.json`'da pinlidir |
| Keşif ve oracle (K0–K2) | Keşif: aracın tüm ihlalleri, taban dahil. Oracle: hedef ihlal kayboldu, mandal tuttu (toplam artmadı) |
| Düzeltme aralığı | Araç düzeltmesi yalnız hedef mesajın `fix` aralığıyla uygulanır; biçimleyiciler dosya başına çalışır ve Aşama 2'de açılır |
| Kaçış | Sağlayıcı reddi ya da `stop_reason: refusal` koşuyu `unresolved` yapar; kimlik, kota, ağ hatası ve zaman aşımı altyapı arızasıdır: ret sayılmaz, sonraki turda yeniden denenir (`29b`); koşu içinde sessiz yeniden deneme yoktur |

## Kurucu

Kurucu oturumu Actions'ta koşmaz: zamanlanmış bir bulut ajan oturumu ya da operatörün makinesi
onu açar; Actions dakikası hakem işlerine kalır. Model Opus. Çalışma dizini beyin reposunun
klonudur; yazabildiği tek yer beyin reposudur. Hedefi çalışma dizininin dışındaki salt okunur bir
klondan **veri olarak** okur; hedefin yönerge, ayar, hook ve MCP dosyaları ona yüklenmez. Her
oturum `control.json`'u okuyarak başlar, oturum tavanı (`policy.json`, başlangıç 20 USD) aşılınca
temiz durur. Takvim oturum sayısıyla ölçülür; sonraki oturum öncekinin sonucu önyükleme hakeminde
ya da kapıda yeşilken başlar. Kurucu kendi maliyetini ölçemez: çalışma ortamı kullanım raporu
veriyorsa defterine `kind: cost` satırı olarak yazar, vermiyorsa `unmeasured` yazar; sertlik
sağlayıcı harcama tavanındadır (`25` 8). Etkinleştirmeden sonra `cost` bölümünde inşa kalemidir.
Her itmeden önce son imzalı sonucu okur; ret nedenleri tiplidir ve nedeni giderilmemiş bir itme
öğrenilmemiş ret sayılır. Sonuç `not_learning` derse oturum durur (`22a`, `29b`).

## Dispatch sözleşmesi (araç kullanan her ajan)

Claude Agent SDK şu seçeneklerle çağrılır; biri eksikse dispatch reddedilir:
`settingSources: []`, `strictMcpConfig: true`, açık `tools` listesi, `persistSession: false`,
`maxTurns`, effort `policy.json`'dan; ortamda `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` ve her koşuda
taze bir `CLAUDE_CONFIG_DIR`. Sistem promptu dispatcher'ın verdiği metindir; repo içeriği talimat
değildir (Y1). **Kanarya kendi-testi:** oyuncak repoya gömülü bir hook, bir `.mcp.json` sunucusu ve
bir yönerge dosyası kanaryası vardır; dispatch edilen ajanda hiçbiri yüklenmemelidir, yüklenirse
dispatcher kırmızıdır. Ajan işi `permissions: {}` ile koşar, `id-token` izni ve docker soketi
yoktur; modele yalnız ayrı bir iş ya da makinedeki sağlayıcı geçidinden, koşuya bağlı belirteçle
ulaşır (`08` 3).

**Araçsız çağrı.** Aşama 1 düzelticisi araç kullanmaz: hakemin `llm.call`'ı tipli girdiden prompt
kurar, tek Messages çağrısı yapar ve yapılandırılmış çıktı ister; `tool_choice` zorlanmaz.
Çıktıyı beynin deterministik uygulayıcısı yalnız hedef aralığa yazar. Bu yolda sandbox kaçışı
yapısal olarak imkânsızdır.

## Aşama 0 ve 1 araçları

Hakem: `exit.sample`, `cases.build`, `snapshot.make`, `harness.score`, `harness.baseline`,
`spec.lint`, `ledger.append`, `chain.verify`, `rekor.anchor`, `secrets.scan`, `drift.check`,
`profile.derive`, `deps.fetch`, `run.contained`, `llm.call`, `agent.dispatch`, `gate.diffguard`,
`gate.check`, `sentinel.run`, `gate.revert`, `exit.drill`, `gozcu.evaluate`, `status.block`,
`lock.check`, `brain.accept`. Beyin: `profile.propose`, `lint.discover`, `fixer.range`, `fixer.llm`,
`candidate.publish`, `docs.render`, `docs.index`. İmzalar ve ilk çağıranıyla açılan araçlar `26a`'da.

## Paket yerleşimi

Beyin reposu: `cli/`, `mcp/`, `adapters/`, `fixers/`, `docs/`, `candidates/`, `spec/`,
`founder-ledger.jsonl`, `tests/fixtures/toy-repo/`; Aşama 0 boyunca ayrıca `referee/` (hakemin
adayı; aktarımdan sonra yalnız aday alanıdır) ve tohumla gelen `seed/bootstrap/` (`29b`).
Hakem reposu: `harness/`, `gate/`, `runner/`, `dispatcher/`, `ledger/`, `gozcu/`, `seats/`,
`vectors/`, `schemas/`, `tests/`, `policy.json`, `control.json`, `setup/`.
