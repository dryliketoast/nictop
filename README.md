# nictop

Python project managed with [uv](https://docs.astral.sh/uv/).

## Setup

    uv sync

## Run

    uv run nictop      # or: uv run ebbflow (alias)
    uv run nictop --theme nord --interval 0.5
    uv run nictop --list-themes

## Keys

| Key | Action |
| --- | --- |
| `space` / `enter` | tick or untick the focused interface (`tab` focuses the list) |
| `a` / `n` | select all / none |
| `t` / `T` | next / previous theme (or `ctrl+p` for the theme picker) |
| `b` | toggle bits (decimal) / bytes (binary) |
| `s` | show or hide the interface list |
| `q` | quit |

Selected tiles fill the whole area and re-flow when the terminal is resized.
Theme, selection and units are remembered in `~/.config/nictop/config.json`.

## Standalone binary

    ./scripts/build.sh        # -> dist/nictop (+ dist/ebbflow symlink), ~17 MB

Single file, no Python needed on the target. PyInstaller binaries are tied to the
OS, CPU architecture and glibc they were built on, so build on the oldest distro
you want to support (and once per architecture).
