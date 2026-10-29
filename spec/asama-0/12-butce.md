# Aşama 0 §0.12 — Bütçe (kaçak freni; değerleri yalnız operatör değiştirir)

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken
Çapa: beklemede: aşama 0 çıkış raporu

---

**Bütçe Aşama 0'da bir kısıt değil, kaçak frenidir.** Sistem `claude` CLI'siyle abonelik üzerinden ve
kendi repolarımızda koşan bir iç denemedir; USD değerleri liste fiyatı tahminidir, fatura değildir
(`tohum/06`). Frenler olağan işi hiçbir zaman durdurmayacak kadar yüksek kurulur; işleri döngüyü kesmektir:
aynı commit'in saatte bir yeniden koşması, art arda yinelenen rakip çağrıları, kendini tekrar eden bir devir.
Değerler `policy.json` `stage_budgets.asama_0` ve anayasal tavan anahtarlarıdır; tablo başlangıç fren
değerlerini verir.

| Kalem | Başlangıç fren değeri | Frene takılınca |
|---|---|---|
| Kurucu oturumu | oturum başına `session_cap_usd` (20 USD; `--max-budget-usd`); aşama toplamı `stage_budgets.asama_0.founder_usd` (220 USD) | başlatıcı yeni oturum açmaz ve operatörü uyarır; Kurucu reddi değildir |
| Tohum rakibi (Sonnet) | `stage_budgets.asama_0.rival_usd` (25 USD) | önyükleme hakemi rakip işini başlatmaz, yoklama uyarıyla geçer, commit tüketilmez; aynı baş politika değişince kendiliğinden yargılanır (`tohum/29b`) |
| (B) kanaryası (`llm.call`) | `stage_budgets.asama_0.canary_usd` (1 USD); çağrı başına `--max-budget-usd` | çağrı yapılmaz, devir kapalıya düşer (test 37) |
| Actions dakikası | anayasal aylık tavan (`monthly_cap_ci_minutes`, başlangıç 1.800); önyükleme koşusu push başına ≤ 30 dk (`tohum/25`) | GitHub harcama sınırı (`tohum/25` 8) |
| Döngü koşusu | `operating{}` sınırları (`kos_wall_s`, `test_total_s`, `worktree_bytes`, `deps_bytes`, `container_mem_bytes`, `output_bytes`, `unit_inputs_bytes`; `tohum/18a`); devir elle tetiklenir | `limit_hit:<anahtar>`; Kurucu'ya sayılmaz, `status.md`'de görünür |

Olağan iş frene takılırsa operatör değeri yükseltir (dokunuş); fren spec'i gevşetmez. Aylık tavan
(`monthly_cap_usd`) aynı anlamda bir frendir. Aşama 0'da Gözcü yoktur; frenler önyükleme hakeminde,
başlatıcıda ve `llm.call`'dadır. `operating{}` sınırları Aşama 0'da kendini ayarlamaz.

**Ölçüm, kapı değil.** Kurucu oturum sayısı ve USD toplamları ilerlemenin ve maliyetin ölçüsüdür:
başlatıcı her oturumun CLI'nin bildirdiği maliyetini `kind: cost` satırı olarak deftere yazar (`tohum/24`);
`status-stage0.md` ve çıkış raporu toplamları gösterir (kopyada ilk canlı merge'e kadar oturum ve USD).
Tahmin 18 MF ve çıkış için yaklaşık 22 oturumdur. Hiçbiri çıkış koşulu değildir ve Kurucu'yu durdurmaz.
Sonraki oturum öncekinin önyükleme sonucu yeşilken başlar.

**Gerçek sınır abonelik penceresidir.** Abonelik kullanım penceresine (5 saatlik ve haftalık kota)
takılmak (HTTP 429) operatör uyarısı ve kesintidir: Kurucu reddi, rakip `unresolved`'ı ya da ret
hafızasına giren bir neden değildir; iş pencere açılınca kaldığı yerden sürer (`tohum/29b` kesinti kuralı).

**Operatör emeği.** Kurulum, tohum dönemleri, dürüstlük ekimi ve anahtarı, aktarım, (B)'nin devirleri
ve `stage-open`; her biri insan dokunuşu sayacındadır.
