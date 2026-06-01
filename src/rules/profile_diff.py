"""Profile diff generator — flatten two profile dicts to dotted paths and emit
a human-readable diff (D-02). Pure stdlib; no new dependencies.

Filters `._source.` paths so provenance metadata churn doesn't drown policy
changes (Pitfall 4).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _unwrap(value: Any) -> Any:
    """If `value` is a methodical-annotated leaf {value, _source}, return value.
    Otherwise return value as-is. Plan 5-01 produces annotated leaves; hand-
    authored GOST profiles use bare scalars. This helper lets the diff compare
    the two on equal footing."""
    if isinstance(value, dict) and set(value.keys()) >= {"value", "_source"}:
        return value["value"]
    return value


def _flatten(d: Any, prefix: str = "") -> dict[str, Any]:
    """Walk nested dict/list/scalar; return {dotted_path: leaf_value}.

    Annotated leaves are unwrapped to their `value` before recording — diff
    sees policy values, not the {value, _source} wrapper.

    The `_source` sub-dict itself is NOT recursed into (Pitfall 4).
    """
    out: dict[str, Any] = {}
    if isinstance(d, dict):
        # Annotated leaf: store unwrapped scalar
        if set(d.keys()) >= {"value", "_source"}:
            out[prefix] = d["value"]
            return out
        for k, v in d.items():
            if k == "_source":
                continue  # Pitfall 4
            new_prefix = f"{prefix}.{k}" if prefix else k
            if isinstance(v, (dict, list)):
                out.update(_flatten(v, new_prefix))
            else:
                out[new_prefix] = v
    elif isinstance(d, list):
        out[prefix] = d  # lists diffed whole-value (avoid index churn)
    else:
        out[prefix] = d
    return out


def compute_profile_diff(
    base: dict[str, Any],
    candidate: dict[str, Any],
) -> list[str]:
    """Return diff lines grouped by top-level key.

    Per D-02:
    - One line per change: `<dotted.path>: <old> → <new>` (U+2192).
    - Grouped under `## <top_level_key>` headers.
    - Sorted alphabetically.
    - `._source.` paths filtered (Pitfall 4) — handled by `_flatten`'s skip rule.
    """
    base_flat = _flatten(base)
    cand_flat = _flatten(candidate)
    all_paths = sorted(set(base_flat) | set(cand_flat))
    lines_by_section: dict[str, list[str]] = {}
    for path in all_paths:
        old = base_flat.get(path, "<missing>")
        new = cand_flat.get(path, "<missing>")
        if old == new:
            continue
        # Extra defensive filter — _flatten already drops _source, but if a
        # caller passes a path-containing dict differently, this is the
        # backstop per Pitfall 4.
        if path.endswith("._source") or "._source." in path:
            continue
        section = path.split(".", 1)[0]
        lines_by_section.setdefault(section, []).append(f"{path}: {old} → {new}")
    out_lines: list[str] = []
    for section in sorted(lines_by_section):
        out_lines.append(f"## {section}")
        out_lines.extend(lines_by_section[section])
    return out_lines


def write_diff_sidecar(lines: list[str], path: Path) -> None:
    """Write diff lines to `path` as UTF-8, newline-joined.

    Per CLAUDE.md atomic-write idiom: ensure parent dir exists, then write_text.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(lines)
    if not body.endswith("\n"):
        body = body + "\n"
    path.write_text(body, encoding="utf-8")
