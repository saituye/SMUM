# Bağımsız Doğrulama Raporu — `screenshot-to-manual`

- **Doğrulanan:** `screenshot-to-manual/` Agent Skill (SKILL.md, README.md, reference/, templates/, examples/, scripts/)
- **Tarih:** 2026-11-03
- **Rol:** Bağımsız doğrulayıcı (skill dosyalarına **hiçbir yazma** yapılmadı; yalnızca bu dosya yazıldı)
- **Yöntem:** Kaynak okuma + gerçek komut çalıştırma (sistem Python 3.14.5 ve DSH bundled Python 3.12.14) + ekran görüntülerinden bağımsız sentetik/olumsuz girdiler
- **Özet:** **1 KRİTİK, 5 ORTA, 9 KÜÇÜK** bulgu. Taşınabilirlik ve dosya haritası büyük ölçüde temiz; ana risk, `convert.py --out` kullanıldığında çıktının **sessizce görselsiz** üretilmesi.

---

## 1. Çalıştırılan testler ve gerçek çıktılar

Tüm komutlar `D:\AI\deepseek\skills\kullanım kılavuzu` dizininden çalıştırıldı. Sistem Python: 3.14.5 (`python-docx` yok, doğrulandı: `ModuleNotFoundError: No module named 'docx'`). Bundled Python: 3.12.14, `python-docx 1.2.0`, Pillow 12.3.0.

| # | Komut | Beklenen | Gerçek (özet) | Kod |
|---|---|---|---|---|
| 1 | `python screenshot-to-manual/scripts/check_manual.py test/output/kilavuz.md --screenshots test/fixtures/ekranlar --reference test/fixtures/ornek-kilavuz.md` | PASS | `Ekranlar: 6 dosya`, `Görsel ref: 6 | Adım: 6`, `(bulgu yok)`, `PASS hata=0 uyarı=0` | 0 |
| 2 | `python .../check_manual.py test/negative/bozuk-kilavuz.md --screenshots test/fixtures/ekranlar` | FAIL | `FAIL hata=10 uyarı=2` — 2 bulunamayan görsel, 4 kullanılmayan ekran, 1 bölüm atlaması, 2 yer tutucu, 1 "Açık Sorular yok" uyarısı, 1 görselsiz adım | 1 |
| 3 | `python .../check_manual.py screenshot-to-manual/templates/manual-template.md` | FAIL (yer tutucular) | `FAIL hata=32 uyarı=0` — 32 `<...>` yer tutucusu/görsel yolu | 1 |
| 4 | `python .../check_manual.py screenshot-to-manual/examples/worked-example.md` | Çökmemeli | `PASS hata=0 uyarı=1` (`'Açık Sorular / Open Questions' bölümü yok` — bölüm kod bloğu içinde olduğu için beklenen); çökme yok | 0 |
| 5 | Bundled Python: `convert.py test/output/kilavuz.md --format html,docx` (varsayılan `--out`) | html + docx | `+ kilavuz.html`, `+ kilavuz.docx`, `Tamam.`; DOCX 153225 bayt, **6 gömülü görsel**, 38 paragraf, 1 tablo, `inline_shapes=6`; HTML MD5 `30E9F54B...` (depodaki `test/output/kilavuz.html` ile **birebir aynı**) | 0 |
| 6 | Aynı komut `--out <geçici-dizin>` ile | html + docx | `Tamam.` / kod 0 **ama** DOCX 38365 bayt, `MEDIA_COUNT 0`, 6 adet "görsel bulunamadı" paragrafı; html'in `images/...` yolları çıktı klasöründe karşılıksız (görseller kopyalanmıyor) | 0 |
| 7 | Sistem Python ile `convert.py ... --format html,docx --out <tmp>` | Docx zarifçe düşmeli | `+ kilavuz.html`; `! python-docx bulunamadı. Kurulum: ...`; `UYARI: bazı formatlar üretilemedi` | 1 |
| 8 | `convert.py screenshot-to-manual/examples/worked-example.md --format html,docx` | Çökmemeli | `Tamam.`, iki dosya üretildi (kod bloğu içeren girdi sorunsuz) | 0 |
| 9 | `convert.py test/output/kilavuz.md --format pdf --out <tmp>` | PDF yok → LibreOffice önerisi | Yalnızca `kilavuz.html` üretildi; **LibreOffice/soffice mesajı yok**, sadece genel `UYARI: bazı formatlar üretilemedi` | 1 |
| 10 | `--format rtf` / olmayan dosya | Kullanım hatası | `HATA: bilinmeyen format: rtf` / `HATA: dosya bulunamadı` | 2 / 2 |
| 11 | `--json` çıktısı | Geçerli JSON | `passed: false`, `findings[]` satır numaralı; JSON geçerli | 1 |
| 12 | Ek sentetik girdiler (aşağıdaki bulgularda kanıtlarıyla) | — | Aşağıya bakınız | — |

**`test/RESULT.md` iddiaları doğrulandı:** 6 `<img>`, 6 `<h2>`, 1 tablo, 3 `<blockquote>` (html); 38 paragraf, 1 tablo, 6 gömülü görsel (docx); DSH bundled Python'da `python-docx 1.2.0` + Pillow 12.3.0. Negatif test sayısı (10 hata / 2 uyarı) da birebir eşleşti.

---

## 2. Taşınabilirlik değerlendirmesi (özet)

- **Frontmatter:** `SKILL.md:2-12` yalnızca `name`, `description`, `disable-model-invocation` içeriyor; başka alan yok. ✅
- **Araç dayatması:** `SKILL.md:69-74` yalnızca "eşleme tablosu" veriyor, zorunlu araç dayatmıyor. `check_manual.py` yalnızca standart kütüphane kullanıyor; `convert.py`'de `python-docx` ve LibreOffice isteğe bağlı. ✅
- **Windows'a özgü yol:** Zorunlu sabit yol yok. `convert.py:465-466` yalnızca isteğe bağlı LibreOffice fallback'i için `C:/Program Files` kullanıyor; README'deki PowerShell blokları kurulum örneği. ✅
- **Not (bulgu değil):** `disable-model-invocation: true` (`SKILL.md:12`) Claude Code'da modelin kendiliğinden tetiklemesini kapatır; `description` içindeki doğal-dil anahtar kelimeleri bu durumda tek başına çalışmaz. README:178-181 bunu belgeliyor, SKILL.md belgelemiyor. **Dış doğrulama yapılamadı:** bu oturumda web erişimi yok (HTTP 402); Codex/Cursor'ın bu alanı ve `~/.agents/skills` yolunu gerçekten okuduğu **bağımsız olarak doğrulanamadı**.
- **Betiklerin gerçek yorumlayıcılarla koşması:** Sistem Python'da (docx yok) ve bundled Python'da (docx var) ayrı ayrı doğrulandı. ✅

## 3. Tutarlılık değerlendirmesi (özet)

- **Dosya haritası** (`SKILL.md:237-248`): listelenen 7 yolun tamamı diskte mevcut; `README.md` → `../test/RESULT.md` bağlantısı da geçerli. ✅
- **Adlandırma:** `kilavuz.md`, `images/`, `00-analiz.md`, "Açık Sorular / Open Questions", `Şekil N` kavramları tüm dosyalarda aynı. ✅
- **Belgelenen ile davranış arasındaki farklar** aşağıdaki bulgularda (özellikle ORTA-2, ORTA-3, ORTA-4, KÜÇÜK-8).

---

## 4. Bulgular

> Biçim: **Dosya:satır — sorun — öneri**

### KRİTİK

**KRİTİK-1 — `convert.py --out` görselleri sessizce kaybediyor.**
- `screenshot-to-manual/scripts/convert.py:323` — `base = out.parent`: görsel yolları **girdi markdown'ının** değil **çıktı klasörünün** altında çözülüyor (`:332` ve `_add_image` `:415-425` da bu `base`'i kullanıyor). `--out` başka bir klasör verildiğinde (docstring `convert.py:12` bunu açıkça öneriyor) DOCX'e hiç görsel gömülmüyor, HTML'in `images/...` yolları da çıktı klasörüne kopyalanmadığı için kırılıyor; buna rağmen çıkış kodu **0** ve mesaj **"Tamam."**.
- **Kanıt (gerçek çalıştırma):** `--out <geçici-dizin>` → `EXIT=0`, docx 38365 bayt, `MEDIA_COUNT 0`, `missing_markers 6`. Aynı komut varsayılan `--out` ile 153225 bayt ve 6 gömülü görsel veriyor.
- **Öneri:** Görselleri `src.parent`'a göre çöz; `--out` farklı klasörse `images/` ağacını hedefe kopyala veya en azından WARNING basıp çıkış kodunu 1 yap; docstring'deki `--out` örneğini bu davranışla uyumlu hale getir.

### ORTA

**ORTA-1 — Yeniden adlandırılan ekran görüntüleri "kullanılmayan" diye hata veriyor (yanlış pozitif).**
- `screenshot-to-manual/scripts/check_manual.py:170-187` — `check_coverage` yalnızca **dosya adı** eşleştiriyor; kılavuzun `images/` altındaki kopyalarının adları orijinal ekranlarla aynı olmak zorunda. Oysa `SKILL.md:53` çıktıyı "Kopyalanmış/**yeniden adlandırılmış** ekran görüntüleri" olarak tanımlıyor. Ad değişince doğru kılavuz FAIL oluyor.
- **Kanıt:** `test/output/kilavuz.md` kopyasında yalnızca `images/01-giris.png` → `images/giris-ekrani.png` yapıldı; checker `[ERROR] Hiç kullanılmayan ekran görüntüsü: 01-giris.png` verdi.
- **Öneri:** Eşleştirmeyi içerik hash'iyle yap veya `--screenshots` yanında `images/` kopyalarını da kabul eden bir eşleme/`--image-map` seçeneği ekle; ya da SKILL.md'de "kopyalarken adları değiştirme" kuralını netleştir.

**ORTA-2 — Karşılaştırma operatörleri (`< 10 >`) yer tutucu sanılıp ERROR üretiyor (yanlış pozitif).**
- `screenshot-to-manual/scripts/check_manual.py:139-148` — `re.finditer(r"<([^<>\n]{1,80})>", line)` satırı bağlamdan bağımsız tarıyor; HTML etiketi/URL dışındaki her `<...>` yer tutucu sayılıyor (inline kod ve düz metindeki `x < 10 > 5` dahil). Bu, geçerli bir kılavuzu "düzelt ve tekrar çalıştır" döngüsüne sokar (`SKILL.md:188`).
- **Kanıt:** `Koşul \`x < 10 > 5\` ise ...` satırı için `[ERROR] Doldurulmamış yer tutucu: <10> (satır 7)` **iki kez** üretildi.
- **Öneri:** Kontrolden önce inline kod span'lerini çıkar; `<...>` yerine yalnızca bilinen yer tutucu kalıplarını (ör. `<[A-ZÇĞİÖŞÜ][^>]*>`, `<\.\.\.>`, `<\d+-[a-z-]+>`) hedefle; en azından `<\s*\d+\s*>` gibi sayısal karşılaştırmaları hariç tut.

**ORTA-3 — Adım numaralandırması global 1..N varsayılıyor; bölüm başına sıfırlanan numaralandırma yanlış pozitif veriyor.**
- `screenshot-to-manual/scripts/check_manual.py:108-114` — `steps` tüm belge boyunca sıralı sayılıyor ve `num != idx` ise ERROR. `SKILL.md:168` ise "numaralandırmayı **referansla aynı** şemada tut" diyor; referans bölüm başına `Adım 1`'den başlıyorsa doğru kılavuz FAIL olur. `check_reference` (`:258-262`) yalnızca "Adım başlığı var mı" diye bakıyor, şemayı karşılaştırmıyor.
- **Kanıt:** İki bölümde `Adım 1, 2` kullanan sentetik kılavuz → `[ERROR] Adım numarası sırası bozuk: 3. adım '1' numaralı`, `4. adım '2' numaralı`.
- **Öneri:** `##` başlığında sayacı sıfırla (veya `--step-numbering global|per-section` seçeneği ekle) ya da sıralamayı referansın şemasını okuyarak doğrula.

**ORTA-4 — SKILL.md/README'deki QA komutlarının çalışma dizini belirsiz; yazıldığı gibi koşulunca çalışmıyor.**
- `screenshot-to-manual/SKILL.md:183` (`python scripts/check_manual.py kilavuz.md ...`) ve `README.md:133-139` (`python scripts/check_manual.py cikti/kilavuz.md ...`) — betik yolu **skill klasörüne**, kılavuz yolu ise **proje/çıktı klasörüne** göreli; aynı komutta iki farklı kök varsayılıyor ve hiçbir yerde "skill klasöründen çalıştır" denmiyor.
- **Kanıt:** Proje kökünden `python scripts/check_manual.py ...` → `can't open file '...\scripts\check_manual.py'`, çıkış 2.
- **Öneri:** Komutları `<skill-dizini>/scripts/check_manual.py <cikti>/kilavuz.md ...` biçiminde veya "komutları skill klasöründen çalıştır" notuyla ver.

**ORTA-5 — `--format pdf` tek başına hiç dönüştürme denemiyor ve kullanıcıya doğru yönlendirme vermiyor.**
- `screenshot-to-manual/scripts/convert.py:527-535` — `:530` koşulu (`docx_path.is_file() or ("docx" in formats and to_docx(...))`) yalnızca `pdf` istendiğinde ve ortada DOCX yoksa `False` kalıyor; `to_pdf_via_soffice` hiç çağrılmıyor, dolayısıyla `to_pdf_via_soffice` içindeki "LibreOffice bulunamadı → Ctrl+P" mesajı (`:472`) hiç basılmıyor. Kullanıcı yalnızca genel "bazı formatlar üretilemedi" uyarısı görüyor.
- **Kanıt:** `convert.py test/output/kilavuz.md --format pdf --out <tmp>` → yalnızca `kilavuz.html`, genel `UYARI`, `EXIT=1`; LibreOffice/pandoc mesajı yok.
- **Öneri:** `pdf` istendiğinde DOCX'i gerektiğinde üret (python-docx yoksa doğrudan html yazdırma önerisi ver) veya koşulu `("docx" in formats or "pdf" in formats)` olacak şekilde düzelt ve tanı mesajını her durumda yazdır.

### KÜÇÜK

**KÜÇÜK-1 — "Açık Sorular" bölümü yokken gövdedeki `[?]` işaretleri hiç raporlanmıyor (erken dönüş).**
- `screenshot-to-manual/scripts/check_manual.py:197-200` — bölüm yoksa `no-open-questions` uyarısı bırakılıp `return False` ile çıkılıyor; `:202-205`'teki gövde taraması hiç çalışmıyor.
- **Kanıt:** `test/negative/bozuk-kilavuz.md:21` gövdede `[?]` var; çıktıda `open-q-marker-in-body` uyarısı **yok**, yalnızca "bölüm yok" uyarısı var.
- **Öneri:** Erken dönüşü kaldır; bölüm yoksa da gövde `[?]` taramasını yap (veya tek bir uyarıda birleştir).

**KÜÇÜK-2 — Boşluk içeren görsel yolları hiç eşleşmiyor; kırık yol sessizce atlanıyor.**
- `screenshot-to-manual/scripts/check_manual.py:38` — `IMAGE_RE` yol kısmında `[^)\s]+` kullanıyor; `![Giriş](images/01 giris.png)` gibi yaygın bir Windows dosya adı hiç yakalanmıyor, dolayısıyla "görsel bulunamadı" denetimi devre dışı kalıyor.
- **Kanıt:** sentetik girdide `images/01 giris.png` (mevcut olmayan dosya) için `missing-image` bulgusu üretilmedi; yalnızca kapsam denetimi "kullanılmayan ekran" dedi.
- **Öneri:** Yolu tırnak/parantezle sınırlayan daha esnek bir kalıp kullan (`!\[[^\]]*\]\(\s*(?:<([^>]+)>|([^)]+?))(?:\s+"[^"]*")?\s*\)`) veya yolu boşluklara göre kesmeyi bırak.

**KÜÇÜK-3 — Aynı satır için aynı bulgu birden çok kez üretiliyor (gürültü).**
- `screenshot-to-manual/scripts/check_manual.py:139-148` — satırdaki her `<...>` eşleşmesi ayrı ERROR; aynı metin iki kez geçince iki özdeş satır yazılıyor.
- **Kanıt:** `x < 10 > 5` iki kez geçen satır → iki adet `Doldurulmamış yer tutucu: <10> (satır 7)`.
- **Öneri:** `(line, message)` bazında tekilleştir.

**KÜÇÜK-4 — Bazı başlık numaralandırma şemaları hiç denetlenmiyor (sessiz yanlış negatif).**
- `screenshot-to-manual/scripts/check_manual.py:39,44,100` — yalnızca `## N.` (H2_NUM_RE) ve `## Bölüm/Chapter N` (BOLUM_RE) tanınıyor; `## 1 — Başlarken`, `## Kısım 1`, `## Part 1` gibi şemalarda numaralandırma kontrolü tamamen atlanıyor.
- **Kanıt:** `## 1 —` ve `## 2 —` kullanan sentetik kılavuzda numaralandırma bulgusu hiç üretilmedi (yalnızca adım numaralandırması konuştu).
- **Öneri:** Ayırıcı olarak `.`, `—`, `-`, `:`, `)` kabul eden ortak bir başlık-numarası kalıbı kullan; desteklenmeyen şemada "denetlenemedi" uyarısı ver.

**KÜÇÜK-5 — `--reference` olarak `.docx`/`.pdf` verilince metin gibi okunup yanıltıcı uyarılar üretiyor.**
- `screenshot-to-manual/SKILL.md:35` referansın `.docx`/`.pdf` olabileceğini söylüyor; `SKILL.md:183` ise aynı dosyayı doğrudan `--reference`'a veriyor. `check_manual.py:298-305` dosyayı `read_text(utf-8, errors="replace")` ile okuyor; DOCX içeriği anlamsız metne dönüşüp şema uyarıları üretiyor.
- **Kanıt:** `--reference test/output/kilavuz.docx` → `Adım başlığı şeması referansla uyuşmuyor`, `Referansta olmayan uyarı kutusu tipi: 'not'`, `'uyarı'` (3 uyarı, hepsi yanıltıcı).
- **Öneri:** `--reference` için `.docx/.pdf` verilirse "önce .md/.txt'ye çevir" uyarısı ver (veya python-docx ile oku); SKILL.md Adım 6'da referansın metin sürümünün geçilmesini söyle.

**KÜÇÜK-6 — Skill paketinde `__pycache__` var.**
- `screenshot-to-manual/scripts/__pycache__/check_manual.cpython-314.pyc`, `convert.cpython-314.pyc` — platforma/sürüme bağlı derlenmiş bayt kodu skill klasöründe taşınıyor.
- **Kanıt:** `Get-ChildItem screenshot-to-manual/scripts/__pycache__` → 2 `.pyc` (cpython-314).
- **Öneri:** Paketten çıkar ve `__pycache__/` + `*.pyc` için `.gitignore` ekle.

**KÜÇÜK-7 — HTML çıktısı her zaman `lang="tr"`.**
- `screenshot-to-manual/scripts/convert.py:285` — `<html lang="tr">` sabit; oysa `SKILL.md:210` kılavuz dilinin kullanıcının istediği dil olmasını emrediyor (İngilizce kılavuz da üretilebilir).
- **Kanıt:** İngilizce içerikli girdi de aynı sabit etiketi alır (kod satırı).
- **Öneri:** `lang` değerini `--lang` parametresi veya basit dil algılama ile belirle; varsayılan `tr` kalsın.

**KÜÇÜK-8 — Ekran görüntülerini `images/` altına kopyalama adımı iş akışında açıkça yok.**
- `screenshot-to-manual/SKILL.md:50-57` çıktı ağacında `images/` "kopyalanmış" diyor, `:102` yalnızca klasörü **oluştur** diyor, `:166` doğrudan `images/...` yolu kullanıyor; "hangi dosyayı nereye kopyala" adımı hiçbir yerde tarif edilmiyor. Ajan, orijinal ekran klasörüne göreli yol yazarsa taşınabilirlik kuralı (`:209`) ve çıktı yapısı bozulur.
- **Kanıt:** Doküman okuması; Adım 1/5 arasında kopyalama talimatı yok.
- **Öneri:** Adım 1'e "her ekranı `images/` altına kopyala (adları koru)" maddesi ekle; ORTA-1 ile birlikte adlandırma kuralını netleştir.

**KÜÇÜK-9 — SKILL.md, `[?]` işaretini "kalıntı" gibi sunuyor; oysa `[?]` bilinçli bir belirsizlik işareti ve gövdede yalnızca uyarı.**
- `screenshot-to-manual/SKILL.md:187` — "`TODO`/`[?]` kalıntısı var mı" deniyor; gerçekte `[?]` "Açık Sorular" bölümünde serbest, gövdede WARNING (`check_manual.py:201-205`) ve tek başına çıkış kodunu düşürmüyor (`:309`). `Kesin kural 4` (`:207`) ve Adım 5.7-8 (`:172-175`) `[?]`'ı meşru kılıyor.
- **Kanıt:** `test/output/kilavuz.md` içinde 2 `[?]` var → `PASS hata=0 uyarı=0`.
- **Öneri:** İfadeyi "`TODO`/`XXX`/`<yer tutucu>` kalıntısı; `[?]` yalnızca Açık Sorular'da" olarak düzelt.

---

## 5. Doğrulanamayanlar / sınırlar

- **Ağ erişimi yok** (web arama HTTP 402 verdi): Codex/Cursor'ın `~/.agents/skills` / `~/.cursor/skills` yolları, `disable-model-invocation` alanını gerçekten okuyup okumadığı ve Codex'in görsel aracının adı **bağımsız doğrulanamadı**. Bu nedenle bunlar bulgu olarak yazılmadı.
- **Görsel okuma adımı** gerçek bir multimodal modelle koşulmadı (bu oturum görselleri okuyamıyor); yalnızca üretim/denetim zinciri test edildi. `test/RESULT.md:80-83` de bunu aynı şekilde sınır olarak belirtiyor.
- **PDF yolu** LibreOffice/pandoc olmadığı için üretilemedi; yalnızca hata davranışı test edildi (ORTA-5 ve test 9).
- **DOCX görsel render'ı** LibreOffice olmadığı için görsel olarak doğrulanamadı; yapısal doğrulama yapıldı (6 `pic:pic`, 6 `word/media`, alt yazı/metin varlığı).

## 6. Değişiklik beyanı

- `screenshot-to-manual/` altındaki hiçbir dosya değiştirilmedi, taşınmadı, silinmedi.
- `test/` altında yalnızca bu dosya (`test/VERIFY.md`) oluşturuldu. Test çıktıları (`kilavuz.html`, `kilavuz.docx`, fixtürler) geçici dizinlere yazıldı; mevcut `test/output/` dosyaları korundu (HTML çıktısı bayt düzeyinde yeniden üretildi, MD5 eşleşti).

---

# Round 2 — Düzeltmelerin yeniden doğrulanması

- **Tarih:** 2026-11-03 (Round 1 raporundan sonra)
- **Yöntem:** Düzeltilmiş kaynaklar okundu; `test/run_tests.py` çalıştırıldı; Round 1 bulgularının her biri **bağımsız üretilen yeni girdilerle** yeniden test edildi. Tüm geçici girdiler/çıktılar `test/.tmp/` altında tutuldu; `screenshot-to-manual/` altına yazılmadı.
- **Sonuç:** **13 DOĞRULANDI, 2 KISMİ, 0 DOĞRULANAMADI.** Düzeltmelerin tamamı hedeflenen davranışı gösteriyor; ancak **1 ORTA regresyon** ve **5 KÜÇÜK yeni bulgu** var (aşağıda).
- **`test/run_tests.py`:** `TOPLAM 26 test | 26 PASS | 0 FAIL`, çıkış kodu 0. (Paket bütünlüğü testleri dahil; suite sonunda `test/.tmp/` kendini temizliyor.)

## 1. Round 1 bulgularının yeniden doğrulanması

| Round 1 bulgusu | Durum | Bağımsız kanıt (komut → gerçek çıktı) |
|---|---|---|
| **KRİTİK-1** `convert.py --out` görselleri kaybediyor | **DOĞRULANDI** | Bundled Python, `convert.py test/output/kilavuz.md --format docx,html --out test/.tmp/k1/out` → `EXIT=0`, `> 6 görsel çıktı klasörüne kopyalandı`, `Tamam.`; DOCX'te `MEDIA_COUNT 6`, `PIC 6`, `missing_markers 0`; çıktı `images/` altında 6 PNG; HTML'de eksik görsel 0. Varsayılan `--out` (girdi klasörü) regresyonu: kopyalanmış kılavuz üzerinde `MEDIA 6`, `MISSING 0`, `EXIT=0`. Kaynakta olmayan görsel: `! görsel kopyalanamadı (kaynak yok): images/99-yok.png`, `EXIT=1`. |
| **ORTA-1** Yeniden adlandırılmış görsel "kullanılmayan" sayılıyor | **DOĞRULANDI** | `images/01-giris.png` → `images/giris-ekrani.png` yeniden adlandırılmış kopyayla `check_manual.py` → `PASS hata=0 uyarı=0`, `(bulgu yok)`, `EXIT=0`. |
| **ORTA-2** `x < 10 > 5` yer tutucu sanılıyor | **DOĞRULANDI** | Hem satır içi kodda (`` `x < 10 > 5` ``) hem düz metinde (`x < 100 > 20`) → `Doldurulmamış` bulgusu yok. Gerçek yer tutucular hâlâ yakalanıyor: `<Urun Adi>`, `<01-ekran.png>` → 2 ERROR. **Ama bkz. yeni ORTA-6.** |
| **ORTA-3** Bölüm başına adım numaralandırma reddediliyor | **DOĞRULANDI** | Bölüm başına `Adım 1,2 / Adım 1,2` → `PASS hata=0`; global `Adım 1..5` → `PASS hata=0`; gerçek atlama (`1,2,4`) → `ERROR: Adım numarası sırası bozuk: '4'`; bölüm içi `1,3` → `ERROR: ... '3'`. Gevşeme gerçek hataları kaçırmıyor. |
| **ORTA-4** QA komutlarının çalışma dizini belirsiz | **DOĞRULANDI** | `SKILL.md:187-193` ve `README.md:131-145` artık "proje kökünden çalıştır" notu + `<skill-dizini>/scripts/...` biçiminde. Proje kökünden `python screenshot-to-manual/scripts/check_manual.py ...` ile tüm testler çalıştı (EXIT 0/1 beklendiği gibi). |
| **ORTA-5** `--format pdf` tek başına yönlendirme vermiyor | **DOĞRULANDI** | Bundled Python (docx var): `! LibreOffice bulunamadı; ... Ctrl+P → PDF ...`, `EXIT=1`. Sistem Python (docx yok): `! python-docx bulunamadı ...` + `! PDF için DOCX üretilemedi; '--format html' ... Ctrl+P ...`, `EXIT=1`. |
| **KÜÇÜK-1** Bölüm yokken gövdedeki `[?]` taranmıyor | **DOĞRULANDI** | "Açık Sorular" bölümü olmayan girdi → `[WARNING] [?] işareti gövdede; Açık Sorular bölümüne taşı (satır 5)` (bölüm yok uyarısıyla birlikte). |
| **KÜÇÜK-2** Boşluklu görsel yolu eşleşmiyor | **DOĞRULANDI** | Mevcut `img/01 giris.png` → `PASS hata=0`; olmayan `img/01 yok.png` → `ERROR Görsel dosyası bulunamadı: img/01 yok.png`. |
| **KÜÇÜK-3** Aynı satırda tekrarlanan bulgu | **DOĞRULANDI** | `<Urun> ve yine <Urun>` aynı satırda → `--json` çıktısında tek `"Doldurulmamış yer tutucu: <Urun>"`. Farklı yer tutucular (`<Urun>` + `<Tarih>`) ayrı ayrı raporlanıyor → dedupe gerçek ayrı bulguları birleştirmiyor. |
| **KÜÇÜK-4** `## 1 —` / `## 1)` şemaları denetlenmiyor | **DOĞRULANDI** | `## 1 —` + `## 3 —` → `ERROR Bölüm numarası sırası bozuk: 2. '3' numaralı`; `## 1)` + `## 2)` → `PASS hata=0`. |
| **KÜÇÜK-5** `.docx` referans metin gibi okunuyor | **KISMİ** | `reference-binary` uyarısı eklendi (`--reference test/output/kilavuz.docx` → `[WARNING] Referans .docx biçiminde; önce düz metne çevirin ...`), **ancak** aynı çalıştırmada eski yanıltıcı karşılaştırma hâlâ yapılıyor: `Bölüm numaralandırma şeması referansla uyuşmuyor`, `Adım başlığı şeması ... uyuşmuyor`, `Referansta olmayan uyarı kutusu tipi: 'not'`, `'uyarı'` → toplam 5 uyarı. **Bkz. KÜÇÜK-10.** |
| **KÜÇÜK-6** Pakette `__pycache__` | **DOĞRULANDI** | `screenshot-to-manual` altında `PYC=0 PYCACHE=0`; kök `.gitignore`'da `__pycache__/`, `*.py[cod]`, `test/.tmp/` var; `run_tests.py` iki testi de PASS. |
| **KÜÇÜK-7** HTML `lang` sabit `tr` | **KISMİ** | Kod bloğu olmayan girdi: `--lang en` → `<html lang="en">`. **Ama** kod bloğu varsa parametre eziliyor: son blok ```` ```python ```` ise `--lang en` → `<html lang="python">`; dilsiz son blok ise `--lang en` → `<html lang="tr">`. **Bkz. KÜÇÜK-11.** |
| **KÜÇÜK-8** Görselleri `images/` altına kopyalama adımı yok | **DOĞRULANDI** | `SKILL.md:103-106` artık "Görselleri kopyala ... adları koru ... Orijinal klasöre göreli yol yazma" maddesini içeriyor; `SKILL.md:209-210` de `--out`/`--lang` davranışını belgeliyor. |
| **KÜÇÜK-9** `[?]` "kalıntı" gibi sunuluyor | **DOĞRULANDI** | `SKILL.md:195-198` artık "`TODO`/`XXX`/`<yer tutucu>` kalıntısı; `[?]` işaretleri Açık Sorular'da" ayrımını yapıyor; `test/output/kilavuz.md` (2 `[?]`) hâlâ `PASS hata=0 uyarı=0`. |

## 2. Round 2'de bulunan yeni sorunlar

> Biçim: **Dosya:satır — sorun — öneri**

### ORTA

**ORTA-6 (regresyon) — Sayısal/`...` yer tutucular artık hiç yakalanmıyor.**
- `screenshot-to-manual/scripts/check_manual.py:70` (`MATH_INNER_RE` yalnızca rakam/noktalama kabul ediyor) ve `:215-224` — `<1.0>`, `<1>`, `<2024-01-01>`, `<...>` gibi gerçek yer tutucular "karşılaştırma" sayılıp atlanıyor. ORTA-2 düzeltmesi, operatör içermeyen sayısal yer tutucuları da yuttu.
- **Kanıt:** `Surum <1.0> · Tarih <2024-01-01> · Sayi <1> · Bosluk <...> · Gercek <Urun Adi>` → yalnızca `<Urun Adi>` ERROR olarak raporlandı (diğer 4'ü sessizce geçti). Şablonda `Doldurulmamış` bulgu sayısı Round 1'de **29** iken şimdi **25**; fark = artık raporlanmayan `<1.0>` + üç `<...>`. Şablondaki toplam hata 32 → 28; kalan 3 hata değişmeyen görsel-yolu hataları.
- **Öneri:** Yalnızca gerçek karşılaştırmayı atla: inner'da `[<>]=?` veya `[+*/]` gibi bir **operatör** ara (ör. `^\d+\s*[<>]=?\s*\d+$`); `...`, `<1.0>`, tarih ve tek sayı biçimlerini yer tutucu olarak raporlamaya devam et.

### KÜÇÜK

**KÜÇÜK-10 — `.docx/.pdf` referansta uyarı eklense de yanıltıcı karşılaştırma sürüyor (KÜÇÜK-5'in kalanı).**
- `screenshot-to-manual/scripts/check_manual.py:400-409` — `reference-binary` uyarısı eklendikten sonra `check_reference()` yine de ikili dosyanın `errors="replace"` metniyle çalıştırılıyor; sonuç 4 adet anlamsız uyarı daha.
- **Kanıt:** yukarıdaki KÜÇÜK-5 satırı (5 uyarı).
- **Öneri:** İkili uzantıda `check_reference` çağrısını atla (`continue`/`else`), yalnızca `reference-binary` uyarısını bırak.

**KÜÇÜK-11 — `--lang` kod bloğu olan belgelerde eziliyor (değişken gölgeleme).**
- `screenshot-to-manual/scripts/convert.py:246,258,296` — `to_html(text, title, lang)` parametresi `lang`, kod bloğu dalında `lang, code = payload` ile eziliyor; sonda `html.escape(lang or 'tr')` parametre yerine son kod bloğunun dilini kullanıyor.
- **Kanıt:** `--lang en` + son blok ```` ```python ```` → `<html lang="python">`; son blok dilsiz ise → `<html lang="tr">` (yine `en` değil); kod bloğu yoksa `<html lang="en">`.
- **Öneri:** Kod bloğu dalında farklı bir ad kullan (`fence_lang`), sonda parametreyi kullan.

**KÜÇÜK-12 — İçerik hash'i, aynı içerikli ikinci ekranın kullanılmadığını gizliyor (yanlış negatif).**
- `screenshot-to-manual/scripts/check_manual.py:255-285` — kapsam kontrolü ad VEYA SHA-256 ile eşleşmeyi kabul ediyor; iki ekran görüntüsü bayt düzeyinde aynıysa biri hiç kullanılmasa da "kullanıldı" sayılıyor.
- **Kanıt:** `test/.tmp/o1/hash/shots/` altına bayt düzeyinde aynı `a.png` + `b.png`; kılavuz yalnızca `images/a.png` kullanıyor → `PASS hata=0 uyarı=0`, "kullanılmayan ekran" bulgusu yok (`Ekranlar: 2/1`). (Beklenen: `b.png` için uyarı/hata.)
- **Öneri:** Hash eşleşmesini yalnızca ad eşleşmediğinde ve kullanıcı bunu açıkça istediğinde (`--match-by-hash`) uygula; varsayılanda hash eşleşince "içerik aynı" uyarısı ver, sessizce PASS verme. En azından aynı hash'e sahip birden fazla ekran varsa uyarı bas.

**KÜÇÜK-13 — `_mirror_images` `../` içeren yolları `--out` klasörünün dışına kopyalıyor.**
- `screenshot-to-manual/scripts/convert.py:473-502` — `rel` normalize edilip `out_dir` içinde kalıp kalmadığı denetlenmiyor; `![x](../pic.png)` hedefi `out_dir`'in üstüne yazılıyor.
- **Kanıt:** `test/.tmp/reg/src/kilavuz.md` (`![Ust](../pic.png)`), `--out test/.tmp/reg/deep/out` → `> 1 görsel çıktı klasörüne kopyalandı`, dosya `test/.tmp/reg/deep/pic.png` (yani `deep/out` **dışında**) oluştu, `EXIT=0`.
- **Öneri:** `rel` içinde `..` varsa veya `(out_dir / rel).resolve()` `out_dir.resolve()` altında değilse kopyalamayı reddet ve uyarı ver.

**KÜÇÜK-14 — İki kullanıcı mesajı kafa karıştırıcı.**
- `screenshot-to-manual/scripts/check_manual.py:199-204` — adım hatasında `local == position` iken "beklenen 3 veya 3" gibi tekrarlı değer yazıyor.
- `screenshot-to-manual/scripts/check_manual.py:433` — "Ekranlar: 6/1 klasör kullanıldı" ifadesi "6 görsel / 1 klasör" demek istiyor ama "6/1 klasör" gibi okunuyor (Round 1'deki "6 dosya, 1 klasör" daha netti).
- **Kanıt:** `[ERROR] Adım numarası sırası bozuk: '4' (beklenen 3 veya 3) (satır 7)`; `Ekranlar    : 6/1 klasör kullanıldı`.
- **Öneri:** Beklenen değerler aynıysa tek değer yaz; durum satırını `Ekranlar: 6 görsel kullanıldı (1 klasör)` biçimine çevir.

## 3. Round 2 kapsamı / sınırlar

- Düzeltmelerin **dosya içeriği** doğrulandı; canlı Claude Code/Cursor/Codex yüklemesi yine test edilmedi (ağ yok, HTTP 402).
- `--out` kopyalama, DOCX gömme, hash eşleşmesi, adım numaralandırma gevşemesi ve dedupe davranışı gerçek dosyalarla, sistem ve bundled Python'da ayrı ayrı koşuldu.
- Round 2 geçici dosyaları `test/.tmp/` altında üretildi; `screenshot-to-manual/` altındaki dosyalara yazılmadı (skill dosyalarının son değişiklik zamanları 16:47 ve öncesi; benim oturumum 16:48'de başladı).

---

# Round 3 — Kalan 6 bulgunun doğrulanması (kapanış)

- **Tarih:** 2026-11-03
- **Yöntem:** Yalnızca Round 2'deki 6 düzeltme, `test/.tmp/r3/` altında **bağımsız üretilen yeni girdilerle** doğrulandı; geniş yeni denetim yapılmadı. Komutlar `python -B` ile çalıştırıldı (skill klasöründe `__pycache__`/`.pyc` oluşmadı: `PYC=0`, `PYCACHE=0`).
- **`test/run_tests.py`:** `TOPLAM 39 test | 39 PASS | 0 FAIL`, çıkış kodu 0.
- **Sonuç:** **6/6 DOĞRULANDI, 0 KISMİ, 0 DOĞRULANAMADI.** Yeni KRİTİK/ORTA bulgu **yok**. 2 KÜÇÜK not var (kapanışa engel değil).

## 1. Düzeltme doğrulamaları

| # | Düzeltme | Durum | Bağımsız kanıt (komut → gerçek çıktı) |
|---|---|---|---|
| 1 | **ORTA-6** `_is_comparison()` — sayısal/`...` yer tutucular yeniden yakalanıyor, gerçek karşılaştırmalar atlanıyor | **DOĞRULANDI** | `Sürüm <1.0> sürümü. Ayrıca <2.0> sürümü var. Sayı <1>. Tarih <2024-01-01>. Boşluk <...>. Miktar <10> adet.` → **6 ERROR**: `<1.0>`, `<2.0>`, `<1>`, `<2024-01-01>`, `<...>`, `<10>` (satır 5). `x < 10 > 5`, `x < 100 > 20`, `10 < 20 > 30` → `PASS hata=0 uyarı=0`. Yani "ardından harf gelen" `<1.0>` de yakalanıyor. |
| 2 | **KÜÇÜK-10** `.docx/.pdf` referansta yalnızca `reference-binary`, karşılaştırma yok | **DOĞRULANDI** | `check_manual.py test/output/kilavuz.md --screenshots test/fixtures/ekranlar --reference test/output/kilavuz.docx` → `PASS hata=0 uyarı=1`; tek uyarı: `Referans .docx biçiminde; önce düz metne çevirin ... Stil karşılaştırması atlandı.` Eski "uyuşmuyor" / "uyarı kutusu tipi" uyarıları **yok**. |
| 3 | **KÜÇÜK-11** `fence_lang` — `--lang` kod bloğu varken de korunuyor | **DOĞRULANDI** | `convert.py ... --format html --lang en`, belgede ```` ```python ```` + dilsiz ```` ``` ```` blokları varken → `<html lang="en">` (`EXIT=0`). Değişken gölgeleme kalmamış (`convert.py:258-262`). |
| 4 | **KÜÇÜK-12** hash eşleşmesinde `duplicate-content` WARNING (sessiz PASS yok) | **DOĞRULANDI** | `shots/` içinde bayt düzeyinde aynı `01-giris.png` + `01-giris-kopya.png`, kılavuz yalnızca `01-giris.png` → `PASS hata=0 uyarı=1`, `[WARNING] 01-giris-kopya.png içerik olarak 01-giris.png ile aynı; kılavuzda gerçekten bu ekran mı kullanıldı doğrula`, `Ekranlar: 2/2`. Kopya yokken (1/1) ve iki ekran da adıyla kullanılırken (3/3) uyarı **yok** — normal akış gürültüsüz. |
| 5 | **KÜÇÜK-13** `_mirror_images()` `../` hedefini reddediyor, dışarı yazmıyor, kod 1 | **DOĞRULANDI** | `![Ust](../pic.png)` + `--out test/.tmp/r3/k13/deep/out` → `EXIT=1`, `! görsel kopyalanamadı (kaynak yok): ../pic.png (çıktı klasörü dışına çıkıyor)`; `deep/` altında yalnızca `out/kilavuz.html` var, `deep/pic.png` **oluşmadı**. Meşru `images/01-giris.png` akışı: `--format html,docx --out ...` → `EXIT=0`, `> 1 görsel çıktı klasörüne kopyalandı`, DOCX üretildi. |
| 6 | **KÜÇÜK-14** adım mesajı tekrarsız, durum satırı net | **DOĞRULANDI** | `Adım 1,2,4` → `[ERROR] Adım numarası sırası bozuk: '4' (beklenen 3) (satır 7)` (artık "3 veya 3" yok). Durum satırları: `Ekranlar    : 6/6 görsel kullanıldı (1 klasör)`; `--screenshots` yokken `0/0 görsel kullanıldı (0 klasör)`; JSON'da `"screenshots_used": 6`, `"screenshots_total": 6`. |

## 2. Regresyon kontrolü

- **`_is_comparison()` yanlış negatif üretmiyor:** `<1.0>`, `<2.0>`, `<1>`, `<2024-01-01>`, `<...>` ve "Sürüm `<1.0>` sürümü" gibi ardından harf gelen biçimler yer tutucu olarak yakalanıyor; `x < 10 > 5` / `x < 100 > 20` / `10 < 20 > 30` karşılaştırma sayılıp atlanıyor. (Tek sınır durumu için KÜÇÜK-16.)
- **`duplicate-content` gürültüsü:** Normal akışta (adıyla kullanılan görseller, kopya yok) uyarı üretmiyor. Yalnızca adı kullanılmayan kopyalar için uyarı veriyor; her kopya için ayrı satır yazdığı için çok kopyalı arşivlerde doğrusal artıyor (KÜÇÜK-15, engel değil).
- **`../` reddi meşru akışı bozmuyor:** `images/...` yoluyla normal kopyalama ve DOCX gömme çalışıyor (EXIT 0); yalnızca çıktı klasörü dışına çıkan yollar reddediliyor (EXIT 1 + açıklayıcı mesaj).
- **Paket bütünlüğü:** `run_tests.py` 39/39 PASS; doğrulama sonrası `screenshot-to-manual/` altında `PYC=0`, `PYCACHE=0`; skill dosyalarına yazılmadı.

## 3. Yeni bulgular (yalnızca KÜÇÜK — kapanışa engel değil)

**KÜÇÜK-15 — `duplicate-content` uyarısı kopya başına üretiliyor (grup başına değil).**
- `screenshot-to-manual/scripts/check_manual.py:301-315` — her kopya için ayrı uyarı yazılıyor ve her uyarı diğer tüm "ikiz"leri listeliyor.
- **Kanıt:** 5 bayt-özdeş dosya (`a.png` + `kopya1..4.png`), kılavuz yeniden adlandırılmış tek kopyayı kullanıyor → **5 uyarı**, her biri diğer 4 dosyayı listeliyor (`PASS hata=0 uyarı=5`). Tek ikizde 1 uyarı (gürültüsüz).
- **Öneri:** Hash grubu başına tek uyarı üret (ör. "bu içerikten N kopya var: ..."); engelleyici değil.
- **Kapanışa engel değil** (yalnızca WARNING, çıkış kodu 0).

**KÜÇÜK-16 — `_is_comparison()` sınırı: ardından sayı değil harf gelen karşılaştırma yer tutucu sayılıyor.**
- `screenshot-to-manual/scripts/check_manual.py:232-245` — "sonrasında rakam" koşulu (`COMPARISON_AFTER_RE = r"\s*\d"`) nedeniyle `x < 10 > y` gibi ifadeler `[ERROR] Doldurulmamış yer tutucu: <10>` üretiyor.
- **Kanıt:** `Koşul x < 10 > y sağlanırsa devam edin.` → `FAIL hata=1`, `<10>` yer tutucu. `x < 10 > 5` ise sorunsuz geçiyor.
- **Öneri:** İsteğe bağlı iyileştirme (düşük öncelik): `>` sonrası tanımlayıcı harf de kabul edilebilir; ancak bu, "Sürüm `<1.0>` sürümü" gibi gerçek yer tutucuları kaçırma riski taşıdığı için mevcut muhafazakâr davranış bilinçli bir denge olarak kabul edilebilir.
- **Kapanışa engel değil** (uç durum; kullanım kılavuzlarında değişkenli karşılaştırma çok nadir).

## 4. Round 3 kapsamı / sınırlar

- Yalnızca 6 düzeltme doğrulandı; canlı Claude Code/Cursor/Codex yüklemesi yine test edilmedi (ağ yok, HTTP 402).
- Tüm geçici girdi/çıktılar `test/.tmp/r3/` altında üretildi; `screenshot-to-manual/` altına yazılmadı, `python -m py_compile` çalıştırılmadı.
- **Kapanış değerlendirmesi:** Round 2'deki 6 bulgu kapanmıştır. Yeni KRİTİK/ORTA yok; yalnızca iki KÜÇÜK iyileştirme notu (KÜÇÜK-15, KÜÇÜK-16) kapanışa engel değildir.
