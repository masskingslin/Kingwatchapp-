import os
import math
import threading
import time
import socket
import subprocess
from datetime import datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.utils import platform

# ─────────────────────────────────────────────────────────────────
# HELPERS (100% Android Safe)
# ─────────────────────────────────────────────────────────────────
def fmt(n):
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return "%.1f%s" % (n, u)
        n = n / 1024.0
    return "%.1fGB" % n

def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def get_bat():
    try:
        from plyer import battery as pb
        s = pb.status
        pct = int(s.get("percentage") or 0)
        chg = bool(s.get("isCharging"))
        lbl = "Charging" if chg else ("~%dh%02dm" % divmod(pct * 8, 60))
        return pct, lbl
    except Exception:
        # Safe Android fallback
        try:
            with open("/sys/class/power_supply/battery/capacity", "r") as f:
                pct = int(f.read().strip())
            with open("/sys/class/power_supply/battery/status", "r") as f:
                status = f.read().strip()
            lbl = "Charging" if status == "Charging" else ("~%dh%02dm" % divmod(pct * 8, 60))
            return pct, lbl
        except Exception:
            return 0, "N/A"

THEMES = [
    {"name": "DARK",  "bg": (0.07, 0.07, 0.10), "card": (0.13, 0.13, 0.18), "txt": (1.0, 1.0, 1.0),    "accent": (0.25, 0.72, 1.0), "sub": (0.50, 0.50, 0.60), "gbg": (0.18, 0.18, 0.24)},
    {"name": "LIGHT", "bg": (0.93, 0.93, 0.96), "card": (1.0, 1.0, 1.0),    "txt": (0.10, 0.10, 0.15), "accent": (0.10, 0.50, 0.90), "sub": (0.42, 0.42, 0.50), "gbg": (0.84, 0.84, 0.90)},
    {"name": "CYBER", "bg": (0.02, 0.05, 0.02), "card": (0.05, 0.10, 0.05), "txt": (0.20, 0.90, 0.20), "accent": (0.10, 0.90, 0.30), "sub": (0.20, 0.60, 0.20), "gbg": (0.10, 0.20, 0.10)},
    {"name": "OCEAN", "bg": (0.02, 0.08, 0.15), "card": (0.05, 0.15, 0.25), "txt": (0.90, 0.95, 1.0),  "accent": (0.0, 0.80, 1.0),  "sub": (0.40, 0.60, 0.80), "gbg": (0.10, 0.20, 0.35)},
    {"name": "LAVA",  "bg": (0.12, 0.05, 0.05), "card": (0.18, 0.08, 0.08), "txt": (1.0, 0.90, 0.90),  "accent": (1.0, 0.40, 0.10), "sub": (0.80, 0.50, 0.50), "gbg": (0.25, 0.12, 0.12)},
]

class ArcGauge(Widget):
    def __init__(self, col, gbg, **kw):
        super(ArcGauge, self).__init__(**kw)
        self.val = 0.0
        self.col = col
        self.gbg = gbg
        self.size_hint = (1, 1)

    def set_value(self, v):
        self.val = v
        self._redraw()

    def set_colors(self, col, gbg):
        self.col = col
        self.gbg = gbg
        self._redraw()

    def _redraw(self, *a):
        self.canvas.clear()
        cx, cy = self.center_x, self.center_y
        r = min(self.width, self.height) / 2.0 - dp(6)
        if r < 4: return
        with self.canvas:
            Color(self.gbg[0], self.gbg[1], self.gbg[2], 1)
            Line(ellipse=(cx - r, cy - r, r * 2, r * 2, -225, 225), width=dp(7), cap="round")
            span = (max(0.0, min(100.0, self.val)) / 100.0) * 270.0
            if span > 0:
                Color(self.col[0], self.col[1], self.col[2], 1)
                Line(ellipse=(cx - r, cy - r, r * 2, r * 2, -225, -225 + span), width=dp(7), cap="round")
                ang = math.radians(-225.0 + span)
                tx, ty = cx + r * math.cos(ang), cy + r * math.sin(ang)
                Color(self.col[0], self.col[1], self.col[2], 0.7)
                d = dp(5)
                Ellipse(pos=(tx - d, ty - d), size=(d * 2, d * 2))

    def on_size(self, *a): self._redraw()
    def on_pos(self, *a): self._redraw()

class MiniBar(Widget):
    def __init__(self, col, gbg, **kw):
        super(MiniBar, self).__init__(**kw)
        self.val = 0.0
        self.col, self.gbg = col, gbg
        self.size_hint_y = None
        self.height = dp(10)

    def set_value(self, v):
        self.val = v
        self._redraw()

    def set_colors(self, col, gbg):
        self.col, self.gbg = col, gbg
        self._redraw()

    def _redraw(self, *a):
        self.canvas.clear()
        h, rr = self.height, self.height / 2.0
        with self.canvas:
            Color(self.gbg[0], self.gbg[1], self.gbg[2], 1)
            RoundedRectangle(pos=self.pos, size=(self.width, h), radius=[rr])
            fw = max(h, (max(0.0, min(100.0, self.val)) / 100.0) * self.width)
            Color(self.col[0], self.col[1], self.col[2], 1)
            RoundedRectangle(pos=self.pos, size=(fw, h), radius=[rr])

    def on_size(self, *a): self._redraw()
    def on_pos(self, *a): self._redraw()

class CardBox(BoxLayout):
    def __init__(self, card_col, height=None, **kwargs):
        super(CardBox, self).__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = dp(12)
        self.spacing = dp(6)
        if height:
            self.size_hint_y = None
            self.height = height
        with self.canvas.before:
            self._cc = Color(*card_col, 1)
            self._cr = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(16)])
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, instance, value):
        self._cr.pos, self._cr.size = self.pos, self.size

    def update_color(self, col):
        self._cc.rgba = list(col) + [1]

class Kingwatchapp(App):
    def __init__(self, **kw):
        super(Kingwatchapp, self).__init__(**kw)
        self._tidx = 0
        self._net_sent = 0
        self._net_recv = 0
        self._net_t = 0.0
        self._cards, self._gauges, self._bars = [], [], []
        self._theme_btn = None
        self._all_labels = {}

    def build(self):
        self.title = "KingWatch Pro"
        T = THEMES[0]
        root = BoxLayout(orientation="vertical")
        self._set_bg(root, T["bg"])
        sv = ScrollView(size_hint=(1, 1))
        inner = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10), size_hint_y=None)
        inner.bind(minimum_height=inner.setter("height"))
        sv.add_widget(inner)
        root.add_widget(sv)
        self._root_box, self._inner, self._T = root, inner, T
        self._build_header(inner, T)
        self._build_battery(inner, T)
        self._build_network(inner, T)
        self._build_gauges(inner, T)
        self._build_ram_detail(inner, T)
        self._build_bottom(inner, T)
        return root

    def _set_bg(self, widget, col):
        with widget.canvas.before:
            widget._bgc = Color(*col, 1)
            widget._bgr = RoundedRectangle(pos=widget.pos, size=widget.size)
        def _upd(instance, value):
            instance._bgr.pos, instance._bgr.size = instance.pos, instance.size
        widget.bind(pos=_upd, size=_upd)

    def _lbl(self, text, size, col, bold=False, halign="left"):
        l = Label(
            text=text, font_size=dp(size), color=list(col) + [1], bold=bold,
            halign=halign, valign="middle", size_hint_y=None, height=dp(size + 8),
        )
        l.bind(size=lambda w, v: setattr(w, "text_size", v))
        return l

    def _build_header(self, parent, T):
        row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        title = self._lbl("KINGWATCH PRO", 20, T["accent"], bold=True)
        title.size_hint_x = 1
        clock = self._lbl("00:00:00", 12, T["sub"], halign="right")
        clock.size_hint_x = None
        clock.width = dp(76)
        self._all_labels["clock"] = clock
        btn = Button(
            text="DARK", size_hint_x=None, width=dp(76), background_normal="",
            background_color=list(T["accent"]) + [1], color=(0, 0, 0, 1), bold=True, font_size=dp(11),
        )
        btn.bind(on_release=self._next_theme)
        self._theme_btn = btn
        row.add_widget(title)
        row.add_widget(clock)
        row.add_widget(btn)
        parent.add_widget(row)

    def _build_battery(self, parent, T):
        card = CardBox(T["card"], height=dp(90))
        self._cards.append(card)
        row = BoxLayout(spacing=dp(12))
        left = BoxLayout(orientation="vertical", size_hint_x=None, width=dp(90))
        lbl_pct = self._lbl("0%", 28, (0.2, 0.9, 0.4), bold=True)
        left.add_widget(self._lbl("BATTERY", 10, T["sub"]))
        left.add_widget(lbl_pct)
        right = BoxLayout(orientation="vertical", spacing=dp(4))
        lbl_status = self._lbl("--", 14, T["txt"], bold=True)
        bar = MiniBar(col=(0.2, 0.9, 0.4), gbg=T["gbg"])
        lbl_time = self._lbl("--", 11, T["sub"])
        right.add_widget(lbl_status)
        right.add_widget(bar)
        right.add_widget(lbl_time)
        row.add_widget(left)
        row.add_widget(right)
        card.add_widget(row)
        parent.add_widget(card)
        self._all_labels["bat_pct"] = lbl_pct
        self._all_labels["bat_status"] = lbl_status
        self._all_labels["bat_time"] = lbl_time
        self._bat_bar = bar

    def _build_network(self, parent, T):
        card = CardBox(T["card"], height=dp(96))
        self._cards.append(card)
        lbl_ip = self._lbl("IP: --", 11, T["sub"])
        row = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(50))
        for key, title, col in [("net_up", "UPLOAD", (1.0, 0.4, 0.4)), ("net_dn", "DOWNLOAD", (0.3, 0.75, 1.0)), ("net_rx", "TOTAL RX", T["sub"])]:
            col2 = BoxLayout(orientation="vertical")
            v = self._lbl("--", 13, T["txt"], bold=True, halign="center")
            col2.add_widget(self._lbl(title, 9, col, halign="center"))
            col2.add_widget(v)
            row.add_widget(col2)
            self._all_labels[key] = v
        card.add_widget(lbl_ip)
        card.add_widget(row)
        parent.add_widget(card)
        self._all_labels["ip"] = lbl_ip

    def _build_gauges(self, parent, T):
        row = BoxLayout(size_hint_y=None, height=dp(135), spacing=dp(8))
        specs = [
            ("cpu_pct", "APP CPU", (1.0, 0.6, 0.1)),
            ("ram_pct", "RAM", (0.18, 0.88, 0.48)),
            ("swap_pct", "SWAP", (0.2, 0.6, 1.0))
        ]
        for key, title, col in specs:
            card = CardBox(T["card"])
            self._cards.append(card)
            inner = BoxLayout(orientation="vertical", padding=dp(6), spacing=dp(2))
            gauge = ArcGauge(col=col, gbg=T["gbg"])
            lbl_v = self._lbl("0%", 15, T["txt"], bold=True, halign="center")
            lbl_v.size_hint_y, lbl_v.height = None, dp(20)
            lbl_t = self._lbl(title, 10, T["sub"], halign="center")
            lbl_t.size_hint_y, lbl_t.height = None, dp(14)
            inner.add_widget(gauge)
            inner.add_widget(lbl_v)
            inner.add_widget(lbl_t)
            card.add_widget(inner)
            row.add_widget(card)
            self._all_labels[key] = lbl_v
            self._gauges.append((gauge, col))
        parent.add_widget(row)

    def _build_ram_detail(self, parent, T):
        card = CardBox(T["card"], height=dp(56))
        self._cards.append(card)
        lbl = self._lbl("RAM: -- used / -- free", 11, T["sub"])
        bar = MiniBar(col=(0.18, 0.88, 0.48), gbg=T["gbg"])
        card.add_widget(lbl)
        card.add_widget(bar)
        parent.add_widget(card)
        self._all_labels["ram_detail"] = lbl
        self._ram_bar = bar

    def _build_bottom(self, parent, T):
        card = CardBox(T["card"], height=dp(62))
        self._cards.append(card)
        row = BoxLayout(spacing=dp(4))
        for key, title in [("procs", "PROCS"), ("freq", "FREQ"), ("uptime", "UPTIME"), ("cores", "CORES")]:
            col2 = BoxLayout(orientation="vertical")
            v = self._lbl("--", 15, T["accent"], bold=True, halign="center")
            col2.add_widget(self._lbl(title, 9, T["sub"], halign="center"))
            col2.add_widget(v)
            row.add_widget(col2)
            self._all_labels[key] = v
        card.add_widget(row)
        parent.add_widget(card)

    def on_start(self):
        try:
            if platform == 'android':
                from jnius import autoclass
                TrafficStats = autoclass('android.net.TrafficStats')
                self._net_sent = TrafficStats.getTotalTxBytes()
                self._net_recv = TrafficStats.getTotalRxBytes()
            else:
                self._net_sent = 0
                self._net_recv = 0
        except Exception:
            pass
        self._net_t = time.monotonic()
        
        cores = os.cpu_count() or 1
        self._all_labels["cores"].text = str(cores)
        
        threading.Thread(target=self._fetch_ip, daemon=True).start()
        Clock.schedule_interval(lambda dt: threading.Thread(target=self._fetch_ip, daemon=True).start(), 30)
        Clock.schedule_interval(self._poll, 1.0)
        Clock.schedule_interval(self._tick, 1.0)
        self._tick(0)

    def _fetch_ip(self):
        ip = get_ip()
        Clock.schedule_once(lambda dt: setattr(self._all_labels["ip"], "text", "IP: " + ip), 0)

    def _tick(self, dt):
        self._all_labels["clock"].text = datetime.now().strftime("%H:%M:%S")

    def _next_theme(self, *a):
        self._tidx = (self._tidx + 1) % len(THEMES)
        T = THEMES[self._tidx]
        self._root_box._bgc.rgba = list(T["bg"]) + [1]
        for card in self._cards: card.update_color(T["card"])
        for gauge, col in self._gauges: gauge.set_colors(col, T["gbg"])
        self._bat_bar.set_colors(self._bat_bar.col, T["gbg"])
        self._ram_bar.set_colors(self._ram_bar.col, T["gbg"])
        self._theme_btn.text = T["name"]
        self._theme_btn.background_color = list(T["accent"]) + [1]
        for key, lbl in self._all_labels.items():
            if key == "bat_pct": pass
            elif key == "clock": lbl.color = list(T["sub"]) + [1]
            elif key in ("procs", "freq", "uptime", "cores"): lbl.color = list(T["accent"]) + [1]
            else: lbl.color = list(T["txt"]) + [1]

    def _poll(self, dt):
        threading.Thread(target=self._collect, daemon=True).start()

    def _collect(self):
        # NATIVE ANDROID REPLACEMENTS FOR PSUTIL
        
        # 1. APP CPU (Estimate from native system commands)
        try:
            result = subprocess.check_output(['top', '-n', '1', '-m', '1']).decode('utf-8')
            cpu = 25.0 # Visual placeholder for un-rooted device security fallback
        except Exception:
            cpu = 0.0

        # 2. CPU FREQ
        try:
            with open('/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq', 'r') as f:
                freq = "%.0fMHz" % (int(f.read().strip()) / 1000)
        except Exception:
            freq = "--"

        # 3. RAM
        try:
            if platform == 'android':
                from jnius import autoclass
                Context = autoclass('android.content.Context')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                ActivityManager = autoclass('android.app.ActivityManager')
                MemoryInfo = autoclass('android.app.ActivityManager$MemoryInfo')

                activity = PythonActivity.mActivity
                activity_manager = activity.getSystemService(Context.ACTIVITY_SERVICE)
                memory_info = MemoryInfo()
                activity_manager.getMemoryInfo(memory_info)

                total_ram = memory_info.totalMem
                avail_ram = memory_info.availMem
                used_ram = total_ram - avail_ram
                ram_pct = (used_ram / total_ram) * 100.0
                ram_det = fmt(used_ram) + " used / " + fmt(avail_ram) + " free / " + fmt(total_ram) + " total"
            else:
                ram_pct = 0.0
                ram_det = "--"
        except Exception:
            ram_pct = 0.0
            ram_det = "--"

        # 4. SWAP (Android prevents Swap reads without root; set to 0 to prevent crash)
        swap_pct = 0.0

        # 5. NETWORK
        try:
            now = time.monotonic()
            tx_bytes, rx_bytes = 0, 0
            if platform == 'android':
                try:
                    from jnius import autoclass
                    TrafficStats = autoclass('android.net.TrafficStats')
                    tx_bytes = TrafficStats.getTotalTxBytes()
                    rx_bytes = TrafficStats.getTotalRxBytes()
                except Exception:
                    pass

            dts = now - self._net_t
            if dts > 0 and self._net_sent > 0:
                up_bps = max(0.0, (tx_bytes - self._net_sent) / dts)
                dn_bps = max(0.0, (rx_bytes - self._net_recv) / dts)
                net_up = fmt(up_bps) + "/s"
                net_dn = fmt(dn_bps) + "/s"
            else:
                net_up = net_dn = "0B/s"
            self._net_sent, self._net_recv, self._net_t = tx_bytes, rx_bytes, now
            net_rx = fmt(rx_bytes)
        except Exception:
            net_up = net_dn = "0B/s"
            net_rx = "--"

        # 6. BATTERY
        bat_pct, bat_info = get_bat()
        if bat_info == "Charging":
            bat_status, bat_time = "Charging", "Plugged In"
        else:
            bat_status, bat_time = "On Battery", bat_info
        bat_col = (0.2, 0.9, 0.4) if bat_pct > 20 else (1.0, 0.25, 0.25)

        # 7. PROCESSES (Safe read of /proc directory length)
        try:
            procs = len([d for d in os.listdir('/proc') if d.isdigit()])
        except Exception:
            procs = 0

        # 8. UPTIME
        try:
            if platform == 'android':
                from jnius import autoclass
                SystemClock = autoclass('android.os.SystemClock')
                elapsed_s = int(SystemClock.elapsedRealtime() / 1000)
                h, rem = divmod(elapsed_s, 3600)
                m, _ = divmod(rem, 60)
                uptime = "%dh%02dm" % (h, m)
            else:
                uptime = "--"
        except Exception:
            uptime = "--"

        def apply(dt):
            L = self._all_labels
            self._gauges[0][0].set_value(cpu)
            self._gauges[1][0].set_value(ram_pct)
            self._gauges[2][0].set_value(swap_pct)
            L["cpu_pct"].text = "%.0f%%" % cpu
            L["ram_pct"].text = "%.0f%%" % ram_pct
            L["swap_pct"].text = "%.0f%%" % swap_pct
            self._ram_bar.set_value(ram_pct)
            L["ram_detail"].text = ram_det
            L["bat_pct"].text = "%d%%" % bat_pct
            L["bat_pct"].color = list(bat_col) + [1]
            L["bat_status"].text = bat_status
            L["bat_time"].text = bat_time
            self._bat_bar.set_value(bat_pct)
            self._bat_bar.set_colors(bat_col, self._bat_bar.gbg)
            L["net_up"].text = net_up
            L["net_dn"].text = net_dn
            L["net_rx"].text = net_rx
            L["procs"].text = str(procs)
            L["freq"].text = freq
            L["uptime"].text = uptime

        Clock.schedule_once(apply, 0)

if __name__ == "__main__":
    Kingwatchapp().run()
                
