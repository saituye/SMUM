#!/usr/bin/env python3
"""read_reference.py -- Örnek kılavuzdan yapı ve stil profili çıkarır.

Amaç: `reference/style-contract.md` tablosunu göz kararıyla değil, ölçerek
doldurmak. PDF, DOCX ve düz metin desteklenir.

Kullanım:
    python read_reference.py ornek-kilavuz.pdf
    python read_reference.py ornek-kilavuz.docx --json profil.json
    python read_reference.py ornek-kilavuz.md --out 00-analiz.md

Çıktı: ekrana Markdown özet, istenirse JSON. Profil şunları içerir:
  * belge künyesi (sayfa, başlık, yazar, tarih)
  * başlık hiyerarşisi ve numaralandırma şeması
  * sayfa üstü/altı tekrar eden metin (doküman no, revizyon, sayfa no)
  * şekil/tablo alt yazı kalıbı
  * baskın fontlar, punto ve renkler (başlık rengi, uyarı rengi)
  * tablo sayısı, madde işareti kullanımı

Bağımlılıklar (isteğe bağlı, zarifçe düşer):
  * PDF  -> PyMuPDF (pymupdf / fitz)
  * DOCX -> python-docx
  * MD   -> bağımlılık yok

Çıkış kodları: 0 = başarılı, 2 = kullanım/IO hatası, 3 = eksik bağımlılık
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import warnings
from collections import Counter
from pathlib import Path

warnings.filterwarnings("ignore", message=".*fitz.*deprecated.*")
warnings.filterwarnings("ignore", category=FutureWarning)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # pragma: no cover
        pass

# "6.5.1.1." / "1." / "1.2" ile başlayan başlıklar
NUMBERED_RE = re.compile(r"^\s*(\d+(?:\.\d+)*)\.?\s+\S")
CAPTION_RE = re.compile(
    r"^\s*(Şekil|Sekil|Resim|Figure|Fig\.?|Tablo|Table)\s*(\d+)\s*[-–—:.]?\s*(.*)$",
    re.IGNORECASE)
DOCNO_RE = re.compile(r"\b[A-ZÇĞİÖŞÜ]{2,}(?:\.[A-Z0-9]+){2,}(?:-[\d.]+)?\b")
BULLET_RE = re.compile(r"^\s*(?:[•·▪◦‣\-*]|\d+[.)])\s+")
WARNING_WORDS = ("TEHLİKE", "UYARI", "DİKKAT", "TEHLIKE", "UYARI", "ONLEM", "ÖNLEM")


def rgb_to_hex(value: int | None) -> str | None:
    if value is None:
        return None
    return f"#{value & 0xFFFFFF:06X}"


def _caption_issues(captions: list[dict]) -> list[str]:
    """Şekil/tablo numaralandırmasındaki tutarsızlıkları raporlar."""
    issues: list[str] = []
    for kind in {c["type"].lower() for c in captions}:
        nums = [c["number"] for c in captions if c["type"].lower() == kind]
        if not nums:
            continue
        dupes = [n for n, c in Counter(nums).items() if c > 1]
        if dupes:
            issues.append(
                f"'{kind}' numaraları tekrar ediyor ({', '.join(map(str, sorted(dupes)[:6]))}); "
                f"kaynakta bölüm içinde yeniden başlıyor. Yeni kılavuzda sürekli "
                f"numaralandırma kullan ve bunu teslim mesajında belirt.")
        if nums != sorted(nums):
            issues.append(f"'{kind}' numaraları artan sırada değil; kaynak tutarsız.")
    return issues


# --------------------------------------------------------------------------- #
# PDF
# --------------------------------------------------------------------------- #

def read_pdf(path: Path) -> dict:
    try:
        import fitz  # type: ignore
    except ImportError:
        try:
            import pymupdf as fitz  # type: ignore
        except ImportError:
            raise SystemExit(
                "HATA: PDF okumak için PyMuPDF gerekli.\n"
                "  Kurulum: python -m pip install pymupdf\n"
                "  Alternatif: PDF'yi Markdown/Word olarak dışa aktarıp onu verin.")

    doc = fitz.open(str(path))
    result: dict = {
        "kind": "pdf",
        "path": str(path),
        "pages": doc.page_count,
        "meta": {k: v for k, v in (doc.metadata or {}).items() if v},
        "toc": [],
        "headings": [],
        "captions": [],
        "header_lines": [],
        "footer_lines": [],
        "font_sizes": {},
        "fonts": {},
        "colors": {},
        "doc_numbers": [],
        "tables": 0,
        "bullets": 0,
        "warnings": [],
        "has_outline": False,
    }

    toc = doc.get_toc(simple=True)
    result["toc"] = [{"level": l, "title": t, "page": p} for l, t, p in toc]
    result["has_outline"] = bool(toc)

    sizes: Counter = Counter()
    fonts: Counter = Counter()
    colors: Counter = Counter()
    size_chars: dict[float, int] = {}
    numbering_depth: Counter = Counter()
    numbering_sample: dict[int, str] = {}
    first_lines: Counter = Counter()
    last_lines: Counter = Counter()
    scan_pages = min(doc.page_count, 60)

    for pno in range(scan_pages):
        page = doc[pno]
        data = page.get_text("dict")
        page_text_lines: list[str] = []

        for block in data.get("blocks", []):
            for line in block.get("lines", []):
                spans = [s for s in line.get("spans", []) if s.get("text", "").strip()]
                if not spans:
                    continue
                text = " ".join(s["text"].strip() for s in spans).strip()
                if not text:
                    continue
                page_text_lines.append(text)
                size = max(s["size"] for s in spans)
                for s in spans:
                    n = len(s["text"].strip())
                    if n:
                        sizes[round(s["size"], 1)] += n
                        fonts[s["font"]] += n
                        colors[s["color"]] += n

                m = CAPTION_RE.match(text)
                if m:
                    result["captions"].append({
                        "type": m.group(1), "number": int(m.group(2)),
                        "text": m.group(3).strip()[:80], "page": pno + 1})
                m = NUMBERED_RE.match(text)
                if m:
                    _num = m.group(1).strip(".")
                    _d = len(_num.split("."))
                    numbering_depth[_d] += 1
                    numbering_sample.setdefault(_d, _num)
                    if 1 <= len(m.group(1).split(".")) <= 4 and len(text) < 100:
                        result["headings"].append({
                            "level": len(m.group(1).split(".")),
                            "number": m.group(1), "text": text[:90],
                            "size": round(size, 1), "page": pno + 1})
                if DOCNO_RE.search(text):
                    for d in DOCNO_RE.findall(text):
                        if d not in result["doc_numbers"]:
                            result["doc_numbers"].append(d)
                if text.upper().startswith(WARNING_WORDS):
                    result["warnings"].append({"page": pno + 1, "text": text[:90]})
                if BULLET_RE.match(text):
                    result["bullets"] += 1

        if page_text_lines:
            first_lines[page_text_lines[0][:120]] += 1
            last_lines[page_text_lines[-1][:120]] += 1
        try:
            result["tables"] += len(page.find_tables().tables)
        except Exception:
            pass

    threshold = max(2, scan_pages // 2)
    result["header_lines"] = [t for t, n in first_lines.most_common(4) if n >= threshold]
    result["footer_lines"] = [t for t, n in last_lines.most_common(4) if n >= threshold]
    result["font_sizes"] = {str(k): v for k, v in sizes.most_common(8)}
    result["fonts"] = {k: v for k, v in fonts.most_common(8)}
    result["colors"] = {rgb_to_hex(k) or "?": v for k, v in colors.most_common(8)}
    result["body_size"] = sizes.most_common(1)[0][0] if sizes else None
    result["numbering"] = [{"depth": d, "count": numbering_depth[d],
                            "sample": numbering_sample.get(d, "")}
                           for d in sorted(numbering_depth)]
    result["headings"] = result["headings"][:40]
    result["captions"] = result["captions"][:40]
    result["caption_issues"] = _caption_issues(result["captions"])
    result["warnings"] = result["warnings"][:15]
    doc.close()
    return result


# --------------------------------------------------------------------------- #
# DOCX
# --------------------------------------------------------------------------- #

def read_docx(path: Path) -> dict:
    try:
        from docx import Document  # type: ignore
    except ImportError:
        raise SystemExit(
            "HATA: DOCX okumak için python-docx gerekli.\n"
            "  Kurulum: python -m pip install python-docx")

    doc = Document(str(path))
    result: dict = {
        "kind": "docx", "path": str(path), "pages": None, "meta": {},
        "toc": [], "headings": [], "captions": [], "header_lines": [],
        "footer_lines": [], "font_sizes": {}, "fonts": {}, "colors": {},
        "doc_numbers": [], "tables": len(doc.tables), "bullets": 0,
        "warnings": [], "has_outline": False,
    }
    cp = doc.core_properties
    result["meta"] = {k: getattr(cp, k, None) for k in
                      ("title", "author", "created", "modified", "subject", "category")}
    result["meta"] = {k: (str(v) if v else "") for k, v in result["meta"].items() if v}

    numbering_depth: Counter = Counter()
    numbering_sample: dict[int, str] = {}
    sizes: Counter = Counter()
    fonts: Counter = Counter()

    for p in doc.paragraphs:
        text = p.text.strip()
        if not text:
            continue
        style = p.style.name if p.style is not None else ""
        m = NUMBERED_RE.match(text)
        if m:
            _num = m.group(1).strip(".")
            _d = len(_num.split("."))
            numbering_depth[_d] += 1
            numbering_sample.setdefault(_d, _num)
        if style.lower().startswith("heading") or m:
            level = 0
            if style.lower().startswith("heading"):
                digits = re.findall(r"\d+", style)
                level = int(digits[0]) if digits else 1
            elif m:
                level = len(m.group(1).split("."))
            result["headings"].append({
                "level": level, "number": m.group(1) if m else "",
                "text": text[:90], "style": style})
        cm = CAPTION_RE.match(text)
        if cm:
            result["captions"].append({"type": cm.group(1),
                                       "number": int(cm.group(2)),
                                       "text": cm.group(3).strip()[:80]})
        if text.upper().startswith(WARNING_WORDS):
            result["warnings"].append({"text": text[:90]})
        if BULLET_RE.match(text):
            result["bullets"] += 1
        for run in p.runs:
            n = len(run.text.strip())
            if not n:
                continue
            if run.font.size is not None:
                sizes[round(run.font.size.pt, 1)] += n
            if run.font.name:
                fonts[run.font.name] += n

    for section in doc.sections:
        try:
            result["header_lines"] = [p.text.strip() for p in
                                      section.header.paragraphs if p.text.strip()]
            result["footer_lines"] = [p.text.strip() for p in
                                      section.footer.paragraphs if p.text.strip()]
        except Exception:
            pass

    full = "\n".join(p.text for p in doc.paragraphs[:400])
    for d in DOCNO_RE.findall(full):
        if d not in result["doc_numbers"]:
            result["doc_numbers"].append(d)

    result["font_sizes"] = {str(k): v for k, v in sizes.most_common(8)}
    result["fonts"] = dict(fonts.most_common(8))
    result["body_size"] = sizes.most_common(1)[0][0] if sizes else None
    result["numbering"] = [{"depth": d, "count": numbering_depth[d],
                            "sample": numbering_sample.get(d, "")}
                           for d in sorted(numbering_depth)]
    result["headings"] = result["headings"][:40]
    result["captions"] = result["captions"][:40]
    result["caption_issues"] = _caption_issues(result["captions"])
    result["warnings"] = result["warnings"][:15]
    return result


# --------------------------------------------------------------------------- #
# Markdown / düz metin
# --------------------------------------------------------------------------- #

def read_text_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    result: dict = {
        "kind": "markdown" if path.suffix.lower() in {".md", ".markdown"} else "text",
        "path": str(path), "pages": None, "meta": {}, "toc": [],
        "headings": [], "captions": [], "header_lines": [], "footer_lines": [],
        "font_sizes": {}, "fonts": {}, "colors": {}, "doc_numbers": [],
        "tables": 0, "bullets": 0, "warnings": [], "has_outline": False,
    }
    numbering_depth: Counter = Counter()
    numbering_sample: dict[int, str] = {}
    for line in lines:
        h = re.match(r"^(#{1,6})\s+(.*)$", line)
        if h:
            content = h.group(2).strip()
            m = NUMBERED_RE.match(content)
            if m:
                _num = m.group(1).strip(".")
                _d = len(_num.split("."))
                numbering_depth[_d] += 1
                numbering_sample.setdefault(_d, _num)
            result["headings"].append({
                "level": len(h.group(1)), "number": m.group(1) if m else "",
                "text": content[:90]})
            continue
        cm = CAPTION_RE.match(line.strip())
        if cm:
            result["captions"].append({"type": cm.group(1),
                                       "number": int(cm.group(2)),
                                       "text": cm.group(3).strip()[:80]})
        if line.strip().upper().startswith(WARNING_WORDS):
            result["warnings"].append({"text": line.strip()[:90]})
        if BULLET_RE.match(line):
            result["bullets"] += 1
        if line.strip().startswith("|") and line.count("|") >= 3:
            result["tables"] += 1
    for d in DOCNO_RE.findall(text):
        if d not in result["doc_numbers"]:
            result["doc_numbers"].append(d)
    result["numbering"] = [{"depth": d, "count": numbering_depth[d],
                            "sample": numbering_sample.get(d, "")}
                           for d in sorted(numbering_depth)]
    result["headings"] = result["headings"][:40]
    result["captions"] = result["captions"][:40]
    result["caption_issues"] = _caption_issues(result["captions"])
    result["warnings"] = result["warnings"][:15]
    result["tables"] = result["tables"] // 3 if result["tables"] else 0
    return result


# --------------------------------------------------------------------------- #
# Markdown raporu -- style-contract.md alanlarına birebir oturacak biçimde
# --------------------------------------------------------------------------- #

def render_markdown(p: dict) -> str:
    out: list[str] = []
    out.append(f"# Referans Profili — `{Path(p['path']).name}`\n")
    out.append("> `read_reference.py` tarafından üretildi. Bu dosyayı "
               "`reference/style-contract.md` tablosuna aktar.\n")

    out.append("## Belge künyesi\n")
    out.append(f"| Alan | Değer |\n|---|---|")
    out.append(f"| Tür | {p['kind']} |")
    out.append(f"| Sayfa | {p['pages'] if p['pages'] is not None else '—'} |")
    for k, v in p.get("meta", {}).items():
        if v:
            out.append(f"| {k} | {str(v)[:120]} |")
    out.append("")

    out.append("## Bölüm yapısı\n")
    if p["has_outline"]:
        out.append("| Düzey | Başlık | Sayfa |\n|---|---|---|")
        for t in p["toc"][:40]:
            out.append(f"| {t['level']} | {t['title']} | {t['page']} |")
    else:
        out.append("Kaynak belge **içindekiler (outline) içermiyor** — başlık yapısı "
                   "metinden çıkarıldı. Referansta içindekiler varsa kılavuzda da "
                   "üret; yoksa üretme.\n")
    if p["headings"]:
        out.append("\n**Başlık hiyerarşisi (örnek):**\n")
        out.append("| Düzey | No | Başlık | Punto |\n|---|---|---|---|")
        for h in p["headings"][:15]:
            out.append(f"| {h['level']} | {h.get('number') or '—'} | "
                       f"{h['text'][:60]} | {h.get('size', '—')} |")
    out.append("")

    out.append("## Numaralandırma\n")
    if p.get("numbering"):
        # Benzersiz numaraları listelemek yerine ŞEMAYI özetle: kaç seviyeli,
        # hangi ayraç, kaç başlıkta kullanılmış.
        total = sum(item["count"] for item in p["numbering"])
        out.append(f"Numaralı başlık sayısı: **{total}**")
        out.append("\n| Derinlik | Örnek kalıp | Adet |\n|---|---|---|")
        for item in p["numbering"]:
            out.append(f"| {item['depth']} seviye | `{item['sample']}.` | "
                       f"{item['count']} |")
        deepest = max(item["depth"] for item in p["numbering"])
        out.append(f"\nEn derin numaralandırma: **{deepest} seviye** — yeni kılavuzda "
                   f"aynı derinliği kullan.")
    else:
        out.append("Numaralı başlık kalıbı bulunamadı — numarasız başlık şeması kullan.")
    out.append("")

    out.append("## Doküman kimliği (üstbilgi/altbilgi)\n")
    if p["doc_numbers"]:
        out.append("Tespit edilen doküman numarası / revizyon kalıpları: " +
                   ", ".join(f"`{d}`" for d in p["doc_numbers"][:6]))
    if p["header_lines"]:
        out.append("\nHer sayfada tekrar eden **üstbilgi**:")
        for line in p["header_lines"]:
            out.append(f"- `{line}`")
    if p["footer_lines"]:
        out.append("\nHer sayfada tekrar eden **altbilgi**:")
        for line in p["footer_lines"]:
            out.append(f"- `{line}`")
    if not (p["doc_numbers"] or p["header_lines"] or p["footer_lines"]):
        out.append("Üstbilgi/altbilgi veya doküman numarası bulunamadı.")
    out.append("")

    out.append("## Görsel ve tablo kalıbı\n")
    if p["captions"]:
        kinds = Counter(c["type"].lower() for c in p["captions"])
        out.append("Alt yazı tipleri: " +
                   ", ".join(f"**{k}** ({n}×)" for k, n in kinds.most_common()))
        out.append("\nÖrnek kalıp (birebir taklit et):\n")
        for c in p["captions"][:5]:
            out.append(f"- `{c['type']} {c['number']}-{c['text']}`")
    else:
        out.append("Şekil/tablo alt yazısı bulunamadı — alt yazı üretme.")
    for issue in p.get("caption_issues", []):
        out.append(f"\n> ⚠️ {issue}")
    out.append(f"\nTablo sayısı: **{p['tables']}**  •  madde işareti satırı: **{p['bullets']}**\n")

    out.append("## Tipografi ve renk\n")
    if p.get("body_size"):
        out.append(f"Gövde punto: **{p['body_size']} pt**")
    if p.get("font_sizes"):
        out.append("\n| Punto | Karakter |\n|---|---|")
        for s, n in p["font_sizes"].items():
            out.append(f"| {s} | {n} |")
    if p.get("fonts"):
        out.append("\nBaskın fontlar: " +
                   ", ".join(f"`{f}`" for f in list(p["fonts"])[:5]))
    if p.get("colors"):
        out.append("\n| Renk | Karakter |\n|---|---|")
        for c, n in p["colors"].items():
            out.append(f"| `{c}` | {n} |")
        non_black = [c for c in p["colors"] if c.upper() not in {"#000000"}]
        if non_black:
            out.append(f"\nVurgu/başlık rengi adayı: **`{non_black[0]}`**")
    out.append("")

    if p["warnings"]:
        out.append("## Uyarı biçimi\n")
        out.append("Uyarı benzeri satırlar:")
        for w in p["warnings"][:8]:
            out.append(f"- `{w['text']}`")
        out.append("")
    return "\n".join(out)


# --------------------------------------------------------------------------- #

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Örnek kılavuzdan yapı/stil profili çıkarır")
    ap.add_argument("reference", help="Örnek kılavuz (.pdf/.docx/.md/.txt)")
    ap.add_argument("--json", dest="json_out", help="Profili JSON olarak buraya yaz")
    ap.add_argument("--out", dest="md_out",
                    help="Markdown profilini buraya yaz (varsayılan: ekran)")
    args = ap.parse_args(argv)

    path = Path(args.reference)
    if not path.is_file():
        print(f"HATA: dosya bulunamadı: {path}", file=sys.stderr)
        return 2

    suffix = path.suffix.lower()
    try:
        if suffix == ".pdf":
            profile = read_pdf(path)
        elif suffix in {".docx", ".doc"}:
            profile = read_docx(path)
        elif suffix in {".md", ".markdown", ".txt"}:
            profile = read_text_file(path)
        else:
            print(f"HATA: desteklenmeyen tür: {suffix} "
                  f"(.pdf/.docx/.md/.txt)", file=sys.stderr)
            return 2
    except SystemExit as exc:
        print(str(exc), file=sys.stderr)
        return 3

    md = render_markdown(profile)
    if args.md_out:
        Path(args.md_out).write_text(md, encoding="utf-8")
        print(f"  + {args.md_out}")
    else:
        print(md)

    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  + {args.json_out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())