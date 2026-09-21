from pathlib import Path

# Newline-delimited set of seen uids per profile, committed back to the repo
# between runs. A text file gives clean git diffs; membership testing is all we
# need. Each profile keeps its own file (state/seen.txt, state/seen_pm.txt).
_DIR = Path(__file__).parent / "state"


def _path(key: str) -> Path:
    name = "seen" if key == "swe" else f"seen_{key}"
    return _DIR / f"{name}.txt"


def load_seen(key: str = "swe") -> set[str]:
    p = _path(key)
    if not p.exists():
        return set()
    return {line.strip() for line in p.read_text().splitlines() if line.strip()}


def is_bootstrap(key: str = "swe") -> bool:
    return not _path(key).exists()


def save_seen(uids: set[str], key: str = "swe") -> None:
    p = _path(key)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(sorted(uids)) + "\n")
