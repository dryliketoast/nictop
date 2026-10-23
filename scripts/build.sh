#!/usr/bin/env bash
# Build a single-file binary for the current OS/arch into dist/nictop (+ dist/ebbflow alias).
set -euo pipefail
cd "$(dirname "$0")/.."

uv run pyinstaller --noconfirm --clean --onefile \
    --name nictop \
    --paths src \
    --collect-data textual \
    --collect-submodules rich._unicode_data \
    --distpath dist --workpath build/pyinstaller --specpath build \
    scripts/entry.py

ln -sf nictop dist/ebbflow
echo "Built: $(du -h dist/nictop | cut -f1)  dist/nictop (also dist/ebbflow)"
