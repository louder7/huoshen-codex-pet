#!/usr/bin/env python3
"""Validate a pet atlas against the repository's inspection map."""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print(json.dumps({"ok": False, "errors": ["Pillow is required: install the development dependency"]}))
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def integer(value):
    return type(value) is int


def read_json(path):
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def local_file(root, name):
    require(isinstance(name, str) and bool(name), "asset path must be a non-empty string")
    path = (root / name).resolve()
    require(path.is_relative_to(root.resolve()), f"asset path escapes repository: {name}")
    require(path.is_file(), f"asset does not exist: {name}")
    return path


def validate(root, mapping_path):
    root = root.resolve()
    mapping = read_json(mapping_path)
    manifest = read_json(root / "pet.json")
    require(isinstance(mapping, dict) and isinstance(manifest, dict), "JSON roots must be objects")
    atlas = local_file(root, manifest.get("spritesheetPath"))
    require(atlas == local_file(root, mapping.get("atlasPath")), "manifest and map reference different atlases")
    require(re.fullmatch(r"[0-9a-f]{40}", str(mapping.get("sourceCommit", ""))) is not None, "invalid sourceCommit")
    expected_hash = mapping.get("atlasSha256")
    require(isinstance(expected_hash, str) and re.fullmatch(r"[0-9a-f]{64}", expected_hash) is not None, "invalid atlasSha256")
    actual_hash = hashlib.sha256(atlas.read_bytes()).hexdigest()
    require(actual_hash == expected_hash, "atlas SHA-256 does not match map")

    names = ("width", "height", "columns", "rows", "cellWidth", "cellHeight")
    require(all(integer(mapping.get(n)) and mapping[n] > 0 for n in names), "grid dimensions must be positive integers")
    width, height, columns, rows, cell_width, cell_height = (mapping[n] for n in names)
    require(width == columns * cell_width and height == rows * cell_height, "atlas dimensions are not divisible by the grid")
    states = mapping.get("states")
    unmapped = mapping.get("unmappedRows")
    require(isinstance(states, dict) and states, "states must be a non-empty object")
    require(isinstance(unmapped, list) and all(integer(row) and 0 <= row < rows for row in unmapped), "invalid unmappedRows")
    require(len(set(unmapped)) == len(unmapped), "duplicate unmapped row")
    expected = {(row, column): "unmapped" for row in unmapped for column in range(columns)}
    for name, state in states.items():
        require(isinstance(name, str) and name and isinstance(state, dict), "invalid state entry")
        row, indexes = state.get("row"), state.get("columns")
        require(integer(row) and 0 <= row < rows, f"{name}: row out of range")
        require(isinstance(indexes, list) and indexes, f"{name}: columns must be a non-empty array")
        require(all(integer(column) and 0 <= column < columns for column in indexes), f"{name}: column out of range")
        require(state.get("status") in ("provisional", "verified"), f"{name}: invalid status")
        require(isinstance(state.get("evidence"), str) and state["evidence"], f"{name}: missing evidence")
        require(("fps" in state) != ("durationMs" in state), f"{name}: specify either fps or durationMs")
        if "fps" in state:
            fps = state["fps"]
            require(fps is None or (type(fps) in (int, float) and 0 < fps < float("inf")), f"{name}: invalid fps")
        else:
            durations = state["durationMs"]
            require(durations is None or (isinstance(durations, list) and len(durations) == len(indexes)
                    and all(integer(value) and value > 0 for value in durations)), f"{name}: invalid durationMs")
        require(state.get("loop") is None or type(state["loop"]) is bool, f"{name}: invalid loop")
        for column in indexes:
            key = (row, column)
            require(key not in expected, f"{name}: duplicate or overlapping cell {row},{column}")
            expected[key] = name

    errors = []
    cells = []
    with Image.open(atlas) as image:
        require(image.format == "WEBP" and getattr(image, "n_frames", 1) == 1, "atlas must be a single-frame WebP")
        require(image.size == (width, height), "atlas pixel dimensions do not match map")
        require("A" in image.getbands(), "atlas has no alpha channel")
        alpha = image.getchannel("A")
        require(alpha.getextrema()[0] == 0 and alpha.getextrema()[1] > 0, "atlas must contain transparent and visible pixels")
        for row in range(rows):
            for column in range(columns):
                x, y = column * cell_width, row * cell_height
                bbox = alpha.crop((x, y, x + cell_width, y + cell_height)).getbbox()
                assigned = expected.get((row, column))
                if assigned and not bbox:
                    errors.append(f"empty assigned cell {row},{column} ({assigned})")
                if not assigned and bbox:
                    errors.append(f"unexpected non-empty cell {row},{column}")
                edge = bool(bbox and (bbox[0] == 0 or bbox[1] == 0 or bbox[2] == cell_width or bbox[3] == cell_height))
                if edge:
                    errors.append(f"alpha touches cell boundary {row},{column}")
                cells.append({"row": row, "column": column, "assignment": assigned, "nonempty": bool(bbox), "bbox": bbox, "touchesBoundary": edge})
    nonempty = sum(cell["nonempty"] for cell in cells)
    return {"ok": not errors, "atlasSha256": actual_hash, "width": width, "height": height,
            "columns": columns, "rows": rows, "nonemptyCells": nonempty,
            "emptyCells": len(cells) - nonempty, "cells": cells, "errors": errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map", type=Path, default=ROOT / "animation-map.json", help="inspection map to validate")
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root containing pet.json")
    args = parser.parse_args()
    try:
        result = validate(args.root, args.map)
    except (OSError, ValueError, TypeError, KeyError, Image.DecompressionBombError) as exc:
        result = {"ok": False, "errors": [str(exc)]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
