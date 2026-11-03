# kullanimkilavuzu

Ekran görüntülerinden, verdiğin **örnek kullanım kılavuzunun üslubuyla** yeni bir
kullanım kılavuzu üreten taşınabilir **Agent Skill**.

A portable **Agent Skill** that turns screenshots into a new user manual, written
in the style of an example manual you supply. Works on Claude Code, Cursor,
Codex, DeepSeek Harness and any other agent that reads `SKILL.md`.

---

## Nasıl çalışır / How it works

```
 ekran görüntüleri ─┐
                    ├─► [stil çıkar] ─► [ekranları oku] ─► [akışa diz] ─► kilavuz.md
 örnek kılavuz ─────┘                                                        │
                                                        images/ ◄─────────────┤
                                                        00-analiz.md ◄─────────┤
                                                        kilavuz.docx/html ◄────┘
```

1. **Stil sözleşmesi** — örnek kılavuzun başlık düzeni, adım kipi, görsel
   yerleşimi, uyarı kutuları, tonu ölçülür. Cümleleri kopyalanmaz.
2. **Ekran analizi** — her görsel tek tek okunur; ekran adı, eylemi, durumu,
   vurgusu ve belirsiz noktaları kaydedilir.
3. **Akış** — görseller sıraya dizilir, eksik ara adımlar işaretlenir.
4. **Yazım** — her adım = bir eylem + bir ekran görüntüsü.
5. **QA** — `check_manual.py`: kullanılmayan görsel, kırık yol, numaralandırma,
   doldurulmamış yer tutucu denetlenir.
6. **Teslim** — Markdown + isteğe bağlı `.docx` / yazdırılabilir `.html`.

---

## Kurulum / Install

Skill, `SKILL.md` içeren bir **klasördür**. Aşağıdaki dizinlerden birine
kopyalamak yeterlidir; her araç kendi dizinini okur.

### Claude Code

```bash
# kişisel (tüm projeler)
mkdir -p ~/.claude/skills
cp -r kullanimkilavuzu ~/.claude/skills/

# ya da proje bazlı
mkdir -p .claude/skills
cp -r kullanimkilavuzu .claude/skills/
```

### Cursor

```bash
mkdir -p ~/.cursor/skills
cp -r kullanimkilavuzu ~/.cursor/skills/

# proje bazlı
mkdir -p .cursor/skills
cp -r kullanimkilavuzu .cursor/skills/
```

### Codex / DeepSeek Harness

```bash
mkdir -p ~/.agents/skills
cp -r kullanimkilavuzu ~/.agents/skills/

# proje bazlı
mkdir -p .agents/skills
cp -r kullanimkilavuzu .agents/skills/
```

### Windows (PowerShell)

```powershell
Copy-Item -Recurse -Force "kullanimkilavuzu" "$env:USERPROFILE\.agents\skills\"
Copy-Item -Recurse -Force "kullanimkilavuzu" "$env:USERPROFILE\.claude\skills\"
Copy-Item -Recurse -Force "kullanimkilavuzu" "$env:USERPROFILE\.cursor\skills\"
```

### Diğer ajanlar / Other agents

`SKILL.md` standart Markdown'dır. Aracın skill/kural mekanizması yoksa dosyayı
sistem istemine ekle veya proje köküne `AGENTS.md` / `CLAUDE.md` içinden
"Ekran görüntüsünden kılavuz üretirken `kullanimkilavuzu/SKILL.md` uygula"
diye yönlendir.

Kurulumdan sonra aracı yeniden başlat; skill listesinde görünmelidir.

---

## Kullanım / Usage

Skill'i adıyla çağır ve iki girdiyi ver:

> `/kullanimkilavuzu`
>
> Ekran görüntüleri: `ekranlar/` klasöründe.
> Örnek kılavuz: `ornek-kilavuz.md`.
> Yeni kılavuz: Belge Yükleme Modülü için olsun, Türkçe, Markdown.

Doğal dille de çalışır:

> "Bu ekran görüntülerini ve şu örnek kılavuzu referans alarak yeni bir kullanım
> kılavuzu oluştur."

### Beklenen girdiler

| Girdi | Zorunlu | Örnek |
|---|---|---|
| Ekran görüntüleri | ✅ | `.png` / `.jpg` klasörü |
| Örnek kılavuz | ✅ | `.md`, `.txt`, `.docx`, `.pdf` |
| Ürün adı, dil, format | ➖ | verilmezse çıkarılır |

### Üretilen çıktı

```
cikti/
├── kilavuz.md        # ana teslim
├── images/           # kılavuzun kullandığı görseller
├── 00-analiz.md      # ekran envanteri + stil sözleşmesi (denetim izi)
├── kilavuz.html      # isteğe bağlı, tarayıcıdan PDF
└── kilavuz.docx      # isteğe bağlı
```

---

## QA ve dönüştürme / QA & conversion

> Komutları **proje kökünden** çalıştır ve betik yolunu skill klasörüne göre tam
> ver: betik skill klasöründe, kılavuz ise çıktı klasöründedir. `--out` başka bir
> klasörü gösterirse `convert.py` göreli görselleri oraya da kopyalar.

```bash
# Kalite kapısı (skill yolunu kendi kurulumuna göre değiştir)
python ~/.agents/skills/kullanimkilavuzu/scripts/check_manual.py \
    cikti/kilavuz.md --screenshots ekranlar/ --reference ornek-kilavuz.md

# Dönüştürme
python ~/.agents/skills/kullanimkilavuzu/scripts/convert.py \
    cikti/kilavuz.md --format html
python ~/.agents/skills/kullanimkilavuzu/scripts/convert.py \
    cikti/kilavuz.md --format docx,html --out cikti/ --lang tr
```

`check_manual.py` çıkış kodu `0` ise kılavuz teslime hazırdır. Hata kodu `1`,
kullanım hatası `2`.

`convert.py` bağımlılıkları zarifçe düşer:

| Format | Gerekli | Yoksa |
|---|---|---|
| `html` | yok | — |
| `docx` | `python-docx` | kurulum komutu yazdırır |
| `pdf` | LibreOffice (`soffice`) | `--format html` + tarayıcıdan Ctrl+P önerir |

> **İpucu:** Sistem Python'unda `python-docx` yoksa ama ajan ortamı kendi
> paketli Python'unu sunuyorsa (DeepSeek Harness, Codex), `convert.py`'yi o
> yorumlayıcıyla çalıştır. Denetlemek için:
> `python -c "import docx; print(docx.__version__)"`

Test sonuçları ve negatif test: [`../test/RESULT.md`](../test/RESULT.md).

---

## Dosyalar / Files

| Yol | İçerik |
|---|---|
| `SKILL.md` | Ana talimatlar (iki dilli), iş akışı, kesin kurallar |
| `scripts/read_reference.py` | **Yeni:** PDF/DOCX/MD referanstan ölçülmüş stil profili |
| `reference/style-contract.md` | Örnek kılavuzdan stil çıkarma şablonu |
| `reference/screenshot-analysis.md` | Ekran okuma şeması ve sıralama sinyalleri |
| `reference/placeholders.md` | **Yeni:** `[ÜRETİCİ TARAFINDAN DOLDURULACAK]` yer tutucu sözlüğü |
| `templates/manual-template.md` | Çıktı iskeleti |
| `templates/alarm-section.md` | **Yeni:** alarm bölümü + özet tablo şablonu |
| `examples/worked-example.md` | Uçtan uca dolu örnek |
| `scripts/check_manual.py` | QA denetimi (bağımlılıksız) |
| `scripts/convert.py` | Markdown → HTML / DOCX / PDF (üstbilgi/altbilgi + sayfa no) |
| `README.md` | Bu dosya |

## Şablon modu / Template mode

Referans bir **PDF/DOCX kurumsal şablonuysa** (kapak, içindekiler, üstbilgi,
doküman no, revizyon tablosu), skill şablonu iskelet olarak korur ve içeriği
ekran görüntülerinden doldurur. Bölüm sırası, numaralandırma derinliği
(`6.5.1.1.` gibi) ve doküman kimliği aynen korunur; PDF'in cümleleri kopyalanmaz.

```bash
# 1) Referansın ölçülmüş profilini çıkar
python scripts/read_reference.py ornek-kilavuz.pdf \
    --out 00-analiz-referans.md --json 00-analiz-referans.json

# 2) Kılavuzu üret, sonra kurumsal kimlikle Word'e çevir
python scripts/convert.py cikti/kilavuz.md --format docx \
    --header "Firma Adı" --doc-no "KK.SP310.TR.00" --footer "Kullanım Kılavuzu"
```

`read_reference.py` PDF için `pymupdf`, DOCX için `python-docx` ister; ikisi de
yoksa betik kurulum komutunu yazdırır.

Bilinmeyen bilgi **uydurulmaz**; `[ÜRETİCİ TARAFINDAN DOLDURULACAK]`,
`[DOĞRULANMASI GEREKİYOR]`, `[ALARM KODU BELİRTİLMEMİŞ]` gibi açıklayıcı yer
tutucular bırakılır ve teslim mesajında sayılır.

---

## Taşınabilirlik notları / Portability notes

- `SKILL.md` yalnızca `name` + `description` alanlarını kullanır. `name` değeri
  `kullanimkilavuzu` olduğu için hem `/kullanimkilavuzu` komutuyla hem de doğal
  dille (ekran görüntüsü + örnek kılavuz verildiğinde) tetiklenir.
- Klasör adı ile `name` alanı **aynı** olmalı: `kullanimkilavuzu/SKILL.md`.
- Talimatlar araç adı dayatmaz; "görseli gör / dosya yaz / betik çalıştır"
  ihtiyaçları için eşleme tablosu verir.
- Betikler yalnızca Python standart kütüphanesini kullanır; `docx` ve `pdf`
  isteğe bağlıdır.
- Görsel yolları her zaman göreli (`images/...`), böylece klasör taşınınca bozulmaz.

## Sınırlar / Limits

- Ekran görüntüsü okunamıyorsa uydurmaz; `[?]` koyar ve "Açık Sorular" bölümüne yazar.
- Örnek kılavuz okunamıyorsa varsayılan şablonu kullanır ve bunu belirtir.
- OCR yapmaz; görseldeki metni görme yeteneğine dayanır.
- **Görsel okuma yeteneği olmayan modelde çalışmaz.** Bu durumda skill durur ve
  kullanıcıdan görsel yetenekli bir oturum ister — dosya adlarından tahminle
  kılavuz üretmez (SKILL.md, Kesin kural 9).