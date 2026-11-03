# Test Sonuçları / Test Results

Skill'in çalıştığının kanıtı. Yeniden üretmek için:

```bash
python test/make_fixtures.py
python kullanimkilavuzu/scripts/check_manual.py test/output/kilavuz.md \
    --screenshots test/fixtures/ekranlar \
    --reference test/fixtures/ornek-kilavuz.md
python kullanimkilavuzu/scripts/convert.py test/output/kilavuz.md \
    --format docx,html --out test/output
```

## Ortam

| Bileşen | Değer |
|---|---|
| OS | Windows |
| Python (sistem) | 3.14.5 — `python-docx` **yok** |
| Python (DSH bundled) | `python-docx` 1.2.0, Pillow 12.3.0 **var** |
| LibreOffice / pandoc | **yok** (PDF yolu test edilemedi) |
| Görsel okuma | Bu oturumun modeli görsel girdi desteklemiyor |

## 1. Fixture üretimi

`test/make_fixtures.py` → 6 PNG (960×640) + `test/fixtures/ornek-kilavuz.md`.

Sentetik uygulama: **Envanter Takip** — giriş, panel, ürünler, yeni ürün, kayıt
onayı, raporlar. Üç ekranda kırmızı vurgu çerçevesi var (vurgu analizini test
etmek için). Örnek kılavuz bilinçli olarak **farklı** bir üslupta: `## Bölüm N`,
`**Adım N.**`, `Şekil N — …` alt yazısı, sıcak "Uyarı/Not" kutuları.

## 2. Uçtan uca üretim

Skill'in 7 adımı izlenerek `test/output/` üretildi:

| Dosya | Ne kanıtlıyor |
|---|---|
| `kilavuz.md` | 4 bölüm, 6 adım, 6 `Şekil`, 3 uyarı kutusu |
| `00-analiz.md` | Stil sözleşmesi + ekran envanteri + belirsizlik listesi |
| `images/` | 6 görsel, göreli yolla bağlı |
| `kilavuz.html` | 6 `<img>`, 6 `<h2>`, 1 tablo, 3 `<blockquote>` |
| `kilavuz.docx` | 6 gömülü görsel, 1 tablo, 38 paragraf |

**Biçim uyumu:** Yeni kılavuz `templates/manual-template.md`'deki `### Adım N`
şemasını **değil**, referansın `**Adım N.**` + `Şekil N — …` şemasını kullandı.
Yani "biçim referanstan" kuralı çalıştı.

## 3. QA kapısı

`check_manual.py` → **PASS** (hata 0, uyarı 0, 6/6 görsel, 6 adım).

### Negatif test — kapı gerçekten yakalıyor mu?

`test/negative/bozuk-kilavuz.md` kasıtlı olarak bozulmuş bir kılavuz → **FAIL,
10 hata**:

| Yakalanan kusur | Sayı |
|---|---|
| Bulunamayan görsel yolu | 2 |
| Hiç kullanılmayan ekran görüntüsü | 4 |
| Bölüm numarası atlaması (1 → 3) | 1 |
| Doldurulmamış `<yer tutucu>` | 2 |
| "Açık Sorular" bölümü yok (uyarı) | 1 |
| Görselsiz adım (uyarı) | 1 |

## 4. Test sırasında bulunan ve düzeltilen bug'lar

| # | Bug | Etki | Düzeltme |
|---|---|---|---|
| 1 | `STEP_RE.findall()` `re.MULTILINE` olmadan `^` eşleşmiyordu | QA "Adım: 0" diyordu, adım denetimleri hiç çalışmıyordu | `re.MULTILINE` eklendi + satır bazlı sayım |
| 2 | "Açık Sorular" karşılaştırması ters (`> start`) | Bölüm **içindeki** her `[?]` hatalı uyarı üretiyordu | `i - 1 < start` (bölümden **öncekiler**) |
| 3 | Alt yazı ile görsel aynı paragrafta birleşiyordu | DOCX'e **hiç görsel gömülmüyordu** (`inline_shapes: 0`) | `STANDALONE_IMG_RE` ile ayrı blok |
| 4 | Blok alıntının her satırı ayrı paragraf | Uyarı kutusu cümleleri bölünüyordu | Boş satıra göre paragraf |
| 5 | `---` yatay çizgisi 40 karakter `─` olarak yazılıyordu | DOCX'te çirkin | `w:pBdr` alt kenarlık |
| 6 | Görsel alt yazısı iki kez ekleniyordu | DOCX'te çift alt yazı | Kaldırıldı (alt yazı zaten üstte) |

## 5. Sınırlar / Test edilemeyenler

- **Görsel okuma adımı gerçek modelle koşulmadı.** Bu oturumun modeli görsel
  girdi desteklemiyor. Bu yüzden görsellerin *okunması* değil, okunan içerikle
  *üretim* zinciri test edildi. Görsel yetenekli bir modelde aynı akış çalışır;
  çalışmıyorsa skill durmayı emreder (SKILL.md Kural 9).
- **PDF yolu** LibreOffice/pandoc olmadığı için üretilemedi; betik bu durumda
  `--format html` + tarayıcıdan yazdırma öneriyor (test edildi: mesaj doğru).
- **DOCX görsel doğrulaması** LibreOffice olmadığı için render edilemedi; yapısal
  doğrulama yapıldı (6 gömülü görsel, doğru sıra).

---

## 6. Bağımsız doğrulama ve düzeltme turları

### Round 1 — bağımsız denetim (`test/VERIFY.md`)

Bağımsız bir doğrulayıcı ajan skill'i denetledi: **1 KRİTİK, 5 ORTA, 9 KÜÇÜK** bulgu.
Bulduğu en önemli şey, benim kendi testimin kaçırdığı gerçek bir hataydı:

| # | Bulgu | Durum |
|---|---|---|
| KRİTİK-1 | `convert.py --out` farklı klasörken görselleri kaybediyordu (0 gömülü görsel) ve yine de "Tamam" + kod 0 diyordu | ✅ düzeltildi |
| ORTA-1 | Yeniden adlandırılmış görsel kopyası "kullanılmayan" sanılıyordu | ✅ içerik hash'i ile eşleştirme |
| ORTA-2 | `x < 10 > 5` karşılaştırması yer tutucu sanılıyordu | ✅ satır içi kod + matematik filtresi |
| ORTA-3 | Adım numaralandırma global 1..N varsayıyordu | ✅ global veya bölüm başına |
| ORTA-4 | QA komutlarının çalışma dizini belirsizdi | ✅ `<skill-dizini>/scripts/...` |
| ORTA-5 | `--format pdf` tek başına dönüştürme denemiyordu | ✅ DOCX üretimi + yönlendirme |
| KÜÇÜK-1…9 | Erken dönüş, boşluklu yol, tekrarlı bulgu, eksik şema, ikili referans, `__pycache__`, sabit `lang`, kopyalama adımı, `[?]` ifadesi | ✅ hepsi düzeltildi |

Tam liste ve kanıtlar: [`VERIFY.md`](VERIFY.md).

### Round 2 — kalıcı regresyon paketi

Bulunan her hata, tekrar oluşmaması için [`run_tests.py`](run_tests.py) içinde bir
teste dönüştürüldü. Paket 5 grupta **40 test** çalıştırır:

```bash
python test/run_tests.py
```

| Grup | Kapsam |
|---|---|
| 1. Temel QA | temiz kılavuz PASS, negatif kılavuz FAIL (5 bulgu tipi), şablon FAIL, çökme yok |
| 2. Yalancı pozitifler | yeniden adlandırılmış görsel, `x < 10 > 5`, bölüm başına adım no, `## 1 —`, docx referans |
| 3. convert.py | html, `--out` kopyalama + 6 gömülü görsel, `--lang`, pdf yönlendirmesi, hata kodları |
| 4. Round 2 regresyonları | sayısal/tarih yer tutucuları, ikili referans, kod bloğu + `--lang`, aynı içerikli ekran, `../` kaçışı, mesaj kalitesi |
| 5. Paket bütünlüğü | `.pyc` / `__pycache__` yok |

Son durum: **40/40 PASS**.

### Round 2 — ikinci bağımsız tur

Round 1 düzeltmeleri bağımsız olarak yeniden denetlendi: **13 DOĞRULANDI, 2 KISMİ**.
Bu tur 1 regresyon + 5 küçük bulgu daha çıkardı; hepsi düzeltildi ve teste bağlandı:

| # | Bulgu | Düzeltme |
|---|---|---|
| ORTA-6 (regresyon) | Sayısal/tarih/`...` yer tutucuları "karşılaştırma" sanılıp atlanıyordu | Karşılaştırma artık üç koşulla ayrılıyor: içerik sayısal + öncesinde sözcük + sonrasında rakam |
| KÜÇÜK-10 | İkili referansta uyarı verilse de yanıltıcı karşılaştırma sürüyordu | İkili uzantıda `check_reference` atlanıyor |
| KÜÇÜK-11 | `--lang` kod bloğu varken eziliyordu (değişken gölgeleme) | `fence_lang` olarak yeniden adlandırıldı |
| KÜÇÜK-12 | Aynı içerikli iki ekranda biri kullanılmasa da PASS | `duplicate-content` uyarısı eklendi |
| KÜÇÜK-13 | `../` yolu `--out` klasörünün dışına kopyalanıyordu | Hedef `out_dir` içinde değilse reddedilir, çıkış kodu 1 |
| KÜÇÜK-14 | "beklenen 3 veya 3", "6/1 klasör" gibi mesajlar | Tek değer yazılıyor; durum satırı `6/6 görsel kullanıldı (1 klasör)` |

Ayrıntılı kanıtlar: `test/VERIFY.md` → "Round 2".

### Round 3 — kapanış turu

Round 2 düzeltmeleri bağımsız olarak doğrulandı: **6/6 DOĞRULANDI**, yeni
KRİTİK/ORTA bulgu yok. İki küçük not da kapatıldı:

| # | Not | Düzeltme |
|---|---|---|
| KÜÇÜK-15 | `duplicate-content` kopya başına uyarı üretiyordu (5 kopya → 5 uyarı) | Hash grubu başına **tek** uyarı; testle kilitlendi |
| KÜÇÜK-16 | `x < 10 > y` (ardından harf) hâlâ yer tutucu sayılıyor | **Bilinçli sınır** olarak `_is_comparison()` docstring'ine yazıldı — gevşetmek gerçek yer tutucuları kaçırırdı |

Ayrıntılı kanıtlar: `test/VERIFY.md` → "Round 3".

## 7. v0.3 — Şablon modu ve referans profili

Gerçek bir endüstriyel makine kılavuzu (`KK.SP310.TR.00`, Forma Makina, 27 sayfa,
Word 2016 kaynaklı PDF) ve onu üreten prompt incelenerek eklendi:

| Yetenek | Ne yapar |
|---|---|
| `scripts/read_reference.py` | PDF/DOCX/MD'den **ölçülmüş** profil: başlık hiyerarşisi, numaralandırma derinliği, üstbilgi/altbilgi, doküman no/revizyon, şekil alt yazı kalıbı, punto, renk |
| `reference/placeholders.md` | `[ÜRETİCİ TARAFINDAN DOLDURULACAK]`, `[DOĞRULANMASI GEREKİYOR]`, `[ALARM KODU BELİRTİLMEMİŞ]` … sözlüğü |
| `templates/alarm-section.md` | Alarm başına 5 parçalı kayıt + özet tablo |
| `SKILL.md` | Şablon modu, kaynak öncelik sırası, ekran başına açıklama bloğu, operatör/servis ayrımı |
| `check_manual.py` | Alan yer tutucularını sayar (`unfilled-field` uyarısı), hata saymaz |
| `convert.py` | DOCX üstbilgi (`--header`, `--doc-no`), altbilgi (`--footer`), sayfa numarası alanı |

Gerçek PDF üzerinde ölçüm: **68 numaralı başlık**, 4 seviye (`6.5.1.1.`),
`KK.SP310.TR.00-15.08.2015` doküman no, 40 şekil alt yazısı, gövde 8 pt,
başlık rengi `#1F497D`. Betik ayrıca kaynaktaki **şekil numaralarının bölüm
içinde yeniden başladığını** tespit edip uyardı.

## 8. Sonuç

- Skill paketi: **hazır**, **56/56** regresyon testi geçiyor.
- Üç bağımsız doğrulama turu; bulunan **21 bulgunun tamamı** kapatıldı.
- Bilinen sınırlar: görsel okuma yeteneği gerektirir (SKILL.md Kural 9);
  `x < 10 > y` uç durumu bilinçli olarak muhafazakâr; PDF okuma için `pymupdf`,
  DOCX okuma için `python-docx` gerekir (yoksa betikler zarifçe düşer).