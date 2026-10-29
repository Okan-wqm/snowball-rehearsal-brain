# Aşama 0 §0.6 — Snapshot üretimi (P1'e taşındı) ve çalışma ağacı

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken
Çapa: beklemede: aşama 0 çıkış raporu

---

Snapshot üretimi (temizleme, planted ve clean, kanarya, `snapshot_id`) P1 partisine taşındı; metin
`asama-1/13c`'dedir. Aşama 0'da snapshot yoktur; `koş` hedef ağacını şöyle kurar:

- **Çıkarma.** `çek` hedefin ağacını dosya listesinden, blob blob kurar; `export-ignore` ve
  `.gitattributes` filtreleri etkisizdir, hiçbir dosya gizlenemez; `.git` yoktur (`tohum/08`).
- **Çalışma ağacı.** Koşu başına taze bir host dizinidir (tmpfs değil); boyutu `operating{}`'in
  `worktree_bytes` anahtarıyla sınırlıdır (§0.12). İçine yalnız birimin `inputs`'u girer.
- **Bağımlılık.** `deps.fetch` (MF5) bağımlılıkları `getir` işinde getirir: kilitteki her tarball
  `integrity` ile doğrulanır, `resolved` izinli kayıt defterinde olmalıdır, git ve dosya bağımlılıkları
  reddedilir; çıktı içerik adresli artefakttır, her koşu onu hash'iyle doğrulayarak alır. `koş`
  kapsayıcısı onları ağsız ve betiksiz kurar; betik gerektiren paket tarifte işaretlidir ve `koş`ta
  ağsız koşar. Actions önbelleği kullanılmaz; artımlı araç önbellekleri kapalıdır (`tohum/08`).
- **Lisans.** Lisans kapısı ürüne giren bağımlılıklar içindir (`tohum/24`): Kurucu'nun ve hakemin
  tekerlekleri kapıdan geçer, izinsiz ya da bulunamayan lisans koşuyu kırmızı yapar. Hedefin
  bağımlılıkları ürüne girmez; lisans raporu yazılır, kapılanmaz.
