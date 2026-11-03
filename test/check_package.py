#!/usr/bin/env python3
"""Skill paketinin bütünlüğünü denetler.

Denetler:
  * SKILL.md 500 satır sınırının altında mı
  * Markdown bağlantıları gerçek dosyalara çözülüyor mu
  * frontmatter geçerli mi (name biçimi, description uzunluğu)
  * Windows'a özgü sabit yol var mı

Kullanım:  python test/check_package.py
Çıkış kodu: 0 = temiz, 1 = problem var
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "screenshot-to-manual"
problems: list[str] = []


def main() -> int:
    md_files = sorted(SKILL.rglob("*.md"))
    if not md_files:
        print(f"HATA: {SKILL} altında Markdown dosyası yok")
        return 1

    print("=== Dosyalar ===")
    for f in md_files:
        n = len(f.read_text(encoding="utf-8").splitlines())
        flag = ""
        if f.name == "SKILL.md":
            if n > 500:
                problems.append(f"SKILL.md {n} satır (500 sınırı aşıldı)")
                flag = "  <-- 500 satır SINIRI"
            else:
                flag = f"  (sınır 500, kalan {500 - n})"
        print(f"  {n:4d} satır  {f.relative_to(SKILL)}{flag}")

    print("\n=== Markdown bağlantıları ===")
    for f in md_files:
        text = f.read_text(encoding="utf-8")
        text = re.sub(r"```.*?```", "", text, flags=re.S)      # kod bloğu
        text = re.sub(r"`[^`\n]*`", "", text)                  # satır içi kod
        for m in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", text):
            target = m.group(2).split("#")[0]
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            if "<" in target or ">" in target:
                continue  # şablondaki kasıtlı yer tutucu yol
            if not (f.parent / target).resolve().exists():
                problems.append(f"{f.relative_to(SKILL)}: kırık bağlantı -> {target}")

    print("\n=== Frontmatter ===")
    skill_md = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    if not skill_md.startswith("---\n"):
        problems.append("SKILL.md: frontmatter yok")
    else:
        fm = skill_md.split("---", 2)[1]
        for key in ("name:", "description:"):
            if key not in fm:
                problems.append(f"SKILL.md: frontmatter'da '{key}' yok")
        name = re.search(r"^name:\s*(\S+)", fm, re.M)
        if name:
            v = name.group(1)
            print(f"  name = {v!r}  (uzunluk {len(v)})")
            if not re.fullmatch(r"[a-z0-9-]{1,64}", v):
                problems.append(f"SKILL.md: geçersiz name '{v}'")
        desc = re.search(r"^description:\s*(.+?)(?=^\w|\Z)", fm, re.M | re.S)
        if desc:
            d = desc.group(1).strip()
            print(f"  description uzunluğu = {len(d)} (sınır 1024)")
            if len(d) > 1024:
                problems.append(f"SKILL.md: description 1024 karakteri aşıyor ({len(d)})")

    print("\n=== Windows'a özgü yollar ===")
    for f in md_files:
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"[A-Za-z]:\\|\\\\", line):
                problems.append(f"{f.relative_to(SKILL)}:{i}: Windows yolu -> {line.strip()[:60]}")

    print("\n=== SONUÇ ===")
    if problems:
        for p in problems:
            print("  [PROBLEM]", p)
        print(f"  {len(problems)} problem")
        return 1
    print("  problem yok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())