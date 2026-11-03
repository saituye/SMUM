# Ekran Görüntüsü Analizi / Screenshot Analysis

Her görsel için aşağıdaki kaydı üret. Amaç: kılavuzu yazarken **hiçbir zaman
görsele geri dönmek zorunda kalmamak** ve uydurmamak.

*Produce one record per image, so drafting never requires guessing.*

## Kayıt şeması / Record schema

```markdown
### <dosya adı>
- **Ekran adı:** (başlık çubuğu, sekme veya sayfa başlığından)
- **Bölüm:** (hangi akışa ait)
- **Görünen bileşenler:** menü, düğme, alan, sekme — ekranda okunan adlarıyla
- **Yapılan eylem:** "X açılır listesinden Y seçilir"
- **Durum:** önce | ara | sonra
- **Vurgu:** kırmızı çerçeve / ok / numara — nereyi gösteriyor
- **Ön koşul:** bu ekrana gelmek için ne yapılmış olmalı
- **Sonuç:** bu adımdan sonra ekranda ne değişiyor
- **Belirsiz:** okunamayan alan → `[?]`
- **Taslak adım no:** N
```

## Okuma kuralları / Reading rules

1. **Yalnızca gördüğünü yaz.** Tahmin ettiğin etiketi `[?]` ile işaretle.
2. **Dili koru.** Ekrandaki etiketleri çevirme; kılavuzda ekranda yazdığı gibi geçsin
   (parantez içinde çeviri ekleyebilirsin: `Kaydet (Save)`).
3. **Eylemi çıkar, tarif etme.** "Ayarlar sayfası görünüyor" bir eylem değildir;
   "Ayarlar sayfasını açın" eylemdir.
4. **Vurguyu kullan.** Kırmızı çerçeve/ok varsa adım o öğeyi hedefliyor demektir.
5. **Durum ayrımı yap.** Aynı ekranın önce/sonra iki görüntüsü varsa ikisi tek
   adımın kanıtıdır; ikisini de kullan, ama adımı ikiye bölme.
6. **Kişisel veri.** Görünen gerçek ad, e-posta, müşteri no, lisans anahtarı
   kılavuza taşınmaz; kullanıcıya sor veya maskele (`kullanici@ornek.com`).
7. **Çözünürlük.** Yazı okunamıyorsa kullanıcıdan daha büyük görüntü iste; körlemesine yazma.

## Envanter tablosu / Inventory table

Tüm kayıtları tek tabloda topla ve `00-analiz.md`'ye koy:

```markdown
| # | Dosya | Ekran | Eylem | Durum | Bölüm | Adım | Belirsiz |
|---|---|---|---|---|---|---|---|
| 1 | 01-giris.png | Giriş | Kullanıcı adı ve parola girip Giriş'e basın | önce | Başlarken | 1 | — |
| 2 | 02-ana-ekran.png | Ana ekran | Ana ekran tanıtımı | ara | Başlarken | 2 | sağ üstteki rozet `[?]` |
```

## Sıralama sinyalleri / Ordering signals

Öncelik sırası:

1. Dosya adındaki sayı (`01-`, `02-`, `adim-3`)
2. Dosya değiştirme zamanı (aynı çekim oturumuysa güvenilir)
3. Ekran durumu: önce → ara → sonra (örn. boş form → dolu form → kaydedildi)
4. Mantıksal akış: giriş → ana ekran → işlem → onay

Çelişki varsa kullanıcıya sor; sorma imkânı yoksa **en tutarlı** sırayı seç ve
`00-analiz.md`'de gerekçelendir.

## Boşluk tespiti / Gap detection

Şu işaretler ara adımın eksik olduğunu gösterir:

- Bir ekranda "sonra" durumu var ama "önce" durumu yok
- Form doldurulmuş görünüyor ama doldurma ekranı yok
- Başarı/hata mesajı var ama tetikleyen eylem yok
- Adım numarası atlıyor (ekran 4'ten 6'ya)

Boşluğu **uydurma**. "Açık Sorular" bölümüne şu biçimde yaz:

```markdown
- **[?]** Adım 4 ile 6 arasında "onay" ekranı eksik. Bu adım için ekran görüntüsü gerekli.
```
