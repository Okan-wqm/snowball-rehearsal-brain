# Aşama 1 §1.13 — Aktarım partileri

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çıkışından sonra, her parti yazılırken ve aktarılırken
Çapa: beklemede: her partinin `imports.jsonl` satırı ve (B) satırı

---

Aşama 0 yalnız ilk canlı döngünün okuduğu 18 mikro özelliği kurar (`asama-0/14`). Hakemin geri kalanı,
ilk okuyucusundan hemen önceki bir **parti** ile gelir (Y4). Parti, aşama çıkışındaki (A) → aktarım → (B)
protokolünün dar hâlidir (`tohum/01a`, `tohum/02`):

1. Kurucu partinin MF'lerini beyin reposunda `referee/` altında yazar; önyükleme hakemi her push'u Aşama
   0'daki gibi yargılar (testler, vektörler, modülsüz kırmızı, rakip). Partinin tablosu tohumdadır
   (`seed/bootstrap/stages/`) ve `setup/stage.json` açtıktan sonra geçerlidir.
2. MF'ler bitince Kurucu parti çıkış isteğini yapar; (A) önyükleme hakeminin imzalı sonucudur.
3. Operatör aktarır (insan dokunuşu); aktarım önyükleme hakemine dokunmaz.
4. (B): döngü hakemi partinin ilk okuyucusunu canlı koşar; kırmızıysa operatör aktarımı geri alır.

| Parti | Ne zaman | İlk okuyucu |
|---|---|---|
| P1 organ ve ölçüm | Aşama 1 MF1'in canlı koşusundan önce | Aşama 1 MF1 `lint.discover`'ın dev ölçümü; MF5'in özerk döngüsü |
| P2 güvenlik gözlemi | Aşama 1 içinde, P1'den sonra | Aşama 1'den güvenlik testi ve bildirimi (`tohum/30f`) |
| Aşama 1 çıkışı | Aşama 1 (A) ile (B) arasında | Aşama 1 (B)'nin kural sayımı; Aşama 2 spec isteği |
| Aşama 2 | ders görünümünden önce | ders provası (`tohum/22a`) |
| Aşama 4 | ilk LLM avcısından önce | taban kıyası |

| Parti | MF | Mekanizma | Test (`asama-0/09`) | Vektör grubu |
|---|---|---|---|---|
| P1 | 1 | Organ koşucusu: `koş`ta yalnız kabul edilmiş organların giriş noktaları | 51 | — |
| P1 | 2 | `snapshot.make` (§1.13c) | 8 | — |
| P1 | 3 | K0 mutasyon kataloğu, `cases.build` (dev), hunk eşleme (§1.13a; eşleme kuralı `asama-0/08`) | 2, 4 | — |
| P1 | 4 | `harness.score`, match-rule v2, istatistik (§1.13e); `26a` ile `29a` CLI'si önce uyumlanır | 1, 6, 7, 12, 28 | `match`, `cp_lower`, `mcnemar` |
| P1 | 5 | LLM yokluğu ve `<state_root>`'un sıfırdan büyümesi | 9, 11 | — |
| P1 | 6 | `drift.check`, her devir (`tohum/21`) | 24 | — |
| P1 | 7 | `gozcu.evaluate` (`tohum/28`) | 41 | — |
| P1 | 8 | `operating{}` sınırlarının bant içinde ayarı (`tohum/18a`) | 52 | — |
| P2 | 1 | `security.derive` ve `security.run` (`tohum/30d`) | `30d`'nin profil testleri | — |
| P2 | 2 | `agent.dispatch` ve dispatch kanaryası; güvenlik avcısı koltuğu (`tohum/30f`) | 22 | — |
| Aşama 1 çıkışı | 1 | `exit.sample` (§1.13a) ve snapshot kanaryası | 27, 16 | — |
| Aşama 1 çıkışı | 2 | `spec.lint` (`tohum/02` listesi) | 33 | — |
| Aşama 2 | 1 | Ders provası yargıcı `harness.drill` (`tohum/29c`) | 25'in ders kısmı | `drill` |
| Aşama 4 | 1 | `harness.baseline`; grep kümesi tohumdan, hash'i özette | 32 | — |

Oyuncu parçaları partiye girmez: `profile.propose` (test 31) ikinci birim ya da ikinci hedef bağlanırken
gelir; `docs.index` (test 44) Aşama 1 MF7'de `docs.render` ile gelir (§1.6).

**Aşama 0 2.2'nin 30 MF'sinin yeri.** Aşama 0'da kalanlar (eski → yeni MF): 1 → 1, 5 → 4, 13 → 3,
14 → 5 (npm), 15 → 7, 16 → 8 ve 9, 17 → 12, 18 → 13 ve 14, 20 → 15, 21 → 2, 23 → 10, 24 → 11, 26 → 16,
30 → 18 (taklit API). Yeni: `unit.verify` (6), iş akışı (17). Partilere: 6, 7, 9, 11 (LLM yokluğu), 19,
25 → P1; 22 → P2; 8, 12 → Aşama 1 çıkışı; 18'in ders provası → Aşama 2; 10 → Aşama 4; 29 → Aşama 1
MF7; 4 → ikinci birim ya da hedef. Tohuma: 2 (Kurucu defteri aracı), 3 (`control` komutu), 11'in ad
denetimi (`asama-0/10` #genellik), 27 (`brain.accept`: önyükleme hakemi itme yargıcı kalır; `accept`
satırını Aşama 1 MF6'da döngünün `yaz`'ı yazar), 28 (`lock.check`: önyükleme hakeminin aşama kapısı
`setup/stage.json`).
