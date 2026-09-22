#!/bin/bash
# Usage:  ./publish.sh 2026-09-22    load + push + verify a batch
#         ./publish.sh check         only verify the live register
set -e
REPO="$HOME/Documents/GitHub/calyx-dc-corpus"
DROP="$HOME/Desktop/*Calyx Intelligence/*Data Centers/*Corpus Repo"
cd "$REPO"

verify() {
  LOCAL=$(python3 -c "import json;print(json.load(open('docs/index.json'))['count'])")
  echo "Local register: $LOCAL entries. Checking register.calyxos.ai ..."
  for i in $(seq 1 30); do
    LIVE=$(curl -s "https://register.calyxos.ai/index.json?t=$(date +%s)" | python3 -c "import json,sys;print(json.load(sys.stdin)['count'])" 2>/dev/null || echo 0)
    if [ "$LIVE" = "$LOCAL" ]; then echo "LIVE: $LIVE entries. Done."; exit 0; fi
    sleep 20
  done
  echo "Live still shows $LIVE after 10 minutes. Check the Actions tab on github.com."; exit 1
}
[ "$1" = "check" ] && verify

DATE="${1:?give the batch date, e.g. ./publish.sh 2026-09-22}"
findbatch() { find "$DROP" -type d -name "corpus-update-$DATE" -exec test -f "{}/_JURISDICTIONS-TO-ADD.json" \; -print -quit; }
B=$(findbatch)
if [ -z "$B" ]; then
  for Z in "$DROP/corpus-update-$DATE.zip" "$HOME/Downloads/corpus-update-$DATE.zip"; do
    [ -f "$Z" ] && unzip -oq "$Z" -d "$DROP/corpus-update-$DATE" && break
  done
  B=$(findbatch)
fi
[ -n "$B" ] || { echo "No batch found for $DATE"; exit 1; }
echo "Batch: $B"

python3 - "$B" <<'EOF'
import json, os, sys
b = sys.argv[1]
J = json.load(open(os.path.join(b, "_JURISDICTIONS-TO-ADD.json")))
have = {k for s in os.listdir("entries") if os.path.isdir("entries/"+s) for k in os.listdir("entries/"+s)}
base = lambda k: k.replace("-county", "").replace("-city", "")
bad = [f"{k} looks like existing {h}" for k in J if k not in have for h in have if h[:5] == k[:5] and base(h) == base(k)]
for f in os.listdir(b):
    if f.endswith(".json") and not f.startswith("_"):
        j = json.load(open(os.path.join(b, f)))["jurisdiction"]
        if j not in have and j not in J: bad.append(f"{f}: unknown jurisdiction {j}")
print("\n".join(bad) or "Keys OK")
sys.exit(1 if bad else 0)
EOF

python3 load.py "$B"
[ -f latest.py ] && python3 latest.py
git add -A
git commit -qm "Corpus update $DATE" || echo "Nothing new to commit"
git push -q
verify
