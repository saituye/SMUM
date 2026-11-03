# Alarm Bölümü Şablonu / Alarm Section Template

Alarm ve hata bölümü, kullanım kılavuzunun **en çok okunan** bölümüdür. Her
alarm için aynı beş parçalı yapıyı kullan; sonunda özet tablo ver.

*The alarm chapter is the most-read part of a manual. Use the same five-part
structure for every alarm, then a summary table.*

## Tek alarm kaydı / Per-alarm record

```markdown
### [ALARM KODU] — [ALARM MESAJI]

**Anlamı.** Alarmın operatöre ne anlattığını sade Türkçe ile 1–2 cümlede açıkla.

**Olası sebepler.**
- ...
- ...
- ...

**Operatörün yapması gerekenler.**
1. Makinayı güvenli şekilde durdurun.
2. Alarm mesajını ve kodunu not edin.
3. İlgili fiziksel durumu kontrol edin (sensör, ürün sıkışması, basınç vb.).
4. Gerekli müdahaleyi yapın.
5. Alarm nedenini giderin.
6. **Reset** işlemini gerçekleştirin.
7. Makineyi kontrollü şekilde yeniden çalıştırın.

**Alarm devam ederse.** Tekrar eden alarmda operatörün makinaya müdahale
etmemesi ve teknik servise başvurması gerektiğini yaz; servise iletilecek
bilgileri listele (alarm kodu, saat, tekrar sıklığı, ekran görüntüsü).
```

## Özet tablo / Summary table

```markdown
| Alarm Kodu | Alarm Mesajı | Olası Sebep | Operatörün Yapması Gerekenler |
|---|---|---|---|
| [ALARM KODU BELİRTİLMEMİŞ] | Kapak açık | Koruma kapağı açıkken çalıştırma denendi | Kapağı kapatın, Reset'e basın |
```

## Kurallar

1. **Kod ve mesaj ekranda göründüğü gibi** yazılır; çevirme, kısaltma, kod uydurma yok.
2. Kod görünmüyorsa: `[ALARM KODU BELİRTİLMEMİŞ]` — sıfırdan kod üretme.
3. Sebepler ekranda/verilen bilgide yoksa `[DOĞRULANMASI GEREKİYOR]` bırak.
4. Her alarm için **Reset** ve **tekrar ederse** davranışı mutlaka yazılır.
5. Alarm sayısı 10'u geçiyorsa özet tablo **zorunlu**dur.
6. Servis gerektiren durumları operatörün yapabileceklerinden ayır.
7. `TEHLİKE` / `UYARI` / `DİKKAT` başlıklarını yalnız gerçekten risk varsa kullan.