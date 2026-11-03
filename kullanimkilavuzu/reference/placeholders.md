# Alan Yer Tutucuları / Field Placeholders

Kılavuzda **bilmediğin** bilgiyi uydurmak yerine, müşterinin/üreticinin
dolduracağı **kendini açıklayan** bir yer tutucu bırak. Bu, uydurmadan daha
profesyoneldir ve teslim edilebilir bir belge üretir.

*When you don't know something, leave a self-describing placeholder instead of
inventing. A placeholder is a professional deliverable; a guess is not.*

## Neden `[?]` yeterli değil

`[?]` kısa bir işarettir ve **AI'ya** "buraya bak" der. Müşteriye giden belgede
ise **kimin, neyi, nereden** dolduracağını söylemek gerekir. Bu yüzden:

- Kısa belirsizlik (tek bir etiket okunamadı) → `[?]`
- **Eksik bilgi** (üretici dolduracak) → sözlükteki açıklayıcı yer tutucu

## Sözlük / Vocabulary

### Üretici / müşteri dolduracak

| Yer tutucu | Ne zaman |
|---|---|
| `[ÜRETİCİ TARAFINDAN DOLDURULACAK]` | Teknik özellik, garanti, menşe gibi yalnız üreticinin bildiği alanlar |
| `[BİLGİ EKLENECEK]` | Kaynakta hiç yok ve tahmin de edilemez |
| `[DOĞRULANMASI GEREKİYOR]` | Bir kaynaktan yazıldı ama teyit edilmeli (ör. ekranda yarım görünen değer) |
| `[ALARM KODU BELİRTİLMEMİŞ]` | Alarm ekranında kod görünmüyor — **kod uydurma**, bunu yaz |
| `[GÖRSEL EKLENECEK]` | Adım var ama ekran görüntüsü verilmemiş |

### Kurumsal iletişim alanları

`[FİRMA ADI]` · `[ADRES]` · `[TELEFON]` · `[E-POSTA]` · `[WEB SİTESİ]` ·
`[TEKNİK SERVİS TELEFONU]` · `[SERİ NO]` · `[MODEL]` · `[ÜRETİM YILI]` ·
`[DOKÜMAN NO]` · `[REVİZYON]` · `[TARİH]`

Bu alanlar **bilerek** boş bırakılır; belge şablon olarak teslim edilir.

## Kurallar

1. **Göremediğin şeyi yazma.** Ekran görüntüsünde olmayan alarm kodu, buton adı,
   parametre değeri veya bakım periyodu → yer tutucu.
2. **Yer tutucu kendini açıklasın.** `[?]` yerine "kimin dolduracağını" söyle.
3. **Tutarlı yaz.** Aynı kavram için aynı yer tutucuyu kullan; eş anlamlı üretme.
4. **Listele.** Kılavuz sonundaki "Açık Sorular" bölümünde ve teslim mesajında
   yer tutucuların tamamını say.
5. **Ekranda görüneni yer tutucuya çevirme.** Görünüyorsa yaz — yer tutucu
   yalnız *eksik* bilgi içindir.
6. **Yayına hazır sürüm.** Kullanıcı isterse yer tutucular üretici tarafından
   doldurulur; bu skill onları **silmez**, sadece işaretler.

## QA davranışı

`check_manual.py`:

- `<...>`, `TODO`, `XXX`, `LOREM` → **ERROR** (doldurulmamış genel şablon kalıntısı)
- Bu sözlükteki `[ÜRETİCİ TARAFINDAN DOLDURULACAK]` gibi alanlar → **uyarı**,
  `unfilled-field` koduyla listelenir. Hata değildir: belge taslak olarak
  teslim edilebilir, ama sayıları teslim mesajında bildirilmelidir.

## Örnek

```markdown
## 6.6.0.1. AC Motorlar

**Adım 1.** Manuel ekrandan ilgili motoru seçiniz ve **START** butonuna basınız.

Şekil 12–AC Motorlar Sayfası
![AC Motorlar](images/12-ac-motorlar.png)

> **UYARI:** Motor hareket halindeyken koruma kapağını açmayınız.

| Parametre | Açıklama | Birim | Operatör Notu |
|---|---|---|---|
| Motor hızı | Manuel modda ayarlanır | rpm | [DOĞRULANMASI GEREKİYOR] |
| Nominal akım | Motor etiketinde yazar | A | [ÜRETİCİ TARAFINDAN DOLDURULACAK] |
```