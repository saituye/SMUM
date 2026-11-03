#!/usr/bin/env python3
"""Skill için regresyon testleri.

Her test, doğrulama sırasında bulunan bir hatayı ya da temel davranışı kilitler.
Çalıştırma:

    python test/run_tests.py

Bağımlılık yok. DOCX testleri için python-docx gerekir; yoksa o testler atlanır.
Geçici dosyalar `test/.tmp/` altında üretilir (sandbox dışına yazmamak için).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "screenshot-to-manual" / "scripts"
CHECK = SCRIPTS / "check_manual.py"
CONVERT = SCRIPTS / "convert.py"
FIXTURES = ROOT / "test" / "fixtures" / "ekranlar"
REFERENCE = ROOT / "test" / "fixtures" / "ornek-kilavuz.md"
CLEAN = ROOT / "test" / "output" / "kilavuz.md"
NEGATIVE = ROOT / "test" / "negative" / "bozuk-kilavuz.md"
TEMPLATE = ROOT / "screenshot-to-manual" / "templates" / "manual-template.md"
EXAMPLE = ROOT / "screenshot-to-manual" / "examples" / "worked-example.md"
TMPROOT = ROOT / "test" / ".tmp"

BUNDLED_PY = Path(os.path.expanduser(
    r"~\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"))

results: list[tuple[str, bool, str]] = []


def fresh_dir(name: str) -> Path:
    p = TMPROOT / name
    shutil.rmtree(p, ignore_errors=True)
    p.mkdir(parents=True, exist_ok=True)
    return p


def run(args: list[str | Path]) -> tuple[int, str]:
    """Alt süreci pipe yerine dosyaya yazarak çalıştırır (sandbox pipe kısıtı)."""
    cmd = [str(a) for a in args]
    log = TMPROOT / "_last.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("w", encoding="utf-8") as fh:
        proc = subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT, cwd=str(ROOT))
    text = log.read_text(encoding="utf-8", errors="replace")
    log.unlink(missing_ok=True)
    return proc.returncode, text


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  -- {detail}" if not ok and detail else ""))


def has_python_docx() -> tuple[bool, str]:
    for exe in ([str(BUNDLED_PY)] if BUNDLED_PY.is_file() else []) + [sys.executable]:
        try:
            rc, _ = run([exe, "-c", "import docx"])
            if rc == 0:
                return True, exe
        except OSError:
            continue
    return False, sys.executable


def docx_media_count(path: Path) -> int:
    try:
        with zipfile.ZipFile(path) as z:
            return len([n for n in z.namelist() if n.startswith("word/media/")])
    except Exception:
        return -1


def main() -> int:
    TMPROOT.mkdir(parents=True, exist_ok=True)

    print("== 1. Temel QA davranışı ==")

    rc, out = run([sys.executable, CHECK, CLEAN, "--screenshots", FIXTURES,
                   "--reference", REFERENCE])
    check("temiz kılavuz PASS", rc == 0 and "PASS" in out, out[-300:])

    rc, out = run([sys.executable, CHECK, NEGATIVE, "--screenshots", FIXTURES])
    check("negatif kılavuz FAIL", rc == 1 and "FAIL" in out, out[-300:])
    for label, needle in (
        ("kullanılmayan ekran", "Hiç kullanılmayan"),
        ("bölüm numarası atlaması", "Bölüm numarası"),
        ("yer tutucu", "Doldurulmamış"),
        ("Açık Sorular eksik", "bölümü yok"),
        ("gövdede [?]", "[?] işareti gövdede"),
    ):
        check(f"negatif: {label} yakalandı", needle in out, out[-400:])

    rc, out = run([sys.executable, CHECK, TEMPLATE])
    check("şablon FAIL (yer tutucular)", rc == 1 and "Doldurulmamış" in out, out[-200:])

    rc, out = run([sys.executable, CHECK, EXAMPLE])
    check("worked-example çökmüyor", "Traceback" not in out, out[-300:])

    print("\n== 2. Yalancı pozitifler (doğrulamada bulunanlar) ==")

    # ORTA-1: yeniden adlandırılmış görsel kopyası "kullanılmayan" sayılmamalı
    ren = fresh_dir("renamed")
    shutil.copytree(ROOT / "test" / "output" / "images", ren / "images")
    text = CLEAN.read_text(encoding="utf-8").replace(
        "images/01-giris.png", "images/giris-ekrani.png")
    (ren / "kilavuz.md").write_text(text, encoding="utf-8")
    (ren / "images" / "01-giris.png").rename(ren / "images" / "giris-ekrani.png")
    rc, out = run([sys.executable, CHECK, ren / "kilavuz.md", "--screenshots", FIXTURES])
    check("yeniden adlandırılmış görsel PASS", rc == 0, out[-400:])

    # ORTA-2: satır içi koddaki karşılaştırma yer tutucu sanılmamalı
    cmp_doc = fresh_dir("cmp") / "karsilastirma.md"
    cmp_doc.write_text(
        "# Test\n\nKoşul `x < 10 > 5` ise devam edin.\n\n"
        "Ayrıca x < 100 > 20 aralığı geçerlidir.\n", encoding="utf-8")
    rc, out = run([sys.executable, CHECK, cmp_doc])
    check("`x < 10 > 5` yer tutucu sayılmıyor", "Doldurulmamış" not in out, out[-400:])

    # ORTA-3: bölüm başına sıfırlanan adım numaralandırması geçerli
    per = fresh_dir("per") / "per-section.md"
    per.write_text(
        "# Test\n\n## Bölüm 1 — A\n\n**Adım 1.** Bir.\n\n**Adım 2.** İki.\n\n"
        "## Bölüm 2 — B\n\n**Adım 1.** Bir.\n\n**Adım 2.** İki.\n", encoding="utf-8")
    rc, out = run([sys.executable, CHECK, per])
    check("bölüm başına adım numaralandırma PASS", "Adım numarası" not in out, out[-400:])

    # KÜÇÜK-4: "## 1 —" şemasında numaralandırma denetlenmeli
    dash = fresh_dir("dash") / "dash.md"
    dash.write_text("# T\n\n## 1 — A\n\nmetin\n\n## 3 — B\n\nmetin\n", encoding="utf-8")
    rc, out = run([sys.executable, CHECK, dash])
    check("'## 1 —' şemasında numara atlaması yakalanıyor",
          "Bölüm numarası" in out, out[-400:])

    # KÜÇÜK-5: docx referans uyarı vermeli
    dummy = fresh_dir("ref") / "sahte.docx"
    dummy.write_bytes(b"PK\x03\x04bozuk")
    rc, out = run([sys.executable, CHECK, CLEAN, "--reference", dummy])
    check("docx referans uyarısı", "düz metne çevirin" in out, out[-400:])

    print("\n== 3. convert.py ==")

    rc, out = run([sys.executable, CONVERT, CLEAN, "--format", "html",
                   "--out", fresh_dir("html")])
    check("html üretimi", rc == 0 and "+ " in out, out[-300:])

    rc, out = run([sys.executable, CONVERT, CLEAN, "--format", "rtf"])
    check("bilinmeyen format -> kod 2", rc == 2, out[-200:])

    rc, out = run([sys.executable, CONVERT, "yok-boyle-dosya.md"])
    check("olmayan dosya -> kod 2", rc == 2, out[-200:])

    # ORTA-5: --format pdf tek başına yönlendirme mesajı vermeli
    rc, out = run([sys.executable, CONVERT, CLEAN, "--format", "pdf",
                   "--out", fresh_dir("pdf")])
    check("pdf istenince yönlendirme mesajı",
          ("LibreOffice" in out or "Ctrl+P" in out or rc == 0), out[-400:])

    ok_docx, exe = has_python_docx()
    if not ok_docx:
        print("  SKIP  docx testleri (python-docx yok)")
    else:
        # KRİTİK-1: --out farklı klasörken görseller gömülmeli ve kopyalanmalı
        out_dir = fresh_dir("docx")
        rc, out = run([exe, CONVERT, CLEAN, "--format", "docx,html", "--out", out_dir])
        docx_path = out_dir / "kilavuz.docx"
        media = docx_media_count(docx_path) if docx_path.is_file() else -1
        copied = sorted((out_dir / "images").glob("*.png")) if (out_dir / "images").is_dir() else []
        check("--out farklı klasör: çıkış kodu 0", rc == 0, out[-300:])
        check("--out farklı klasör: DOCX'te görseller gömülü", media == 6, f"media={media}")
        check("--out farklı klasör: görseller kopyalandı", len(copied) == 6,
              f"kopya={len(copied)}")
        html = (out_dir / "kilavuz.html").read_text(encoding="utf-8")
        check("--out: html görsel yolları çözülüyor",
              all((out_dir / f"images/{n}").is_file() for n in
                  ["01-giris.png", "02-panel.png", "03-urunler.png",
                   "04-yeni-urun.png", "05-kayit-basarili.png", "06-raporlar.png"]),
              "eksik hedef")
        check("--out: html lang varsayılan tr", 'lang="tr"' in html)

        en_dir = fresh_dir("lang")
        rc, out = run([exe, CONVERT, CLEAN, "--format", "html", "--lang", "en",
                       "--out", en_dir])
        en_html = (en_dir / "kilavuz.html").read_text(encoding="utf-8")
        check("--lang en html'e yansıyor", 'lang="en"' in en_html, out[-200:])

    print("\n== 4. Round 2 regresyonları ==")

    # ORTA-6: sayısal/tarih/"..." yer tutucuları hâlâ yakalanmalı, karşılaştırma değil
    ph = fresh_dir("ph") / "ph.md"
    ph.write_text(
        "# Test\n\nSürüm <1.0> · Tarih <2024-01-01> · Sayı <1> · Boşluk <...>\n\n"
        "Gerçek <Ürün Adı> burada. Koşul `x < 10 > 5` ise devam et.\n"
        "Ayrıca x < 100 > 20 aralığı da geçerli.\n", encoding="utf-8")
    rc, out = run([sys.executable, CHECK, ph])
    for needle in ("<1.0>", "<2024-01-01>", "<...>", "<Ürün Adı>"):
        check(f"sayısal/tarih yer tutucu yakalanıyor: {needle}", needle in out, out[-500:])
    check("karşılaştırma yer tutucu sayılmıyor: <10>", "<10>" not in out, out[-500:])
    check("karşılaştırma yer tutucu sayılmıyor: <100>", "<100>" not in out, out[-500:])

    # KÜÇÜK-10: ikili referansta yanıltıcı karşılaştırma yapılmamalı
    docx_ref = ROOT / "test" / "output" / "kilavuz.docx"
    if docx_ref.is_file():
        rc, out = run([sys.executable, CHECK, CLEAN, "--reference", docx_ref])
        check("docx referans: karşılaştırma atlanıyor",
              "uyuşmuyor" not in out and "düz metne çevirin" in out, out[-500:])
    else:
        print("  SKIP  docx referans testi (kilavuz.docx yok)")

    # KÜÇÜK-11: kod bloğu varken --lang ezilmemeli
    code_md = fresh_dir("lang2") / "code.md"
    code_md.write_text("# T\n\n```python\nprint(1)\n```\n\nmetin\n", encoding="utf-8")
    code_out = fresh_dir("lang2out")
    run([sys.executable, CONVERT, code_md, "--format", "html",
         "--lang", "en", "--out", code_out])
    html = (code_out / "code.html").read_text(encoding="utf-8")
    check("kod bloğu varken --lang en korunuyor", 'lang="en"' in html, "")

    # KÜÇÜK-12: aynı içerikli iki ekran sessizce geçmemeli
    dup = fresh_dir("dup")
    (dup / "shots").mkdir()
    (dup / "images").mkdir()
    src_png = ROOT / "test" / "output" / "images" / "01-giris.png"
    shutil.copy2(src_png, dup / "shots" / "a.png")
    shutil.copy2(src_png, dup / "shots" / "b.png")
    shutil.copy2(src_png, dup / "images" / "a.png")
    (dup / "kilavuz.md").write_text(
        "# T\n\n## Bölüm 1 — A\n\n![Giriş](images/a.png)\n", encoding="utf-8")
    rc, out = run([sys.executable, CHECK, dup / "kilavuz.md",
                   "--screenshots", dup / "shots"])
    check("aynı içerikli ekran uyarısı (duplicate-content)",
          "Aynı içerikten" in out, out[-500:])

    # KÜÇÜK-15: çok kopyalı grupta TEK uyarı (kopya başına değil)
    dup5 = fresh_dir("dup5")
    (dup5 / "shots").mkdir()
    (dup5 / "images").mkdir()
    for n in ["a", "kopya1", "kopya2", "kopya3", "kopya4"]:
        shutil.copy2(src_png, dup5 / "shots" / f"{n}.png")
    shutil.copy2(src_png, dup5 / "images" / "a.png")
    (dup5 / "kilavuz.md").write_text(
        "# T\n\n## Bölüm 1 — A\n\n![Giriş](images/a.png)\n", encoding="utf-8")
    rc, out = run([sys.executable, CHECK, dup5 / "kilavuz.md",
                   "--screenshots", dup5 / "shots"])
    dup_warnings = out.count("Aynı içerikten")
    check("kopya grubunda tek uyarı", dup_warnings == 1, f"uyarı={dup_warnings}")

    # KÜÇÜK-13: "../" ile çıktı klasörü dışına kopyalama reddedilmeli
    trav = fresh_dir("trav")
    (trav / "src").mkdir()
    (trav / "pic.png").write_bytes(src_png.read_bytes())
    (trav / "src" / "kilavuz.md").write_text(
        "# T\n\n![Üst](../pic.png)\n", encoding="utf-8")
    trav_out = fresh_dir("travdeep") / "out"
    rc, out = run([sys.executable, CONVERT, trav / "src" / "kilavuz.md",
                   "--format", "html", "--out", trav_out])
    escaped = (trav / "travdeep" / "pic.png").is_file()
    check("../ yolu çıktı klasörü dışına yazmıyor", not escaped,
          "dosya out dışına kopyalandı")
    check("../ yolu reddedilince çıkış kodu 1", rc == 1, f"rc={rc}")

    # KÜÇÜK-14: "beklenen 3 veya 3" gibi tekrarlı mesaj olmamalı
    msg = fresh_dir("msg") / "msg.md"
    msg.write_text(
        "# T\n\n## Bölüm 1 — A\n\n**Adım 1.** Bir.\n\n**Adım 2.** İki.\n\n"
        "**Adım 4.** Dört.\n", encoding="utf-8")
    rc, out = run([sys.executable, CHECK, msg])
    check("mesajda 'veya 3' tekrarı yok", "veya 3" not in out, out[-400:])
    check("durum satırı net", "görsel kullanıldı" in out, out[-400:])

    print("\n== 5. Paket bütünlüğü ==")
    pyc = list((ROOT / "screenshot-to-manual").rglob("*.pyc"))
    check("skill paketinde .pyc yok", not pyc, f"{len(pyc)} dosya")
    cache = list((ROOT / "screenshot-to-manual").rglob("__pycache__"))
    check("skill paketinde __pycache__ yok", not cache, f"{len(cache)} dizin")

    shutil.rmtree(TMPROOT, ignore_errors=True)

    print("\n" + "=" * 52)
    failed = [r for r in results if not r[1]]
    print(f"TOPLAM {len(results)} test  |  {len(results) - len(failed)} PASS  |  {len(failed)} FAIL")
    for name, _, detail in failed:
        print(f"  FAIL: {name}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
