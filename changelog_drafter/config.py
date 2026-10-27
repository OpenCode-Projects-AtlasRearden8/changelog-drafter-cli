"""Small config loader: optional changelog.toml with a [polish] table.

Kept dependency-free and forgiving; if parsing fails we just use defaults.
"""

import os
import sys

if sys.version_info >= (3, 11):
    import tomllib
else:  # very small fallback parser for our tiny config shape
    tomllib = None


def _parse_simple(text: str):
    section = None
    out = {}
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip()
            continue
        if "=" not in line:
            continue
        key, val = (part.strip() for part in line.split("=", 1))
        val = val.strip().strip('"').strip("'")
        out[f"{section}.{key}" if section else key] = val
    return out


def load_config(paths):
    """Return dict of dotted keys, e.g. polish.base_url, from the first file."""
    for path in paths:
        if path and os.path.isfile(path):
            with open(path, "rb") as fh:
                raw = fh.read().decode("utf-8", errors="replace")
            try:
                if tomllib is not None:
                    data = tomllib.loads(raw)
                else:
                    data = _parse_simple(raw)
                polish = data.get("polish", {}) or {}
                return {
                    "polish.base_url": polish.get("base_url"),
                    "polish.model": polish.get("model"),
                    "polish.timeout": polish.get("timeout"),
                }
            except Exception:
                return {}
    return {}
