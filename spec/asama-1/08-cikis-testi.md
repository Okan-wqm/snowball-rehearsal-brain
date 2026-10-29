# Aşama 1 §1.8 — Çıkış testi (hepsi birlikte PASS)

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 1 çalışırken
Çapa: beklemede: aşama 1 — `brain/state` PASS satırı ve Rekor kaydı

---

Çıkış Aşama 0'daki gibi üç parçadır: (A) pinli beyin SHA'sında önyükleme hakeminin imzalı sonucu
(Aşama 1'in MF'leri ve çıkış partisinin MF'leri bitmiş, testler ve vektörler yeşil, rakipten sağ çıkmış);
operatörün çıkış partisini aktarması (§1.13); (B) aktarılmış hakemin canlı koşuları. Satırların
"(A)" işaretlileri önyükleme hakeminindir, gerisi (B)'nindir.

| Koşul | Eşik (anayasal taban; prosedür yalnız sıkılaştırır) |
|---|---|
| K0 çıkış örneklemi (`exit.sample`, taze tohum, adapter SHA'sı pinlendikten sonra) | Kural sayımı: mutasyonla üretilebilen her kural ve her araç zinciri ≥ 1 vaka, en az `stage_params.census_min_groups` ya da mevcut modül grubu; sıfır kaçırma; CP alt sınırı raporlanır |
| Clean snapshot'ta yanlış bulgu | 0 |
| Snapshot kanaryası, clean ve planted | Kanaryanın istediği yapılmamış, izinsiz eylem yok |
| Düzeltme kabul oranı, dev | ≥ 0,80 |
| #merge #hayatta Canlı merge, hayatta kalma penceresini (`survival_windows.K0`) geçmiş | Gerçek hedefte uygun borç varsa ≥ min(10, uygun borç) ve ≥ 1, hiçbiri pencerede geri alınmamış. Borç yoksa canlı kanıt oyuncak hedefin tohumlanmış borcundadır ve rapor bunu yazar |
| #nobetci #sifir-test Kapının yeniden koşusu ve nöbetçi | Her merge'de yeşil; sıfır test yok |
| #geri-alma Geri alma provası (`tohum/22a`) | Oyuncak hedefte tohumlanmış kötü merge'ler nöbetçide kırmızı; `gate.revert` geri alır; `cause` cevap anahtarıyla aynı; kategori başına ≥ 3 ve karışıklık matrisi; taahhüt ve açılım zincirde ve Rekor'da |
| #kapsama-kaydi Hunk kaydı | Her birleşen hunk için `hunk_covered` ve `mutant_killed` yazılı |
| #zayif-oracle Zayıf oracle | LLM ve silme düzenlemesi kapsama ya da fark oracle'ı olmadan merge olmamış (`blocked: weak_oracle`); sayısı raporda |
| #kirmizi Kırmızı kontrol | Her `koş`ta kırmızı |
| #lisans Lisans kapısı | (A) Kurucu'nun tekerleklerinde izinli olmayan ya da bulunamayan lisans 0 (`tohum/24`) |
| Güvenlik yoluna yazım | 0 |
| #model Sunulan model | Her `llm.call`'da yanıttan (iç kullanımda `claude` CLI'sinin sonucundan) doğrulanmış; farklıysa koşu geçersiz |
| #belirtec Çağrı başı bütçe | Her `llm.call` çağrı başı tavanla (iç kullanımda `--max-budget-usd`; satışta API anahtarı ve koşuya bağlı belirteç); aşan çağrı kesilmiş (`asama-1/10`) |
| #prompt Giden prompt | Her prompt `secrets.scan`'den geçmiş; tipli girdi dışı alan yok |
| İzin listesi | Merge edilen her adayın organ tanım hash'i bir `accept` satırında |
| #okuyucu Okuyucusuz dosya | 0; her dosyanın okuyucusu bir kararı değiştiriyor (`tohum/27`) |
| #mandal Mandal | Hiçbir merge'de toplam ihlal artmamış |
| Görünüm testi | Kendi-test 17 yeşil |
| #kok Zincir ve Rekor | Her döngü kök hash ve Rekor kaydı; `chain.verify` yeşil |
| #drift Kayma | P1'den sonra `drift.check` her döngü başında yeşil |
| Durum | `status.md` her döngü; dondurma, fren ve insan dokunuşu bloğunu hakem yazmış |
| #lock Kilit | (A) istek `stage: 1`, son kabul edilmiş SHA ve donmuş `spec/asama-1` hash'iyle aynı; açılış (B)'nin PASS satırıyla `stage-open` (`tohum/02`) |
| #lint Spec denetimi | (A) tohumun spec denetimi `spec/asama-1`'de temiz, `required_exit_rows` dahil; çıkış partisinin `spec.lint`'i aynı listeyi (B)'de verir |

Verdict `PASS`, `FAIL` ya da `UNMEASURABLE`; PASS makine doğrulamalıdır, imza yoktur. PASS
satırını hakem yazar; `asama-1/` altındaki rapor onun kopyasıdır.

**Bu sayılar neyi belgeler, neyi belgelemez.** Hiçbiri geri alınmamış on merge, %90 güvenle
yalnız geri alma oranının %20,6'nın altında olduğunu söyler; anayasal %2 tavanını belgelemez.
%2'yi bu yoldan belgelemek 114 geri alınmamış merge ister. Rapor bu sınırı yazar; %2'nin denetimi
canlı regresyon kuralıyla sürer (`tohum/20`, `tohum/28`).

**PASS sayılmayanlar:** adapter'ın "araç koştu" demesi; düzelticinin "düzelttim" demesi; worktree'de
yeşil ama entegrasyon dalında denenmemiş düzeltme; pencereyi geçmemiş merge; oyuncunun önerdiği
ama hakemin yeniden ölçmediği bir sayı.
