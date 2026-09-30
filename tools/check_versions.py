#!/usr/bin/env python3
"""发布前检查三套插件清单的 name / version 是否一致：python3 tools/check_versions.py"""
import json, pathlib, sys
root = pathlib.Path(__file__).resolve().parent.parent
files = {"Claude Code": ".claude-plugin/plugin.json", "Codex": ".codex-plugin/plugin.json", "Kimi Code": "kimi.plugin.json"}
seen = {}
for tool, f in files.items():
    d = json.loads((root / f).read_text(encoding="utf-8"))
    seen[tool] = (d["name"], d["version"]); print(f"{tool:12} {d['name']}  {d['version']}")
ok = len(set(seen.values())) == 1
print("\n✓ 三套清单一致" if ok else "\n✗ 名称或版本不一致，请改成同一个值再发布")
sys.exit(0 if ok else 1)
