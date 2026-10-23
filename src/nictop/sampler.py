"""Per-interface throughput sampling built on psutil."""

import time
from collections import deque
from dataclasses import dataclass, field

import psutil

HISTORY = 1000


@dataclass
class Iface:
    name: str
    rx: deque[float] = field(default_factory=lambda: deque(maxlen=HISTORY))
    tx: deque[float] = field(default_factory=lambda: deque(maxlen=HISTORY))
    rx_total: int = 0
    tx_total: int = 0
    up: bool = True
    speed: int = 0  # link speed in Mb/s, 0 when unknown
    _prev: tuple[int, int] | None = None


class Sampler:
    def __init__(self) -> None:
        self.ifaces: dict[str, Iface] = {}
        self._last: float | None = None

    def names(self) -> list[str]:
        return sorted(self.ifaces)

    def sample(self) -> None:
        now = time.monotonic()
        dt = None if self._last is None else max(now - self._last, 1e-3)
        self._last = now
        counters = psutil.net_io_counters(pernic=True)
        stats = psutil.net_if_stats()

        for name in set(self.ifaces) - set(counters):
            del self.ifaces[name]
        for name, c in counters.items():
            it = self.ifaces.setdefault(name, Iface(name))
            rx_rate = tx_rate = 0.0
            if dt and it._prev:
                # a counter reset (driver reload) shows as a negative delta
                rx_rate = max(0, c.bytes_recv - it._prev[0]) / dt
                tx_rate = max(0, c.bytes_sent - it._prev[1]) / dt
            it._prev = (c.bytes_recv, c.bytes_sent)
            it.rx.append(rx_rate)
            it.tx.append(tx_rate)
            it.rx_total, it.tx_total = c.bytes_recv, c.bytes_sent
            st = stats.get(name)
            it.up = bool(st and st.isup)
            it.speed = st.speed if st else 0
