# Stil Sözleşmesi Çıkarma / Extracting the Style Contract

Amaç: örnek kılavuzun **biçimini** ölçüp yazıya dökmek, böylece yeni kılavuz
onun devamı gibi görünür — ama tek bir cümlesi kopyalanmaz.

*Goal: measure the example manual's form so the new manual looks like a
continuation of it, without copying a single sentence.*

## Nasıl çıkarılır / How to extract

1. Referansı baştan sona oku, bölüm sınırlarını işaretle.
2. Aşağıdaki tabloyu **gözlemle** doldur. Uydurma; göremediğin alanı `—` bırak.
3. En az 3 adım örneğini yan yana koy: ortak kalıbı gör.
4. Doldurulmuş tabloyu `00-analiz.md` içine yapıştır.

## Şablon / Template

```markdown
## Stil Sözleşmesi — <referans dosya adı>

| Alan | Gözlem | Kanıt (bölüm/adım) |
|---|---|---|
| Belge dili | | |
| Ton | resmî / samimi | |
| Hitap | siz / sen | |
| Başlık hiyerarşisi | # ürün, ## bölüm, ### adım | |
| Numaralandırma | `1.`, `1.1`, `Adım 1`, yok | |
| Adım kipi | emir kipi / "-iniz" | |
| Adım uzunluğu | 1–3 cümle | |
| Görsel yerleşimi | adımdan önce / sonra | |
| Görsel alt yazısı | var / yok — biçimi | |
| Görsel numaralandırma | `Şekil 1`, `Resim 1`, yok | |
| Uyarı kutuları | Not / Uyarı / İpucu / Dikkat — biçimi | |
| Tablo kullanımı | | |
| Kod/komut bloğu | var / yok | |
| Ön bölüm | kapak, sürüm, tarih, içindekiler | |
| Son bölüm | SSS, sorun giderme, sözlük, iletişim | |
| Terim sözlüğü | terim → kullanılan ad | |
| Ortalama bölüm uzunluğu | | |

### Çıkarılan kalıp örneği (3 adım)
> Adım 3 — Kaydet'e tıklayın.
> ![Ayarlar](images/03.png)
```

## Doldurulmuş örnek / Filled example

```markdown
| Alan | Gözlem | Kanıt |
|---|---|---|
| Belge dili | Türkçe | tümü |
| Ton | resmî, kısa | Bölüm 2 |
| Hitap | siz | "tıklayınız" |
| Başlık hiyerarşisi | # ürün, ## bölüm, ### adım | |
| Numaralandırma | `1.` bölüm, `Adım N` adım | |
| Adım kipi | emir kipi | "Dosya menüsünü açın." |
| Görsel yerleşimi | adımdan sonra | |
| Görsel alt yazısı | yok | |
| Uyarı kutuları | `> **Not:**` | Bölüm 1 |
| Son bölüm | SSS | Bölüm 5 |
```

## Kurallar / Rules

- Referansta olmayan bir biçim öğesini (örn. renkli uyarı kutusu) **ekleme**.
- Referans tutarsızsa (iki farklı adım kipi), **çoğunluğu** seç ve seçimini
  `00-analiz.md`'de gerekçelendir.
- Referans hiç okunamıyorsa varsayılan sözleşmeyi kullan ve bunu teslim
  mesajında açıkça belirt:
  - `# <Ürün> Kullanım Kılavuzu`, `## N. Bölüm`, `### Adım N — <eylem>`
  - Emir kipi, siz hitabı, görsel adımdan sonra, alt yazı yok
  - `> **Not:**` uyarı kutusu, sonda SSS
