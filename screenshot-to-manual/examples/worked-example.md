# Dolu Örnek / Worked Example

Küçük ama uçtan uca: 4 ekran görüntüsü + 1 örnek kılavuz → 1 yeni kılavuz.
Bu dosyayı, işe başlamadan önce **kalite çıtası** olarak oku.

*A small end-to-end run: 4 screenshots + 1 example manual → 1 new manual.
Read this as the quality bar before you start.*

---

## Girdi 1 — Ekran görüntüleri

```
ekranlar/
├── 01-giris.png
├── 02-dosya-sec.png
├── 03-yukleme.png
└── 04-basarili.png
```

## Girdi 2 — Örnek kılavuz (özet)

```markdown
# Rapor Takip Sistemi Kullanım Kılavuzu
## 1. Başlarken
### Adım 1 — Sisteme giriş yapın
Kullanıcı adınızı ve parolanızı girerek Giriş düğmesine tıklayınız.
![Giriş ekranı](images/giris.png)
> **Not:** Parolanızı 3 kez yanlış girerseniz hesap 10 dakika kilitlenir.
## 2. Sık Sorulan Sorular
```

**Çıkarılan stil sözleşmesi (kısa):**

| Alan | Gözlem |
|---|---|
| Hitap / kip | siz, "-iniz" kipi |
| Başlıklar | `## 1. Bölüm` / `### Adım N — Eylem` |
| Görsel | adımdan sonra, alt yazı YOK |
| Uyarı | `> **Not:**` |
| Son bölüm | SSS |

## Ara çıktı — Envanter

| # | Dosya | Ekran | Eylem | Durum | Adım |
|---|---|---|---|---|---|
| 1 | 01-giris.png | Giriş | Kimlik bilgileriyle giriş | önce | 1 |
| 2 | 02-dosya-sec.png | Dosya Seç | Göz At ile dosya seç | ara | 2 |
| 3 | 03-yukleme.png | Yükleme | Yükle'ye bas, ilerleme çubuğu | ara | 3 |
| 4 | 04-basarili.png | Başarılı | Tamam ile onayla | sonra | 4 |

Boşluk: yok. Belirsiz: yok.

## Çıktı — Yeni kılavuz

```markdown
# Belge Yükleme Modülü Kullanım Kılavuzu

> **Sürüm:** 1.0  •  **Hedef kitle:** Kayıtlı kullanıcılar

## 1. Başlarken

Bu bölümde sisteme girip ilk belgenizi yüklemeyi öğreneceksiniz.

**Ön koşullar**
- Aktif bir kullanıcı hesabı
- Yüklenecek dosya (en fazla 25 MB)

### Adım 1 — Sisteme giriş yapın

Kullanıcı adınızı ve parolanızı girerek **Giriş** düğmesine tıklayınız.

![Giriş](images/01-giris.png)

### Adım 2 — Dosyayı seçin

**Göz At** düğmesine tıklayıp yüklemek istediğiniz dosyayı seçiniz.

![Dosya seç](images/02-dosya-sec.png)

### Adım 3 — Yüklemeyi başlatın

**Yükle** düğmesine tıklayınız. İlerleme çubuğu tamamlandığında işlem biter.

![Yükleme](images/03-yukleme.png)

> **Not:** Yükleme sırasında sayfayı kapatmayınız.

### Adım 4 — Onayı tamamlayın

İşlem tamamlandığında görünen **Tamam** düğmesine tıklayınız.

![Başarılı](images/04-basarili.png)

## 2. Sık Sorulan Sorular

**Dosyam neden yüklenmiyor?**
25 MB sınırını aştığında yükleme reddedilir.

## Açık Sorular / Open Questions

Yok.
```

## Bu örnekten çıkarılacak dersler

1. Referansın "siz / -iniz" kipi ve alt yazısız görsel düzeni **korundu**.
2. Referansın SSS bölümü **korundu**; referansta olmayan tablo/sözlük **eklenmedi**.
3. Ekranlardaki etiketler (`Göz At`, `Yükle`, `Tamam`) birebir geçti; çevrilmedi.
4. Her ekran tam bir kez kullanıldı; hiçbiri artmadı.
5. Ekranda görünmeyen bir sınır değeri (25 MB) **ekran metninden** alındı;
   görünmeseydi `[?]` olacaktı.
