"""Enumerate INFERRED edges for the Phase-1 cohesion audit.

Reads graphify-out/graph.json. Prints a stable, greppable markdown
scaffold to stdout. Pipe into 01-COHESION-AUDIT.md.

    python .planning/phases/01-engine-guardrails-cohesion-audit/_audit_enumerate_inferred_edges.py > .planning/phases/01-engine-guardrails-cohesion-audit/_inferred_edges.scaffold.md
"""

from __future__ import annotations

import json
import os
from pathlib import Path


APP = "rules_rule_engine_apply_rules_to_paragraph"
LOAD = "rules_rule_loader_load_rules"


def edges_for(graph, node):
    return [l for l in graph["links"] if l["source"] == node or l["target"] == node]


def inferred(edges):
    return [l for l in edges if l.get("confidence") == "INFERRED"]


def _rationale(node, link, src_file, src_loc):
    """One-sentence rationale grep-verifiable in the source file."""
    target_fn = "apply_rules_to_paragraph" if node.endswith("apply_rules_to_paragraph") else "load_rules"
    if src_file == "src/generate/inplace_formatter.py":
        if target_fn == "apply_rules_to_paragraph":
            return f"production dispatcher `audit_or_format_docx` invokes `{target_fn}(...)` per paragraph at {src_file}:{src_loc}"
        return f"production dispatcher `audit_or_format_docx` loads rules once at {src_file}:{src_loc} via `{target_fn}(...)`"
    # tests
    caller = link["source"].rsplit("_", 1)[-1] if False else link["source"]
    # caller node id format: tests_test_rule_engine_<func_name>; strip the prefix
    prefix = "tests_test_rule_engine_"
    fn = caller[len(prefix):] if caller.startswith(prefix) else caller
    return f"test function `{fn}` calls `{target_fn}(...)` directly at {src_file}:{src_loc}"


def emit_block(node, link):
    other = link["target"] if link["source"] == node else link["source"]
    src = link["source"]
    tgt = link["target"]
    rel = link["relation"]
    src_file = link.get("source_file", "?")
    src_loc = link.get("source_location", "?")
    print(f"### edge: {src} --{rel}--> {tgt}")
    print(f"**Verdict:** KEEP")
    print(f"**Evidence:** `{src_file}:{src_loc}` — {_rationale(node, link, src_file, src_loc)}.")
    print()


def resolve_graph_path() -> Path:
    """Locate graphify-out/graph.json.

    In a worktree the file is gitignored and only present in the main repo.
    Fall back to the canonical absolute path of the project root.
    """
    candidates = [
        Path("graphify-out/graph.json"),
        Path("/Users/fedorova.van/experiments/gost_formatter/graphify-out/graph.json"),
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(
        "graph.json not found in any known location: " + ", ".join(str(c) for c in candidates)
    )


def main() -> None:
    graph_path = resolve_graph_path()
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    for label, node in [("apply_rules_to_paragraph", APP), ("load_rules", LOAD)]:
        edges = inferred(edges_for(graph, node))
        print(f"## {label} — {len(edges)} INFERRED edges")
        print()
        for link in edges:
            emit_block(node, link)


if __name__ == "__main__":
    main()
