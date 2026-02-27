#!/bin/bash

# Round-trip test: extract assets from build-src, recompile into build, compare checksums.
# STAGE.DIR is skipped (no extraction tooling yet).
# ZMOVIE.STR is copied directly (no recompiler yet) — its checksum will trivially pass.

source .venv/bin/activate

PASS=0
FAIL=0
FAILURES=()
ERRORS=()

# Temp empty dir used as --new-bins so the rejoiners never pick up pre-existing modified files
EMPTY_NEWBINS=$(mktemp -d)
trap "rm -rf $EMPTY_NEWBINS" EXIT

checksum() {
    if command -v md5sum &>/dev/null; then
        md5sum "$1" | cut -d' ' -f1
    else
        md5 -q "$1"
    fi
}

compare() {
    local DISK="$1"
    local FILE="$2"
    local ORIG="build-src/$DISK/MGS/$FILE"
    local NEW="build/$DISK/MGS/$FILE"

    if [ ! -f "$ORIG" ]; then
        echo "  SKIP  $FILE (not found in build-src)"
        return
    fi
    if [ ! -f "$NEW" ]; then
        echo "  FAIL  $FILE (not found in build)"
        FAILURES+=("$DISK/$FILE")
        ((FAIL++))
        return
    fi

    if cmp -s "$ORIG" "$NEW"; then
        echo "  PASS  $FILE"
        ((PASS++))
    else
        local ORIG_SUM NEW_SUM
        ORIG_SUM=$(checksum "$ORIG")
        NEW_SUM=$(checksum "$NEW")
        echo "  FAIL  $FILE"
        echo "        src: $ORIG_SUM"
        echo "        new: $NEW_SUM"
        FAILURES+=("$DISK/$FILE")
        ((FAIL++))
    fi
}

for DISK in "jpn-d1" "jpn-d2" "usa-d1" "usa-d2" "integral-d1" "integral-d2"; do
    VERSION=$(echo "$DISK" | cut -d'-' -f1)
    SRC="build-src/$DISK/MGS"
    BUILD="build/$DISK/MGS"
    WORK="workingFiles/$DISK"

    echo ""
    echo "=============================="
    echo "  $DISK"
    echo "=============================="

    # --- RADIO.DAT ---
    echo "[RADIO.DAT] Extracting..."
    mkdir -p "$WORK/radio"
    RADIO_FLAGS="-x"
    { [ "$VERSION" = "jpn" ] || [ "$VERSION" = "integral" ]; } && RADIO_FLAGS="-jx"
    if python3 myScripts/RadioDatTools.py "$SRC/RADIO.DAT" "$WORK/radio/RADIO" $RADIO_FLAGS; then
        echo "[RADIO.DAT] Recompiling..."
        python3 myScripts/RadioDatRecompiler.py "$WORK/radio/RADIO.xml" "$BUILD/RADIO.DAT" -x -D
    else
        echo "[RADIO.DAT] ERROR: extraction failed."
        ERRORS+=("$DISK/RADIO.DAT (extraction)")
    fi

    # --- DEMO.DAT ---
    echo "[DEMO.DAT] Extracting..."
    mkdir -p "$WORK/demo/bins"
    if python3 myScripts/DemoTools/demoSplitter.py "$SRC/DEMO.DAT" "$WORK/demo/bins"; then
        echo "[DEMO.DAT] Recompiling..."
        python3 myScripts/DemoTools/demoRejoiner.py "$WORK/demo/bins" "$BUILD/DEMO.DAT" --new-bins "$EMPTY_NEWBINS"
    else
        echo "[DEMO.DAT] ERROR: extraction failed."
        ERRORS+=("$DISK/DEMO.DAT (extraction)")
    fi

    # --- VOX.DAT ---
    echo "[VOX.DAT] Extracting..."
    mkdir -p "$WORK/vox/bins"
    if python3 myScripts/voxTools/voxSplit.py "$SRC/VOX.DAT" "$WORK/vox/bins"; then
        echo "[VOX.DAT] Recompiling..."
        python3 myScripts/voxTools/voxRejoiner.py "$WORK/vox/bins" "$BUILD/VOX.DAT" --source "$SRC/VOX.DAT" --new-bins "$EMPTY_NEWBINS"
    else
        echo "[VOX.DAT] ERROR: extraction failed."
        ERRORS+=("$DISK/VOX.DAT (extraction)")
    fi

    # --- ZMOVIE.STR ---
    echo "[ZMOVIE.STR] Extracting..."
    mkdir -p "$WORK/zmovie/bins"
    if python3 myScripts/zmovieTools/movieSplitter.py "$SRC/ZMOVIE.STR" "$WORK/zmovie"; then
        echo "[ZMOVIE.STR] Recompiling..."
        python3 myScripts/zmovieTools/zMovieTextInjector.py "$WORK/zmovie/bins" "$BUILD/ZMOVIE.STR" --source "$SRC/ZMOVIE.STR"
    else
        echo "[ZMOVIE.STR] ERROR: extraction failed."
        ERRORS+=("$DISK/ZMOVIE.STR (extraction)")
    fi

    # --- Checksums ---
    echo ""
    echo "  Checksums:"
    compare "$DISK" "RADIO.DAT"
    compare "$DISK" "DEMO.DAT"
    compare "$DISK" "VOX.DAT"
    compare "$DISK" "ZMOVIE.STR"

done

echo ""
echo "=============================="
echo "  Results: PASS=$PASS  FAIL=$FAIL"
echo "=============================="

if [ ${#FAILURES[@]} -gt 0 ]; then
    echo ""
    echo "Failed files:"
    for f in "${FAILURES[@]}"; do
        echo "  - $f"
    done
fi

if [ ${#ERRORS[@]} -gt 0 ]; then
    echo ""
    echo "Step errors (extract/recompile failed):"
    for e in "${ERRORS[@]}"; do
        echo "  - $e"
    done
fi
