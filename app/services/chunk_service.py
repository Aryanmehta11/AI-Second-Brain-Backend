import re

_TRAILING_PUNCT = (".", ",", ";", ":", "?", "!", ")")
_BULLET = re.compile(r"^[\-•▪●☐o□]\s")


def _is_heading(line: str, prev_blank: bool) -> bool:
    """Heuristic for section titles in PDF text: a short, title-like line after a blank line."""
    words = line.split()
    if not prev_blank or not (1 <= len(words) <= 8) or not (3 <= len(line) <= 60):
        return False
    if line.endswith(_TRAILING_PUNCT) or _BULLET.match(line):
        return False
    capitalised = sum(1 for w in words if w[:1].isupper() or w[:1].isdigit())
    return capitalised / len(words) >= 0.6


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> list[str]:
    """
    Split text into ~chunk_size character chunks on line boundaries, with
    `overlap` characters of trailing lines repeated at the start of the next
    chunk. Each chunk is prefixed with the most recent section heading so a
    chunk that starts mid-section still knows which section it belongs to.
    """
    # Lines that repeat across pages (running headers/footers, page numbers stripped)
    # are never treated as section headings
    counts: dict[str, int] = {}
    for raw in text.splitlines():
        key = re.sub(r"\d+", "", raw).strip().lower()
        if key:
            counts[key] = counts.get(key, 0) + 1
    repeated = {k for k, n in counts.items() if n >= 3}

    chunks: list[str] = []
    current: list[str] = []
    heading = ""
    chunk_heading = ""
    prev_blank = True

    def flush():
        body = "\n".join(current).strip()
        if body:
            prefix = f"[Section: {chunk_heading}]\n" if chunk_heading and not body.startswith(chunk_heading) else ""
            chunks.append(prefix + body)

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            prev_blank = True
            continue

        # Very long lines (e.g. PDFs without line breaks) are split on word boundaries
        pieces = [line]
        if len(line) > chunk_size:
            pieces = re.findall(rf".{{1,{chunk_size}}}(?:\s|$)", line + " ")

        for piece in (p.strip() for p in pieces):
            if _is_heading(piece, prev_blank) and re.sub(r"\d+", "", piece).strip().lower() not in repeated:
                heading = piece
            if current and len("\n".join(current)) + len(piece) + 1 > chunk_size:
                flush()
                tail, size = [], 0
                for prev in reversed(current):
                    if size + len(prev) > overlap:
                        break
                    tail.insert(0, prev)
                    size += len(prev) + 1
                current = tail
                chunk_heading = heading
            if not current:
                chunk_heading = heading
            current.append(piece)
            prev_blank = False

    flush()
    return chunks
