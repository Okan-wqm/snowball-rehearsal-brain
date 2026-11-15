# Değişiklik Günlüğü — Tohum, 2.2'nin Beşinci Kayıtları

Tarih: 2026-11-06 · Sürüm: 2.2
Okunma: bir sayfanın geçmişi aranırken
Çapa: git geçmişi ve zincirdeki spec hash satırları

- 2.2 (2026-11-14, E583; gözlem): (B)'nin ilk denemesi kırmızı. Aktarılan 91bbd27; `loop.yml`'un `cagir` işi
  `unusable input: cagir: policy.json has no stage_budgets.asama_0.canary_usd` ile durdu (koşu 43534260172), `yaz`
  koşmadı, hedeflere yazılmadı; aktarım `25a` "Başarısızlık" ile geri alındı, 91bbd27 `reverted_exits`'te. `kos`'un
  ilk durması (`operating` yok) operatöründü: `policy.json`'a `operating{}` ve `security_keywords` yazıldı.
  E584: `canary_usd` da `policy.json`'da hiç yoktu (operatörün eksiği; `18a:60`'ın 1 USD'si yazıldı); şema `26b:54-59`.
- 2.2 (2026-11-06, E561–E566; sahibin kararı): `02` "Sahip istisnası": #spec de istisna edilir (E286), Aşama 1'in
  (A)'sına taşınır; `26c`: `spec_exception` ve yanında tohumun taşıma kaydının (`stages/carry-spec.json`) hash'i
  `spec_commitment`. Arayüz olgusu (E563): `exit.owner_exception` ve PASS satırının `owner_exception`'ı `anchor`'a göre
  sıralı bir dizidir (`26d:45-47`, denetim 7); çıkış isteği olmayan push'un sonucu değişmez.
- 2.2 (2026-11-06, E560; üç uzmanlı iki turlu çıkış panelinin kararı): `seed/founder/prompt.md` "Çıkış sırası": bir
  aşamanın ya da partinin mikro özellikleri bitince sıradaki iş çıkış isteğidir, koşulların tutup tutmadığını isteğe
  verilen hakem kararı söyler; istekten önce ancak `referee/` kodunun yanlış karar verdiği gerçek bir girdiyi (girdi,
  beklenen, gözlenen) gösteren iş gelir, ölçülmemiş ya da sınanmamış olmak bu kanıt değildir. Kural tek yerdedir,
  tohum sayfaları onu yinelemez. Önceden yanıtlanmış: `seed-046-pass-row-unnamed`'in sonraki düzenlemesi bir ilerleme
  notudur; `26d:36-47`, `10a:44` ve `seed-048-copy-gate-record-and-a-result-bytes`'ın yanıtı (`26d:47`) onu karşılar.
  80 satır sınırı için 2026-11-01 E478–E485 kaydı `CHANGELOG-5.md`'ye taşındı.
- 2.2 (2026-11-05, E550, E551, E553; Kurucu raporları, sahibin kararı): yeni `29e` "Bütçe durması": rakibin bir koşudaki
  payı ayın tavanından ve aşamanın freninden kalanla koşu başı tavanın en küçüğüdür; payı biten ya da çağrısı frene
  takılan baş yargılanmaz (`last_evaluated_sha`, seriler ve rakip hata serisi değişmez), sonuç `budget_stop` ile freni
  ve payı adlandırır, yoklama aynı başı pay büyüyene dek uyarıyla geçer; `29e:26`'nın bütçe istisnası kalktı, `29b`
  oraya bakar. `18a`: rakip freni 2026-11-05'ten Aşama 0'da da Aşama 1'de de 1000 USD'dir (rakip `claude` CLI
  aboneliğiyle koşar, fren yalnız kaçak frenidir; `asama-1/10`), `26e` sayıyı yinelemez. Yanıtlanan raporlar:
  `referee-049-rival-budget-consumes-commit` → `29e:42-53` (bütçe durması; çağrı başı tavan da fren, `per_run`),
  `29e:26` (bütçe rakip tarafı hata değildir), `29b:76-77` (baş tüketilmez), `18a:59` (politika: 1000 USD),
  `29e:53` (bu kuraldan önce yargılanmış sayılan baş yeniden açılmaz); declined (11-03 güncellemesi):
  `seed-044-revert-facts-producers`: ret geçerli (2026-11-01 kaydındaki `declined: seed-044-revert-facts-producers`
  satırı; `29j:53-60`); `asama-0/10a:26` `#geri-alma` Aşama 0'da değişmedi. 80 satır sınırı için 2026-11-02 E506 ve
  E507 kayıtları `CHANGELOG-5.md`'ye taşındı.
