# Çalışma Notları — Envanter Takip Kılavuzu

> Bu dosya teslim edilen belge değil, **denetim izidir**. Hangi ekranın hangi
> adıma gittiğini ve referanstan hangi stil kararının alındığını gösterir.

Kaynak: `test/fixtures/ekranlar/` (6 görsel), `test/fixtures/ornek-kilavuz.md`.

---

## 1. Stil Sözleşmesi — ornek-kilavuz.md

| Alan | Gözlem | Kanıt |
|---|---|---|
| Belge dili | Türkçe | tümü |
| Ton | resmî, kısa | Bölüm 1–2 |
| Hitap | "siz", "-iniz" kipi | "tıklayınız", "giriniz" |
| Başlık hiyerarşisi | `#` ürün, `## Bölüm N — ad` | Bölüm 1 |
| Numaralandırma | `Bölüm N`, `**Adım N.**`, `Şekil N` | Bölüm 1–2 |
| Adım kipi | emir kipi, 1–2 cümle | "yazınız ve Enter tuşuna basınız" |
| Görsel yerleşimi | adımdan **sonra** | Bölüm 1 |
| Görsel alt yazısı | **var**: `Şekil N — açıklama`, görselin **üstünde** | Şekil 1 |
| Uyarı kutuları | `> **Uyarı:**`, `> **Not:**` | Bölüm 1, 2 |
| Ön bölüm | başlık + tek satır künye (`**Sürüm …** · **Son güncelleme:** … · **Hedef kitle:** …`) | baş |
| Son bölüm | `## Bölüm N — Sık Sorulan Sorular` + `Terim / Anlamı` tablosu | son |
| Terim sözlüğü | Şekil, SKU | son tablo |
| Görsel yolu | `images/<ad>.png` (göreli) | `![…](images/sek1-giris.png)` |

**Referansta olmayan, bu yüzden eklenmeyen öğeler:** içindekiler, sürüm geçmişi
tablosu, kod bloğu, renkli kutu, numaralı liste.

**Varsayılan iskeletten sapma:** `templates/manual-template.md` içindeki
`### Adım N` başlıkları **kullanılmadı**; referans `**Adım N.**` kalın metnini
kullanıyor. Biçim referanstan alındı.

---

## 2. Ekran Envanteri

| # | Dosya | Ekran | Yapılan eylem | Durum | Bölüm | Adım |
|---|---|---|---|---|---|---|
| 1 | 01-giris.png | Giriş | E-posta + parola girip **Giriş Yap** | önce | 1 | 1 |
| 2 | 02-panel.png | Panel | Özet kartlarını ve son hareketleri incele | ara | 1 | 2 |
| 3 | 03-urunler.png | Ürünler | **Yeni Ürün** düğmesine bas | ara | 2 | 3 |
| 4 | 04-yeni-urun.png | Yeni Ürün Ekle | Alanları doldur, **Kaydet** | ara | 2 | 4 |
| 5 | 05-kayit-basarili.png | Ürünler (onay) | **Tamam** ile onayla | sonra | 2 | 5 |
| 6 | 06-raporlar.png | Raporlar | Tarih aralığı + **Excel'e Aktar** | sonra | 3 | 6 |

- **Vurgular:** 03 (Yeni Ürün), 04 (Kaydet), 06 (Excel'e Aktar) kırmızı çerçeveli
  → adımlar bu öğeleri hedefliyor.
- **Kullanılmayan görsel:** yok. **Kullanılmayan adım:** yok.
- **Boşluk:** 05 sonrası listeye dönüş görüntüsü yok → `[?]` olarak işaretlendi.

## 3. Belirsizlikler

| # | Konu | Neden |
|---|---|---|
| 1 | Tamam'a basıldıktan sonra liste güncelleniyor mu? | Sonraki ekran görüntüsü yok |
| 2 | 04'teki onay kutusunun varsayılan durumu | Görselde işaretsiz çizilmiş; kesin değil |

## 4. QA sonucu

`check_manual.py` → FAIL→düzeltme→PASS. Ayrıntı: `test/RESULT.md`.
