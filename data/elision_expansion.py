# ── Elision expansion ─────────────────────────────────────────────────────────
# Run this cell once. Then use expand_elisions(line) anywhere in the notebook.

import re
import urllib.request

ELISIONS = [
    # Specific tokens first (most specific → least specific)
    (r"\bne'er\b",          "never"),
    (r"\be'er\b",           "ever"),
    (r"\bo'er\b",           "over"),
    (r"(?<!\w)'fore\b",     "before"),
    (r"(?<!\w)'gainst\b",   "against"),
    (r"(?<!\w)'tis\b",      "it is"),
    (r"(?<!\w)'twas\b",     "it was"),
    (r"(?<!\w)'twere\b",    "it were"),
    (r"(?<!\w)'twixt\b",    "betwixt"),
    (r"\bth'(?=\s|$)",      "the"),        # th' executor → the executor
    (r"\bwh'r\b",           "whether"),
    (r"\bo'er",             "over"),       # o'er- compounds: o'ertake, o'erworn
    # General suffix elisions
    (r"'st\b",              "est"),        # mak'st→makest, feel'st→feelest
    (r"'d\b",               "ed"),         # distill'd→distilled, belov'd→beloved
    (r"'t\b",               "it"),         # on't→onit (rare)
]

def expand_elisions(line: str) -> str:
    """Expand Shakespeare elisions to full forms. Leaves possessives (beauty's) untouched."""
    for pattern, replacement in ELISIONS:
        line = re.sub(pattern, replacement, line, flags=re.IGNORECASE)
    return line


def load_sonnets_from_gutenberg(url: str = "https://www.gutenberg.org/cache/epub/1041/pg1041.txt") -> list[dict]:
    """
    Fetch the Gutenberg Shakespeare sonnets, parse into per-line records,
    and apply elision expansion.

    Returns list of dicts:
        sonnet   : int  — sonnet number (1–154)
        original : str  — line as printed
        expanded : str  — line with elisions expanded
        changed  : bool — whether any expansion was applied
    """
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    raw = urllib.request.urlopen(req).read().decode("utf-8")

    # Trim to just the sonnets content
    start = raw.index("THE SONNETS")
    try:
        end = raw.index("*** END OF THE PROJECT GUTENBERG")
    except ValueError:
        end = len(raw)
    text = raw[start:end]

    # Split on Roman numeral headers (lines that are only Roman numerals)
    blocks = re.split(r'\n[ \t]*([IVXLC]+)[ \t]*\n', text)

    records = []
    sonnet_num = 0

    i = 0
    while i < len(blocks):
        chunk = blocks[i].strip()
        # Check if next chunk is a Roman numeral header
        if i + 1 < len(blocks) and re.fullmatch(r'[IVXLC]+', blocks[i+1].strip()):
            sonnet_num = len([b for b in blocks[:i+2] if re.fullmatch(r'[IVXLC]+', b.strip())])
            i += 2
            continue
        if sonnet_num == 0:
            i += 1
            continue

        for raw_line in chunk.splitlines():
            line = raw_line.strip()
            if not line or len(line.split()) < 4:
                continue
            if re.fullmatch(r'[IVXLC]+', line):
                continue
            original = line
            expanded = expand_elisions(line)
            records.append({
                "sonnet":   sonnet_num,
                "original": original,
                "expanded": expanded,
                "changed":  original != expanded,
            })
        i += 1

    return records


# ── Quick demo ────────────────────────────────────────────────────────────────
demo = [
    "Feed'st thy light's flame with self-substantial fuel,",
    "But flowers distill'd, though they with winter meet,",
    "Beauty o'er-snowed and bareness every where:",
    "Which, used, lives th' executor to be.",
    "O'ercharg'd with burthen of mine own love's might.",
    "And nothing 'gainst Time's scythe can make defence",
    "'Tis not enough that through the cloud thou break,",
    "That thereby beauty's rose might never die,",   # possessive — unchanged
]

print("Elision expansion demo:")
for line in demo:
    exp = expand_elisions(line)
    tag = "→" if exp != line else "="
    print(f"  {tag} {exp}")

print("\nexpand_elisions() ready. Call load_sonnets_from_gutenberg() to fetch the full corpus.")
