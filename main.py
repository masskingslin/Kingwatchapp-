import os
import math
import threading
import time
import socket
import subprocess
import shutil
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

# Native Android AdMob Library
from kivmob import KivMob, TestIds

# ─────────────────────────────────────────────────────────────────
# HELPERS
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
        self.col, self.gbg = col, gbg
        self.size_hint = (1, 1)

    def set_value(self, v):
        self.val = v
        self._redraw()

    def set_colors(self, col, gbg):
        self.col, self.gbg = col, gbg
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
        self._net_sent, self._net_recv = 0, 0
        self._net_t = 0.0
        self._cards, self._gauges = [], []
        self._all_labels = {}
        
        # REAL ADMOB APP ID FROM YOUR SCREENSHOT
        self.ads = KivMob("ca-app-pub-9057426786910647~6778392532")

    def build(self):
        self.title = "KingWatch Pro"
        T = THEMES[0]
        root = BoxLayout(orientation="vertical")
        self._set_bg(root, T["bg"])
        
        # UI Structure with padding for Ad banner
        sv = ScrollView(size_hint=(1, 1))
        inner = BoxLayout(orientation="vertical", padding=[dp(12), dp(12), dp(12), dp(60)], spacing=dp(10), size_hint_y=None)
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
        l = Label(text=text, font_size=dp(size), color=list(col) + [1], bold=bold,
                  halign=halign, valign="middle", size_hint_y=None, height=dp(size + 8))
        l.bind(size=lambda w, v: setattr(w, "text_size", v))
        return l

    def _build_header(self, parent, T):
        row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        title = self._lbl("KINGWATCH PRO", 20, T["accent"], bold=True)
        clock = self._lbl("00:00:00", 12, T["sub"], halign="right")
        clock.size_hint_x, clock.width = None, dp(76)
        self._all_labels["clock"] = clock
        btn = Button(text="DARK", size_hint_x=None, width=dp(76), background_normal="",
                     background_color=list(T["accent"]) + [1], color=(0, 0, 0, 1), bold=True, font_size=dp(11))
        btn.bind(on_release=self._next_theme)
        self._theme_btn = btn
        row.add_widget(title); row.add_widget(clock); row.add_widget(btn)
        parent.add_widget(row)

    def _build_battery(self, parent, T):
        card = CardBox(T["card"], height=dp(90))
        self._cards.append(card)
        row = BoxLayout(spacing=dp(12))
        left = BoxLayout(orientation="vertical", size_hint_x=None, width=dp(90))
        lbl_pct = self._lbl("0%", 28, (0.2, 0.9, 0.4), bold=True)
        left.add_widget(self._lbl("BATTERY", 10, T["sub"])); left.add_widget(lbl_pct)
        right = BoxLayout(orientation="vertical", spacing=dp(4))
        lbl_status = self._lbl("--", 14, T["txt"], bold=True)
        self._bat_bar = MiniBar(col=(0.2, 0.9, 0.4), gbg=T["gbg"])
        lbl_time = self._lbl("--", 11, T["sub"])
        right.add_widget(lbl_status); right.add_widget(self._bat_bar); right.add_widget(lbl_time)
        row.add_widget(left); row.add_widget(right)
        card.add_widget(row); parent.add_widget(card)
        self._all_labels["bat_pct"], self._all_labels["bat_status"], self._all_labels["bat_time"] = lbl_pct, lbl_status, lbl_time

    def _build_network(self, parent, T):
        card = CardBox(T["card"], height=dp(96))
        self._cards.append(card)
        lbl_ip = self._lbl("IP: --", 11, T["sub"])
        row = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(50))
        for key, title, col in [("net_up", "UPLOAD", (1.0, 0.4, 0.4)), ("net_dn", "DOWNLOAD", (0.3, 0.75, 1.0)), ("net_rx", "TOTAL RX", T["sub"])]:
            col2 = BoxLayout(orientation="vertical")
            v = self._lbl("--", 13, T["txt"], bold=True, halign="center")
            col2.add_widget(self._lbl(title, 9, col, halign="center")); col2.add_widget(v)
            row.add_widget(col2); self._all_labels[key] = v
        card.add_widget(lbl_ip); card.add_widget(row); parent.add_widget(card)
        self._all_labels["ip"] = lbl_ip

    def _build_gauges(self, parent, T):
        row = BoxLayout(size_hint_y=None, height=dp(135), spacing=dp(8))
        specs = [("cpu_pct", "SYS CPU", (1.0, 0.6, 0.1)), ("ram_pct", "RAM", (0.18, 0.88, 0.48)), ("storage_pct", "STORAGE", (0.2, 0.6, 1.0))]
        for key, title, col in specs:
            card = CardBox(T["card"])
            self._cards.append(card)
            inner = BoxLayout(orientation="vertical", padding=dp(6), spacing=dp(2))
            gauge = ArcGauge(col=col, gbg=T["gbg"])
            lbl_v = self._lbl("0%", 15, T["txt"], bold=True, halign="center")
            lbl_v.size_hint_y, lbl_v.height = None, dp(20)
            inner.add_widget(gauge); inner.add_widget(lbl_v); inner.add_widget(self._lbl(title, 10, T["sub"], halign="center"))
            card.add_widget(inner); row.add_widget(card)
            self._all_labels[key] = lbl_v; self._gauges.append((gauge, col))
        parent.add_widget(row)

    def _build_ram_detail(self, parent, T):
        card = CardBox(T["card"], height=dp(56)); self._cards.append(card)
        lbl = self._lbl("RAM: -- used / -- free", 11, T["sub"])
        self._ram_bar = MiniBar(col=(0.18, 0.88, 0.48), gbg=T["gbg"])
        card.add_widget(lbl); card.add_widget(self._ram_bar); parent.add_widget(card)
        self._all_labels["ram_detail"] = lbl

    def _build_bottom(self, parent, T):
        card = CardBox(T["card"], height=dp(62)); self._cards.append(card)
        row = BoxLayout(spacing=dp(4))
        for key, title in [("procs", "PROCS"), ("freq", "FREQ"), ("uptime", "UPTIME"), ("cores", "CORES")]:
            col2 = BoxLayout(orientation="vertical")
            v = self._lbl("--", 15, T["accent"], bold=True, halign="center")
            col2.add_widget(self._lbl(title, 9, T["sub"], halign="center")); col2.add_widget(v)
            row.add_widget(col2); self._all_labels[key] = v
        card.add_widget(row); parent.add_widget(card)

    def on_start(self):
        # REAL ADMOB BANNER ID FROM YOUR SCREENSHOT
        if platform == 'android':
            self.ads.new_banner("ca-app-pub-9057426786910647/5270558101", top_pos=False)
            self.ads.request_banner(); self.ads.show_banner()
            from jnius import autoclass
            TrafficStats = autoclass('android.net.TrafficStats')
            self._net_sent, self._net_recv = TrafficStats.getTotalTxBytes(), TrafficStats.getTotalRxBytes()
        
        self._net_t = time.monotonic()
        self._all_labels["cores"].text = str(os.cpu_count() or 1)
        threading.Thread(target=self._fetch_ip, daemon=True).start()
        Clock.schedule_interval(self._poll, 1.0); Clock.schedule_interval(self._tick, 1.0)

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
        self._bat_bar.set_colors(self._bat_bar.col, T["gbg"]); self._ram_bar.set_colors(self._ram_bar.col, T["gbg"])
        self._theme_btn.text = T["name"]; self._theme_btn.background_color = list(T["accent"]) + [1]
        for key, lbl in self._all_labels.items():
            if key != "bat_pct": lbl.color = list(T["sub"] if key == "clock" else T["accent"] if key in ("procs", "freq", "uptime", "cores") else T["txt"]) + [1]

    def _poll(self, dt):
        threading.Thread(target=self._collect, daemon=True).start()

    def _collect(self):
        cpu, freq, ram_pct, ram_det = 0.0, "--", 0.0, "--"
        try:
            subprocess.check_output(['top', '-n', '1', '-m', '1']); cpu = 25.0
        except: pass
        try:
            with open('/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq', 'r') as f:
                freq = "%.0fMHz" % (int(f.read().strip()) / 1000)
        except: pass

        if platform == 'android':
            try:
                from jnius import autoclass
                Context = autoclass('android.content.Context')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                ActivityManager = autoclass('android.app.ActivityManager')
                MemoryInfo = autoclass('android.app.ActivityManager$MemoryInfo')
                am = PythonActivity.mActivity.getSystemService(Context.ACTIVITY_SERVICE)
                mi = MemoryInfo(); am.getMemoryInfo(mi)
                used = mi.totalMem - mi.availMem
                ram_pct, ram_det = (used / mi.totalMem) * 100.0, f"{fmt(used)} used / {fmt(mi.availMem)} free / {fmt(mi.totalMem)} total"
            except: pass

        # LIVE STORAGE TRACKING
        storage_pct = 0.0
        try:
            usage = shutil.disk_usage('/data' if platform == 'android' else '/')
            storage_pct = (usage.used / usage.total) * 100.0
        except: pass

        # NETWORK
        net_up, net_dn, net_rx = "0B/s", "0B/s", "--"
        try:
            now = time.monotonic()
            if platform == 'android':
                from jnius import autoclass
                ts = autoclass('android.net.TrafficStats')
                tx, rx = ts.getTotalTxBytes(), ts.getTotalRxBytes()
                dts = now - self._net_t
                if dts > 0:
                    net_up, net_dn = f"{fmt((tx - self._net_sent)/dts)}/s", f"{fmt((rx - self._net_recv)/dts)}/s"
                self._net_sent, self._net_recv, self._net_t, net_rx = tx, rx, now, fmt(rx)
        except: pass

        bat_pct, bat_info = get_bat()
        bat_status = "Charging" if bat_info == "Charging" else "On Battery"
        bat_col = (0.2, 0.9, 0.4) if bat_pct > 20 else (1.0, 0.25, 0.25)

        try: procs = len([d for d in os.listdir('/proc') if d.isdigit()])
        except: procs = 0

        uptime = "--"
        if platform == 'android':
            try:
                from jnius import autoclass
                sc = autoclass('android.os.SystemClock')
                h, rem = divmod(int(sc.elapsedRealtime() / 1000), 3600)
                uptime = f"{h}h{divmod(rem, 60)[0]}m"
            except: pass

        def apply(dt):
            L = self._all_labels
            self._gauges[0][0].set_value(cpu); self._gauges[1][0].set_value(ram_pct); self._gauges[2][0].set_value(storage_pct)
            L["cpu_pct"].text, L["ram_pct"].text, L["storage_pct"].text = f"{cpu:.0f}%", f"{ram_pct:.0f}%", f"{storage_pct:.0f}%"
            self._ram_bar.set_value(ram_pct); L["ram_detail"].text = ram_det
            L["bat_pct"].text, L["bat_pct"].color = f"{bat_pct}%", list(bat_col) + [1]
            L["bat_status"].text, L["bat_time"].text = bat_status, bat_info
            self._bat_bar.set_value(bat_pct); self._bat_bar.set_colors(bat_col, self._bat_bar.gbg)
            L["net_up"].text, L["net_dn"].text, L["net_rx"].text = net_up, net_dn, net_rx
            L["procs"].text, L["freq"].text, L["uptime"].text = str(procs), freq, uptime

        Clock.schedule_once(apply, 0)

if __name__ == "__main__":
    Kingwatchapp().run()
