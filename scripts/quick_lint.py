#!/usr/bin/env python3
"""Conservative structural lint for native simai / maidata text.

NOT a full simai grammar parser; success does not certify playability.
Python 3.9+, no external dependencies.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

FIELD = re.compile(r"(?m)^[ \t]*&([A-Za-z][A-Za-z0-9_]*)=(.*)$")
NUM = r"(?:\d+(?:\.\d+)?)"


def sections(text: str) -> tuple[list[tuple[str, str]], list[str]]:
    fields = list(FIELD.finditer(text))
    issues: list[str] = []
    if not fields:
        return [("chart", text)], issues
    seen: set[str] = set()
    charts: list[tuple[str, str]] = []
    for index, match in enumerate(fields):
        name = match.group(1)
        if name in seen:
            issues.append(f"WARN duplicate field '&{name}=' (first-match semantics may apply)")
        seen.add(name)
        if name.startswith("inote_"):
            after = fields[index + 1].start() if index + 1 < len(fields) else len(text)
            charts.append((name, text[match.start(2):after]))
    if not charts:
        issues.append("ERROR maidata fields found but no &inote_N= chart")
    return charts, issues


def check_balanced(source: str) -> list[str]:
    stack: list[tuple[str, int]] = []
    pairs = {')': '(', ']': '[', '}': '{'}
    issues = []
    for index, char in enumerate(source):
        if char in "([{":
            stack.append((char, index))
        elif char in pairs:
            if not stack or stack[-1][0] != pairs[char]:
                issues.append(f"ERROR mismatched closing '{char}' at character {index + 1}")
            else:
                stack.pop()
    for char, index in stack:
        issues.append(f"ERROR unclosed '{char}' at character {index + 1}")
    return issues


def _positive(raw: str) -> bool:
    try:
        return float(raw) > 0
    except ValueError:
        return False


def lint_chart(body: str) -> list[str]:
    issues: list[str] = []
    clean = body.strip()
    if not clean:
        return ["ERROR empty chart"]
    issues.extend(check_balanced(clean))
    if not re.search(r"E\s*$", clean):
        issues.append("ERROR missing final E terminator")
    else:
        clean = re.sub(r"E\s*$", "", clean)
    if not clean.strip(" ,\n\t"):
        issues.append("WARN chart has no notes or timing instructions")
    if re.search(r"(?:^|,)\s*E\s*,", clean):
        issues.append("ERROR E appears before the final chart position")
    if not re.search(r"\(\s*" + NUM + r"\s*\)|\{\s*#?" + NUM + r"\s*\}", clean):
        issues.append("WARN no explicit initial BPM or timing grid; target-engine default may differ")
    if "//" in clean:
        issues.append("WARN '//' text is not guaranteed to be a simai comment; check target parser")
    for m in re.finditer(r"\(([^()]*)\)", clean):
        if not _positive(m.group(1).strip()):
            issues.append(f"ERROR invalid BPM '({m.group(1)})'")
    for m in re.finditer(r"\{([^{}]*)\}", clean):
        content = m.group(1).strip().removeprefix('#')
        if not _positive(content):
            issues.append(f"ERROR invalid timing grid '{{{m.group(1)}}}'")
    for m in re.finditer(r"\[([^\[\]]*)\]", clean):
        inner = m.group(1).strip()
        # Recognize the common time forms only; don't reject unfamiliar extensions.
        pieces = re.findall(NUM, inner)
        if not pieces:
            issues.append(f"WARN unrecognized duration '[{inner}]'; verify with full parser")
        elif any(not _positive(v) for v in pieces):
            issues.append(f"ERROR nonpositive duration component '[{inner}]'")
        if re.fullmatch(r"\d+(?:\.\d+)?:0+(?:\.0+)?", inner):
            issues.append(f"ERROR zero count in duration '[{inner}]'")
    if re.search(r"(?<!\d)\b0h|\b9h", clean):
        issues.append("WARN possible invalid button index in HOLD; verify with full parser")
    return issues


def lint(text: str) -> list[str]:
    found, global_issues = sections(text.lstrip("\ufeff"))
    result = list(global_issues)
    for label, body in found:
        result.extend(f"{label}: {problem}" for problem in lint_chart(body))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, help="UTF-8 maidata.txt or raw simai chart")
    args = parser.parse_args()
    try:
        text = args.file.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"ERROR cannot read input: {exc}")
        return 2
    problems = lint(text)
    for problem in problems:
        print(problem)
    errors = sum("ERROR" in problem for problem in problems)
    warns = sum("WARN" in problem for problem in problems)
    print(f"Structural lint: {errors} error(s), {warns} warning(s). Not a full parser or playtest.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
