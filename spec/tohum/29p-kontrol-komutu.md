# Kontrol Komutu: Döngü İşlerinin İlk Adımı

Tarih: 2026-10-30 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: `loop.yml` yazılırken; döngünün her işinde
Çapa: `seed/bootstrap/snowball_bootstrap/` (`cli.py` `control`, `config.py` `loop_goes`, `wiring.py` `control_step`)

---

Döngü hakeminin her işi (`08` 1) ilk adımında hakem reposunun `main`'indeki `control.json`'u canlı okur
(`asama-0/01` D0). Okuyan Kurucu'nun kodu değil, tohumun `control` komutudur: önyükleme hakeminin paketi, hakem
reposunda `bootstrap/` (`25` 3); aktarım ona dokunmaz (`25a`). Aynı komut `--root` ile önyükleme hakeminin kendi
iş akışında operatör dosyalarını da okur (`29b`).

**Çağrı.**

```text
python3 -m snowball_bootstrap control --control <control.json> --job <iş> --event <tetik> --github-output <dosya>
```

Dört bayrak birlikte verilir; biri eksikse çıkış 2'dir. `--job` `loop.yml`'un beş işinden biridir (`cek`, `getir`,
`kos`, `cagir`, `yaz`), `--event` GitHub'ın `GITHUB_EVENT_NAME`'idir.

**Sonuç** (`26c`'nin kapalıya düşüşüyle):

| Durum | Çıkış | `--github-output`'a |
|---|---|---|
| `kill_switch` tam olarak `false` değil (eksikse açık); `budget_state` `ok` değil (eksikse fren); `control.json` yok ya da nesne değil | 2: iş kırmızı durur | hiçbir şey |
| tetik `schedule` ya da `workflow_dispatch` değil; iş beşinden biri değil | 2 | hiçbir şey |
| `schedule` ve `loop_schedule` tam olarak `true` değil (eksikse `false`) | 0: `paused`, yeşil | `go=false` |
| `workflow_dispatch` (operatörün elle tetiklemesi, `25a`); `schedule` ve `loop_schedule: true` | 0 | `go=true` |

`merge_paused`'u `gate.check` (`26a`), `founder_resume`'u başlatıcı (`24a`) okur; bu komut okumaz.

**Adım.** `loop.yml`'da her işin ilk adımı bayt bayt budur; `LOOP_JOB` işin kendi adıdır. Hakem reposunun `main`'ini
seyrek ve kimliksiz çeker (kök dosyaları ve `bootstrap/`), komutu `bootstrap/`'tan koşar; `control.json` o anki
`main`'dendir.

```yaml
      - name: control
        id: control
        env:
          LOOP_JOB: <iş>
        run: |
          set -eu
          git clone --quiet --depth 1 --branch main --filter=blob:none --sparse "$GITHUB_SERVER_URL/$GITHUB_REPOSITORY" "$RUNNER_TEMP/control"
          git -C "$RUNNER_TEMP/control" sparse-checkout set bootstrap
          cd "$RUNNER_TEMP/control/bootstrap"
          python3 -m snowball_bootstrap control --control ../control.json --job "$LOOP_JOB" --event "$GITHUB_EVENT_NAME" --github-output "$GITHUB_OUTPUT"
```

Sonraki her adım `if: steps.control.outputs.go == 'true'` taşır. GitHub bu koşula `success()` ekler: kırmızı
duran kontrol adımı sonraki adımları da durdurur, `go=false` onları atlatır ve iş yeşil biter.

**`wiring` kuralı** (`asama-0/09` test 46 "her işin ilk adımı `control` ve kill switch açıkken iş durur";
`asama-0/10` #is-akisi). Bir kabuk betiği ne yaptığı için okunamaz; kural dosyayı okuyarak karar verir:
- her işin ilk adımı yukarıdaki adımdır, tam olarak: `LOOP_JOB` işin adı; fazladan anahtar (`if`,
  `continue-on-error`, `shell`, başka `env`) yok. Değilse `workflow_control_step:<iş>`.
- sonraki her adımın `if`'i tam olarak `steps.control.outputs.go == 'true'`'dur (`${{ }}` içinde ya da
  `always()` ile değil). Değilse `workflow_control_gate:<iş>:<n>`.
- adımın nerede ve nasıl koştuğunu üstten değiştiren bir şey yoktur. Kural yasaklananı değil izin verileni sayar:
  iş akışında yalnız `name`, `run-name`, `on`, `permissions`, `concurrency`, `jobs`; işte yalnız `name`, `if`,
  `needs`, `runs-on`, `permissions`, `environment`, `concurrency`, `outputs`, `timeout-minutes`, `strategy`,
  `continue-on-error`, `steps` ve adımı olmayan (ilk kuralın reddettiği) iş akışı çağrısının `uses`, `with`,
  `secrets`'i. `env`, `defaults`, işin `container`'ı ve `services`'i (ikisi de ilk adımdan önce başlar; hizmetin
  bağladığı dizin koşucunun dosyalarına yazar) ve adı geçmeyen her anahtar `workflow_control_context:<iş>` ya da
  `workflow_control_context:workflow`.

Kural kod push'unda MF17 bitince her push'ta ve çıkışta koşar (`asama-0/14`); öbür test 46 kuralları gibi
`wiring.py`'dedir.

**Sınır.** Seyrek çekme kimliksizdir: hakem reposu özel olunca (`25` 0) adım çekemez ve iş kırmızı durur
(kapalıya düşer). Özel hakem reposunun okuma yolu o zamandan önce tohum dönemiyle gelir.
