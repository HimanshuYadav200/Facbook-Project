#!/bin/zsh
# Render a run folder with Remotion.
# Usage: engine/tools/render.sh runs/<niche>/<id> [--preview]     (--preview = half size, faster, for checking)
#
# Builds a small "stage" folder with only what the render needs (APFS clones: instant, no extra disk),
# so Remotion doesn't copy the run's big out/ videos into its bundle every time.
# Needs Node 22: Node 26 hangs Remotion ("Waiting for root component to load").
set -euo pipefail
RUN=${1:?usage: render.sh runs/<niche>/<id> [--preview]}
RUN=$(cd "$RUN" && pwd)
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
REMOTION="$ROOT/engine/remotion"
ID=$(basename "$RUN")
STAGE="$REMOTION/.stage/$ID"
export PATH="/opt/homebrew/opt/node@22/bin:$PATH"

STYLE=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['style'])" "$RUN/plan.json")
MUSIC=$(python3 -c "import json,sys; m=json.load(open(sys.argv[1])).get('music'); print(m['track'] if m else '')" "$RUN/plan.json")

rm -rf "$STAGE"; mkdir -p "$STAGE/assets/music"
for f in plan.json words.json voice.wav eyes.json data img; do
  [[ -e "$RUN/$f" ]] && cp -Rc "$RUN/$f" "$STAGE/"
done
cp -Rc "$ROOT/library/sfx" "$STAGE/assets/sfx"
[[ -n "$MUSIC" ]] && cp -c "$ROOT/library/music/$MUSIC.mp3" "$STAGE/assets/music/"

mkdir -p "$RUN/out"
OUT="$RUN/out/raw.mp4"; EXTRA=()
if [[ "${2:-}" == "--preview" ]]; then OUT="$RUN/out/preview.mp4"; EXTRA=(--scale=0.5); fi

cd "$REMOTION"
npx remotion render src/index.ts "$STYLE" "$OUT" --public-dir "$STAGE" "${EXTRA[@]}"
rm -rf "$STAGE"
echo "rendered $OUT"
