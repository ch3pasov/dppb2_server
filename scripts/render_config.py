#!/usr/bin/env python3
"""
Render config.yaml (current layout) into pball/configs/:
  - server.cfg (with auto-generated banner; do not edit by hand)
  - motd.txt + set motdfile when root or server.motd has text (no banner — shown in-game)
  - logins<port>.txt from server.operators (no banner — format is strict id lines only)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Mapping

try:
    import yaml
except ImportError:
    print(
        "PyYAML is required (image installs python3-yaml; locally: apt install python3-yaml)",
        file=sys.stderr,
    )
    sys.exit(1)

LISTING_KEYS = frozenset({"listed_in_browser", "master_server", "port", "identity"})
GENERATED_MOTD_CVAR_PATH = "pball/configs/motd.txt"

# Prepended to outputs so people edit config.yaml instead (Quake-style // comments).
BANNER_SERVER_CFG = """// -----------------------------------------------------------------------------
// AUTO-GENERATED — do not edit by hand. This file is overwritten on container start.
// Source of truth: config.yaml (repo root). Renderer: scripts/render_config.py
// -----------------------------------------------------------------------------
"""

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


def _emit_flat_cvars(lines: list[str], block: Mapping[str, Any]) -> None:
    for key, val in block.items():
        lines.append(f"set {str(key)} {render_cvar_value(val)}")


def _public_from_listed_in_browser(val: Any) -> int:
    if isinstance(val, bool):
        return int(val)
    if isinstance(val, int) and val in (0, 1):
        return val
    print("listing.listed_in_browser must be a boolean or 0/1", file=sys.stderr)
    sys.exit(1)


def _emit_listing(lines: list[str], lst: Mapping[str, Any]) -> None:
    extra = set(lst) - LISTING_KEYS
    if extra:
        print(f"server.listing: unknown keys {sorted(extra)!r}", file=sys.stderr)
        sys.exit(1)

    if "listed_in_browser" in lst:
        lines.append(f"set public {_public_from_listed_in_browser(lst['listed_in_browser'])}")

    if lst.get("master_server"):
        host = str(lst["master_server"]).strip()
        if host:
            lines.append(f"setmaster {host}")


def _emit_identity(lines: list[str], ident: Mapping[str, Any]) -> None:
    for key, val in ident.items():
        k = str(key)
        if k in ("contact", "motdfile"):
            continue
        lines.append(f"set {k} {render_cvar_value(val)}")


def _emit_contact(lines: list[str], block: Mapping[str, Any]) -> None:
    for key, val in block.items():
        k = str(key)
        lines.append(f'set {k} "{escape_quake(str(val))}" s')


def _extract_motd(data: dict[str, Any]) -> Any:
    srv = data.get("server")
    if isinstance(srv, dict) and "motd" in srv:
        return srv.get("motd")
    return data.get("motd")


def _normalized_motd_text(data: dict[str, Any]) -> str | None:
    raw = _extract_motd(data)
    if raw is None or not isinstance(raw, str):
        return None
    s = raw.strip()
    return s if s else None


def _emit_gameplay(lines: list[str], gp: Mapping[str, Any], game_port: int) -> None:
    gp = dict(gp) if gp else {}
    if "maxplayers" in gp:
        lines.append(f"set maxclients {render_cvar_value(gp['maxplayers'])}")
    lines.append(f"set port {game_port}")
    for key, val in gp.items():
        k = str(key)
        if k in ("maxplayers", "bots"):
            continue
        lines.append(f"set {k} {render_cvar_value(val)}")
    bots = gp.get("bots")
    if bots is not None:
        if not isinstance(bots, dict):
            print("gameplay.bots must be a mapping", file=sys.stderr)
            sys.exit(1)
        _emit_flat_cvars(lines, bots)


def build_lines(data: dict[str, Any]) -> tuple[list[str], int]:
    srv = data.get("server")
    if not isinstance(srv, dict):
        print("config must contain a server: mapping", file=sys.stderr)
        sys.exit(1)

    lst = srv.get("listing")
    if not isinstance(lst, dict):
        print("server.listing must be a mapping", file=sys.stderr)
        sys.exit(1)
    if "port" not in lst:
        print("server.listing.port is required", file=sys.stderr)
        sys.exit(1)
    port = int(lst["port"])

    lines: list[str] = []
    _emit_listing(lines, lst)

    ident = lst.get("identity")
    contact_block: Mapping[str, Any] | None = None
    if ident is not None:
        if not isinstance(ident, dict):
            print("server.listing.identity must be a mapping", file=sys.stderr)
            sys.exit(1)
        cb = ident.get("contact")
        if cb is not None:
            if not isinstance(cb, dict):
                print("server.listing.identity.contact must be a mapping", file=sys.stderr)
                sys.exit(1)
            contact_block = cb
        _emit_identity(lines, ident)

    if _normalized_motd_text(data) is not None:
        lines.append(f"set motdfile {render_cvar_value(GENERATED_MOTD_CVAR_PATH)}")

    gp = data.get("gameplay")
    if gp is not None and not isinstance(gp, dict):
        print("gameplay must be a mapping", file=sys.stderr)
        sys.exit(1)
    _emit_gameplay(lines, gp if isinstance(gp, dict) else {}, port)

    if contact_block is not None:
        _emit_contact(lines, contact_block)

    return lines, port


def main() -> None:
    ap = argparse.ArgumentParser(description="Render dppb2 config.yaml to pball/configs/")
    ap.add_argument("--config", required=True, type=Path, help="Path to config.yaml")
    ap.add_argument("--dest", required=True, type=Path, help="pball/configs directory")
    args = ap.parse_args()

    raw = args.config.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    if not data or not isinstance(data, dict):
        print("Config must be a YAML mapping", file=sys.stderr)
        sys.exit(1)

    args.dest.mkdir(parents=True, exist_ok=True)

    raw_motd = _extract_motd(data)
    if raw_motd is not None and not isinstance(raw_motd, str):
        print("motd must be a string (use | for multiline)", file=sys.stderr)
        sys.exit(1)

    lines, port = build_lines(data)

    server_cfg_body = "\n".join(lines) + "\n"
    (args.dest / "server.cfg").write_text(BANNER_SERVER_CFG + "\n" + server_cfg_body, encoding="utf-8")
    print(f"Wrote {args.dest / 'server.cfg'}")

    motd_write = _normalized_motd_text(data)
    if motd_write is not None:
        (args.dest / "motd.txt").write_text(motd_write.rstrip() + "\n", encoding="utf-8")
        print(f"Wrote {args.dest / 'motd.txt'}")

    srv = data.get("server")
    operators = srv.get("operators") if isinstance(srv, dict) else None
    if operators:
        if not isinstance(operators, list):
            print("server.operators must be a list", file=sys.stderr)
            sys.exit(1)
        lp = args.dest / f"logins{port}.txt"
        with lp.open("w", encoding="utf-8") as out:
            for entry in operators:
                if not isinstance(entry, dict):
                    print("each server.operators[] entry must be a mapping with id and op_level", file=sys.stderr)
                    sys.exit(1)
                oid = entry.get("id")
                lvl = entry.get("op_level", entry.get("level", 200))
                if oid is None:
                    print("server.operators[].id is required", file=sys.stderr)
                    sys.exit(1)
                out.write(f"{int(oid)} {int(lvl)}\n")
        print(f"Wrote {lp.name}")


if __name__ == "__main__":
    main()
