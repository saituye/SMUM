# Ekran Görüntüsünden Kullanım Kılavuzu — Skill Paketi

[![tests](https://github.com/saituye/screenshot-to-manual/actions/workflows/tests.yml/badge.svg)](https://github.com/saituye/screenshot-to-manual/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Ekran görüntüleri + örnek bir kullanım kılavuzu verdiğinde, **örneğin üslubunu
taklit eden ama içeriği ekranlardan gelen** yeni bir kullanım kılavuzu üreten
taşınabilir Agent Skill.

Claude Code, Cursor, Codex, DeepSeek Harness ve `SKILL.md` okuyan her ajanda çalışır.

```bash
git clone https://github.com/saituye/screenshot-to-manual.git
```

```
kullanım kılavuzu/
├── screenshot-to-manual/     ← SKILL paketi (kurulacak olan)
│   ├── SKILL.md              ana talimatlar (iki dilli)
│   ├── README.md             kurulum + taşınabilirlik
│   ├── reference/            stil sözleşmesi, ekran analizi şeması
│   ├── templates/            çıktı iskeleti
│   ├── examples/             uçtan uca dolu örnek
│   └── scripts/              QA + dönüştürme betikleri
└── test/                     kanıt: fixture'lar, çıktı, testler, doğrulama raporları
```

## Ne yapıyor?

1. **Stil çıkarır** — örnek kılavuzun başlık düzeni, adım kipi, görsel yerleşimi,
   uyarı kutuları, tonu ölçülür. Cümleleri kopyalanmaz.
2. **Ekranları okur** — her görsel tek tek incelenir; ekran adı, eylemi, durumu,
   vurgusu, belirsizlikleri kaydedilir.
3. **Akışa dizer** — görseller sıralanır, eksik ara adımlar uydurulmadan işaretlenir.
4. **Yazar** — her adım = tek eylem + tek ekran görüntüsü.
5. **Denetler** — `check_manual.py` kırık yolu, kullanılmayan ekranı, numara
   atlamasını, doldurulmamış yer tutucuyu yakalar.
6. **Teslim eder** — Markdown + istenirse `.docx` / yazdırılabilir `.html`.

## Kurulum

Skill, `SKILL.md` içeren bir klasördür; aracın okuduğu dizine kopyalamak yeterli.

| Araç | Kişisel dizin | Proje dizini |
|---|---|---|
| Claude Code | `~/.claude/skills/` | `.claude/skills/` |
| Cursor | `~/.cursor/skills/` | `.cursor/skills/` |
| Codex / DeepSeek Harness | `~/.agents/skills/` | `.agents/skills/` |

```powershell
# Windows — üçüne birden
Copy-Item -Recurse -Force "screenshot-to-manual" "$env:USERPROFILE\.agents\skills\"
Copy-Item -Recurse -Force "screenshot-to-manual" "$env:USERPROFILE\.claude\skills\"
Copy-Item -Recurse -Force "screenshot-to-manual" "$env:USERPROFILE\.cursor\skills\"
```

```bash
# macOS / Linux
cp -r screenshot-to-manual ~/.agents/skills/
cp -r screenshot-to-manual ~/.claude/skills/
cp -r screenshot-to-manual ~/.cursor/skills/
```

Kopyalamadan sonra aracı yeniden başlat. Kurulum ayrıntıları:
[screenshot-to-manual/README.md](screenshot-to-manual/README.md)

## Kullanım

> `/screenshot-to-manual`
>
> Ekran görüntüleri: `ekranlar/` klasöründe.
> Örnek kılavuz: `ornek-kilavuz.md`.
> Yeni kılavuz Türkçe olsun, Markdown.

Doğal dille de çalışır: *"Bu ekran görüntülerini ve şu örnek kılavuzu referans
alarak yeni bir kullanım kılavuzu oluştur."*

## Test durumu

```bash
python test/run_tests.py      # 26/26 PASS
```

```bash
python test/check_package.py  # frontmatter, bağlantılar, 500 satır sınırı
```

- Girdi/çıktı kanıtı: [`test/RESULT.md`](test/RESULT.md)
- Bağımsız denetim raporu: [`test/VERIFY.md`](test/VERIFY.md)
- Fixture üretici: `test/make_fixtures.py`

CI her push'ta bu iki betiği ve uçtan uca örnek kılavuzun QA kapısını çalıştırır:
[`.github/workflows/tests.yml`](.github/workflows/tests.yml).

## Lisans

MIT — bkz. [LICENSE](LICENSE).

## Bilinen sınır

Skill **görsel okuma yeteneği ister**. Model görsel desteklemiyorsa skill durur
ve uygun bir oturum ister; dosya adlarından tahminle kılavuz üretmez.
