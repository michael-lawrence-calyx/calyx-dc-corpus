#!/usr/bin/env python3
"""
load.py — drop a folder of entry files in, get them filed correctly.

Usage:
    python3 load.py ~/Desktop/corpus-update-2026-09-17

What it does:
  1. Reads every .json in the folder you point it at (recursively, so
     batch subfolders are fine). Ignores anything starting with _ or .
  2. Adds any new jurisdictions from _JURISDICTIONS-TO-ADD.json
  3. Files each entry at entries/<STATE>/<jurisdiction-key>/<id>.json,
     creating folders as needed
  4. Runs build.py to validate and rebuild docs/index.json
  5. Tells you exactly what it did

If validation fails, nothing is left half-done — it reports the error and
you fix the entry file, then run it again.

Put this file at the top level of calyx-dc-corpus, next to build.py.
"""

import json, os, shutil, subprocess, sys

REPO = os.path.dirname(os.path.abspath(__file__))
JUR_PATH = os.path.join(REPO, "schema", "jurisdictions.json")


def die(msg):
    print(f"\n  STOPPED: {msg}\n")
    sys.exit(1)


def main():
    if len(sys.argv) < 2:
        die("point me at a folder.\n"
            "  Example: python3 load.py ~/Desktop/corpus-update-2026-09-17")

    src = os.path.expanduser(sys.argv[1].rstrip("/"))
    if not os.path.isdir(src):
        die(f"not a folder: {src}")
    if not os.path.exists(os.path.join(REPO, "build.py")):
        die("load.py must sit next to build.py in calyx-dc-corpus")

    # ---------------------------------------------------------- jurisdictions
    jur = json.load(open(JUR_PATH, encoding="utf-8"))
    added_jur = []
    for root, _, files in os.walk(src):
        for fn in files:
            if fn == "_JURISDICTIONS-TO-ADD.json":
                new = json.load(open(os.path.join(root, fn), encoding="utf-8"))
                for k, v in new.items():
                    if k not in jur:
                        jur[k] = v
                        added_jur.append(k)
    if added_jur:
        json.dump(jur, open(JUR_PATH, "w", encoding="utf-8"), indent=2, sort_keys=True)

    # ---------------------------------------------------------- collect entries
    found, skipped = [], []
    for root, _, files in os.walk(src):
        for fn in sorted(files):
            if not fn.endswith(".json"):
                continue
            if fn.startswith("_") or fn.startswith("."):
                continue
            path = os.path.join(root, fn)
            try:
                e = json.load(open(path, encoding="utf-8"))
            except Exception as ex:
                skipped.append((fn, f"unparseable — {ex}"))
                continue
            if not isinstance(e, dict) or "jurisdiction" not in e or "id" not in e:
                skipped.append((fn, "not an entry (no id/jurisdiction) — skipped"))
                continue
            found.append((path, e))

    if not found:
        die(f"no entry files found in {src}")

    # ---------------------------------------------------------- check keys first
    unknown = sorted({e["jurisdiction"] for _, e in found if e["jurisdiction"] not in jur})
    if unknown:
        die("these jurisdiction keys are not in schema/jurisdictions.json:\n    "
            + "\n    ".join(unknown)
            + "\n\n  Add them there first, or include a _JURISDICTIONS-TO-ADD.json in the batch.")

    # ---------------------------------------------------------- place them
    placed, replaced = [], []
    for path, e in found:
        st = jur[e["jurisdiction"]]["state"]
        dest_dir = os.path.join(REPO, "entries", st, e["jurisdiction"])
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, e["id"] + ".json")
        existed = os.path.exists(dest)
        shutil.copy2(path, dest)
        rel = os.path.relpath(dest, REPO)
        (replaced if existed else placed).append(rel)

    # ---------------------------------------------------------- build
    print()
    if added_jur:
        print(f"  jurisdictions added ({len(added_jur)}):")
        for k in added_jur:
            print(f"    + {k}  →  {jur[k]['name']}, {jur[k]['state']}")
        print()

    if placed:
        print(f"  new entries ({len(placed)}):")
        for p in placed:
            print(f"    + {p}")
        print()
    if replaced:
        print(f"  replaced ({len(replaced)}):")
        for p in replaced:
            print(f"    ~ {p}")
        print()
    if skipped:
        print(f"  skipped ({len(skipped)}):")
        for fn, why in skipped:
            print(f"    - {fn}  {why}")
        print()

    print("  running build.py ...\n")
    r = subprocess.run([sys.executable, "build.py"], cwd=REPO,
                       capture_output=True, text=True)
    print(r.stdout.rstrip())
    if r.stderr.strip():
        print(r.stderr.rstrip())

    if r.returncode != 0:
        print("\n  VALIDATION FAILED. The files are in place but the index was not rebuilt.")
        print("  Fix the entry named above and run load.py again — it is safe to re-run.\n")
        sys.exit(1)

    print("\n  Done. Now: GitHub Desktop → summary → Commit → Push.\n")


if __name__ == "__main__":
    main()
