import argparse

from . import __version__


def main() -> None:
    from .app import NicTop

    parser = argparse.ArgumentParser(
        prog="nictop", description="Live per-interface network traffic graphs in a tiling TUI."
    )
    parser.add_argument("-i", "--interval", type=float, default=1.0, help="seconds between samples (default 1)")
    parser.add_argument("--theme", help="theme name (default: last used)")
    parser.add_argument("--list-themes", action="store_true", help="print available themes and exit")
    parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args()

    app = NicTop(interval=max(0.1, args.interval), theme=args.theme)
    if args.list_themes:
        print("\n".join(sorted(app.available_themes)))
        return
    app.run()


if __name__ == "__main__":
    main()
