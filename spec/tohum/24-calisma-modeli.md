# Çalışma Modeli: Beyin, Hakem ve Kurucu Nasıl Koşar

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 inşasından önce ve her dispatch değişikliğinde
Çapa: beklemede: aşama 0 — beyin ve hakem reposu README'leri; run_meta

---

| Karar | Değer |
|---|---|
| Beyin reposu | Yeni, ayrı bir repo (`snowball-mcp` değil; iç kullanımda açık); Kurucu'nun ince taneli belirteci yalnız ona içerik yazar; `main`'de `non_fast_forward` ve `deletion` (`25`). Yerleşimi `24a`'da |
| Hakem reposu | Ayrı repo (iç kullanımda açık, `01a`); yalnız operatör yazar. Önyükleme hakemi (`bootstrap/`, `bootstrap.yml`) Aşama 0'dan sonra da beyin reposunun itme yargıcıdır (`29b`); döngü hakemi aktarımla kökte (`25a`); anayasal `policy.json`, `control.json`, kurulum özeti, tohum vektörleri ve koltuk promptları |
| Dil ve paket | İkisi de Python paketi; `pyproject` ile kurulur; bağımlılıklar hash'le pinlidir |
| İki yüzey | **CLI** deterministik, CI'nın çağırdığı yüzey. **MCP** ajanlara açılan yüzey (Aşama 1'den, beyin `mcp/`; sunucu adı `snowball`, hedefte aynı adlı sunucu varsa profil çakışmayı raporlar); CI bir MCP sunucusunu doğrudan çağıramaz |
| Tetik | Önyükleme hakeminin zamanlayıcısı beyin reposunu kimliksiz yoklar; döngü hakemi (`loop.yml`) hedefleri yoklar, zamanlayıcısı `control.json` `loop_schedule` ile açılır, (B)'de devirleri operatör elle tetikler. Hedefte beynin iş akışı ve kimliği yoktur (`01b`) |
| İşler | `çek`, `getir`, `koş`, `çağır`, `yaz` (`08` 1; önyükleme hakeminde ayrıca yeniden üreticiler için `yeniden`); hedef ve oyuncu kodu yalnız `koş`ta (ve `yeniden`de), iç içe ağsız konteynerde |
| Kimlikler | Kurucu belirteci, yazar App'i, özel hedef gelince okuyucu App'i, Aşama 4'ten mühür App'i (`25`). Beyin App'i yoktur |
| Hedefe yazım | Yalnız `yaz` işinde, yazar App belirteciyle, GitHub REST ve Git Data API'siyle ve yalnız `refs/heads/brain/**` altına (`target.write`, `26a`); hedefte git push ve `main`'e yazım yoktur |
| Model kimlikleri | Yüksek: `claude-opus-5-5`. Düşük: `claude-sonnet-5-5`. En ucuz: `policy.json`'da adlandırılır. Effort rol başına `policy.json`'da |
| Model kaydı | Sunulan model ve maliyeti ajan değil `çağır` işi ya da sağlayıcı geçidi yanıttan yazar; istenenden farklıysa koşu geçersizdir |
| Sağlayıcı kimliği | Hakem reposunun sırlarında: iç kullanımda operatörün `CLAUDE_CODE_OAUTH_TOKEN`'ı, satışta API anahtarı; yalnız `çağır` işinde ve (satışta) sağlayıcı geçidinde. Oyuncu kodu koşan hiçbir işte yoktur |
| Durum dalı | `<state_root>` hedef repoda yetim `brain/state` dalında; uygulama kodunun CI'ını kirletmez |
| Entegrasyon dalı | `brain/integration`; etkinleştirmede `main`'den kesilir, Aşama 0–1'de senkronlanmaz (`07`) |
| Çalışma ağacı | `çek` ağacı dosya listesinden kurar, `export-ignore` dikkate alınmaz; `.git` yoktur; `koş` onu koşu başına taze bir host dizinine açar. Snapshot P1'le gelir (`asama-1/13c`) |
| Bağımlılık | `getir` işinde, kurulum betikleri kapalı, içerik adresli artefakt; Actions önbelleği kullanılmaz (`08` 4). Aşama 0'da tek ekosistem npm'dir: kilitteki `integrity` ve izinli `resolved` (`asama-0/14` MF5) |
| Lisans | Kapı **ürüne giren** bağımlılıklar içindir: her biri ticari kullanıma açık, `license_allowlist`'teki bir lisanstadır (`18a`). Lisans tekerleğin kendisinden okunur (`License-Expression`, `License`, sınıflandırıcılar, `dist-info` lisans dosyaları) ve lisansı söyleyen her yer izinli olmalıdır; lisansı bulunamayan paket reddedilir; istisna yalnız operatörün `license_exceptions`'ıdır. MPL-2.0 dosyaları değiştirilmez. Dağıtılan sürüm lisans raporundan üretilen üçüncü taraf bildirimini taşır. Hedefin bağımlılıkları ürüne girmez: lisans raporu yazılır, kapılanmaz. Konteyner imajı, git ve docker ürünü koşturur, ürüne girmez; model sağlayıcı, Sigstore ve GitHub ticari şartlarıyla kullanılan servislerdir; rakibin `claude` CLI'si (tescilli, `LICENSE.md`) tekerlek değildir, dağıtılmaz ve lisans kapısına girmez: hakemin aracıdır, sürümü ve sha512 bütünlüğü `requirements/claude-cli/package-lock.json`'da pinlidir |
| Keşif ve oracle (K0–K2) | Keşif: aracın tüm ihlalleri, taban dahil. Oracle: taban ağaçta hedef ihlal var, aday ağaçta eşlenmiş satırda yok, mandal tuttu (toplam artmadı) (`asama-0/08`) |
| Düzeltme aralığı | Araç düzeltmesi yalnız hedef mesajın `fix` aralığıyla uygulanır; biçimleyiciler dosya başına çalışır ve Aşama 2'de açılır |
| Kaçış | Sağlayıcı reddi ya da `stop_reason: refusal` koşuyu `unresolved` yapar; kimlik, kota (abonelik penceresi, HTTP 429), ağ hatası, zaman aşımı ve 5xx altyapı arızasıdır: ret sayılmaz, sonraki turda yeniden denenir; kalıcı istek hatası (400/404/413/422) `request_rejected`'dır (`29b`); koşu içinde sessiz yeniden deneme yoktur |

## Kurucu

Kurucu oturumu Actions'ta koşmaz, Actions dakikası harcamaz; onu tohumun başlatıcısı açar (`24a`). Model
Opus. Yazabildiği tek yer beyin reposudur. Hedefi salt okunur bir klondan **veri olarak** okur; hedefin
yönerge, ayar, hook ve MCP dosyaları ona yüklenmez; hedef kodunu kendi makinesinde koşturmaz. Maliyetini
başlatıcı `kind: cost` satırı olarak yazar: oturum sayısı ve USD ölçümdür, kapı değildir; oturum tavanı
yalnız kaçak frenidir, gerçek sınır abonelik penceresidir (429 kesintidir, ret değildir). Sonuç
`not_learning` derse oturum durur (`22a`, `29b`). Başlatıcı sözleşmesi ve repoların yerleşimi `24a`'dadır.

## Dispatch sözleşmesi (araç kullanan her ajan)

Ajan iç kullanımda pinli `claude` CLI'siyle, satışta Claude Agent SDK ile şu seçeneklerin karşılığıyla
çağrılır; biri eksikse dispatch reddedilir: `settingSources: []`, `strictMcpConfig: true`, açık `tools`
listesi, `persistSession: false`, `maxTurns`, effort `policy.json`'dan; ortamda
`CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` ve her koşuda taze bir `CLAUDE_CONFIG_DIR`. Sistem promptu
dispatcher'ın verdiği metindir; repo içeriği talimat değildir (Y1). **Kanarya kendi-testi:** oyuncak
repoya gömülü bir hook, bir `.mcp.json` sunucusu ve bir yönerge dosyası kanaryası vardır; dispatch edilen
ajanda hiçbiri yüklenmemelidir, yüklenirse dispatcher kırmızıdır. İç kullanımda geçit yoktur: araç
kullanan ajan `çağır` işinde `claude` CLI'siyle ve yalnız hakemin MCP araçlarıyla koşar, oyuncu kodu
koşturmaz; koşuya bağlı belirteçli geçit ticari kullanımda API anahtarıyla açılır (`08` 5). Hakemin
`agent.dispatch`'i P2 partisiyle gelir (`asama-1/13`); Aşama 0'da araç kullanan ajan yoktur.

**Araçsız çağrı.** Aşama 0'ın (B) kanaryası ve Aşama 1 düzelticisi araç kullanmaz: hakemin `llm.call`'ı
tipli girdiden prompt kurar ve çağrıyı tohum rakibi gibi yapar (`29b`): pinli `claude` CLI'si, operatörün
`CLAUDE_CODE_OAUTH_TOKEN`'ı, yerleşik araç, ayar kaynağı ve oturum kaydı yok, tavan `--max-budget-usd`;
yapılandırılmış çıktı ister. API anahtarıyla (satışta) aynı çağrı Messages API'sine gider; `tool_choice`
zorlanmaz. Çıktıyı beynin deterministik uygulayıcısı yalnız hedef aralığa yazar. Bu yolda sandbox kaçışı
yapısal olarak imkânsızdır.

## Aşama 0 ve 1 araçları

Hakem, Aşama 0 (`asama-0/14`): `ledger.chain`, `chain.verify`, `secrets.scan`, `run.contained`,
`profile.derive`, `deps.fetch`, `unit.verify`, `gate.diffguard`, `gate.check`, `target.write`,
`ledger.append`, `rekor.anchor`, `sentinel.run`, `gate.revert`, `exit.drill` (yalnız geri alma),
`llm.call`, `status.block`, `activate`. Partilerle (`asama-1/13`): `snapshot.make`, `cases.build`,
`harness.score`, `drift.check`, `gozcu.evaluate` (P1); `agent.dispatch`, `security.*` (P2); `exit.sample`,
`spec.lint` (Aşama 1 çıkışı); `harness.drill` (Aşama 2); `harness.baseline` (Aşama 4). Push kabulü ve
aşama kilidi önyükleme hakemindedir (`29b`). Beyin, Aşama 1: `profile.propose`, `lint.discover`,
`fixer.range`, `fixer.llm`, `candidate.publish`, `docs.render`, `docs.index`. İmzalar `26a`'da.
