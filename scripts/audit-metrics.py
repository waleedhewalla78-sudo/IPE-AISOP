#!/usr/bin/env python3
"""Collect audit metrics for FULL-PRODUCT-STATUS-AUDIT.md"""
import json, os, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICES = ROOT / "services"
WEB = ROOT / "apps" / "web" / "src"

def count_lines(paths):
    total = 0
    for p in paths:
        if p.is_file() and p.suffix in {".py", ".ts", ".tsx"}:
            try:
                total += sum(1 for _ in p.open(encoding="utf-8", errors="ignore"))
            except OSError:
                pass
    return total

def py_files(base):
    if not base.exists():
        return []
    return [p for p in base.rglob("*.py") if "node_modules" not in str(p) and ".venv" not in str(p)]

def count_tests(base):
    td = base / "tests"
    if not td.exists():
        return 0, 0
    files = list(td.rglob("test_*.py"))
    funcs = 0
    for f in files:
        txt = f.read_text(encoding="utf-8", errors="ignore")
        funcs += len(re.findall(r"^\s*(async )?def test_", txt, re.M))
    return len(files), funcs

def endpoints_in_service(app_dir: Path):
    eps = set()
    if not app_dir.exists():
        return eps
    pat = re.compile(r"@(?:router|app)\.(get|post|put|patch|delete)\([\"']([^\"']+)", re.I)
    for f in app_dir.rglob("*.py"):
        for m in pat.finditer(f.read_text(encoding="utf-8", errors="ignore")):
            eps.add(f"{m.group(1).upper()} {m.group(2)}")
    return eps

cards = []
for svc_dir in sorted(SERVICES.iterdir()):
    if not svc_dir.is_dir():
        continue
    app = svc_dir / "app"
    if not app.is_dir():
        continue
    loc = count_lines(py_files(svc_dir))
    tf, tc = count_tests(svc_dir)
    eps = endpoints_in_service(app)
    main = svc_dir / "app" / "main.py"
    port = "?"
    if main.exists():
        t = main.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"port[=:\s]+(\d{4})", t) or re.search(r"uvicorn.*--port\s+(\d+)", t)
        if m:
            port = m.group(1)
    cards.append({
        "service": svc_dir.name,
        "loc": loc,
        "endpoints": len(eps),
        "test_files": tf,
        "test_funcs": tc,
        "port": port,
    })

# scoped test counts
all_test_files = [p for p in ROOT.rglob("test_*.py") if ".venv" not in str(p) and "node_modules" not in str(p)]
fe_tests = list((WEB.parent / "tests").rglob("*.test.ts")) + list((WEB.parent / "tests").rglob("*.test.tsx")) + list((ROOT / "apps" / "web" / "e2e").rglob("*.spec.ts"))

py_loc = count_lines(py_files(SERVICES) + py_files(ROOT / "migrations") + py_files(ROOT / "tests"))
ts_loc = count_lines(list(WEB.rglob("*.ts")) + list(WEB.rglob("*.tsx")))

todo = 0
for base in [SERVICES, WEB]:
    for f in base.rglob("*"):
        if f.suffix not in {".py", ".ts", ".tsx"}:
            continue
        if any(x in str(f) for x in [".venv", "node_modules"]):
            continue
        todo += len(re.findall(r"TODO|FIXME|HACK|XXX", f.read_text(encoding="utf-8", errors="ignore")))

md_files = [p for p in ROOT.rglob("*.md") if "node_modules" not in str(p) and ".venv" not in str(p)]

out = {
    "py_loc_services": sum(c["loc"] for c in cards),
    "py_loc_total_scoped": py_loc,
    "ts_loc_web": ts_loc,
    "test_py_files": len(all_test_files),
    "test_fe_files": len(fe_tests),
    "todo_fixme_count": todo,
    "md_files": len(md_files),
    "services": cards,
    "total_endpoints": sum(c["endpoints"] for c in cards),
}
print(json.dumps(out, indent=2))
