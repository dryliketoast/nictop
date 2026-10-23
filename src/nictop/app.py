import asyncio

from rich.console import Group
from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.color import Color
from textual.containers import Horizontal, Vertical
from textual.events import Resize
from textual.widget import Widget
from textual.widgets import Footer, SelectionList, Static
from textual.widgets.selection_list import Selection

from . import config
from .graph import MIN_SCALE, fmt_rate, fmt_total, graph_rows, nice_ceiling
from .layout import best_columns, split_rows
from .sampler import Sampler


class Tile(Widget):
    """One interface: download graph on top, upload mirrored underneath."""

    DEFAULT_CSS = """
    Tile {
        width: 1fr;
        height: 1fr;
        background: $surface;
        border: round $primary;
    }
    Tile.down { border: round $panel-lighten-2; }
    """

    def __init__(self, name: str) -> None:
        super().__init__()
        self.iface = name

    def render(self) -> Group | Text:
        app: NicTop = self.app  # type: ignore[assignment]
        it = app.sampler.ifaces.get(self.iface)
        width, height = self.content_size.width, self.content_size.height
        if it is None or width < 4 or height < 1:
            return Text("")

        self.set_class(not it.up, "down")
        speed = f" · {it.speed} Mb/s" if it.speed else ""
        self.border_title = f" {self.iface}{'' if it.up else ' (down)'}{speed} "
        self.border_subtitle = f" ▼ {fmt_total(it.rx_total)}  ▲ {fmt_total(it.tx_total)} "

        p = app.palette
        bg = self.background_colors[1]
        rx, tx = list(it.rx)[-width:], list(it.tx)[-width:]
        scale = nice_ceiling(max([MIN_SCALE, *rx, *tx]))

        def label(arrow: str, vals: list[float], color: Color, note: str = "") -> Text:
            """Rate line; peak and the right-aligned note are dropped when the tile is narrow."""
            line = Text(no_wrap=True)
            line.append(f"{arrow} ", color.hex6)
            line.append(fmt_rate(vals[-1] if vals else 0.0, app.bits), "bold")
            peak = f"  peak {fmt_rate(max(vals, default=0), app.bits)}"
            if line.cell_len + len(peak) <= width:
                line.append(peak, "dim")
            if note and line.cell_len + len(note) + 2 <= width:
                line.append(" " * (width - line.cell_len - len(note)))
                line.append(note, "dim")
            return line

        lines = [label("▼", rx, p["primary"], f"scale {fmt_rate(scale, app.bits)}")]
        graph_h = height - 2  # one label row above each half
        if graph_h >= 2:
            up_h = graph_h // 2 + graph_h % 2
            lines += graph_rows(rx, width, up_h, scale, p["primary"], p["accent"], bg)
            lines.append(label("▲", tx, p["secondary"]))
            lines += graph_rows(
                tx, width, graph_h - up_h, scale, p["secondary"], p["warning"], bg, inverted=True
            )
        else:
            lines.append(label("▲", tx, p["secondary"]))
        return Group(*lines)


class NicTop(App):
    TITLE = "nictop"
    CSS = """
    #ifaces { width: 26; border: round $primary; background: $surface; }
    #ifaces:focus { border: round $accent; }
    #tiles { width: 1fr; height: 1fr; }
    .row { width: 1fr; height: 1fr; }
    #empty { width: 1fr; height: 1fr; content-align: center middle; color: $text-muted; }
    """
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("t", "next_theme", "Theme"),
        Binding("T", "prev_theme", "Prev theme", show=False),
        Binding("b", "toggle_bits", "Bits/Bytes"),
        Binding("s", "toggle_sidebar", "Sidebar"),
        Binding("a", "select_all", "All"),
        Binding("n", "select_none", "None"),
        Binding("tab", "focus_next", "Focus", show=False),
    ]

    def __init__(self, interval: float = 1.0, theme: str | None = None) -> None:
        super().__init__()
        self.interval = interval
        self.cfg = config.load()
        self.sampler = Sampler()
        self.sampler.sample()  # baseline so the first tick has a delta
        self.bits: bool = self.cfg.get("bits", False)
        self.selected: set[str] = set(self.cfg.get("selected") or self._default_selection())
        self.palette: dict[str, Color] = {}
        self._sig: tuple | None = None
        self._option_names: list[str] = []
        self._lock = asyncio.Lock()
        self._theme_pref = theme or self.cfg.get("theme")

    def _default_selection(self) -> list[str]:
        return [n for n, it in self.sampler.ifaces.items() if it.up and n != "lo"]

    def compose(self) -> ComposeResult:
        with Horizontal():
            sidebar = SelectionList[str](id="ifaces")
            sidebar.border_title = "Interfaces"
            yield sidebar
            yield Vertical(id="tiles")
        yield Footer()

    async def on_mount(self) -> None:
        if self._theme_pref in self.available_themes:
            self.theme = self._theme_pref
        self._load_palette()
        self.sync_options()
        self.set_interval(self.interval, self.tick)
        self.query_one("#ifaces").display = self.cfg.get("sidebar", True)
        await self.relayout()

    # -- theming --------------------------------------------------------

    def _load_palette(self) -> None:
        vars_ = self.get_css_variables()
        self.palette = {
            k: Color.parse(vars_[k]) for k in ("primary", "secondary", "accent", "warning")
        }

    def watch_theme(self, theme: str) -> None:
        if not self.is_mounted:
            return
        self._load_palette()
        self.refresh_tiles()
        self.save_config()

    def _cycle_theme(self, step: int) -> None:
        names = sorted(self.available_themes)
        self.theme = names[(names.index(self.theme) + step) % len(names)]
        self.notify(self.theme, title="Theme", timeout=1.5)

    def action_next_theme(self) -> None:
        self._cycle_theme(1)

    def action_prev_theme(self) -> None:
        self._cycle_theme(-1)

    # -- data + layout ----------------------------------------------------

    def tick(self) -> None:
        self.sampler.sample()
        self.sync_options()
        self.refresh_tiles()
        self.run_worker(self.relayout(), exclusive=False)

    def refresh_tiles(self) -> None:
        for tile in self.query(Tile):
            tile.refresh()

    def sync_options(self) -> None:
        """Keep the checkbox list in step with interfaces that appear or vanish."""
        names = self.sampler.names()
        if names == self._option_names:
            return
        self._option_names = names
        lst = self.query_one("#ifaces", SelectionList)
        lst.clear_options()
        lst.add_options([Selection(n, n, n in self.selected) for n in names])

    def visible_names(self) -> list[str]:
        return [n for n in self.sampler.names() if n in self.selected]

    async def relayout(self) -> None:
        async with self._lock:
            container = self.query_one("#tiles")
            names = self.visible_names()
            size = container.size
            cols = best_columns(len(names), size.width, size.height)
            sig = (tuple(names), cols)
            if sig == self._sig:
                return
            self._sig = sig
            await container.remove_children()
            if not names:
                await container.mount(Static("No interfaces selected — tick some on the left.", id="empty"))
                return
            for chunk in split_rows(names, cols):
                await container.mount(Horizontal(*[Tile(n) for n in chunk], classes="row"))

    @on(Resize)
    def on_resize(self) -> None:
        if self.is_mounted:
            self.run_worker(self.relayout(), exclusive=False)

    # -- selection --------------------------------------------------------

    @on(SelectionList.SelectedChanged)
    def selection_changed(self, event: SelectionList.SelectedChanged) -> None:
        present = set(self.sampler.names())
        self.selected = (self.selected - present) | set(event.selection_list.selected)
        self.save_config()
        self.run_worker(self.relayout(), exclusive=False)

    def action_select_all(self) -> None:
        self.query_one("#ifaces", SelectionList).select_all()

    def action_select_none(self) -> None:
        self.query_one("#ifaces", SelectionList).deselect_all()

    def action_toggle_sidebar(self) -> None:
        side = self.query_one("#ifaces")
        side.display = not side.display
        self.save_config()

    def action_toggle_bits(self) -> None:
        self.bits = not self.bits
        self.refresh_tiles()
        self.save_config()

    def save_config(self) -> None:
        config.save(
            {
                "theme": self.theme,
                "selected": sorted(self.selected),
                "bits": self.bits,
                "sidebar": self.query_one("#ifaces").display,
            }
        )
