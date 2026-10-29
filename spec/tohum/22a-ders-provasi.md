# Ders Provası: Öğrenmenin ve Kullanmanın Testi

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: ders görünümünü, merge'ü ya da çok repolu terfiyi getiren aşamanın spec'i yazılırken
Çapa: beklemede: aşama 0 — `ledger.jsonl` `part: drill` (`revert`) satırları; aşama 2 — ders provası; taahhüt hash'leri Rekor'da

---

"Ders yazıldı" öğrenmenin kanıtı değildir. Kanıt üç şeydir: ders doğru olaydan doğdu, doğru işe
verildi ve verildiği işte hatayı azalttı (Y5). Canlı hedefte bunu `22`'nin kredi kuralı ölçer, ama
`rules.lesson_n_min` koşu ister. Prova aynı soruları oyuncak hedefte, cevabı önceden bağlanmış
tuzaklarla, günler içinde sorar. Prova mekanizmayı sınar, canlı ölçümün yerine geçmez.

**Örnekler.** Hakemin `exit.drill` işi oyuncak hedefte bir **tuzak ailesinin** örneklerini üretir:
aynı gizli nedenle kırılan değişiklikler, örneğin adı değişen bir alanı metinle çağıran ve içe
aktarma grafında görünmeyen bir tüketici. Örnekler hakem sırrındaki gizli tohumdan koşu anında
üretilir. Cevap anahtarı (her örneğin gizli testi ve doğru `cause` kategorisi) koşudan önce hash'lenir,
hash zincire ve Rekor'a girer, koşudan sonra açılır. Oyuncu üreticiyi koşturmaz, tohumu görmez. Aile
listesi aşama spec'indedir ve donar. Sonuç, açılan gizli testin adayın worktree'sindeki koşusudur.

## Ders provası (`#ders-*`)

| Soru | Nasıl sorulur | Geçme koşulu |
|---|---|---|
| Doğuş | Ailenin ilk örneği tohumlanmış kötü bir merge'tür; nöbetçi kırmızıyı görür | `gate.revert` geri alır; `cause` cevap anahtarındaki kategoriyle aynı; ders `origin_event` ile o satıra bağlı ve `scope` aileyi taşıyor |
| Kullanım | Ailenin sonraki örnekleri ve başka bir ailenin örnekleri | Dispatcher dersi uygun her koşuya verir, öteki aileye vermez; `run_meta.lessons_injected` ve `prompt_sha256` bunu gösterir; planlayıcı ve düzeltici alır, test-yazıcı ve oracle almaz |
| Etki | `k` örnek, her biri dersli ve derssiz iki kolda | Eşli, tam tek yönlü McNemar; en az 8 uyuşmaz çift; p < 0,10; yön dersten yana (`gate_rules.lesson_drill`) |
| Yanlış ders | İkinci ailede `llm_prior` kökenli, bir koşulda zararlı bir ders hipotez olarak verilir | O koşulda örneğin kendi tuzak testi kırılınca ders `superseded_at` alır ya da koşul dışlanır, ders kaydına yazılır; o koşuldaki sonraki örneklere verilmez |
| Plasebo | Ham isabeti dersinkinden yüksek, kolay bir ailede doğru ama ilgisiz bir ders aynı rastgele saklamayla verilir | Beynin bildirdiği kredi hakemin Newcombe alt sınırına eşit; plasebonun kredisi sıfırı geçmez; sıralama krediyi izler, ham orana göre sıralayan yakalanır |
| Kalıcılık | Görünüm silinir; yeni oturum açılır | Görünüm defterden bayt bayt aynı kurulur; sonraki örnekte aynı ders aynı hash'le verilir |

Provada kollar rastgele saklama yerine eşlidir: her örnek iki kez koşar. Canlıdaki rastgele saklama
kuralı (`22`) değişmez. Aileyi bilen Kurucu bir kestirme yazsa da prova geçmez: dersten bağımsız bir
kestirme iki kolu birlikte geçirir ve uyuşmaz çift üretmez.

**Provanın kendisi de sınanır.** Kararı veren yargıcın tam kuralları, tohumla gelen referans
yargıç ve 14 ayrı kusurlu simüle beyinle ölçülmüş ayırma gücü `29c`'dedir. Ders provası yargıcı
(`harness.drill`) ve `drill` vektörleri ders görünümünden önceki Aşama 2 partisiyle gelir
(`asama-1/13`); Kurucu'nun yazdığı yargıç vektörlerde referansla aynı kararı vermezse o parti kabul
edilmez. Derssiz kolun da kırılmadığı aile ölçülemez; prova `UNMEASURABLE` olur ve aile değiştirilir.

## Geri alma provası (`#geri-alma`)

Merge getiren aşamada, öğrenmenin ham maddesi olan `cause` satırının doğru doğduğu ayrıca sınanır:
oyuncak hedefe cevabı bağlanmış kötü bir merge tohumlanır; nöbetçi kırmızıyı görür, `gate.revert`
geri alır, `cause` cevap anahtarındaki kategoriyle aynıdır ve satır zincirdedir. Yanlış kategori
öğrenmeyi baştan zehirler; bu yüzden ders görünümünden önce gelir.

**Aşama 0'da yalnız bu prova vardır** (`asama-0/14` MF14): `exit.drill` yalnız `revert` ailesini koşar;
seçim `HMAC(prova_tohumu, cycle_id)` ile önceki devrin `yaz`'ında taahhüt edilir ve taahhüt koşudan önce
zincirdedir; ekilen kötü merge'ler tohumun prova fikstürlerindendir. Oyuncakta üç kategori
(`test_regression`, `build_break`, `lint_regression`) en az birer kez (`asama-0/10a` #geri-alma); kategori
başına ≥ 3 ve karışıklık matrisi Aşama 1 çıkışındadır.

## Bağlam provası (`#baglam`)

Çok repolu terfiyi getiren aşamada iki oyuncak hedef zıt koşullarla kurulur: aynı ders birinde
doğru, ötekinde yanlıştır (K1, `21a`). Geçme koşulu: ders birinci hedefte doğar ve verilir; ikinci
hedefte çelişen test `scope.conditions`'a ayırt edici koşulu yazar; küresel katmanda ders koşullu
hâliyle durur; ikinci hedefte o koşulda zararlı enjeksiyon 0, birinci hedefte ders verilmeye devam
eder (`gate_rules.context_drill`).

## Kurucu da öğrendiğini kullanır

Önyükleme hakemi her reddi imzasıyla (tür ve test, kontrol ya da koşul) sayar. Aynı imza ardışık
`stage_params.repeat_reject_limit` retten geçerse sonuç `not_learning` der: Kurucu oturumu durur,
nedeni ve denediklerini `founder-ledger.jsonl`'a yazar; yeniden başlatma operatörün işidir ve
insan dokunuşu sayılır (`24`, `29b`). Aşama 0 çıkışı tekrar sayısını raporlar.
