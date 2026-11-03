#!/usr/bin/env python3
"""check_manual.py -- QA gate for manuals produced by the kullanimkilavuzu skill.

Denetler / Checks:
  1. Her görsel yolu gerçekten var mı                (ERROR)
  2. Her ekran görüntüsü en az bir kez kullanıldı mı (ERROR, ad veya içerik hash'i)
  3. Başlık / bölüm numaralandırması sürekli mi       (ERROR)
  4. Adım numaralandırması (global veya bölüm başına) (ERROR)
  5. TODO/XXX/LOREM/<yer tutucu> kalıntısı            (ERROR)
  6. [?] işaretleri "Açık Sorular" bölümünde mi       (WARNING)
  7. Her adımda en az bir görsel var mı               (WARNING)
  8. Şekil alt yazıları sıralı ve görselli mi         (WARNING)
  9. Referans kılavuzla biçim uyumu                   (WARNING, --reference ile)

Kullanım / Usage -- komutları proje kökünden çalıştırın, betik yolunu skill
klasörüne göre TAM verin (betik ile kılavuz farklı klasörlerdedir):

  python <skill-dizini>/scripts/check_manual.py <cikti>/kilavuz.md
  python <skill-dizini>/scripts/check_manual.py <cikti>/kilavuz.md \
      --screenshots <ekran-klasoru> --reference <ornek-kilavuz.md>
  python <skill-dizini>/scripts/check_manual.py <cikti>/kilavuz.md --strict --json

Çıkış kodları / Exit codes: 0 = temiz, 1 = hata var, 2 = kullanım/IO hatası
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # pragma: no cover - exotic stdout
        pass

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff"}
# Yol boşluk içerebilir; isteğe bağlı "başlık" kuyruğu image_path() içinde atılır.
IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(\s*([^)\n]+?)\s*\)")
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
H2_ANY_RE = re.compile(r"^##\s")
# "## 1. Başlarken", "## 1 — Başlarken", "## 1)", "## 1"  (## 1.1 hariç)
H2_NUM_RE = re.compile(r"^##\s+(\d+)(?:\.(?!\d)|\s*[—–:\-)]|\s*$)")
BOLUM_RE = re.compile(r"^##\s+(?:Bölüm|Bolum|Chapter)\s+(\d+)\b",
                      re.IGNORECASE | re.MULTILINE)
# Adım işaretleri: "### Adım 3 — ...", "**Adım 3.** ...", "Step 3"
STEP_RE = re.compile(r"^(?:#{2,5}\s+|\*\*)(?:Adım|Step)\s+(\d+)\b",
                     re.IGNORECASE | re.MULTILINE)
DECIMAL_RE = re.compile(r"^#{2,5}\s+(\d+\.\d+(?:\.\d+)?)[\.\s]")
SEKIL_RE = re.compile(r"^(?:Şekil|Sekil|Figure|Resim)\s+(\d+)\b", re.IGNORECASE)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
PLACEHOLDER_WORDS = ("TODO", "FIXME", "XXX", "LOREM", "TBD", "PLACEHOLDER")
OPEN_Q_RE = re.compile(r"(açık\s+sorular|acik\s+sorular|open\s+questions)", re.IGNORECASE)
CALLOUT_RE = re.compile(
    r"^>\s*\*\*(Not|Uyarı|Uyari|İpucu|Ipucu|Dikkat|Önemli|Onemli|Warning|Note|Tip|Caution|Important)\b",
    re.IGNORECASE | re.MULTILINE)

HTML_TAGS = {
    "a", "b", "br", "code", "dd", "div", "dl", "dt", "em", "h1", "h2", "h3", "h4",
    "h5", "h6", "hr", "i", "img", "kbd", "li", "ol", "p", "pre", "s", "span",
    "strong", "sub", "summary", "sup", "table", "tbody", "td", "tfoot", "th",
    "thead", "tr", "u", "ul", "details", "blockquote", "figure", "figcaption",
}
# "<10>" tek başına yer tutucu da olabilir, "x < 10 > 5" karşılaştırması da.
# Karşılaştırma saymak için ÜÇ koşul birlikte aranır: içerik sayısal, hemen
# öncesinde bir sözcük/rakam ve hemen sonrasında bir rakam. Böylece "<1.0>",
# "<...>", "<2024-01-01>" ve "<1>" yer tutucu olarak raporlanmaya devam eder.
MATH_INNER_RE = re.compile(r"^[\d\s.,]+$")
COMPARISON_AFTER_RE = re.compile(r"\s*\d")
BINARY_REF_EXTS = {".docx", ".pdf", ".odt", ".doc"}


class Finding:
    __slots__ = ("level", "code", "message", "line")

    def __init__(self, level: str, code: str, message: str, line: int | None = None):
        self.level = level
        self.code = code
        self.message = message
        self.line = line

    @property
    def key(self) -> tuple:
        return (self.level, self.code, self.message, self.line)

    def as_dict(self) -> dict:
        d = {"level": self.level, "code": self.code, "message": self.message}
        if self.line is not None:
            d["line"] = self.line
        return d

    def __str__(self) -> str:
        where = f" (satır {self.line})" if self.line else ""
        return f"[{self.level}] {self.message}{where}"


def dedupe(findings: list[Finding]) -> list[Finding]:
    seen: set[tuple] = set()
    out: list[Finding] = []
    for f in findings:
        if f.key in seen:
            continue
        seen.add(f.key)
        out.append(f)
    return out


def strip_fenced_code(text: str) -> str:
    """Fenced code bloklarını boş satırlarla değiştirir; satır numaraları korunur."""
    out: list[str] = []
    fence: str | None = None
    for line in text.splitlines():
        stripped = line.lstrip()
        if fence is None:
            if stripped.startswith("```") or stripped.startswith("~~~"):
                fence = stripped[:3]
                out.append("")
                continue
            out.append(line)
        else:
            if stripped.startswith(fence):
                fence = None
            out.append("")
    return "\n".join(out)


def image_path(match: re.Match) -> str:
    """Görsel hedefini temizler: <...> sarmalı ve "başlık" kuyruğu atılır."""
    raw = match.group(2).strip()
    raw = re.sub(r"""\s+(["']).*\1$""", "", raw)  # "title" kuyruğu
    raw = raw.strip()
    if raw.startswith("<") and raw.endswith(">"):
        raw = raw[1:-1].strip()
    return raw


def file_sha256(path: Path) -> str | None:
    try:
        h = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


# --------------------------------------------------------------------------- #
# Denetimler
# --------------------------------------------------------------------------- #

def heading_numbering(lines: list[str], findings: list[Finding]) -> None:
    for pattern, code, label in (
        (H2_NUM_RE, "h2-numbering", "Bölüm"),
        (BOLUM_RE, "bolum-numbering", "Bölüm"),
    ):
        nums = [(i + 1, int(m.group(1))) for i, line in enumerate(lines)
                if (m := pattern.match(line))]
        for idx, (lineno, num) in enumerate(nums, start=1):
            if num != idx:
                findings.append(Finding(
                    "ERROR", code,
                    f"{label} numarası sırası bozuk: {idx}. '{num}' numaralı", lineno))

    decimals = [(i + 1, m.group(1)) for i, line in enumerate(lines)
                if (m := DECIMAL_RE.match(line))]
    for idx, (lineno, value) in enumerate(decimals, start=1):
        if value.split(".")[0] != str(idx):
            findings.append(Finding(
                "WARNING", "decimal-numbering",
                f"Ondalık numaralandırma beklentinin dışında: '{value}'", lineno))


def step_numbering(lines: list[str], findings: list[Finding]) -> int:
    """Adımlar global 1..N ise ya da her bölüm kendi içinde 1..n ise geçerlidir."""
    steps: list[tuple[int, int, int]] = []  # (bölüm, satır, num)
    section = 0
    for i, line in enumerate(lines, start=1):
        if H2_ANY_RE.match(line):
            section += 1
        m = STEP_RE.match(line)
        if m:
            steps.append((section, i, int(m.group(1))))
    if not steps:
        return 0

    global_ok = [num for _, _, num in steps] == list(range(1, len(steps) + 1))
    by_section: dict[int, list[int]] = {}
    for sec, _, num in steps:
        by_section.setdefault(sec, []).append(num)
    per_section_ok = all(nums == list(range(1, len(nums) + 1))
                         for nums in by_section.values())

    if not (global_ok or per_section_ok):
        reported: set[int] = set()
        for position, (sec, lineno, num) in enumerate(steps, start=1):
            local = by_section[sec].index(num) + 1
            if num not in (position, local) and sec not in reported:
                reported.add(sec)
                findings.append(Finding(
                    "ERROR", "step-numbering",
                    f"Adım numarası sırası bozuk: '{num}' "
                    f"(beklenen {local if local == position else f'{local} veya {position}'})",
                    lineno))
    return len(steps)


def check_placeholders(lines: list[str], findings: list[Finding]) -> None:
    for i, line in enumerate(lines, start=1):
        scan = INLINE_CODE_RE.sub("", line)  # satır içi kod örnektir, yer tutucu değil
        for word in PLACEHOLDER_WORDS:
            if word in scan:
                findings.append(Finding("ERROR", "placeholder",
                                        f"Yer tutucu kalıntısı '{word}'", i))
        for m in re.finditer(r"<([^<>\n]{1,80})>", scan):
            inner = m.group(1).strip()
            if not inner or inner.lower() in HTML_TAGS:
                continue
            if "@" in inner or inner.startswith(("http", "!")):
                continue
            if _is_comparison(scan, m):
                continue
            findings.append(Finding("ERROR", "angle-placeholder",
                                    f"Doldurulmamış yer tutucu: <{inner}>", i))


def _is_comparison(line: str, match: re.Match) -> bool:
    """`x < 10 > 5` gibi karşılaştırmayı yer tutucudan ayırır.

    Üç koşul birlikte: içerik sayısal, `<` öncesinde sözcük/rakam, `>` sonrasında
    rakam. `<1.0>`, `<...>`, `<1>`, `<2024-01-01>` bu testi geçemez ve yer tutucu
    olarak raporlanır.

    BİLİNÇLİ SINIR: `x < 10 > y` (ardından rakam değil harf) karşılaştırma
    sayılmaz; yer tutucu uyarısı verir. Bunu gevşetmek "Sürüm <1.0> sürümü"
    gibi gerçek yer tutucuların kaçmasına yol açar. Kılavuzlarda değişkenli
    karşılaştırma çok nadir olduğundan muhafazakâr davranış tercih edildi.
    """
    inner = match.group(1).strip()
    if not MATH_INNER_RE.fullmatch(inner):
        return False
    before = line[:match.start()].rstrip()
    if not before or not (before[-1].isalnum() or before[-1] in "_)]}"):
        return False
    return bool(COMPARISON_AFTER_RE.match(line[match.end():]))


def check_images(lines: list[str], manual_dir: Path,
                 findings: list[Finding]) -> tuple[set[str], set[str]]:
    """Kılavuzdaki görsel referanslarını toplar; ad ve içerik hash'i döndürür."""
    names: set[str] = set()
    hashes: set[str] = set()
    for i, line in enumerate(lines, start=1):
        for m in IMAGE_RE.finditer(line):
            raw = image_path(m)
            if not raw:
                continue
            if raw.startswith(("http://", "https://", "data:")):
                names.add(Path(raw).name.lower())
                continue
            target = (manual_dir / raw.replace("\\", "/")).resolve()
            names.add(target.name.lower())
            if target.is_file():
                digest = file_sha256(target)
                if digest:
                    hashes.add(digest)
            else:
                findings.append(Finding("ERROR", "missing-image",
                                        f"Görsel dosyası bulunamadı: {raw}", i))
            if "\\" in raw or re.match(r"^[A-Za-z]:", raw) or raw.startswith("/"):
                findings.append(Finding("WARNING", "non-portable-path",
                                        f"Taşınabilir olmayan görsel yolu: {raw}", i))
    return names, hashes


def check_coverage(used_names: set[str], used_hashes: set[str],
                   screenshot_dirs: list[Path],
                   findings: list[Finding]) -> tuple[int, int]:
    """Kapsam denetimi. (kullanılan, toplam) döndürür.

    Eşleşme sırası: önce dosya adı; ad tutmuyorsa içerik hash'i (yeniden
    adlandırılmış kopya). Aynı içerikli birden fazla ekran varsa hash eşleşmesi
    sessizce geçilmez, `duplicate-content` uyarısı verilir.
    """
    available: dict[str, Path] = {}
    for d in screenshot_dirs:
        if not d.is_dir():
            findings.append(Finding("ERROR", "bad-screenshots-dir",
                                    f"Ekran görüntüsü klasörü yok: {d}"))
            continue
        for p in sorted(d.rglob("*")):
            if p.is_file() and p.suffix.lower() in IMAGE_EXTS:
                available.setdefault(p.name.lower(), p)
    # Aynı içeriği paylaşan dosyaları grupla (hash -> adlar)
    by_hash: dict[str, list[str]] = {}
    for name, path in available.items():
        digest = file_sha256(path)
        if digest:
            by_hash.setdefault(digest, []).append(name)

    used = 0
    ambiguous: dict[str, set[str]] = {}  # hash -> adlar (grup başına TEK uyarı)
    for name, path in available.items():
        if name in used_names:
            used += 1
            continue
        digest = file_sha256(path)
        if digest and digest in used_hashes:
            used += 1
            twins = [n for n in by_hash.get(digest, []) if n != name]
            if twins:
                ambiguous.setdefault(digest, set()).update([name, *twins])
            continue
        findings.append(Finding(
            "ERROR", "unused-screenshot",
            f"Hiç kullanılmayan ekran görüntüsü: {path.name} "
            f"(ne adı ne içeriği kılavuzda geçiyor)"))
    for digest, names in ambiguous.items():
        listed = ", ".join(sorted(available[n].name for n in names if n in available))
        findings.append(Finding(
            "WARNING", "duplicate-content",
            f"Aynı içerikten {len(names)} ekran görüntüsü var ({listed}); "
            f"kılavuzda gerçekten hangisinin kullanıldığını doğrula"))
    return used, len(available)


def check_open_questions(lines: list[str], findings: list[Finding]) -> None:
    start = None
    for i, line in enumerate(lines):
        m = HEADING_RE.match(line)
        if m and OPEN_Q_RE.search(m.group(2)):
            start = i
            break
    if start is None:
        findings.append(Finding("WARNING", "no-open-questions",
                                "'Açık Sorular / Open Questions' bölümü yok"))
    # Bölümün ÜSTÜNDE kalan [?] işaretleri gövdededir; bölüm içindekiler normaldir.
    for i, line in enumerate(lines, start=1):
        if "[?]" not in line:
            continue
        if start is not None and i - 1 >= start:
            continue
        findings.append(Finding("WARNING", "open-q-marker-in-body",
                                "[?] işareti gövdede; Açık Sorular bölümüne taşı", i))


def check_step_images(lines: list[str], findings: list[Finding]) -> None:
    current: tuple[int, int] | None = None
    has_image = False

    def close() -> None:
        if current and not has_image:
            findings.append(Finding("WARNING", "step-without-image",
                                    f"{current[0]}. adımda ekran görüntüsü yok",
                                    current[1]))

    for i, line in enumerate(lines, start=1):
        m = STEP_RE.match(line)
        if m:
            close()
            current, has_image = (int(m.group(1)), i), False
            continue
        if IMAGE_RE.search(line):
            if current is None:
                findings.append(Finding("WARNING", "image-outside-step",
                                        "Adım dışında görsel kullanılmış", i))
            has_image = True
    close()


def check_captions(lines: list[str], findings: list[Finding]) -> None:
    captions = [(i, int(m.group(1))) for i, line in enumerate(lines)
                if (m := SEKIL_RE.match(line.strip()))]
    for idx, (i, num) in enumerate(captions, start=1):
        if num != idx:
            findings.append(Finding(
                "WARNING", "figure-numbering",
                f"Şekil numarası sırası bozuk: {idx}. şekil '{num}' numaralı", i + 1))
        nxt = next((lines[j] for j in range(i + 1, len(lines)) if lines[j].strip()), "")
        if not IMAGE_RE.search(nxt):
            findings.append(Finding(
                "WARNING", "caption-without-image",
                f"Şekil {num} alt yazısının ardından görsel gelmiyor", i + 1))


def check_reference(ref_text: str, lines: list[str], findings: list[Finding]) -> None:
    ref_stripped = strip_fenced_code(ref_text)
    manual_text = "\n".join(lines)
    ref_h2 = bool(H2_NUM_RE.search(ref_stripped) or BOLUM_RE.search(ref_stripped))
    man_h2 = bool(H2_NUM_RE.search(manual_text) or BOLUM_RE.search(manual_text))
    if ref_h2 != man_h2:
        findings.append(Finding(
            "WARNING", "reference-h2-scheme",
            "Bölüm numaralandırma şeması referansla uyuşmuyor "
            f"(referans numaralı={ref_h2}, kılavuz numaralı={man_h2})"))
    ref_steps = bool(STEP_RE.search(ref_stripped))
    man_steps = bool(STEP_RE.search(manual_text))
    if ref_steps != man_steps:
        findings.append(Finding("WARNING", "reference-step-scheme",
                                "Adım başlığı şeması referansla uyuşmuyor"))
    ref_callouts = {m.group(1).lower() for m in CALLOUT_RE.finditer(ref_stripped)}
    man_callouts = {m.group(1).lower() for m in CALLOUT_RE.finditer(manual_text)}
    for extra in sorted(man_callouts - ref_callouts):
        findings.append(Finding("WARNING", "reference-callout",
                                f"Referansta olmayan uyarı kutusu tipi: '{extra}'"))


# --------------------------------------------------------------------------- #

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Kullanım kılavuzu QA denetimi / Manual QA check")
    ap.add_argument("manual", help="Denetlenecek kılavuz (.md)")
    ap.add_argument("--screenshots", action="append", default=[],
                    help="Ekran görüntüsü klasörü (tekrarlanabilir)")
    ap.add_argument("--reference", help="Örnek kılavuz (.md/.txt)")
    ap.add_argument("--strict", action="store_true", help="Uyarıları da hata say")
    ap.add_argument("--json", action="store_true", help="JSON çıktı")
    args = ap.parse_args(argv)

    manual = Path(args.manual)
    if not manual.is_file():
        print(f"HATA: kılavuz bulunamadı: {manual}", file=sys.stderr)
        return 2

    text = manual.read_text(encoding="utf-8", errors="replace")
    lines = strip_fenced_code(text).splitlines()
    findings: list[Finding] = []

    used_names, used_hashes = check_images(lines, manual.parent, findings)
    screenshot_dirs = [Path(p) for p in args.screenshots]
    shots_used, shots_total = check_coverage(used_names, used_hashes,
                                             screenshot_dirs, findings)
    heading_numbering(lines, findings)
    steps = step_numbering(lines, findings)
    check_placeholders(lines, findings)
    check_open_questions(lines, findings)
    check_step_images(lines, findings)
    check_captions(lines, findings)
    if args.reference:
        ref = Path(args.reference)
        if ref.suffix.lower() in BINARY_REF_EXTS:
            findings.append(Finding(
                "WARNING", "reference-binary",
                f"Referans {ref.suffix} biçiminde; önce düz metne çevirin "
                f"(python-docx / pdftotext). Stil karşılaştırması atlandı."))
        elif ref.is_file():
            check_reference(ref.read_text(encoding="utf-8", errors="replace"),
                            lines, findings)
        else:
            findings.append(Finding("WARNING", "reference-missing",
                                    f"Referans kılavuz bulunamadı: {ref}"))

    findings = dedupe(findings)
    errors = [f for f in findings if f.level == "ERROR"]
    warnings = [f for f in findings if f.level == "WARNING"]
    failed = bool(errors) or (args.strict and bool(warnings))

    if args.json:
        print(json.dumps({
            "manual": str(manual),
            "screenshots_used": shots_used,
            "screenshots_total": shots_total,
            "images_referenced": len(used_names),
            "steps": steps,
            "errors": len(errors),
            "warnings": len(warnings),
            "passed": not failed,
            "findings": [f.as_dict() for f in findings],
        }, ensure_ascii=False, indent=2))
    else:
        print("== check_manual ==")
        print(f"Kılavuz     : {manual}")
        print(f"Ekranlar    : {shots_used}/{shots_total} görsel kullanıldı "
              f"({len(screenshot_dirs)} klasör)")
        print(f"Görsel ref  : {len(used_names)}  |  Adım: {steps}")
        if args.reference:
            print(f"Referans    : {args.reference}")
        print()
        for f in findings:
            print(f)
        if not findings:
            print("(bulgu yok)")
        print()
        print(f"{'FAIL' if failed else 'PASS'}  hata={len(errors)} uyarı={len(warnings)}")
        if failed and warnings and not errors:
            print("(--strict açık olduğu için uyarılar hata sayıldı)")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
