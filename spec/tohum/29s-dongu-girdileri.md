# Döngü Girdileri: Beyin, Hedefler, Sigstore

Tarih: 2026-11-01 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: `loop.yml` ve döngünün `çek` ve `yaz` işleri yazılırken
Çapa: `seed/bootstrap/snowball_bootstrap/config.py` (`load_bootstrap`, `load_summary`); `seed/bootstrap/requirements/sign.txt`

---

Döngü hakeminin her koşusu üç girdiyi hakem reposunun kendi dosyalarından okur. Hiçbiri operatör değişkeni (`vars.*`),
tetik girdisi ya da koşucunun PATH'inde hazır bulunan bir program değildir: hiçbir devir insan dokunuşu istemez
(`25`: listede olmayan hiçbir şey sonradan insandan istenmez).

**Beyin reposu.** Hakem reposunun kökündeki `bootstrap.json`'un `brain_repo`'sudur: `owner/name`, önyükleme hakeminin
izlediği repo (`25` 3; aktarım dosyayı korur, `25a` 1). Döngünün her işinde iki yerde bulunur: işin
`actions/checkout`'unun kökünde ve kontrol adımının seyrek klonunda, `$RUNNER_TEMP/control/bootstrap.json` (`29p`).
D1'in okuduğu son imzalı sonuç bu reponun önyükleme hakeminindir (`asama-0/01`); kabul edilmiş SHA
`state.last_accepted_sha`'dır (`29b` "Durum").

**Hedefler.** Bir `loop.yml` koşusu, işin checkout'undaki `setup/summary.json`'un `targets[]`'ındaki her girdiye dizinin
sırasıyla hizmet eder: her hedefte bir devir, her hedefin defterinde aynı `cycle_id` (koşunun kimliği, `asama-0/01`).
Zamanlanmış koşu ile operatörün elle tetiklediği koşu aynı hedefleri koşar; hedef seçen bir değişken ya da tetik girdisi
yoktur. Aşama 0'da iki hedef vardır, `kind: toy` ve `kind: copy` (`26c`). Kopyanın genesis'i `25a` 7'nin şartını
(oyuncağın 1–5. devirleri yeşil) oyuncağın `brain/state`'inden okur; şart tutana kadar kopyanın devri hiçbir şey yazmaz
ve koşuyu kırmızı yapmaz.

**Sigstore.** Döngünün Sigstore'u önyükleme hakeminin pinli kümesidir (`asama-0/01`: tohumun Sigstore pinleri döngü iş
akışına da hizmet eder): hakem reposunda `bootstrap/requirements/sign.txt`, `sigstore==4.5.0` ve bağımlılıkları, CPython
3.12 manylinux x86_64 tekerlekleri, her biri hash'e sabitli (`ubuntu-24.04`'ün `python3`'ü 3.12'dir). Onu koşturan her
iş (`çek` doğrular, `yaz` imzalar) kontrol adımından sonra şu adımla kurar; adım kontrol adımının klonunu okur,
tekerlekleri kurmadan önce lisans kapısından geçirir (`29b` `koş`) ve indirileni ağsız kurar:

```yaml
      - name: sigstore
        if: steps.control.outputs.go == 'true'
        run: |
          set -eu
          cd "$RUNNER_TEMP/control/bootstrap"
          python3 -m venv "$RUNNER_TEMP/sig"
          "$RUNNER_TEMP/sig/bin/pip" download --quiet --require-hashes --only-binary=:all: --no-deps -d "$RUNNER_TEMP/sigw" -r requirements/sign.txt
          python3 -m snowball_bootstrap licenses --root .. --wheels "$RUNNER_TEMP/sigw"
          "$RUNNER_TEMP/sig/bin/pip" install --quiet --no-index --find-links "$RUNNER_TEMP/sigw" --require-hashes --only-binary=:all: --no-deps -r requirements/sign.txt
```

Program `"$RUNNER_TEMP/sig/bin/python" -m sigstore`'dur: tohumun `--sigstore-python` biçimi; `29b` "Durum"un
`sigstore verify identity`'si ve `26d`'nin `sign --rekor-version 1`'i onunla koşar. Her iş kendisi kurar; kurulan küme
artefaktla ya da önbellekle taşınmaz (`08` 4). Adım `29p`'nin kuralına uyar (`if`'i kontrol kapısıdır), kural
değişmez. Hash, lisans ya da indirme tutmazsa adım kırmızıdır ve iş durur.

**Kanaryanın `claude` CLI'si ve modeli** (D4, `çağır`). CLI tohum rakibinin pinli CLI'sidir: hakem reposunda
`bootstrap/requirements/claude-cli/` (`package.json`'ın pinlediği sürüm, `package-lock.json`'ın her tarball için
`integrity` sha512'si; `npm ci` tutmayanı reddeder). Pin bu kilit ve sürüm denetimidir; çalıştırılabilir dosyanın
baytlarına ayrı bir pin yoktur. `bootstrap.yml`'ın `cagir`'ı gibi, kontrol adımından sonra sır taşımayan şu adımla
kurulur; sır yalnız modeli çağıran adımın `env`'indedir:

```yaml
      - name: claude
        if: steps.control.outputs.go == 'true'
        run: |
          set -eu
          C="$RUNNER_TEMP/control/bootstrap/requirements/claude-cli"
          node -e 'process.exit(Number(process.versions.node.split(".")[0]) >= 22 ? 0 : 1)'
          npm ci --prefix "$C" --no-audit --no-fund
          pinned=$(node -p "require('$C/package.json').dependencies['@anthropic-ai/claude-code']")
          test "$("$C/node_modules/.bin/claude" --version | cut -d' ' -f1)" = "$pinned"
```

Program `$RUNNER_TEMP/control/bootstrap/requirements/claude-cli/node_modules/.bin/claude`'dur. Kanaryanın istediği
model `bootstrap.json`'un `rival.model`'idir: operatör dosyasının adlandırdığı tek model; kanarya modelden bağımsız bir
sözleşmeyi sınar (sunulan model istenen, tavan, `cost` satırı; `asama-0/10a` #model).
