#!/usr/bin/env python3
"""
Render config/server.yaml into PB2 runtime files under pball/configs/:
  - server.cfg (prelude, vars, vars_trailing_s only — no comments; document in YAML)
  - motd.txt (optional multiline string)
  - logins<port>.txt (optional operators list)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print(
        "PyYAML is required (image installs python3-yaml; locally: apt install python3-yaml)",
        file=sys.stderr,
    )
    sys.exit(1)


def escape_quake(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def render_cvar_value(v: object) -> str:
    if isinstance(v, bool):
        return str(int(v))
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        t = str(v)
        if t.endswith(".0") and t[:-2].lstrip("-").isdigit():
            return t[:-2]
        return t
    if v is None:
        return '""'
    return f'"{escape_quake(str(v))}"'


def main() -> None:
    ap = argparse.ArgumentParser(description="Render dppb2 server.yaml to pball/configs/")
    ap.add_argument("--config", required=True, type=Path, help="Path to server.yaml")
    ap.add_argument("--dest", required=True, type=Path, help="pball/configs directory")
    args = ap.parse_args()

    raw = args.config.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    if not data or not isinstance(data, dict):
        print("Config must be a YAML mapping", file=sys.stderr)
        sys.exit(1)

    args.dest.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []

    prelude = data.get("prelude")
    if prelude is not None:
        if not isinstance(prelude, list):
            print("prelude must be a list of strings", file=sys.stderr)
            sys.exit(1)
        for line in prelude:
            lines.append(str(line).strip())

    vars_ = data.get("vars")
    if not isinstance(vars_, dict):
        print("vars must be a mapping", file=sys.stderr)
        sys.exit(1)
    for key, val in vars_.items():
        k = str(key)
        lines.append(f"set {k} {render_cvar_value(val)}")

    trailing = data.get("vars_trailing_s")
    if trailing is not None:
        if not isinstance(trailing, dict):
            print("vars_trailing_s must be a mapping", file=sys.stderr)
            sys.exit(1)
        for key, val in trailing.items():
            k = str(key)
            lines.append(f'set {k} "{escape_quake(str(val))}" s')

    (args.dest / "server.cfg").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {args.dest / 'server.cfg'}")

    if "motd" in data and data["motd"] is not None:
        motd = data["motd"]
        if not isinstance(motd, str):
            print("motd must be a string (use | for multiline)", file=sys.stderr)
            sys.exit(1)
        (args.dest / "motd.txt").write_text(motd.rstrip() + "\n", encoding="utf-8")
        print(f"Wrote {args.dest / 'motd.txt'}")

    if "port" not in vars_:
        print("vars.port is required", file=sys.stderr)
        sys.exit(1)
    port = int(vars_["port"])

    operators = data.get("operators")
    if operators:
        if not isinstance(operators, list):
            print("operators must be a list", file=sys.stderr)
            sys.exit(1)
        lp = args.dest / f"logins{port}.txt"
        with lp.open("w", encoding="utf-8") as out:
            for entry in operators:
                if not isinstance(entry, dict):
                    print("each operators[] entry must be a mapping with id and op_level", file=sys.stderr)
                    sys.exit(1)
                oid = entry.get("id")
                lvl = entry.get("op_level", entry.get("level", 200))
                if oid is None:
                    print("operators[].id is required", file=sys.stderr)
                    sys.exit(1)
                out.write(f"{int(oid)} {int(lvl)}\n")
        print(f"Wrote {lp.name}")


if __name__ == "__main__":
    main()
