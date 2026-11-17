"""The class checklist inside settings.txt.

After you sign in, the program writes every class and break it finds on your page into the bottom of
settings.txt as a checklist. You put an x in the brackets of the ones you want, so there is nothing to
type and no name can be misspelled:

    [looking for]
    [ ] ECEN 325 - Electronics
    [x] ECEN 340 - Electric Energy Conversion      <- chosen
    [registered]
    [x] ECEN 350 - Computer Architecture and Design (CRN 12345)
    [breaks]
    [ ] afternoon

Every run refreshes the list from the page and keeps the x marks you already made.
"""
import re
from pathlib import Path

BEGIN = "# >>>>>>>>>> YOUR CLASSES: written by the program from your page, put an x in the brackets <<<<<<<<<<"
END = "# >>>>>>>>>> END OF YOUR CLASSES <<<<<<<<<<"

INTRO = [
    "# This list was copied from YOUR schedule page, so the names are exactly right.",
    "# Put an x in the brackets of the ones you want, like  [x] ECEN 340 - ...  then save this file.",
    "#   [looking for]  the classes you want to get into (the Courses list on the page)",
    "#   [registered]   classes you are already enrolled in (only used when SELECT_MODE=specified:",
    "#                  mark the ones you KEEP; leave unmarked the one you are replacing)",
    "#   [breaks]       breaks to have ticked (mark none to leave your breaks alone)",
    "# The program refreshes this list from the page every run and keeps your x marks.",
]

GROUPS = ("looking for", "registered", "breaks")
ENTRY = re.compile(r"^\[( |x|X)\]\s+(.*\S)\s*$")
HEADER = re.compile(r"^\[(looking for|registered|breaks)\]\s*$")
CRN = re.compile(r"\(CRN (\d{5})\)\s*$")


def entry_text(group, item):
    text = item["label"]
    if group == "registered":
        text += " (CRN %s)" % item["id"].rsplit("_", 1)[-1]
    return text


def _split(lines):
    """Return (before, block_lines, after); block_lines is None when there is no checklist yet."""
    try:
        start = next(i for i, l in enumerate(lines) if l.strip() == BEGIN)
        end = next(i for i, l in enumerate(lines) if i > start and l.strip() == END)
    except StopIteration:
        return lines, None, []
    return lines[:start], lines[start:end + 1], lines[end + 1:]


def parse_block(block_lines):
    """-> {group: [(ticked, text)]} from the lines of the checklist."""
    groups = {g: [] for g in GROUPS}
    current = None
    for line in block_lines or []:
        raw = line.strip()
        h = HEADER.match(raw)
        if h:
            current = h.group(1)
            continue
        e = ENTRY.match(raw)
        if e and current:
            groups[current].append((e.group(1) in "xX", e.group(2)))
    return groups


def sync(path, found):
    """Write/refresh the checklist from what is on the page. `found` = {group: [items from selection.read_group]}.

    Returns "created", "updated", "unchanged" or "empty" (nothing found on the page, so nothing was written).
    """
    path = Path(path)
    if not any(found.get(g) for g in GROUPS):
        return "empty"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    lines = text.splitlines()
    before, block, after = _split(lines)
    old = parse_block(block) if block else {g: [] for g in GROUPS}
    ticked_before = {(g, t) for g in GROUPS for ok, t in old[g] if ok}

    new_block = [BEGIN] + INTRO
    for g in GROUPS:
        new_block.append("")
        new_block.append("[%s]" % g)
        for item in found.get(g, []):
            t = entry_text(g, item)
            new_block.append(("[x] " if (g, t) in ticked_before else "[ ] ") + t)
    new_block += ["", END]

    if block == new_block:
        return "unchanged"
    if block is None:
        merged = list(before)
        if merged and merged[-1].strip():
            merged.append("")
        merged += new_block
        status = "created"
    else:
        merged = before + new_block + after
        status = "updated"
    path.write_text("\n".join(merged) + "\n", encoding="utf-8")
    return status


def chosen(path):
    """Names the user ticked with an x, ready for selection.apply_selection:
    registered classes by CRN, everything else as '=exact label'."""
    path = Path(path)
    if not path.exists():
        return {g: [] for g in GROUPS}
    _, block, _ = _split(path.read_text(encoding="utf-8").splitlines())
    groups = parse_block(block) if block else {g: [] for g in GROUPS}
    out = {g: [] for g in GROUPS}
    for g in GROUPS:
        for ok, text in groups[g]:
            if not ok:
                continue
            m = CRN.search(text)
            out[g].append(m.group(1) if m else "=" + text)
    return out
