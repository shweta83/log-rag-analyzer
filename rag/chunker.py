"""
chunker.py — Log file chunking module
--------------------------------------
Splits log files into structured chunks with source metadata.
Each chunk is a dict: { "text": str, "source": str }

Used by main.py — not intended to be run directly.
"""

import re
from pathlib import Path

LOG_LEVELS = {"ERROR", "WARN", "WARNING", "INFO", "DEBUG", "CRITICAL", "FATAL"}


def _is_log_entry_start(line: str) -> bool:
    """
    Detect if a line is the start of a new log entry.
    Handles common formats:
      2024-01-15 14:32:11 ERROR ...
      [ERROR] 2024-01-15 ...
      ERROR: some message
    """
    timestamp_pattern = r"^\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}"
    bracket_pattern   = r"^\[(ERROR|WARN|WARNING|INFO|DEBUG|CRITICAL|FATAL)\]"
    level_pattern     = r"^(ERROR|WARN|WARNING|INFO|DEBUG|CRITICAL|FATAL)[\s:]"

    return bool(
        re.match(timestamp_pattern, line) or
        re.match(bracket_pattern,   line) or
        re.match(level_pattern,     line)
    )


def _chunk_by_log_entry(lines: list[str]) -> list[str]:
    """
    Group lines into log entries.
    Multi-line entries (stack traces, tracebacks) are attached to their
    parent log line rather than split into separate chunks.
    """
    chunks  = []
    current = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if _is_log_entry_start(stripped):
            if current:
                chunks.append("\n".join(current))
            current = [stripped]
        else:
            current.append(stripped)  # continuation: stack trace, etc.

    if current:
        chunks.append("\n".join(current))

    return chunks


def _chunk_by_fixed_lines(lines: list[str], lines_per_chunk: int = 10, overlap: int = 2) -> list[str]:
    """
    Fallback: split into fixed-size overlapping blocks.
    Overlap preserves context across chunk boundaries.
    """
    clean = [l.strip() for l in lines if l.strip()]
    step  = max(1, lines_per_chunk - overlap)
    return [
        "\n".join(clean[i: i + lines_per_chunk])
        for i in range(0, len(clean), step)
        if clean[i: i + lines_per_chunk]
    ]


def _filter_noise(chunks: list[str], min_length: int = 20) -> list[str]:
    """Remove chunks that are too short to carry useful signal."""
    return [c for c in chunks if len(c.strip()) >= min_length]


def chunk_log_file(filepath: str, strategy: str = "auto") -> list[dict]:
    """
    Read a log file and return a list of chunks with metadata.

    Each chunk is a dict:
        {
            "text":   str,   # the log content
            "source": str    # filename the chunk came from
        }

    strategy:
        "auto"  — tries entry-based chunking; falls back to fixed-line if
                  fewer than 3 entries are detected
        "entry" — always chunk by log entry (best for structured logs)
        "fixed" — always chunk by fixed line count (best for unstructured logs)

    Returns an empty list if the file cannot be read or yields no chunks.
    """
    path = Path(filepath)
    source = path.name

    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as e:
        print(f"  WARNING: Could not read '{filepath}': {e}")
        return []

    lines = text.splitlines()

    if strategy == "entry":
        raw_chunks = _chunk_by_log_entry(lines)
    elif strategy == "fixed":
        raw_chunks = _chunk_by_fixed_lines(lines)
    else:  # auto
        raw_chunks = _chunk_by_log_entry(lines)
        if len(raw_chunks) < 3:
            print(f"  Few structured entries in '{source}' — switching to fixed-line chunking.")
            raw_chunks = _chunk_by_fixed_lines(lines)

    clean_chunks = _filter_noise(raw_chunks)

    return [{"text": chunk, "source": source} for chunk in clean_chunks]