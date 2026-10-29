# Kapı Kuralları, Tetik, Döngü İşlemi

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: her merge ve her state yazımında
Çapa: beklemede: aşama 0 — `gate.diffguard`, `gate.check`, `drift.check` kendi-testleri

---

**Aday nedir.** Beyin bir adayı kendi reposunda, `candidates/` altında yayımlar: bulgu, diff ve
onu üreten organların tanım hash'leri. Hakem yalnız kabul edilmiş beyin SHA'sındaki organların
adaylarını çeker (`brain.accept`); tanım hash'i kapının izin listesinde olmayan organın çıktısı
reddedilir. Oyuncunun önerdiği her satır `trust: inferred` saklanır; `brain/state`'in satırlarını
yalnız hakem yazar.

**Ret listesi.** Kapının diff-guard'ı (`gate.diffguard`) şunlara dokunan adayı reddeder:
kökteki `.github/**`, `.gitattributes`, lint, tip ve test yapılandırmaları, bağımlılık manifestleri ve
lockfile'lar, `<state_root>/**`; profildeki `banned_constructs`; `policy.json`'daki yasaklı
ifadeler; tavanın üstünde brüt silme; K6 canlı olana kadar güvenlik yolları, biçimleyici dahil.
**Yalnız düz dosya:** sembolik bağ, alt modül, `../` içeren ya da depo kökü dışına çözülen yol
reddedilir. Doküman yolları yalnız K8 sınıfının adaylarında geçer (`03`). Aynı liste
`brain.accept`'te beyin kodu değişikliklerine uygulanır; `referee/` altındaki iş akışı dosyaları
düz dosyadır ve canlıya yalnız operatör aktarımıyla girer.

**`brain/state` kuralları.** Yazarı yalnız hakemin `yaz` işidir; döngü başına tek doğrudan commit,
PR yok. Ruleset: `deletion`, `non_fast_forward`; bypass aktörü yok. Hakem commit'ten önce şunları
denetler; tutmazsa yazmaz ve sert durur:

| Yol | Kural |
|---|---|
| `chain/*`, `ledger.jsonl` | Yalnız ekleme: önceki satırlar bayt düzeyinde aynı, yeni satırlar zincire bağlı, kök Rekor'da |
| `cases/` | Yalnız ekleme; `provenance` zorunlu; dev vakası silinmez, `withdrawn` satırıyla kapanır |
| `policy.json` | Anayasal bölümü yalnız operatör, hakem reposunda yazar; buradaki kopyanın hash'i onunla aynı. Performans bölümü yalnız `18`'deki prosedürle ve dev arşivi yeniden oynatma raporuyla |
| `profile.json` | Hakem profili hedeften yeniden türetir (`profile.derive`); oyuncunun önerisi türetmeden farklıysa reddedilir: `banned_constructs` silme, `registry_egress` genişletme, güvenlik yolu, hariç dizin ve test yolu daralması dahil |
| `docs/`, `status.md` | Yalnız `docs.render` çıktısı ve hakemin `status.block` bloğu; elle düzenleme ret |

**`brain/integration` kuralları.** Ruleset: `deletion`, `non_fast_forward`, `pull_request`, zorunlu
kontrol (strict, `integration_id` = yazar App'i); bypass aktörü yok. Her düzeltme kendi
`brain/c/<id>` dalından tek PR'dır. Merge'ler sıralıdır: bir merge'ün nöbetçisi yeşil olmadan
sonraki merge yapılmaz; nöbetçi kırmızıysa o merge'ü hakem geri alır (`07`).

**Kapı yeniden koşturur.** Merge kararında kapı (`gate.check`) oyuncunun raporunu okumakla
yetinmez: aracı, oracle'ı ve etkilenen-test komutunu kendi `koş` işinde yeniden koşturur, sonuçları
artefakt kimliği ve hash'le okur, baseline'ı yeniden ölçer ve mandalı uygular. Sıfır test
kırmızıdır. Aynı koşudaki kırmızı kontrol kırmızı çıkmadıysa koşu geçersizdir (`08`).

**Tetik.** Hedefte beynin iş akışı ve kimliği yoktur. Hakem reposunun zamanlayıcısı beyin
reposunu ve hedefi okuyucu App'iyle yoklar; yeni beyin SHA'sı, yeni aday ya da yeni hedef başı bir
döngü başlatır. Hakemin kendi yazımları döngü başlatmaz. Yoklamanın en az beş dakikalık gecikmesi
kabul edilir.

**Döngü bir işlemdir.** Her döngü deftere başlangıç ve bitiş satırı yazar. Bitiş satırı olmayan
döngü çökmüş sayılır; sonraki döngü önce onun aday dallarını ve kiralarını temizler. Her döngü
ilk yazımından önce `drift.check` koşar ve canlı durumu hakem reposundaki kurulum özetiyle
karşılaştırır:

- `brain/*` ve `main` için etkin kurallar (`GET rules/branches/{dal}`) ve yazar App'inin
  `current_user_can_bypass` alanı; yazma modunda yazar App'i `main`'i güncelleyemez;
- kurulu App'ler beyan edilenlerle aynı; etkinlik API'sinde beyan dışı aktörün `brain/*` ref
  değişikliği yok;
- hakem reposunda iş akışı varsayılan izni salt okunur, yazma izinli App kurulu değil;
- hedefte sır kullanan ve `brain/**` dallarında ya da PR'larında tetiklenen iş akışı yok;
- tohum ağacı, anayasal politika ve vektör dosyasının hash'leri kurulum özetiyle aynı.

Fark varsa sert duruş (`28`).

**Tavanlar.** Döngü ve gün başına PR, merge, model çağrısı ve CI dakikası tavanları
`policy.json`'dadır; aylık Actions dakikası anayasal tavandır (`monthly_cap_ci_minutes`). Aşım
temiz bir duruştur.
