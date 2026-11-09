#!/usr/bin/env python3
"""Conservative simai/maidata structural lint; Python 3.9+, standard library only.

Checks supported time forms and control ordering. Does not check geometry,
end-time coverage, audio alignment, sensor conflicts, difficulty or playability.
"""
from __future__ import annotations

import argparse
import math
import re
from pathlib import Path

FIELD = re.compile(r"(?m)^[ \t]*&([A-Za-z][A-Za-z0-9_]*)=(.*)$")
NUMBER = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)"


def sections(text: str) -> tuple[list[tuple[str, str]], list[str]]:
    fields = list(FIELD.finditer(text))
    if not fields:
        return [("chart", text)], []
    seen, charts, issues = set(), [], []
    for index, match in enumerate(fields):
        name = match.group(1)
        if name in seen:
            issues.append(f"WARN duplicate field '&{name}=' (engine behavior may differ)")
        seen.add(name)
        if re.fullmatch(r"inote_\d+", name):
            after = fields[index + 1].start() if index + 1 < len(fields) else len(text)
            charts.append((name, text[match.start(2):after]))
    if not charts:
        issues.append("ERROR maidata fields found but no &inote_N= chart")
    return charts, issues


def check_balanced(source: str) -> list[str]:
    stack, issues = [], []
    pairs = {')': '(', ']': '[', '}': '{'}
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


def valid_number(raw: str, allow_zero: bool = False) -> bool:
    if not re.fullmatch(NUMBER, raw.strip()):
        return False
    value = float(raw)
    return math.isfinite(value) and (value >= 0 if allow_zero else value > 0)


def duration_issues(inner: str) -> list[str]:
    """Validate numeric roles in documented time forms, not note-type legality."""
    inner = inner.strip()
    parts, tail = [], inner
    unknown = [f"WARN unrecognized duration '[{inner}]'; verify with full parser"]
    if "##" in tail:
        wait, tail = tail.split("##", 1)
        if not re.fullmatch(NUMBER, wait):
            return unknown
        parts.append(("slide wait", wait, True))
    if "#" in tail:
        bpm, tail = tail.split("#", 1)
        if bpm:
            if not re.fullmatch(NUMBER, bpm):
                return unknown
            parts.append(("duration BPM", bpm, False))
        elif "##" in inner or ":" in tail:
            return unknown
    if ":" in tail:
        pair = tail.split(":")
        if len(pair) != 2 or not all(re.fullmatch(NUMBER, p) for p in pair):
            return unknown
        parts.extend([("length divider", pair[0], False), ("duration count", pair[1], False)])
    elif re.fullmatch(NUMBER, tail):
        if "#" not in inner:
            return unknown
        parts.append(("duration seconds", tail, False))
    else:
        return unknown
    return [f"ERROR invalid {role} '{raw}' in '[{inner}]'"
            for role, raw, zero in parts if not valid_number(raw, zero)]


def check_sequence(source: str) -> list[str]:
    issues, cell = [], []
    bpm_known, absolute_grid, saw_note, ended = False, False, False, False

    def flush():
        nonlocal saw_note, ended
        token = ''.join(cell).strip()
        cell.clear()
        if not token:
            return
        if ended:
            issues.append("ERROR content appears after E terminator")
        elif token == 'E':
            ended = True
        else:
            if not saw_note and not (bpm_known or absolute_grid):
                issues.append("WARN no explicit initial BPM or seconds grid before first note; verify engine defaults")
            saw_note = True

    i = 0
    while i < len(source):
        ch = source[i]
        if ch in '({[':
            close = {'(': ')', '{': '}', '[': ']'}[ch]
            j = source.find(close, i + 1)
            if j == -1:
                break  # check_balanced reports the missing delimiter.
            value = source[i + 1:j].strip()
            if ch == '[':
                cell.append(source[i:j + 1])
            else:
                token = ''.join(cell).strip()
                if ended or token == 'E':
                    issues.append("ERROR timing instruction appears after E terminator")
                if token not in ('', 'E'):
                    issues.append("WARN timing instruction inside a note cell; verify with full parser")
                if ch == '(':
                    if not valid_number(value):
                        issues.append(f"ERROR invalid BPM '({value})'")
                    else:
                        bpm_known = True
                else:
                    absolute_grid = value.startswith('#')
                    number = value[1:] if absolute_grid else value
                    if not valid_number(number):
                        issues.append(f"ERROR invalid timing grid '{{{value}}}'")
                    elif not absolute_grid and not bpm_known:
                        issues.append("WARN relative timing grid appears before BPM; verify engine defaults")
            i = j + 1
            continue
        if ch == ',':
            flush()
        else:
            cell.append(ch)
        i += 1
    flush()
    if not ended:
        issues.append("ERROR missing final E terminator")
    if not saw_note:
        issues.append("WARN chart has no notes")
    return list(dict.fromkeys(issues))


def lint_chart(body: str) -> list[str]:
    clean = body.strip()
    if not clean:
        return ["ERROR empty chart"]
    issues = check_balanced(clean) + check_sequence(clean)
    if '//' in clean or '||' in clean:
        issues.append("WARN comment-like text detected; this checker does not interpret engine-specific comments")
    for m in re.finditer(r"\[([^\[\]]*)\]", clean):
        issues.extend(duration_issues(m.group(1)))
    if re.search(r"(?<!\d)\b0h|\b9h", clean):
        issues.append("WARN possible invalid button index in HOLD; verify with full parser")
    return list(dict.fromkeys(issues))


def lint(text: str) -> list[str]:
    found, issues = sections(text.lstrip('\ufeff'))
    return issues + [f"{label}: {problem}" for label, body in found for problem in lint_chart(body)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', type=Path, help='UTF-8 maidata.txt or raw simai chart')
    args = parser.parse_args()
    try:
        text = args.file.read_text(encoding='utf-8-sig')
    except (OSError, UnicodeDecodeError) as exc:
        print(f"ERROR cannot read input: {exc}")
        return 2
    problems = lint(text)
    for problem in problems:
        print(problem)
    errors = sum('ERROR' in p for p in problems)
    warns = sum('WARN' in p for p in problems)
    print(f"Structural lint: {errors} error(s), {warns} warning(s). Not a full parser or playtest.")
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())

