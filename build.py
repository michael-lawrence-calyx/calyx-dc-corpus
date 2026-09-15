#!/usr/bin/env python3
"""Validate entries/ and compile docs/index.json. Run after every change."""
import json, os, glob, sys, re, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
JUR  = json.load(open(os.path.join(ROOT, "schema", "jurisdictions.json"), encoding="utf-8"))

REQUIRED  = ["id","jurisdiction","instrument","mechanism","summary",
             "origin","entry_state","freshness","retrieved","source"]
ORIGINS   = {"OBSERVED","ASSERTED","DERIVED","RELAYED"}
STATES    = {"CONFIRMED","DEVIATION","CONFLICTING","NOT_CHECKED","UNRESOLVED"}
FRESH     = {"FIXED","LIVE","WARM","STALE"}
STATUS    = {"adopted","proposed","recommended","draft","expired","void"}
MECHS     = {"use-permission","quantity-cap","definition","load-trigger","acoustic",
             "utility-service","water","generation","storage","rate-allocation",
             "process","litigation","incentive","connectivity"}
SRCKINDS  = {"primary","secondary","sponsored","advocacy","commercial-tracker"}
ID_RE     = re.compile(r"^[a-z0-9-]+$")
DATE_RE   = re.compile(r"^\d{4}-\d{2}-\d{2}$")

entries, errors, warnings, seen = [], [], [], set()

for p in sorted(glob.glob(os.path.join(ROOT, "entries", "**", "*.json"), recursive=True)):
    rel = os.path.relpath(p, ROOT)
    def err(m): errors.append(rel + ": " + m)
    def warn(m): warnings.append(rel + ": " + m)
    try:
        e = json.load(open(p, encoding="utf-8"))
    except Exception as ex:
        err("unparseable - " + str(ex)); continue

    for k in REQUIRED:
        if not e.get(k): err("missing required field '" + k + "'")

    eid = e.get("id","")
    if eid in seen: err("duplicate id '" + eid + "'")
    seen.add(eid)
    if eid and not ID_RE.match(eid): err("id '" + eid + "' must be lowercase letters, digits and hyphens")

    ju = e.get("jurisdiction")
    if ju not in JUR:
        err("jurisdiction '" + str(ju) + "' is not a key in schema/jurisdictions.json - add it there first")
    else:
        expect = os.path.join("entries", JUR[ju]["state"], ju)
        if not rel.startswith(expect):
            err("filed under " + os.path.dirname(rel) + ", should be " + expect)

    if e.get("mechanism") not in MECHS:     err("unknown mechanism '" + str(e.get("mechanism")) + "'")
    if e.get("origin") not in ORIGINS:      err("bad origin '" + str(e.get("origin")) + "'")
    if e.get("entry_state") not in STATES:  err("bad entry_state '" + str(e.get("entry_state")) + "'")
    if e.get("freshness") not in FRESH:     err("bad freshness '" + str(e.get("freshness")) + "'")
    if e.get("status") and e["status"] not in STATUS: err("bad status '" + e["status"] + "'")

    for f in ("retrieved","effective"):
        if e.get(f) and not DATE_RE.match(e[f]): err(f + " '" + e[f] + "' must be YYYY-MM-DD")

    src = e.get("source") or {}
    if src.get("kind") not in SRCKINDS: err("bad source.kind '" + str(src.get("kind")) + "'")
    if not src.get("citation") and not src.get("url") and not src.get("file"):
        err("source names no citation, url or file - an entry whose source cannot be retrieved is not an entry")

    if e.get("text") and e.get("origin") == "RELAYED":
        err("RELAYED entry carries verbatim text - you cannot quote what you have not read")
    if e.get("origin") == "OBSERVED" and src.get("kind") != "primary":
        warn("OBSERVED but source.kind is not 'primary' - check this")
    if e.get("origin") == "RELAYED" and e.get("entry_state") == "CONFIRMED":
        err("RELAYED cannot be CONFIRMED - confirmation requires reading the record")
    if e.get("entry_state") in ("NOT_CHECKED","UNRESOLVED","CONFLICTING") and not e.get("confidence_note"):
        warn(str(e.get("entry_state")) + " without a confidence_note - say what is unresolved")
    if e.get("supersedes") and e["supersedes"] == eid:
        err("entry supersedes itself")

    e["state"] = JUR.get(ju, {}).get("state", "??")
    e["jurisdiction_name"] = JUR.get(ju, {}).get("name", ju)
    e["_path"] = rel
    entries.append(e)

for e in entries:
    if e.get("supersedes") and e["supersedes"] not in seen:
        errors.append(e["_path"] + ": supersedes '" + e["supersedes"] + "' which does not exist")

if warnings:
    print("WARNINGS\n" + "\n".join("  " + w for w in warnings) + "\n")
if errors:
    print("VALIDATION FAILED\n" + "\n".join("  " + x for x in errors))
    sys.exit(1)

out = {
    "generated": datetime.date.today().isoformat(),
    "count": len(entries),
    "states": sorted(set(e["state"] for e in entries)),
    "jurisdictions": sorted(set(e["jurisdiction_name"] for e in entries)),
    "mechanisms": sorted(set(e["mechanism"] for e in entries)),
    "by_origin": dict((o, sum(1 for e in entries if e["origin"] == o)) for o in sorted(ORIGINS)),
    "entries": entries,
}
os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, "docs", "index.json"), "w", encoding="utf-8"), indent=1)

obs = out["by_origin"].get("OBSERVED", 0)
pct = round(100.0 * obs / max(1, len(entries)))
print("OK - %d entries, %d jurisdictions, %d states, %d read in original (%d%%)"
      % (len(entries), len(out["jurisdictions"]), len(out["states"]), obs, pct))
