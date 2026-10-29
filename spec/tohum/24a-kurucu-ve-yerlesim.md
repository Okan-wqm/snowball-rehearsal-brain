# Çalışma Modeli, Devam: Kurucu Başlatıcısı ve Yerleşim

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Kurucu başlatıcısını yazarken, beyin reposunu kurarken ve her yerleşim değişikliğinde
Çapa: `seed/launcher/` (tohum kodu, `snowball-mcp` CI'ında testli); beyin reposunun ağacı

---

`24`'ün devamıdır.

## Kurucu

Kurucu oturumu Actions'ta koşmaz; onu tohumun başlatıcısı açar. Model Opus. Çalışma dizini beyin
reposunun klonudur; yazabildiği tek yer beyin reposudur. Hedefi çalışma dizininin dışındaki salt okunur
bir klondan **veri olarak** okur; hedefin yönerge, ayar, hook ve MCP dosyaları ona yüklenmez; hedef
kodunu kendi makinesinde koşturmaz, adayını hakemin yayımladığı araç çıktısından yazar
(`asama-0/08`). Her itmeden önce son imzalı sonucu okur; ret nedenleri tiplidir ve nedeni giderilmemiş
bir itme öğrenilmemiş ret sayılır. Sonuç `not_learning` derse oturum durur (`22a`, `29b`).

**Başlatıcı sözleşmesi** (`seed/launcher/`, tohum kodu). Operatör onu Kurucu'nun kapsülünde ya da ayrı
bir Windows kullanıcısında koşar; Kurucu'nun yapılandırması repo dışında, başlatıcıya aittir:

1. `control.json`'u hakem reposunun `main`'inden okur; kill switch açıksa çıkar.
2. Son imzalı önyükleme sonucunu (`actions:read` belirteci, Sigstore doğrulaması) ve beyin başını okur:
   baş için sonuç yoksa beklemededir, çıkar; park ya da kesinti varsa başlatmaz ve operatörü uyarır;
   `not_learning`'den sonra yalnız `founder_resume {after_run, note}` o koşuyu adlandırıyorsa bir kez
   başlatır (Kurucu önce "ne değiştiriyorum" defter satırını yazar); kabul ya da ret varsa başlatır.
3. `claude -p`: pinli sürüm, Opus model kimliği, `--max-budget-usd <session_cap_usd>`, ayar kaynağı yok
   ya da operatörün yönettiği dosya, `--strict-mcp-config`, taze `CLAUDE_CONFIG_DIR`,
   `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`; çalışma dizini beyin klonu, hedefin salt okunur klonu dışarıda;
   açılış "`00` ve `00a`'yı oku" ve tipli durum.
4. Bitince CLI'nin bildirdiği maliyeti `kind: cost` satırı olarak `founder-ledger.jsonl`'a tohumun defter
   aracıyla ekler; oturum sayısı ve USD `status-stage0.md`'ye girer.

**Maliyet bir ölçümdür, kapı değil** (`asama-0/12`). Kurucu kendi maliyetini ölçemez; ölçümü başlatıcı
yazar (rapor yoksa `unmeasured`). Oturum sayısı ve USD toplamları ilerlemenin ve maliyetin ölçüsüdür;
çıkış koşulu değildir ve Kurucu'yu durdurmaz. `session_cap_usd` ve aşama toplamı yalnız kaçak frenidir:
olağan işi durdurmayacak kadar yüksektir, döngüyü keser; takılınca başlatıcı yeni oturum açmaz ve
operatörü uyarır, bu bir ret değildir. Gerçek sınır aboneliğin kullanım penceresidir (5 saatlik ve
haftalık kota): takılmak (HTTP 429) operatör uyarısı ve kesintidir, Kurucu reddi değildir; oturum pencere
açılınca kaldığı yerden sürer. Sonraki oturum öncekinin sonucu önyükleme hakeminde yeşilken başlar.
Etkinleştirmeden sonra `cost` bölümünde inşa kalemidir.

## Yerleşim

**Beyin reposu** (yeni, ayrı; `25` 1):

```
spec/                           tohum dönemindeki spec/tohum ve aşama sayfaları
seed/                           tohum dönemindeki seed/** (bootstrap, drill, launcher)
referee/                        döngü hakeminin adayı; .github/workflows/loop.yml, schemas/, tests/ dahil
targets/<hedef>/units.json      birim tarifi önerisi (veri, `26c`)
candidates/<hedef>/<cid>/       finding.json, diff.patch, expect.json (`26c`)
tests/fixtures/toy-repo/        oyuncak hedefin içeriği; ajan yapılandırması taşımaz
reports/*.json                  tipli bildirimler (`26c`)
founder-ledger.jsonl            tohumun aracıyla zincirli
snowball-tests.json             {tests, done_mf, lockfiles}
exit-request.json               yalnız çıkış ve parti isteğinde
```

Aşama 1'den oyuncu kodu da beyindedir: `cli/`, `mcp/`, `adapters/`, `fixers/`, `docs/`. Beyindeki başka
kod `referee/`'yi, `referee/` başka kodu import etmez. Beyin push'unda herhangi bir yerde (büyük-küçük
harf duyarsız) `.claude/**`, `CLAUDE.md`, `AGENTS.md`, `.mcp.json`, `.vscode/**`, `.envrc`,
`.devcontainer/**` → `agent_config_modified` (`29b`).

**Hakem reposu:** `bootstrap/` ve `.github/workflows/bootstrap.yml` (önyükleme hakemi, tohum dönemiyle
değişir); aktarılan `referee/` ağacı kökte (`ledger/`, `gate/`, `runner/`, `profile/`, `target/`,
`dispatcher/`, `status/`, `harness/`, `schemas/`, `tests/`, `activate.py`) ve
`.github/workflows/loop.yml`; `seats/`, `vectors/`, `policy.json`, `control.json`, `setup/`.
