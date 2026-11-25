from datetime import datetime, timedelta, timezone
from pathlib import Path

# Per-profile seen memory, committed back to the repo between runs. Each line is
# "<uid> <YYYY-MM-DD>": the id and the last date we saw the role still open. The
# date drives TTL expiry, so a role that closes and later reopens can re-alert.
_DIR = Path(__file__).parent / "state"


def _path(key: str) -> Path:
    # "v3": ids are now per-posting and entries carry a date (TTL). Bumping the
    # name re-bootstraps cleanly instead of misreading the old format.
    name = "seen_v3" if key == "swe" else f"seen_v3_{key}"
    return _DIR / f"{name}.txt"


def load_seen(key: str = "swe") -> dict[str, str]:
    p = _path(key)
    if not p.exists():
        return {}
    out: dict[str, str] = {}
    today = datetime.now(timezone.utc).date().isoformat()
    for line in p.read_text().splitlines():
        parts = line.split()
        if not parts:
            continue
        out[parts[0]] = parts[1] if len(parts) > 1 else today
    return out


def is_bootstrap(key: str = "swe") -> bool:
    return not _path(key).exists()


def save_seen(seen: dict[str, str], key: str = "swe", ttl_days: int = 14) -> None:
    cutoff = (datetime.now(timezone.utc).date() - timedelta(days=ttl_days)).isoformat()
    kept = {u: d for u, d in seen.items() if d >= cutoff}
    p = _path(key)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(f"{u} {d}" for u, d in sorted(kept.items())) + "\n")
