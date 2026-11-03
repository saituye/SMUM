#!/usr/bin/env python3
"""Test fixture üretir: 6 sentetik ekran görüntüsü + örnek kılavuz.

Skill'i gerçek bir girdi çiftiyle test etmek için kullanılır.
Gereksinim: Pillow (pip install pillow)

    python test/make_fixtures.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent
SHOTS = ROOT / "fixtures" / "ekranlar"
SHOTS.mkdir(parents=True, exist_ok=True)

W, H = 960, 640
INK = (26, 26, 26)
MUTED = (95, 105, 120)
LINE = (214, 220, 228)
BG = (245, 247, 250)
SOFT = (246, 248, 250)
ACCENT = (31, 111, 235)
DANGER = (214, 40, 40)
WHITE = (255, 255, 255)

FONT_DIRS = [Path("C:/Windows/Fonts"), Path("/usr/share/fonts/truetype/dejavu")]


def font(size: int, bold: bool = False):
    names = (["segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"] if bold
             else ["segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"])
    for d in FONT_DIRS:
        for n in names:
            p = d / n
            if p.is_file():
                try:
                    return ImageFont.truetype(str(p), size)
                except OSError:
                    pass
    return ImageFont.load_default()


def new_window(title: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([24, 20, W - 24, H - 20], radius=14, fill=WHITE, outline=LINE)
    d.rounded_rectangle([24, 20, W - 24, 68], radius=14, fill=SOFT)
    d.rectangle([24, 50, W - 24, 68], fill=SOFT)
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([48 + i * 22, 37, 62 + i * 22, 51], fill=c)
    d.text((140, 36), title, font=font(15, bold=True), fill=MUTED)
    d.line([24, 68, W - 24, 68], fill=LINE)
    return img, d


def field(d, box, label: str, value: str = "", hint: str = "") -> None:
    x0, y0, x1, y1 = box
    d.text((x0, y0 - 24), label, font=font(13, True), fill=INK)
    d.rounded_rectangle([x0, y0, x1, y1], radius=8, fill=WHITE, outline=LINE, width=2)
    if value:
        d.text((x0 + 14, y0 + 12), value, font=font(15), fill=INK)
    elif hint:
        d.text((x0 + 14, y0 + 12), hint, font=font(15), fill=(155, 163, 174))


def button(d, box, label: str, primary: bool = True, highlight: bool = False) -> None:
    x0, y0, x1, y1 = box
    fill = ACCENT if primary else WHITE
    d.rounded_rectangle([x0, y0, x1, y1], radius=8, fill=fill,
                        outline=ACCENT if not primary else ACCENT, width=2)
    tw = d.textlength(label, font=font(15, True))
    d.text((x0 + ((x1 - x0) - tw) / 2, y0 + 10), label,
           font=font(15, True), fill=WHITE if primary else ACCENT)
    if highlight:
        d.rounded_rectangle([x0 - 5, y0 - 5, x1 + 5, y1 + 5], radius=11,
                            outline=DANGER, width=3)


def sidebar(d) -> None:
    d.rectangle([24, 69, 250, H - 20], fill=SOFT)
    d.line([250, 69, 250, H - 20], fill=LINE)
    d.text((46, 92), "Envanter Takip", font=font(17, True), fill=INK)
    for i, item in enumerate(["Panel", "Ürünler", "Raporlar", "Ayarlar"]):
        y = 150 + i * 44
        active = item == "Ürünler"
        if active:
            d.rounded_rectangle([40, y - 8, 234, y + 28], radius=8, fill=(226, 236, 252))
        d.text((60, y), item, font=font(15, active), fill=ACCENT if active else MUTED)


def header(d, text: str) -> None:
    d.text((286, 96), text, font=font(26, True), fill=INK)
    d.line([286, 142, W - 56, 142], fill=LINE)


# --------------------------------------------------------------------------- #

def shot_01_giris() -> None:
    img, d = new_window("Envanter Takip — Giriş")
    d.rounded_rectangle([300, 130, 660, 560], radius=14, fill=WHITE, outline=LINE, width=2)
    d.text((340, 166), "Tekrar hoş geldiniz", font=font(22, True), fill=INK)
    d.text((340, 202), "Devam etmek için giriş yapınız.", font=font(13), fill=MUTED)
    field(d, (340, 276, 620, 322), "E-posta Adresi", hint="ornek@sirket.com")
    field(d, (340, 380, 620, 426), "Parola", hint="••••••••")
    button(d, (340, 460, 620, 502), "Giriş Yap")
    d.text((340, 518), "Parolamı unuttum", font=font(12), fill=ACCENT)
    img.save(SHOTS / "01-giris.png")


def shot_02_panel() -> None:
    img, d = new_window("Envanter Takip — Panel")
    sidebar(d)
    header(d, "Panel")
    cards = [("Toplam Ürün", "1.248"), ("Kritik Stok", "12"), ("Bugünkü Giriş", "34")]
    for i, (label, value) in enumerate(cards):
        x = 286 + i * 220
        d.rounded_rectangle([x, 170, x + 200, 280], radius=12, fill=SOFT, outline=LINE)
        d.text((x + 18, 190), label, font=font(13), fill=MUTED)
        d.text((x + 18, 216), value, font=font(30, True), fill=INK)
    d.text((286, 320), "Son Hareketler", font=font(16, True), fill=INK)
    rows = ["Kablosuz Klavye  +20", "Monitör Standı  −3", "USB-C Kablo  +150"]
    for i, r in enumerate(rows):
        y = 356 + i * 40
        d.line([286, y + 30, W - 56, y + 30], fill=LINE)
        d.text((286, y), r, font=font(14), fill=INK)
    img.save(SHOTS / "02-panel.png")


def shot_03_urunler() -> None:
    img, d = new_window("Envanter Takip — Ürünler")
    sidebar(d)
    header(d, "Ürünler")
    button(d, (760, 96, 900, 132), "Yeni Ürün", highlight=True)
    cols = ["Ürün Adı", "SKU", "Miktar", "Kategori"]
    xs = [286, 470, 640, 760]
    d.rectangle([286, 154, W - 56, 186], fill=SOFT)
    for x, c in zip(xs, cols):
        d.text((x + 10, 162), c, font=font(13, True), fill=MUTED)
    rows = [
        ("Kablosuz Klavye", "KLV-001", "120", "Aksesuar"),
        ("Monitör Standı", "MNT-014", "8", "Mobilya"),
        ("USB-C Kablo", "KAB-207", "340", "Kablo"),
        ("Laptop Çantası", "CNT-003", "0", "Aksesuar"),
    ]
    for i, r in enumerate(rows):
        y = 190 + i * 46
        d.line([286, y + 40, W - 56, y + 40], fill=LINE)
        for x, v in zip(xs, r):
            d.text((x + 10, y + 10), v, font=font(14), fill=INK)
    img.save(SHOTS / "03-urunler.png")


def shot_04_yeni_urun() -> None:
    img, d = new_window("Envanter Takip — Yeni Ürün")
    sidebar(d)
    header(d, "Yeni Ürün Ekle")
    field(d, (286, 208, 586, 254), "Ürün Adı", hint="Örn. Kablosuz Klavye")
    field(d, (626, 208, 900, 254), "SKU", hint="KLV-001")
    field(d, (286, 320, 420, 366), "Miktar", value="120")
    field(d, (460, 320, 700, 366), "Kategori", value="Aksesuar")
    d.text((286, 420), "Kritik stok uyarısı", font=font(13, True), fill=INK)
    d.rounded_rectangle([286, 448, 316, 478], radius=6, fill=WHITE, outline=LINE, width=2)
    d.line([290, 463, 312, 463], fill=ACCENT, width=2)
    d.line([301, 452, 301, 474], fill=ACCENT, width=2)
    d.text((330, 452), "Stok 10'un altına düştüğünde bildir", font=font(13), fill=MUTED)
    button(d, (286, 510, 420, 552), "Kaydet", highlight=True)
    button(d, (440, 510, 574, 552), "Vazgeç", primary=False)
    img.save(SHOTS / "04-yeni-urun.png")


def shot_05_basarili() -> None:
    img, d = new_window("Envanter Takip — Ürünler")
    sidebar(d)
    header(d, "Ürünler")
    d.rectangle([24, 69, W - 24, H - 20], fill=(24, 24, 24, 255))
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rectangle([24, 69, W - 24, H - 20], fill=(20, 25, 35, 140))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([330, 240, 630, 400], radius=14, fill=WHITE, outline=LINE, width=2)
    d.ellipse([452, 264, 508, 320], fill=(220, 245, 228), outline=(39, 160, 84), width=3)
    d.line([468, 292, 482, 306], fill=(39, 160, 84), width=5)
    d.line([482, 306, 500, 280], fill=(39, 160, 84), width=5)
    d.text((360, 336), "Ürün başarıyla kaydedildi.", font=font(15, True), fill=INK)
    button(d, (430, 360, 530, 392), "Tamam")
    img.save(SHOTS / "05-kayit-basarili.png")


def shot_06_raporlar() -> None:
    img, d = new_window("Envanter Takip — Raporlar")
    sidebar(d)
    header(d, "Raporlar")
    field(d, (286, 178, 480, 222), "Başlangıç Tarihi", value="01.03.2025")
    field(d, (500, 178, 694, 222), "Bitiş Tarihi", value="31.03.2025")
    button(d, (760, 178, 900, 214), "Excel'e Aktar", highlight=True)
    d.text((286, 250), "Mart 2025 Stok Hareketleri", font=font(15, True), fill=INK)
    d.rounded_rectangle([286, 282, 900, 560], radius=10, fill=SOFT, outline=LINE)
    for i in range(6):
        y = 300 + i * 42
        d.line([300, y + 30, 886, y + 30], fill=LINE)
        d.text((310, y), f"{i + 1:02d}.03.2025", font=font(13), fill=MUTED)
        d.text((470, y), ["Giriş", "Çıkış", "Giriş"][i % 3], font=font(13), fill=INK)
        d.text((640, y), str(15 + i * 7), font=font(13), fill=INK)
    img.save(SHOTS / "06-raporlar.png")


def write_reference() -> None:
    text = """# Rapor Takip Sistemi Kullanım Kılavuzu

**Sürüm 2.3** · **Son güncelleme:** 12.03.2025 · **Hedef kitle:** Tüm kullanıcılar

## Bölüm 1 — Sisteme Erişim

Bu bölümde sisteme nasıl giriş yapacağınızı öğreneceksiniz.

**Adım 1.** Tarayıcınızın adres çubuğuna sistem adresini yazınız ve Enter tuşuna basınız. Giriş formu görüntülenir.

Şekil 1 — Giriş formu
![Giriş formu](images/sek1-giris.png)

**Adım 2.** E-posta adresinizi ve parolanızı ilgili alanlara giriniz. Ardından **Giriş Yap** düğmesine tıklayınız.

Şekil 2 — Giriş bilgilerinin doldurulması
![Giriş bilgileri](images/sek2-doldurma.png)

> **Uyarı:** Parolanızı üç kez yanlış girerseniz hesabınız 15 dakika kilitlenir.

## Bölüm 2 — Rapor Oluşturma

**Adım 3.** Sol menüden **Raporlar** başlığına tıklayınız.

Şekil 3 — Raporlar ekranı
![Raporlar ekranı](images/sek3-raporlar.png)

**Adım 4.** Tarih aralığını seçip **Excel'e Aktar** düğmesine tıklayınız. Rapor dosyası indirilir.

> **Not:** Rapor en fazla 12 aylık dönem için oluşturulabilir.

## Bölüm 3 — Sık Sorulan Sorular

**Rapora neden erişemiyorum?**
Yetkiniz yoksa sistem sizi giriş ekranına yönlendirir. Sistem yöneticinizle iletişime geçiniz.

| Terim | Anlamı |
|---|---|
| Şekil | Ekran görüntüsü |
| SKU | Ürün stok kodu |
"""
    (ROOT / "fixtures" / "ornek-kilavuz.md").write_text(text, encoding="utf-8")


if __name__ == "__main__":
    shot_01_giris()
    shot_02_panel()
    shot_03_urunler()
    shot_04_yeni_urun()
    shot_05_basarili()
    shot_06_raporlar()
    write_reference()
    for p in sorted(SHOTS.glob("*.png")):
        print(f"  + {p.relative_to(ROOT)}")
    print(f"  + fixtures/ornek-kilavuz.md")
    print("Fixture'lar hazır.")
