#!/usr/bin/env python3
"""convert.py -- Markdown kılavuzunu HTML / DOCX / PDF'e çevirir.

Bağımlılıklar isteğe bağlıdır ve zarifçe düşer:
  * HTML  -- her zaman çalışır (harici paket gerekmez)
  * DOCX  -- python-docx gerekir
  * PDF   -- LibreOffice (soffice) veya pandoc gerekir; yoksa HTML yazdırma önerilir

Kullanım / Usage:
  python convert.py kilavuz.md
  python convert.py kilavuz.md --format docx,html
  python convert.py kilavuz.md --format html --out cikti/ --title "Başlık"

Çıkış kodları: 0 = istenen tüm formatlar üretildi, 1 = en az biri başarısız,
               2 = kullanım hatası.
"""

from __future__ import annotations

import argparse
import html
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # pragma: no cover
        pass

INLINE_RE = re.compile(
    r"(!\[[^\]]*\]\([^)]+\)"
    r"|\*\*.+?\*\*|__.+?__"
    r"|\*[^*\n]+?\*|_[^_\n]+?_"
    r"|`[^`\n]+`"
    r"|\[[^\]]+\]\([^)]+\))"
)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?\s*$")
LIST_RE = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
# Yol boşluk içerebilir; isteğe bağlı "başlık" kuyruğu clean_img_path() içinde atılır.
IMG_RE = re.compile(r"!\[([^\]]*)\]\(\s*([^)\n]+?)\s*\)")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
# Kendi satırında duran görsel ("Şekil 1 — ..." alt yazısının hemen altındaki satır)
STANDALONE_IMG_RE = re.compile(r"^\s*!\[[^\]]*\]\([^)]+\)\s*$")

CSS = """
:root{--ink:#1a1a1a;--muted:#5b6470;--line:#d8dee6;--bg:#fff;--accent:#1f6feb;--soft:#f6f8fa}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  font-size:16px;line-height:1.65}
main{max-width:860px;margin:0 auto;padding:48px 32px 96px}
h1{font-size:2.1em;line-height:1.2;margin:0 0 .3em;letter-spacing:-.02em}
h2{font-size:1.45em;margin:2.2em 0 .5em;padding-top:.6em;border-top:1px solid var(--line)}
h3{font-size:1.15em;margin:1.7em 0 .4em}
h4,h5,h6{font-size:1em;margin:1.3em 0 .3em}
p{margin:.7em 0}
img{display:block;max-width:100%;height:auto;margin:1em 0;border:1px solid var(--line);border-radius:8px}
blockquote{margin:1.1em 0;padding:.8em 1.1em;border-left:3px solid var(--accent);
  background:var(--soft);border-radius:0 8px 8px 0;color:var(--ink)}
blockquote p{margin:.2em 0}
table{border-collapse:collapse;width:100%;margin:1.2em 0;font-size:.94em}
th,td{border:1px solid var(--line);padding:.5em .7em;text-align:left;vertical-align:top}
th{background:var(--soft);font-weight:600}
code{font-family:ui-monospace,Consolas,"Courier New",monospace;font-size:.9em;
  background:var(--soft);padding:.12em .35em;border-radius:4px}
pre{background:var(--soft);border:1px solid var(--line);border-radius:8px;
  padding:.9em 1em;overflow:auto}
pre code{background:none;padding:0}
hr{border:none;border-top:1px solid var(--line);margin:2.2em 0}
ul,ol{margin:.7em 0;padding-left:1.5em}
li{margin:.3em 0}
a{color:var(--accent)}
.meta{color:var(--muted);font-size:.92em}
@media print{
  main{max-width:none;padding:0}
  body{font-size:11pt}
  h2{page-break-after:avoid}
  img,blockquote,table{page-break-inside:avoid}
  a{color:inherit;text-decoration:none}
}
"""

# --------------------------------------------------------------------------- #
# Markdown blok ayrıştırma
# --------------------------------------------------------------------------- #

def clean_img_path(raw: str) -> str:
    """Görsel hedefini temizler: <...> sarmalı ve "başlık" kuyruğu atılır."""
    raw = raw.strip()
    raw = re.sub(r"""\s+(["']).*\1$""", "", raw).strip()
    if raw.startswith("<") and raw.endswith(">"):
        raw = raw[1:-1].strip()
    return raw


def parse_blocks(text: str) -> list[tuple[str, object]]:
    """(kind, payload) listesi döndürür. kind: heading/para/hr/quote/code/table/list/img-para"""
    lines = text.splitlines()
    blocks: list[tuple[str, object]] = []
    i = 0
    n = len(lines)

    def is_table_row(s: str) -> bool:
        return s.strip().startswith("|") and s.count("|") >= 2

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # fenced code
        if stripped.startswith("```") or stripped.startswith("~~~"):
            fence = stripped[:3]
            lang = stripped[3:].strip()
            i += 1
            buf: list[str] = []
            while i < n and not lines[i].strip().startswith(fence):
                buf.append(lines[i])
                i += 1
            i += 1
            blocks.append(("code", (lang, "\n".join(buf))))
            continue

        # horizontal rule
        if re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", stripped):
            blocks.append(("hr", None))
            i += 1
            continue

        # heading
        m = HEADING_RE.match(line)
        if m:
            blocks.append(("heading", (len(m.group(1)), m.group(2).strip())))
            i += 1
            continue

        # table
        if is_table_row(line) and i + 1 < n and TABLE_SEP_RE.match(lines[i + 1]):
            header = [c.strip() for c in line.strip().strip("|").split("|")]
            rows: list[list[str]] = []
            i += 2
            while i < n and is_table_row(lines[i]):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            blocks.append(("table", (header, rows)))
            continue

        # blockquote
        if stripped.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            blocks.append(("quote", "\n".join(buf)))
            continue

        # list
        if LIST_RE.match(line):
            items: list[tuple[int, str, str]] = []
            while i < n:
                m = LIST_RE.match(lines[i])
                if not m:
                    if not lines[i].strip():
                        i += 1
                        continue
                    if lines[i].startswith(("  ", "\t")) and items:
                        indent = len(lines[i]) - len(lines[i].lstrip())
                        items.append((indent, "cont", lines[i].strip()))
                        i += 1
                        continue
                    break
                indent = len(m.group(1))
                ordered = "ordered" if m.group(2)[0].isdigit() else "bullet"
                items.append((indent, ordered, m.group(3).strip()))
                i += 1
            blocks.append(("list", items))
            continue

        # kendi satırındaki görsel: ayrı blok olsun ki DOCX'e resim olarak gömülsün
        if STANDALONE_IMG_RE.match(line):
            blocks.append(("para", line.strip()))
            i += 1
            continue

        # paragraph
        buf = []
        while i < n and lines[i].strip() and not (
            HEADING_RE.match(lines[i]) or lines[i].strip().startswith((">", "```", "~~~"))
            or LIST_RE.match(lines[i]) or re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", lines[i].strip())
            or STANDALONE_IMG_RE.match(lines[i])
            or (is_table_row(lines[i]) and i + 1 < n and TABLE_SEP_RE.match(lines[i + 1]))
        ):
            buf.append(lines[i].strip())
            i += 1
        if buf:
            blocks.append(("para", " ".join(buf)))
    return blocks


# --------------------------------------------------------------------------- #
# Inline dönüşümler
# --------------------------------------------------------------------------- #

def inline_html(s: str) -> str:
    out: list[str] = []
    pos = 0
    for m in INLINE_RE.finditer(s):
        out.append(html.escape(s[pos:m.start()]))
        tok = m.group(0)
        if tok.startswith("!["):
            mm = IMG_RE.match(tok)
            if mm:
                src = clean_img_path(mm.group(2))
                out.append(f'<img src="{html.escape(src)}" alt="{html.escape(mm.group(1))}">')
            else:
                out.append(html.escape(tok))
        elif tok.startswith("["):
            mm = LINK_RE.match(tok)
            if mm:
                out.append(f'<a href="{html.escape(mm.group(2))}">{html.escape(mm.group(1))}</a>')
            else:
                out.append(html.escape(tok))
        elif tok.startswith("`"):
            out.append(f"<code>{html.escape(tok[1:-1])}</code>")
        elif tok.startswith("**") or tok.startswith("__"):
            out.append(f"<strong>{html.escape(tok[2:-2])}</strong>")
        elif tok.startswith(("*", "_")):
            out.append(f"<em>{html.escape(tok[1:-1])}</em>")
        else:
            out.append(html.escape(tok))
        pos = m.end()
    out.append(html.escape(s[pos:]))
    return "".join(out)


def to_html(text: str, title: str | None, lang: str = "tr") -> str:
    blocks = parse_blocks(text)
    body: list[str] = []
    for kind, payload in blocks:
        if kind == "heading":
            level, content = payload  # type: ignore[misc]
            body.append(f"<h{level}>{inline_html(content)}</h{level}>")
        elif kind == "para":
            body.append(f"<p>{inline_html(payload)}</p>")  # type: ignore[arg-type]
        elif kind == "hr":
            body.append("<hr>")
        elif kind == "code":
            # DİKKAT: burada `lang` adını kullanma; fonksiyon parametresi `lang`
            # (HTML dili) gölgelenir ve <html lang> yanlış çıkar.
            fence_lang, code = payload  # type: ignore[misc]
            cls = f' class="language-{html.escape(fence_lang)}"' if fence_lang else ""
            body.append(f"<pre><code{cls}>{html.escape(code)}</code></pre>")
        elif kind == "quote":
            # Kaynak markdown'da satır sonu sadece sarma; paragraf ayrımı boş satırdır.
            chunks = [c.strip() for c in re.split(r"\n\s*\n", str(payload)) if c.strip()]
            parts = [f"<p>{inline_html(' '.join(c.split()))}</p>" for c in chunks]
            body.append("<blockquote>" + "".join(parts) + "</blockquote>")
        elif kind == "table":
            header, rows = payload  # type: ignore[misc]
            th = "".join(f"<th>{inline_html(c)}</th>" for c in header)
            trs = "".join(
                "<tr>" + "".join(f"<td>{inline_html(c)}</td>" for c in r) + "</tr>"
                for r in rows)
            body.append(f"<table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>")
        elif kind == "list":
            items = payload  # type: ignore[assignment]
            html_items: list[str] = []
            stack: list[tuple[int, str]] = []
            for indent, typ, content in items:  # type: ignore[misc]
                if typ == "cont":
                    continue
                tag = "ol" if typ == "ordered" else "ul"
                while stack and indent < stack[-1][0]:
                    html_items.append(f"</li></{stack[-1][1]}>")
                    stack.pop()
                if not stack or indent > stack[-1][0]:
                    html_items.append(f"<{tag}>")
                    stack.append((indent, tag))
                    html_items.append(f"<li>{inline_html(content)}")
                else:
                    html_items.append(f"</li><li>{inline_html(content)}")
            while stack:
                html_items.append(f"</li></{stack[-1][1]}>")
                stack.pop()
            body.append("".join(html_items))
    page_title = html.escape(title or _first_heading(text) or "Kullanım Kılavuzu")
    return (
        f"<!DOCTYPE html>\n<html lang=\"{html.escape(lang or 'tr')}\">\n"
        "<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
        f"<title>{page_title}</title>\n<style>{CSS}</style>\n</head>\n<body>\n<main>\n"
        + "\n".join(body)
        + "\n</main>\n</body>\n</html>\n"
    )


def _first_heading(text: str) -> str | None:
    for line in text.splitlines():
        m = HEADING_RE.match(line)
        if m:
            return m.group(2).strip()
    return None


# --------------------------------------------------------------------------- #
# DOCX
# --------------------------------------------------------------------------- #

def to_docx(text: str, out: Path, base: Path) -> bool:
    """`base`, görsellerin çözüleceği klasördür: GİRDİ markdown'ının klasörü."""
    try:
        from docx import Document  # type: ignore
        from docx.enum.text import WD_ALIGN_PARAGRAPH  # noqa: F401
        from docx.shared import Inches, Pt
    except ImportError:
        print("  ! python-docx bulunamadı. Kurulum: python -m pip install python-docx")
        print("    Alternatif: python convert.py kilavuz.md --format html"
              "  → tarayıcıda Ctrl+P ile PDF.")
        return False

    doc = Document()
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.9)
        section.right_margin = Inches(0.9)

    for kind, payload in parse_blocks(text):
        if kind == "heading":
            level, content = payload  # type: ignore[misc]
            doc.add_heading(_plain(content), level=min(level, 9))
        elif kind == "para":
            raw = str(payload)
            mm = IMG_RE.fullmatch(raw.strip())
            if mm:
                _add_image(doc, base, clean_img_path(mm.group(2)), mm.group(1), Inches(6))
            else:
                p = doc.add_paragraph()
                _add_inline_runs(p, raw)
        elif kind == "hr":
            _add_hr(doc)
        elif kind == "code":
            lang, code = payload  # type: ignore[misc]
            for line in code.splitlines() or [""]:
                p = doc.add_paragraph()
                run = p.add_run(line)
                run.font.name = "Consolas"
                run.font.size = Pt(9)
        elif kind == "quote":
            for chunk in re.split(r"\n\s*\n", str(payload)):
                if not chunk.strip():
                    continue
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Inches(0.3)
                _add_inline_runs(p, " ".join(chunk.split()))
        elif kind == "table":
            header, rows = payload  # type: ignore[misc]
            cols = max([len(header)] + [len(r) for r in rows]) if rows else len(header)
            table = doc.add_table(rows=1, cols=cols)
            table.style = "Table Grid"
            for j, cell_text in enumerate(header):
                _set_cell(table.rows[0].cells[j], cell_text, bold=True)
            for r in rows:
                cells = table.add_row().cells
                for j in range(cols):
                    _set_cell(cells[j], r[j] if j < len(r) else "")
        elif kind == "list":
            items = payload  # type: ignore[assignment]
            for indent, typ, content in items:  # type: ignore[misc]
                if typ == "cont":
                    continue
                style = "List Number" if typ == "ordered" else "List Bullet"
                try:
                    p = doc.add_paragraph(style=style)
                except KeyError:
                    p = doc.add_paragraph()
                if indent:
                    p.paragraph_format.left_indent = Inches(0.25 + indent / 100.0)
                _add_inline_runs(p, content)

    doc.save(str(out))
    return True


def _plain(markdown: str) -> str:
    s = IMG_RE.sub("", markdown)
    s = LINK_RE.sub(r"\1", s)
    s = re.sub(r"(\*\*|__)(.+?)\1", r"\2", s)
    s = re.sub(r"([*_])(.+?)\1", r"\2", s)
    s = s.replace("`", "")
    return s.strip()


def _add_inline_runs(paragraph, raw: str) -> None:
    pos = 0
    for m in INLINE_RE.finditer(raw):
        if m.start() > pos:
            paragraph.add_run(raw[pos:m.start()])
        tok = m.group(0)
        if tok.startswith("!["):
            paragraph.add_run("[görsel]")
        elif tok.startswith("`"):
            run = paragraph.add_run(tok[1:-1])
            run.font.name = "Consolas"
        elif tok.startswith("**") or tok.startswith("__"):
            paragraph.add_run(tok[2:-2]).bold = True
        elif tok.startswith(("*", "_")):
            paragraph.add_run(tok[1:-1]).italic = True
        elif tok.startswith("["):
            mm = LINK_RE.match(tok)
            paragraph.add_run(mm.group(1) if mm else tok)
        else:
            paragraph.add_run(tok)
        pos = m.end()
    if pos < len(raw):
        paragraph.add_run(raw[pos:])


def _add_image(doc, base: Path, src: str, alt: str, width) -> None:
    target = (base / src.replace("\\", "/")).resolve()
    if target.is_file():
        try:
            doc.add_picture(str(target), width=width)
            # Alt yazı genelde görselin ÜSTÜNDE ayrı bir paragraf olarak gelir
            # (Şekil N — ...); burada tekrar eklemeyiz, yoksa çift alt yazı olur.
        except Exception as exc:  # pragma: no cover
            doc.add_paragraph(f"[görsel eklenemedi: {src} — {exc}]")
    else:
        doc.add_paragraph(f"[görsel bulunamadı: {src}]")


def _add_hr(doc) -> None:
    """Yatay çizgi: karakter tekrarı yerine gerçek alt kenarlık."""
    try:
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn
    except ImportError:  # pragma: no cover
        doc.add_paragraph("─" * 40)
        return
    p = doc.add_paragraph()
    p_pr = p._p.get_or_add_pPr()
    p_bdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "D8DEE6")
    p_bdr.append(bottom)
    p_pr.append(p_bdr)


def _set_cell(cell, text: str, bold: bool = False) -> None:
    cell.text = ""
    p = cell.paragraphs[0]
    _add_inline_runs(p, text)
    if bold:
        for run in p.runs:
            run.bold = True


# --------------------------------------------------------------------------- #
# PDF
# --------------------------------------------------------------------------- #

def _mirror_images(text: str, src_dir: Path, out_dir: Path) -> tuple[int, list[str]]:
    """`--out` farklı klasörse göreli görselleri çıktı ağacına kopyalar.

    (kopyalanan sayısı, kopyalanamayan yollar) döndürür.
    """
    copied = 0
    missing: list[str] = []
    seen: set[Path] = set()
    for line in text.splitlines():
        for m in IMG_RE.finditer(line):
            raw = clean_img_path(m.group(2))
            if not raw or raw.startswith(("http://", "https://", "data:")):
                continue
            rel = Path(raw.replace("\\", "/"))
            if rel.is_absolute():
                rel = Path(rel.name)
            if rel in seen:
                continue
            seen.add(rel)
            source = (src_dir / rel).resolve()
            target = (out_dir / rel).resolve()
            # `../` ile çıktı klasörünün dışına yazmayı reddet.
            try:
                target.relative_to(out_dir.resolve())
            except ValueError:
                missing.append(f"{raw} (çıktı klasörü dışına çıkıyor)")
                continue
            if not source.is_file():
                missing.append(raw)
                continue
            if target == source:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            copied += 1
    return copied, missing


def to_pdf_via_soffice(src: Path, out_dir: Path) -> bool:
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        for candidate in (
            Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "LibreOffice/program/soffice.exe",
            Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "LibreOffice/program/soffice.exe",
        ):
            if candidate.is_file():
                soffice = str(candidate)
                break
    if not soffice:
        print("  ! LibreOffice bulunamadı; PDF için: python convert.py dosya.md --format html"
              "  → tarayıcıda Ctrl+P → PDF olarak kaydet.")
        return False
    try:
        subprocess.run([soffice, "--headless", "--convert-to", "pdf",
                        "--outdir", str(out_dir), str(src)],
                       check=True, capture_output=True, timeout=180)
        return True
    except Exception as exc:  # pragma: no cover
        print(f"  ! LibreOffice dönüşümü başarısız: {exc}")
        return False


# --------------------------------------------------------------------------- #

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Markdown kılavuzu → HTML/DOCX/PDF")
    ap.add_argument("manual", help="Girdi Markdown dosyası")
    ap.add_argument("--format", default="html",
                    help="html,docx,pdf (virgülle; varsayılan: html)")
    ap.add_argument("--out", help="Çıktı klasörü (varsayılan: girdinin klasörü)")
    ap.add_argument("--title", help="HTML başlığı")
    ap.add_argument("--lang", default="tr",
                    help="HTML <html lang> değeri (varsayılan: tr)")
    ap.add_argument("--keep-html", action="store_true",
                    help="PDF üretilirken ara HTML dosyasını da bırak")
    args = ap.parse_args(argv)

    src = Path(args.manual)
    if not src.is_file():
        print(f"HATA: dosya bulunamadı: {src}", file=sys.stderr)
        return 2

    text = src.read_text(encoding="utf-8", errors="replace")
    # Görseller GİRDİ klasörüne göre çözülür; --out farklıysa aşağıda kopyalanır.
    base = src.parent
    out_dir = Path(args.out) if args.out else src.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = src.stem
    formats = [f.strip().lower() for f in args.format.split(",") if f.strip()]
    unknown = set(formats) - {"html", "docx", "pdf"}
    if unknown:
        print(f"HATA: bilinmeyen format: {', '.join(sorted(unknown))}", file=sys.stderr)
        return 2

    ok = True
    html_path = out_dir / f"{stem}.html"

    if "html" in formats or "pdf" in formats:
        html_path.write_text(to_html(text, args.title, args.lang), encoding="utf-8")
        print(f"  + {html_path}")

    if "docx" in formats:
        docx_path = out_dir / f"{stem}.docx"
        if to_docx(text, docx_path, base):
            print(f"  + {docx_path}")
        else:
            ok = False

    # Görselleri çıktı klasörüne yansıt: göreli yollar --out ile birlikte çalışsın.
    if out_dir.resolve() != base.resolve():
        copied, missing = _mirror_images(text, base, out_dir)
        if copied:
            print(f"  > {copied} görsel çıktı klasörüne kopyalandı")
        if missing:
            ok = False
            for name in missing:
                print(f"  ! görsel kopyalanamadı (kaynak yok): {name}")

    if "pdf" in formats:
        docx_path = out_dir / f"{stem}.docx"
        if not docx_path.is_file() and not to_docx(text, docx_path, base):
            print("  ! PDF için DOCX üretilemedi;"
                  " '--format html' kullanıp tarayıcıdan Ctrl+P → PDF deneyin.")
            ok = False
        else:
            produced = to_pdf_via_soffice(docx_path, out_dir)
            if not produced:
                ok = False
            if produced and not args.keep_html and "html" not in formats:
                html_path.unlink(missing_ok=True)

    if not ok:
        print("UYARI: bazı formatlar üretilemedi (yukarıdaki kurulum önerilerine bakın).")
        return 1
    print("Tamam.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
