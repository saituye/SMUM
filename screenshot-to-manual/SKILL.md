---
name: screenshot-to-manual
description: >-
  Builds a new step-by-step user manual from screenshots, using a supplied
  example manual as the style and structure reference. Use when the user hands
  over screenshots together with an example manual, guide, or tutorial and asks
  for a new manual, guide, or documentation built from those images. Triggers:
  "kullanım kılavuzu", "kullanım kılavuzu oluştur", "ekran görüntülerinden
  kılavuz", "ekran resimleri", "ekran görüntüsü ekle", "adım adım kılavuz",
  "dokümantasyon üret", "user manual from screenshots", "screenshot to manual",
  "write a how-to guide from images", "document these screens".
disable-model-invocation: true
---

# Ekran Görüntüsünden Kullanım Kılavuzu / Screenshot → User Manual

Girdi: **ekran görüntüleri** + **örnek bir kullanım kılavuzu**. Çıktı: örnek
kılavuzun üslubunu ve yapısını taklit eden, ama içeriği ekran görüntülerinden
gelen **yeni bir kullanım kılavuzu**.

Input: **screenshots** + **one example manual**. Output: a **new manual** that
copies the example's style and structure while its content comes from the images.

Bu dosya iki dillidir: talimatlar Türkçe, kritik kurallar İngilizce olarak da
tekrarlanmıştır. Üretilen kılavuzun dili **kullanıcının istediği dildir**;
belirtilmediyse referans kılavuzun dili kullanılır.

---

## 1. Girdiler / Inputs

| Girdi | Zorunlu | Notlar |
|---|---|---|
| Ekran görüntüleri | ✅ | Klasör veya dosya listesi. Sıralama ipucu: dosya adı, zaman damgası, EXIF. |
| Örnek kullanım kılavuzu | ✅ | `.md`, `.txt`, `.docx`, `.pdf`, `.html`. Sadece **stil** kaynağıdır. |
| Ürün / süreç adı | ➖ | Yoksa ekranlardan çıkar, kullanıcıya doğrulat. |
| Hedef kitle ve dil | ➖ | Yoksa referans kılavuzdan çıkar. |
| Çıktı formatı | ➖ | Varsayılan: Markdown (+ istenirse `.docx` / yazdırılabilir `.html`). |

Eksik bilgiyi **sormadan önce çıkarmayı dene**. Yalnızca ekranlardan ve referans
kılavuzdan çıkarılamayan şeyleri sor; en fazla 3 soru.

*Infer before you ask. Ask at most 3 questions, only for what the images and the
reference manual cannot answer.*

---

## 2. Çıktılar / Outputs

```
<cikti-klasoru>/
├── kilavuz.md          # Ana teslim — yeni kullanım kılavuzu
├── images/             # Kopyalanmış/yeniden adlandırılmış ekran görüntüleri
├── kilavuz.html        # (isteğe bağlı) tarayıcıdan yazdırılabilir sürüm
├── kilavuz.docx        # (isteğe bağlı) Word sürümü
└── 00-analiz.md        # Çalışma notları: ekran envanteri + stil sözleşmesi
```

`00-analiz.md` teslim edilen bir belge değil, **denetlenebilir kanıt**tır: hangi
ekranın hangi adıma gittiğini ve referanstan hangi stil kararını aldığını
gösterir. Onu her zaman üret.

---

## 3. Araç eşlemesi / Tool mapping

Skill hiçbir araca özel yazılmadı. Elindeki karşılığı kullan:

| İhtiyaç | Claude Code | Cursor | Codex / DeepSeek Harness | Diğer |
|---|---|---|---|---|
| Görseli **gör** | `Read` (görsel) | `Read` | `read_image` | görseli mesaja ekle |
| Dosya yaz | `Write` / `Edit` | `Write` | `write` / `edit` | editör |
| Betik çalıştır | `Bash` | terminal | `pwsh` / `bash` | terminal |
| `.docx` / `.pdf` oku | `Bash` + python | terminal | `pwsh` + python | python |

**Kritik:** Görselleri mutlaka gerçekten *gör*. Dosya adından veya önceden
bildiğin bir arayüzden içerik uydurma.

*Always actually view the images. Never infer screen content from file names.*

---

## 4. İş akışı / Workflow

İlerlemeyi bu listeyle takip et:

```
- [ ] 1. Girdileri topla ve doğrula
- [ ] 2. Referanstan stil sözleşmesi çıkar
- [ ] 3. Her ekran görüntüsünü tek tek oku
- [ ] 4. Ekranları akışa diz, boşlukları işaretle
- [ ] 5. Kılavuzu yaz
- [ ] 6. QA kapısı — `check_manual.py`
- [ ] 7. Teslim (+ isteğe bağlı docx/html)
```

### Adım 1 — Girdileri topla ve doğrula / Intake & validate

- Ekran görüntüsü dosyalarını listele; sayıyı ve formatları raporla.
- Referans kılavuzu oku (`.docx` → python-docx, `.pdf` → pypdf/pdftotext, düz metin → doğrudan).
- Okunamayan veya bozuk dosya varsa **hemen** söyle, sessizce atlama.
- Çıktı klasörünü belirle ve `images/` alt klasörünü oluştur.
- **Görselleri kopyala:** kılavuzda kullanacağın her ekranı `images/` altına
  kopyala. Adları **koru** (ör. `01-giris.png` → `images/01-giris.png`); yeniden
  adlandırırsan QA betiği içerik hash'iyle eşleştirir ama sırayı kaybetmemek için
  adı korumak daha güvenlidir. Orijinal klasöre göreli yol **yazma**.

*List every screenshot, read the reference manual, report unreadable files,
create the output folder, then COPY each screenshot into `images/` keeping its
file name. Never link back to the original screenshots folder.*

### Adım 2 — Referanstan stil sözleşmesi çıkar / Extract the style contract

Referans kılavuzun **içeriğini kopyalamayacaksın**, **biçimini** kopyalayacaksın.
`reference/style-contract.md` dosyasındaki alanları doldur ve `00-analiz.md`'ye yaz:

- Başlık hiyerarşisi ve numaralandırma (`1.`, `1.1`, `Adım 1`, `Bölüm`)
- Adım cümlesi kipi (emir kipi mi, "tıklayın" mı, "tıklayınız" mı) ve uzunluğu
- Ekran görüntüsü yerleşimi: adımdan önce mi sonra mı, alt yazı var mı, numaralı mı
- Uyarı/ipucu kutusu tipleri (Not, Uyarı, İpucu, Dikkat) ve işaretleme biçimi
- Tablo, liste, kalın yazı kullanımı
- Ön bölüm: kapak, sürüm, tarih, içindekiler
- Son bölüm: sık sorulan sorular, sorun giderme, sözlük
- Ton: resmî / samimi, "siz" / "sen"
- Terim sözlüğü (referansın kullandığı adlandırma)

*Extract form, not content: hierarchy, numbering, step voice, image placement,
callout types, tables, front/back matter, tone, terminology.*

### Adım 3 — Her ekran görüntüsünü tek tek oku / Read every screenshot

Her görsel için `reference/screenshot-analysis.md` şemasına göre kaydet:

| Alan | Örnek |
|---|---|
| Dosya | `03-ayarlar.png` |
| Ekran / sayfa adı | Ayarlar |
| Görünen ana bileşenler | sol menü, kaydet düğmesi, dil açılır listesi |
| Yapılan eylem | "Dil" açılır listesinden Türkçe seçilir |
| Durum | önce / sonra / ara adım |
| Vurgu / ok / kutu | kırmızı çerçeve "Kaydet" düğmesinde |
| Okunamayan / belirsiz | alan adı bulanık → `[?]` |
| Adım no (taslak) | 4 |

**Uydurma yasağı:** Ekranda görünmeyen düğme adı, menü yolu, alan etiketi veya
hata mesajı yazma. Emin değilsen `[?]` koy ve "Açık sorular" bölümüne ekle.

*Never invent a button label, menu path, field name or message that is not
visible in the image. Mark uncertainty with `[?]` and list it under Open questions.*

### Adım 4 — Ekranları akışa diz / Order into a flow

- Sıralama sinyallerini kullan: dosya adı numarası → zaman damgası → ekran
  durumu (önce/sonra) → mantıksal akış.
- Ekranları **bölümlere** grupla (örn. Kurulum, İlk Ayarlar, Günlük Kullanım).
- **Boşlukları işaretle:** "1. adımdan 3. adıma geçerken ara ekran eksik" gibi.
  Eksik adımı uydurma; kullanıcıdan iste veya "Açık sorular" bölümüne yaz.
- Her ekranı **tam olarak bir** adıma bağla. Aynı ekran birden fazla adımı
  anlatıyorsa görseli tek adımda kullanıp metinde diğer adıma atıf yap.

*Order with file names → timestamps → before/after state. Group into sections.
Flag gaps instead of inventing steps. One screenshot maps to exactly one step.*

### Adım 5 — Kılavuzu yaz / Draft the manual

`templates/manual-template.md` iskeletini al, **Adım 2'deki stil sözleşmesiyle**
doldur. Kurallar:

1. Her adım = **tek eylem** + o eylemi gösteren **tek ekran görüntüsü**.
2. Adım metni kısa: 1–3 cümle. Gerekçe/teori gerekiyorsa ayrı "Neden?" notuna taşı.
3. Görsel yolu göreli ve taşınabilir: `![Ayarlar ekranı](images/03-ayarlar.png)`.
   Alt yazıyı referansın biçimine uydur.
4. Başlıkları ve numaralandırmayı referansla aynı şemada tut; **içeriği** ekrandan al.
5. Terimleri referansın sözlüğüyle birebir kullan — eş anlamlı uydurma.
6. Ön bölüm (başlık, sürüm, hedef kitle) ve son bölüm (SSS, sorun giderme,
   sözlük) referansta varsa ekle; yoksa ekleme.
7. Ekranlardan doğrulanamayan her bilgi `[?]` ile işaretlenir.
8. Kılavuzun sonuna **"Açık Sorular / Open Questions"** bölümü ekle (boşsa "Yok." yaz).
   Bu bölüm bir **QA ekidir**, referans üslubunun parçası değildir; yayına
   hazırlarken kullanıcı silebilir. Bunu teslim mesajında belirt.

*One step = one action + one screenshot. Relative image paths. Mirror the
reference's numbering and terminology. Mark unverifiable claims with `[?]`.*

### Adım 6 — QA kapısı / QA gate

Komutları **proje kökünden** çalıştır ve betik yolunu skill klasörüne göre tam
ver — betik ile kılavuz farklı klasörlerdedir:

```bash
python <skill-dizini>/scripts/check_manual.py <cikti>/kilavuz.md \
    --screenshots <ekran-klasoru> --reference <ornek-kilavuz.md>
```

Betik şunları denetler: görsel yolları var mı, her ekran en az bir kez
kullanılmış mı (ad **veya** içerik hash'i), başlık/bölüm numaralandırması sürekli
mi, adım numaralandırması tutarlı mı (global ya da bölüm başına), `TODO`/`XXX`/
`<yer tutucu>` kalıntısı var mı, `[?]` işaretleri "Açık Sorular" bölümünde mi.
Hata varsa **düzelt ve tekrar çalıştır**. Geçmeden teslim etme.

`--reference` olarak `.docx`/`.pdf` verme; önce düz metne çevir, yoksa stil
karşılaştırması anlamsız olur (betik bunu uyarı olarak söyler).

*Run the checker; fix and re-run until it passes. Do not deliver a failing manual.*

### Adım 7 — Teslim / Deliver

- `kilavuz.md` + `images/` + `00-analiz.md` hazır.
- İstenirse: `python <skill-dizini>/scripts/convert.py <cikti>/kilavuz.md --format docx,html`
  (`--out` başka klasörse görseller oraya da kopyalanır; `--lang` HTML dilini belirler).
  - `.docx` için python-docx gerekir; yoksa betik kurulum komutunu yazdırır.
  - `.html` her zaman üretilebilir ve tarayıcıdan **Ctrl+P → PDF** ile yazdırılır.
- Teslim mesajında: kaç ekran, kaç adım, kaç bölüm, kaç `[?]` ve eksik ekran varsa listesi.

---

## 5. Kesin kurallar / Hard rules

1. **Görmeden yazma.** Her ekran görüntüsünü gerçekten gör; dosya adından içerik çıkarma.
2. **Uydurma yok.** Ekranda olmayan etiket, menü, mesaj, sürüm veya sayı yazma.
3. **Biçim referanstan, içerik ekrandan.** Referans kılavuzun cümlelerini kopyalama.
4. **Belirsizlik görünür olsun.** `[?]` + "Açık Sorular" bölümü; sessiz tahmin yok.
5. **Bir ekran = bir adım.** Hiçbir görsel kullanılmadan kalmaz.
6. **Taşınabilir yollar.** `images/...` göreli yol; mutlak Windows yolu yazma.
7. **Kullanıcının dili.** Kılavuz dili istenen dilde; skill talimatlarının dili değil.
8. **Eksik girdiyi bildir.** Okunamayan dosya veya eksik ara ekran varsa söyle.
9. **Göremiyorsan dur.** Görsel okuma yeteneğin yoksa (araç yok veya model
   görsel desteklemiyor) kılavuz yazmaya **başlama**. Kullanıcıya bu oturumda
   görselleri okuyamadığını söyle ve görsel yetenekli bir oturum iste.
   Dosya adlarından tahminle içerik üretmek yasaktır.

*1 Never write without viewing. 2 Never invent UI. 3 Form from reference, content
from images. 4 Surface uncertainty. 5 One screenshot = one step, none unused.
6 Relative image paths. 7 Manual language = requested language. 8 Report gaps.*

---

## 6. Kalite kapısı / Quality gate

- [ ] Her ekran görüntüsü en az bir adımda kullanıldı
- [ ] Her adımın tek bir eylemi var ve emir kipinde yazıldı
- [ ] Tüm görsel yolları mevcut dosyalara çözülüyor
- [ ] Başlık numaralandırması sürekli ve referansla aynı şemada
- [ ] Terimler referans sözlüğüyle tutarlı
- [ ] `TODO`, `XXX`, `LOREM` kalıntısı yok
- [ ] `[?]` işaretleri "Açık Sorular" bölümünde listeli
- [ ] Kılavuz dili istenen dilde
- [ ] `check_manual.py` hatasız geçti

---

## 7. Dosya haritası / File map

| Dosya | Ne zaman okunur |
|---|---|
| [reference/style-contract.md](reference/style-contract.md) | Adım 2 — stil çıkarımı |
| [reference/screenshot-analysis.md](reference/screenshot-analysis.md) | Adım 3 — ekran okuma şeması |
| [templates/manual-template.md](templates/manual-template.md) | Adım 5 — çıktı iskeleti |
| [examples/worked-example.md](examples/worked-example.md) | Başlamadan önce — dolu örnek |
| [scripts/check_manual.py](scripts/check_manual.py) | Adım 6 — QA |
| [scripts/convert.py](scripts/convert.py) | Adım 7 — docx/html |
| [README.md](README.md) | Kurulum ve diğer AI araçlarına taşıma |

---

## 8. Sık hatalar / Failure modes

| Durum | Yapılacak |
|---|---|
| Model/araç görsel okuyamıyor | **Dur.** Kılavuz yazma. Kullanıcıya söyle, görsel yetenekli oturum iste. Tahminle üretmek yasak. |
| Ekran görüntüsü okunamıyor (bozuk/çok küçük) | Bildir, o adımı `[?]` ile bırak, kalanı üret |
| Referans kılavuz okunamıyor | Kullanıcıdan `.md`/`.txt` sürümünü iste; stil sözleşmesini varsayılanla kur ve bunu belirt |
| Ekranlar arasında sıra belirsiz | Zaman damgası/durum ile çıkar; hâlâ belirsizse "Açık Sorular"a yaz |
| Ekran sayısı adım sayısından çok | Birden fazla ekranı tek adımda gruplama yerine adımı böl |
| Kullanıcı çıktıyı Word istiyor, python-docx yok | `convert.py --format html` ile yazdırılabilir HTML üret, kurulum komutunu söyle |
| Ekranlarda kişisel veri var | Ad/soley/e-posta gibi alanları kılavuza taşımadan önce kullanıcıya sor |
