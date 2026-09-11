from pathlib import Path

# Newline-delimited set of seen uids, committed back to the repo between runs.
# A text file gives clean git diffs; membership testing is all we need.
STATE_FILE = Path(__file__).parent / "state" / "seen.txt"


def load_seen() -> set[str]:
    if not STATE_FILE.exists():
        return set()
    return {line.strip() for line in STATE_FILE.read_text().splitlines() if line.strip()}


def is_bootstrap() -> bool:
    return not STATE_FILE.exists()


def save_seen(uids: set[str]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text("\n".join(sorted(uids)) + "\n")
