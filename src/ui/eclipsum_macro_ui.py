import sys
import json
import os
import asyncio
import subprocess
import tempfile
import shutil

import qasync
import aiohttp
import aiofiles

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QStackedWidget, QLineEdit,
    QTextEdit, QSlider, QCheckBox, QScrollArea, QComboBox,
    QSizePolicy, QProgressBar, QDialog
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QCursor

# ── Palette ───────────────────────────────────────────────────────────────────
PRIMARY  = "#F08A14"
ACCENT   = "#FF6B35"
BG       = "#111114"
PANEL    = "#18181C"
SURFACE  = "#1E1E24"
BORDER   = "#2A2A32"
TEXT     = "#E8E8F0"
TEXT_DIM = "#5A5A6E"
TEXT_MID = "#8888A0"
GREEN    = "#3DDC84"
RED      = "#FF4444"
YELLOW   = "#F5C542"

PREFS_FILE   = "eclipsum_prefs.json"
DEFAULT_TABS = ["Macro", "Settings", "Webhook", "Customization", "Credits"]

# ── Auto-Updater Config ───────────────────────────────────────────────────────
GITHUB_REPO      = "TheEndyy/eclipsum-solsrng"
GITHUB_BRANCH    = "main"
GITHUB_API_TREE  = f"https://api.github.com/repos/{GITHUB_REPO}/git/trees/{GITHUB_BRANCH}?recursive=1"
GITHUB_RAW_BASE  = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}"
GITHUB_INFO_URL  = f"{GITHUB_RAW_BASE}/INFO.py"

# Folders/files to never download (dev/env artifacts)
SKIP_PREFIXES = (".venv/", ".vscode/", ".git/")
SKIP_FILES    = (".gitignore",)

# The file that IS running right now
THIS_SCRIPT = os.path.abspath(__file__)

# How often to poll for updates (milliseconds)
UPDATE_POLL_MS = 5 * 60 * 1000   # every 5 minutes

# ── QSS ───────────────────────────────────────────────────────────────────────
QSS = f"""
* {{
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    font-size: 12px; color: {TEXT}; outline: none;
}}
QMainWindow, QWidget#root {{ background: {BG}; }}

QWidget#topbar {{ background: {PANEL}; border-bottom: 1px solid {BORDER}; }}
QLabel#logo_text {{ font-size: 13px; font-weight: 700; letter-spacing: 3px; color: {TEXT}; }}
QLabel#logo_dot {{ color: {PRIMARY}; font-size: 16px; }}
QLabel#ver_badge {{
    background: {SURFACE}; color: {TEXT_DIM}; font-size: 9px;
    font-weight: 600; letter-spacing: 1px; border-radius: 3px;
    padding: 2px 6px; border: 1px solid {BORDER};
}}
QLabel#update_badge {{
    background: {PRIMARY}22; color: {PRIMARY}; font-size: 9px;
    font-weight: 700; letter-spacing: 1px; border-radius: 3px;
    padding: 2px 6px; border: 1px solid {PRIMARY}66;
}}

QPushButton#wc_btn {{
    background: transparent; border: none; color: {TEXT_DIM}; font-size: 14px;
    min-width: 32px; max-width: 32px; min-height: 28px; max-height: 28px; border-radius: 4px;
}}
QPushButton#wc_btn:hover {{ background: {SURFACE}; color: {TEXT}; }}
QPushButton#close_btn {{
    background: transparent; border: none; color: {TEXT_DIM}; font-size: 13px;
    min-width: 32px; max-width: 32px; min-height: 28px; max-height: 28px; border-radius: 4px;
}}
QPushButton#close_btn:hover {{ background: #5C1515; color: #FF6060; }}

QWidget#sidebar {{ background: {PANEL}; border-right: 1px solid {BORDER}; }}
QPushButton#nav_btn {{
    background: transparent; border: none; color: {TEXT_DIM};
    font-size: 12px; font-weight: 500; text-align: left; padding: 0px 14px;
    min-height: 36px; max-height: 36px; border-radius: 6px;
}}
QPushButton#nav_btn:hover {{ background: {SURFACE}; color: {TEXT}; }}
QPushButton#nav_btn_active {{
    background: {SURFACE}; border: none; border-left: 2px solid {PRIMARY};
    color: {PRIMARY}; font-size: 12px; font-weight: 600; text-align: left;
    padding: 0px 12px; min-height: 36px; max-height: 36px; border-radius: 6px;
}}

QWidget#statusbar {{ background: {PANEL}; border-top: 1px solid {BORDER}; }}
QLabel#status_label {{ color: {TEXT_MID}; font-size: 10px; letter-spacing: 0.5px; }}
QWidget#content {{ background: {BG}; }}
QLabel#section_title {{ font-size: 17px; font-weight: 700; color: {TEXT}; }}
QLabel#section_sub   {{ font-size: 11px; color: {TEXT_DIM}; }}
QLabel#field_label   {{ font-size: 10px; font-weight: 600; color: {TEXT_DIM}; letter-spacing: 1.5px; }}
QWidget#card         {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 8px; }}
QWidget#card_async   {{ background: {SURFACE}; border: 1px solid {PRIMARY}44; border-radius: 8px; }}

QLineEdit, QTextEdit {{
    background: {PANEL}; border: 1px solid {BORDER}; border-radius: 6px;
    color: {TEXT}; font-size: 12px; padding: 4px 10px;
    selection-background-color: {PRIMARY};
}}
QLineEdit:focus, QTextEdit:focus {{ border: 1px solid {PRIMARY}; }}

QPushButton#primary_btn {{
    background: {PRIMARY}; border: none; color: #000;
    font-size: 12px; font-weight: 700; letter-spacing: 1px;
    min-height: 36px; border-radius: 6px;
}}
QPushButton#primary_btn:hover {{ background: {ACCENT}; }}
QPushButton#primary_btn:pressed {{ background: #C0700F; }}
QPushButton#primary_btn:disabled {{
    background: {SURFACE}; color: {TEXT_DIM}; border: 1px solid {BORDER};
}}
QPushButton#secondary_btn {{
    background: {SURFACE}; border: 1px solid {BORDER};
    color: {TEXT}; font-size: 12px; font-weight: 500;
    min-height: 36px; border-radius: 6px;
}}
QPushButton#secondary_btn:hover {{ background: #28282E; border-color: #3A3A48; }}
QPushButton#danger_btn {{
    background: #1E0808; border: 1px solid #3A1010;
    color: {RED}; font-size: 12px; font-weight: 600;
    min-height: 36px; border-radius: 6px;
}}
QPushButton#danger_btn:hover {{ background: #2E0E0E; border-color: #5C2020; }}

QCheckBox {{ color: {TEXT}; font-size: 12px; spacing: 8px; }}
QCheckBox::indicator {{
    width: 36px; height: 20px; border-radius: 10px;
    background: {BORDER}; border: 1px solid {BORDER};
}}
QCheckBox::indicator:checked {{ background: {PRIMARY}; border: 1px solid {PRIMARY}; }}

QSlider::groove:horizontal {{ height: 4px; background: {BORDER}; border-radius: 2px; }}
QSlider::sub-page:horizontal {{ background: {PRIMARY}; border-radius: 2px; }}
QSlider::handle:horizontal {{
    background: {PRIMARY}; width: 14px; height: 14px; margin: -5px 0; border-radius: 7px;
}}

QComboBox {{
    background: {PANEL}; border: 1px solid {BORDER}; border-radius: 6px;
    color: {TEXT}; padding: 4px 10px; min-height: 28px;
}}
QComboBox:focus {{ border: 1px solid {PRIMARY}; }}
QComboBox::drop-down {{ border: none; width: 20px; }}
QComboBox QAbstractItemView {{
    background: {SURFACE}; border: 1px solid {BORDER};
    color: {TEXT}; selection-background-color: {PRIMARY}33;
}}

QScrollBar:vertical {{ background: transparent; width: 4px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 2px; min-height: 24px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollArea {{ border: none; background: transparent; }}

QProgressBar {{
    background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 4px;
    height: 6px; text-align: center; color: transparent;
}}
QProgressBar::chunk {{
    background: {PRIMARY}; border-radius: 4px;
}}
"""

# ── Helpers ───────────────────────────────────────────────────────────────────
def card(async_style=False):
    w = QWidget(); w.setObjectName("card_async" if async_style else "card"); return w

def field_label(text):
    l = QLabel(text.upper()); l.setObjectName("field_label"); return l

def h_line():
    f = QFrame(); f.setFrameShape(QFrame.HLine)
    f.setStyleSheet(f"background: {BORDER}; border: none; max-height: 1px;")
    f.setFixedHeight(1); return f

def section_header(title, subtitle):
    w = QWidget(); w.setObjectName("card")
    w.setStyleSheet(f"""
        QWidget#card {{
            background: {PANEL}; border: none;
            border-bottom: 1px solid {BORDER}; border-radius: 0px;
        }}
    """)
    lay = QVBoxLayout(w); lay.setContentsMargins(22, 16, 22, 12); lay.setSpacing(2)
    t = QLabel(title); t.setObjectName("section_title")
    s = QLabel(subtitle); s.setObjectName("section_sub")
    lay.addWidget(t); lay.addWidget(s)
    accent = QFrame(); accent.setFixedHeight(2)
    accent.setStyleSheet(f"""
        background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
            stop:0 {PRIMARY}, stop:0.4 {PRIMARY}66, stop:1 transparent);
        border: none;
    """)
    lay.addWidget(accent); return w

def async_badge():
    l = QLabel("⚡ async")
    l.setStyleSheet(f"""
        color: {PRIMARY}; background: {PRIMARY}18; font-size: 9px; font-weight: 700;
        letter-spacing: 0.5px; border-radius: 3px; padding: 1px 6px;
        border: 1px solid {PRIMARY}44;
    """)
    return l

# ── Async helpers ─────────────────────────────────────────────────────────────
def run_async(coro):
    loop = asyncio.get_event_loop()
    return loop.create_task(coro)

async def async_load_prefs():
    if not os.path.exists(PREFS_FILE):
        return {}
    try:
        async with aiofiles.open(PREFS_FILE, "r") as f:
            return json.loads(await f.read())
    except Exception:
        return {}

async def async_save_prefs(data: dict):
    try:
        async with aiofiles.open(PREFS_FILE, "w") as f:
            await f.write(json.dumps(data, indent=2))
    except Exception:
        pass

# ── Widget registry ───────────────────────────────────────────────────────────
WIDGET_REGISTRY: list[dict] = []

def register_widget(widget_id: str, label: str, default_tab: str):
    def decorator(fn):
        WIDGET_REGISTRY.append({"id": widget_id, "label": label, "tab": default_tab, "builder": fn})
        return fn
    return decorator

_app_ref = None  # set after instantiation

# ═════════════════════════════════════════════════════════════════════════════
# Auto-Updater Engine
# ═════════════════════════════════════════════════════════════════════════════

class AutoUpdater(QObject):
    """
    Polls INFO.py on GitHub every UPDATE_POLL_MS milliseconds.
    When a new version is detected:
      1. Queries the GitHub API tree to discover EVERY file in the repo.
      2. Skips dev/env paths (SKIP_PREFIXES, SKIP_FILES).
      3. Downloads all remaining files into their local equivalents,
         preserving subdirectory structure.
      4. If this script itself was replaced, performs a graceful self-restart.
    """
    update_available   = Signal(str, str)   # (current_ver, remote_ver)
    update_applied     = Signal(str)         # (new_ver,)
    update_error       = Signal(str)         # (error_msg,)
    download_progress  = Signal(int, int)    # (done_files, total_files)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_version: str | None = None
        self._updating = False

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)
        self._timer.start(UPDATE_POLL_MS)

    def start_immediate_check(self):
        """Fire a check right now (used on startup)."""
        run_async(self._check_for_update())

    def _poll(self):
        if not self._updating:
            run_async(self._check_for_update())

    # ── Version parsing ───────────────────────────────────────────────────────
    @staticmethod
    def _parse_version(source: str) -> str | None:
        """
        Parses VERSION="0.0.1" (with or without spaces around =, single or double quotes).
        Matches: VERSION="x", VERSION='x', VERSION = "x", version="x", __version__="x"
        """
        import re
        pattern = re.compile(
            r'^(?:__)?version(?:__)?\s*=\s*["\']([^"\']+)["\']',
            re.IGNORECASE
        )
        for line in source.splitlines():
            m = pattern.match(line.strip())
            if m:
                return m.group(1)
        return None

    # ── Network helpers ───────────────────────────────────────────────────────
    @staticmethod
    async def _fetch_text(session: aiohttp.ClientSession, url: str) -> str:
        headers = {"Accept": "application/vnd.github+json"}
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as resp:
            resp.raise_for_status()
            return await resp.text()

    @staticmethod
    async def _fetch_bytes(session: aiohttp.ClientSession, url: str) -> bytes:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
            resp.raise_for_status()
            return await resp.read()

    # ── Discover all repo files via GitHub API ────────────────────────────────
    @staticmethod
    async def _discover_files(session: aiohttp.ClientSession) -> dict[str, str]:
        """
        Calls the GitHub tree API and returns {relative_path: raw_download_url}
        for every blob (file) that is not in SKIP_PREFIXES / SKIP_FILES.
        """
        headers = {"Accept": "application/vnd.github+json"}
        async with session.get(
            GITHUB_API_TREE, headers=headers, timeout=aiohttp.ClientTimeout(total=20)
        ) as resp:
            resp.raise_for_status()
            tree_data = await resp.json()

        files: dict[str, str] = {}
        for item in tree_data.get("tree", []):
            if item.get("type") != "blob":
                continue
            path: str = item["path"]

            # Skip dev/env paths
            if any(path.startswith(p) for p in SKIP_PREFIXES):
                continue
            if path in SKIP_FILES:
                continue

            raw_url = f"{GITHUB_RAW_BASE}/{path}"
            files[path] = raw_url

        return files

    # ── Core version check ────────────────────────────────────────────────────
    async def _check_for_update(self):
        try:
            async with aiohttp.ClientSession() as session:
                info_src = await self._fetch_text(session, GITHUB_INFO_URL)
            remote_ver = self._parse_version(info_src)
            if remote_ver is None:
                return  # can't parse — skip silently

            if self._current_version is None:
                # First run — establish baseline from local INFO.py if it exists
                local_info = os.path.join(os.path.dirname(THIS_SCRIPT), "INFO.py")
                if os.path.exists(local_info):
                    try:
                        async with aiofiles.open(local_info, "r") as f:
                            local_src = await f.read()
                        self._current_version = self._parse_version(local_src) or remote_ver
                    except Exception:
                        self._current_version = remote_ver
                else:
                    self._current_version = remote_ver

            if remote_ver != self._current_version:
                self.update_available.emit(self._current_version, remote_ver)
                await self._apply_update(remote_ver)

        except Exception as e:
            self.update_error.emit(str(e))

    # ── Apply update ──────────────────────────────────────────────────────────
    async def _apply_update(self, new_ver: str):
        self._updating = True
        self_was_updated = False
        base_dir = os.path.dirname(THIS_SCRIPT)

        try:
            async with aiohttp.ClientSession() as session:
                # Step 1 — discover all files in the repo dynamically
                managed_files = await self._discover_files(session)
                total = len(managed_files)

                # Step 2 — download every file
                downloaded: dict[str, bytes] = {}
                for i, (rel_path, raw_url) in enumerate(managed_files.items()):
                    self.download_progress.emit(i, total)
                    data = await self._fetch_bytes(session, raw_url)
                    downloaded[rel_path] = data

            # Step 3 — write all files atomically (temp-then-replace)
            for rel_path, data in downloaded.items():
                dest = os.path.join(base_dir, rel_path)
                # Create subdirectories if needed (e.g. src/)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                tmp = dest + ".eclipsum_tmp"
                async with aiofiles.open(tmp, "wb") as f:
                    await f.write(data)
                shutil.move(tmp, dest)

                if os.path.abspath(dest) == THIS_SCRIPT:
                    self_was_updated = True

            self.download_progress.emit(total, total)
            self._current_version = new_ver
            self.update_applied.emit(new_ver)

            if self_was_updated:
                await asyncio.sleep(1.5)
                self._restart()

        except Exception as e:
            self.update_error.emit(f"Update failed: {e}")
        finally:
            self._updating = False

    # ── Self-restart ─────────────────────────────────────────────────────────
    @staticmethod
    def _restart():
        """Re-launch with same interpreter + args, then hard-exit."""
        subprocess.Popen([sys.executable] + sys.argv, close_fds=True)
        QApplication.quit()
        os._exit(0)


# ═════════════════════════════════════════════════════════════════════════════
# Update-notification banner (overlays the main window)
# ═════════════════════════════════════════════════════════════════════════════

class UpdateBanner(QFrame):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setObjectName("card")
        self.setStyleSheet(f"""
            QFrame#card {{
                background: {PRIMARY}14;
                border: 1px solid {PRIMARY}55;
                border-radius: 8px;
            }}
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 10, 16, 10)
        lay.setSpacing(10)

        self._icon = QLabel("⬆")
        self._icon.setStyleSheet(f"color: {PRIMARY}; font-size: 14px;")
        self._msg  = QLabel("Checking for updates…")
        self._msg.setStyleSheet(f"color: {TEXT}; font-size: 11px;")
        self._msg.setWordWrap(True)

        self._bar  = QProgressBar()
        self._bar.setFixedHeight(6)
        self._bar.setFixedWidth(120)
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.hide()

        self._dismiss = QPushButton("✕")
        self._dismiss.setObjectName("wc_btn")
        self._dismiss.setFixedSize(24, 24)
        self._dismiss.clicked.connect(self.hide)

        lay.addWidget(self._icon)
        lay.addWidget(self._msg, 1)
        lay.addWidget(self._bar)
        lay.addWidget(self._dismiss)
        self.hide()

    def show_checking(self):
        self._msg.setText("Checking for updates…")
        self._bar.hide(); self.show()

    def show_update_found(self, cur: str, new: str):
        self._msg.setText(f"Update found!  {cur} → {new}  Downloading…")
        self._bar.setValue(0); self._bar.show(); self.show()

    def show_progress(self, done: int, total: int):
        pct = int(done / total * 100) if total else 0
        self._bar.setValue(pct)

    def show_applied(self, ver: str, self_updated: bool):
        if self_updated:
            self._msg.setText(f"✓  Updated to {ver}. Restarting…")
        else:
            self._msg.setText(f"✓  Updated to {ver}. Files replaced in-place.")
        self._bar.hide()

    def show_error(self, msg: str):
        self._msg.setText(f"⚠  Update error: {msg}")
        self._bar.hide()


# ═════════════════════════════════════════════════════════════════════════════
# Registered widget builders
# ═════════════════════════════════════════════════════════════════════════════

@register_widget("macro_status", "Macro Status & Controls", "Macro")
def _build_macro_status(lay):
    c = card()
    cl = QVBoxLayout(c); cl.setContentsMargins(20, 16, 20, 16); cl.setSpacing(10)

    hrow = QHBoxLayout(); hrow.setSpacing(8)
    dot = QLabel("●"); dot.setObjectName("_macro_dot")
    dot.setStyleSheet(f"color: {RED}; font-size: 10px;")
    stat = QLabel("STOPPED"); stat.setObjectName("_macro_status")
    stat.setStyleSheet(f"color: {RED}; font-size: 13px; font-weight: 700; letter-spacing: 1px;")
    hrow.addWidget(dot); hrow.addWidget(stat); hrow.addStretch()
    hrow.addWidget(async_badge())
    cl.addLayout(hrow)

    btn_row = QHBoxLayout(); btn_row.setSpacing(8)
    start_btn = QPushButton("▶  START"); start_btn.setObjectName("primary_btn")
    start_btn.setCursor(QCursor(Qt.PointingHandCursor))
    stop_btn  = QPushButton("■  STOP");  stop_btn.setObjectName("danger_btn")
    stop_btn.setCursor(QCursor(Qt.PointingHandCursor))
    stop_btn.setEnabled(False)

    def _start():
        stat.setText("RUNNING")
        stat.setStyleSheet(f"color: {GREEN}; font-size: 13px; font-weight: 700; letter-spacing: 1px;")
        dot.setStyleSheet(f"color: {GREEN}; font-size: 10px;")
        start_btn.setEnabled(False); stop_btn.setEnabled(True)
        if _app_ref: _app_ref.set_status("MACRO RUNNING")

    def _stop():
        stat.setText("STOPPED")
        stat.setStyleSheet(f"color: {RED}; font-size: 13px; font-weight: 700; letter-spacing: 1px;")
        dot.setStyleSheet(f"color: {RED}; font-size: 10px;")
        start_btn.setEnabled(True); stop_btn.setEnabled(False)
        if _app_ref: _app_ref.set_status("MACRO STOPPED")

    start_btn.clicked.connect(_start); stop_btn.clicked.connect(_stop)
    btn_row.addWidget(start_btn); btn_row.addWidget(stop_btn)
    cl.addLayout(btn_row)
    lay.addWidget(c)


@register_widget("macro_hotkey", "Hotkey Binding", "Macro")
def _build_macro_hotkey(lay):
    c = card(); cl = QVBoxLayout(c); cl.setContentsMargins(20, 14, 20, 14); cl.setSpacing(8)
    cl.addWidget(field_label("Hotkey"))
    e = QLineEdit(); e.setPlaceholderText("e.g.  F6"); e.setFixedHeight(32)
    cl.addWidget(e); lay.addWidget(c)


@register_widget("macro_delay", "Action Delay (ms)", "Macro")
def _build_macro_delay(lay):
    c = card(); cl = QVBoxLayout(c); cl.setContentsMargins(20, 14, 20, 14); cl.setSpacing(8)
    cl.addWidget(field_label("Delay Between Actions"))
    row = QHBoxLayout()
    s = QSlider(Qt.Horizontal); s.setRange(0, 2000); s.setValue(250)
    v = QLabel("250 ms"); v.setStyleSheet(f"color: {PRIMARY}; font-size: 12px; font-weight: 700; min-width: 52px;")
    s.valueChanged.connect(lambda x: v.setText(f"{x} ms"))
    row.addWidget(s); row.addSpacing(6); row.addWidget(v)
    cl.addLayout(row); lay.addWidget(c)


@register_widget("settings_toggles", "Feature Toggles", "Settings")
def _build_settings_toggles(lay):
    toggles = [
        ("Auto Roll",     True,  "Automatically roll on schedule"),
        ("Notifications", False, "Desktop push notifications"),
        ("Sound Effects", True,  "Play audio feedback"),
        ("Auto-Save",     True,  "Save preferences on exit"),
    ]
    c = card(); cl = QVBoxLayout(c); cl.setContentsMargins(20, 8, 20, 8); cl.setSpacing(0)
    for i, (lbl_text, default, desc) in enumerate(toggles):
        row = QWidget(); row.setStyleSheet("background: transparent;")
        rl = QHBoxLayout(row); rl.setContentsMargins(0, 10, 0, 10)
        info = QVBoxLayout(); info.setSpacing(2)
        lbl = QLabel(lbl_text); lbl.setStyleSheet(f"font-weight: 500; color: {TEXT};")
        d   = QLabel(desc);     d.setStyleSheet(f"font-size: 10px; color: {TEXT_DIM};")
        info.addWidget(lbl); info.addWidget(d)
        cb = QCheckBox(); cb.setChecked(default); cb.setFixedSize(44, 22)
        rl.addLayout(info); rl.addStretch(); rl.addWidget(cb)
        cl.addWidget(row)
        if i < len(toggles) - 1: cl.addWidget(h_line())
    lay.addWidget(c)


@register_widget("settings_speed", "Roll Speed Slider", "Settings")
def _build_settings_speed(lay):
    c = card(); cl = QVBoxLayout(c); cl.setContentsMargins(20, 14, 20, 14); cl.setSpacing(10)
    cl.addWidget(field_label("Roll Speed"))
    row = QHBoxLayout()
    s = QSlider(Qt.Horizontal); s.setRange(1, 10); s.setValue(5)
    v = QLabel("5"); v.setStyleSheet(f"color: {PRIMARY}; font-size: 13px; font-weight: 700; min-width: 22px;")
    s.valueChanged.connect(lambda x: v.setText(str(x)))
    row.addWidget(s); row.addSpacing(6); row.addWidget(v)
    cl.addLayout(row); lay.addWidget(c)


@register_widget("webhook_url", "Webhook URL Input", "Webhook")
def _build_webhook_url(lay):
    c = card(); cl = QVBoxLayout(c); cl.setContentsMargins(20, 14, 20, 14); cl.setSpacing(8)
    cl.addWidget(field_label("Webhook URL"))
    url = QLineEdit(); url.setObjectName("_webhook_url")
    url.setPlaceholderText("https://discord.com/api/webhooks/..."); url.setFixedHeight(32)
    cl.addWidget(url); lay.addWidget(c)


@register_widget("webhook_message", "Message Composer", "Webhook")
def _build_webhook_message(lay):
    c = card(); cl = QVBoxLayout(c); cl.setContentsMargins(20, 14, 20, 14); cl.setSpacing(8)
    cl.addWidget(field_label("Message"))
    msg = QTextEdit(); msg.setObjectName("_webhook_msg")
    msg.setPlainText("Eclipsum notification"); msg.setFixedHeight(72)
    cl.addWidget(msg); lay.addWidget(c)


@register_widget("webhook_send", "Send Test (async)", "Webhook")
def _build_webhook_send(lay):
    c = card(async_style=True)
    cl = QVBoxLayout(c); cl.setContentsMargins(20, 14, 20, 14); cl.setSpacing(10)

    hrow = QHBoxLayout()
    hrow.addWidget(field_label("Test Webhook"))
    hrow.addStretch(); hrow.addWidget(async_badge())
    cl.addLayout(hrow)

    result_lbl = QLabel(""); result_lbl.setStyleSheet(f"font-size: 11px; color: {TEXT_DIM};")
    send_btn = QPushButton("⚡  SEND TEST"); send_btn.setObjectName("primary_btn")
    send_btn.setCursor(QCursor(Qt.PointingHandCursor))

    async def _send():
        send_btn.setEnabled(False); send_btn.setText("Sending…")
        result_lbl.setText(""); result_lbl.setStyleSheet(f"font-size: 11px; color: {TEXT_DIM};")
        url_val, msg_val = "", "Eclipsum notification"
        if _app_ref:
            u = _app_ref.findChild(QLineEdit,  "_webhook_url")
            m = _app_ref.findChild(QTextEdit,  "_webhook_msg")
            if u: url_val = u.text().strip()
            if m: msg_val = m.toPlainText().strip()
        if not url_val:
            result_lbl.setText("⚠  No URL provided")
            result_lbl.setStyleSheet(f"font-size: 11px; color: {YELLOW};")
            send_btn.setEnabled(True); send_btn.setText("⚡  SEND TEST"); return
        try:
            async with aiohttp.ClientSession() as session:
                payload = {"content": msg_val or "Eclipsum notification"}
                async with session.post(url_val, json=payload, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                    if resp.status in (200, 204):
                        result_lbl.setText("✓  Sent successfully")
                        result_lbl.setStyleSheet(f"font-size: 11px; color: {GREEN};")
                        if _app_ref: _app_ref.set_status("WEBHOOK SENT")
                    else:
                        result_lbl.setText(f"✗  HTTP {resp.status}")
                        result_lbl.setStyleSheet(f"font-size: 11px; color: {RED};")
        except asyncio.TimeoutError:
            result_lbl.setText("✗  Timed out")
            result_lbl.setStyleSheet(f"font-size: 11px; color: {RED};")
        except Exception as ex:
            result_lbl.setText(f"✗  {type(ex).__name__}")
            result_lbl.setStyleSheet(f"font-size: 11px; color: {RED};")
        finally:
            send_btn.setEnabled(True); send_btn.setText("⚡  SEND TEST")

    send_btn.clicked.connect(lambda: run_async(_send()))
    cl.addWidget(send_btn); cl.addWidget(result_lbl)
    lay.addWidget(c)


@register_widget("credits_info", "Credits Info", "Credits")
def _build_credits_info(lay):
    c = card(); cl = QVBoxLayout(c); cl.setContentsMargins(24, 24, 24, 24); cl.setSpacing(4)
    n = QLabel("ECLIPSUM ENGINE")
    n.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {TEXT}; letter-spacing: -0.5px;")
    t = QLabel("v2.0  —  Macro Automation Suite")
    t.setStyleSheet(f"font-size: 12px; color: {TEXT_MID};")
    cl.addWidget(n); cl.addWidget(t)
    cl.addSpacing(10); cl.addWidget(h_line()); cl.addSpacing(10)
    by = QLabel("Made by"); by.setStyleSheet(f"font-size: 11px; color: {TEXT_DIM};")
    steve = QLabel("Steve"); steve.setStyleSheet(f"font-size: 17px; font-weight: 700; color: {PRIMARY};")
    cl.addWidget(by); cl.addWidget(steve)
    cl.addSpacing(8); cl.addWidget(h_line()); cl.addSpacing(8)
    stack = QLabel("Built with  PySide6  ×  Python 3  ×  qasync  ×  aiohttp")
    stack.setStyleSheet(f"font-size: 11px; color: {TEXT_DIM};")
    rights = QLabel("© All rights reserved  2025")
    rights.setStyleSheet(f"font-size: 10px; color: {TEXT_DIM};")
    cl.addWidget(stack); cl.addWidget(rights); lay.addWidget(c)


# ═════════════════════════════════════════════════════════════════════════════
# Main App
# ═════════════════════════════════════════════════════════════════════════════

class EclipsumApp(QMainWindow):
    def __init__(self):
        super().__init__()
        global _app_ref
        _app_ref = self

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setFixedSize(760, 520)   # +40px for banner row
        self.setWindowTitle("Eclipsum")
        self.setStyleSheet(QSS)

        self._drag_pos   = None
        self.active_tab  = None
        self.nav_buttons = {}
        self.tab_order   = list(DEFAULT_TABS)
        self.tab_labels  = {t: t for t in DEFAULT_TABS}
        self.widget_placement = {w["id"]: w["tab"] for w in WIDGET_REGISTRY}

        self._build_ui()
        self._show_tab(self.tab_order[0])

        self.setWindowOpacity(0.0)
        self._opacity = 0.0
        self._fade = QTimer(); self._fade.timeout.connect(self._fade_step); self._fade.start(10)
        self._pulse_on = True
        self._pt = QTimer(); self._pt.timeout.connect(self._pulse); self._pt.start(900)

        # ── Wire up auto-updater ──────────────────────────────────────────────
        self._updater = AutoUpdater(self)
        self._updater.update_available.connect(self._on_update_found)
        self._updater.update_applied.connect(self._on_update_applied)
        self._updater.update_error.connect(self._on_update_error)
        self._updater.download_progress.connect(self._on_dl_progress)

        run_async(self._async_init())

    async def _async_init(self):
        data = await async_load_prefs()
        if data:
            order     = data.get("tab_order", [])
            labels    = data.get("tab_labels", {})
            placement = data.get("widget_placement", {})
            self.tab_order = [t for t in order if t in DEFAULT_TABS]
            for t in DEFAULT_TABS:
                if t not in self.tab_order: self.tab_order.append(t)
            self.tab_labels = {t: labels.get(t, t) for t in DEFAULT_TABS}
            for wid, tab in placement.items():
                if wid in self.widget_placement and tab in DEFAULT_TABS:
                    self.widget_placement[wid] = tab
            self._rebuild_sidebar_btns()
            self._rebuild_all_tab_contents()
            self._show_tab(self.tab_order[0])
            self._refresh_custom_panel()
        self.set_status("READY")
        # Kick off first update check after UI is settled
        self._updater.start_immediate_check()

    # ── Update event handlers ─────────────────────────────────────────────────
    def _on_update_found(self, cur: str, new: str):
        self._banner.show_update_found(cur, new)
        self.set_status(f"UPDATING  {cur} → {new}")
        self._ver_badge.setObjectName("update_badge")
        self._ver_badge.setText(f"↑ {new}")
        self._ver_badge.style().unpolish(self._ver_badge)
        self._ver_badge.style().polish(self._ver_badge)

    def _on_dl_progress(self, done: int, total: int):
        self._banner.show_progress(done, total)

    def _on_update_applied(self, ver: str):
        # The updater auto-restarts the process if THIS_SCRIPT was replaced.
        # This slot fires just before that; always show 'restarting' state.
        self._banner.show_applied(ver, self_updated=True)
        self.set_status(f"UPDATED TO {ver}")
        self._ver_badge.setObjectName("ver_badge")
        self._ver_badge.setText(f"v{ver}")
        self._ver_badge.style().unpolish(self._ver_badge)
        self._ver_badge.style().polish(self._ver_badge)

    def _on_update_error(self, msg: str):
        self._banner.show_error(msg)
        self.set_status("UPDATE ERROR")

    # ── Fade ──────────────────────────────────────────────────────────────────
    def _fade_step(self):
        self._opacity = min(1.0, self._opacity + 0.08)
        self.setWindowOpacity(self._opacity)
        if self._opacity >= 1.0: self._fade.stop()

    def _pulse(self):
        self._pulse_on = not self._pulse_on
        self.status_dot.setStyleSheet(f"color: {PRIMARY if self._pulse_on else TEXT_DIM}; font-size: 8px;")

    # ── Build ─────────────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QWidget(); root.setObjectName("root"); self.setCentralWidget(root)
        rlay = QVBoxLayout(root); rlay.setContentsMargins(0,0,0,0); rlay.setSpacing(0)
        rlay.addWidget(self._mk_topbar())

        # Update banner (hidden by default, sits between topbar and body)
        self._banner = UpdateBanner(root)
        self._banner.setContentsMargins(10, 4, 10, 4)
        self._banner.setFixedHeight(48)
        rlay.addWidget(self._banner)

        body = QWidget()
        blay = QHBoxLayout(body); blay.setContentsMargins(0,0,0,0); blay.setSpacing(0)
        blay.addWidget(self._mk_sidebar())
        self.stack = QStackedWidget(); self.stack.setObjectName("content")
        blay.addWidget(self.stack)
        rlay.addWidget(body); rlay.addWidget(self._mk_statusbar())

        subtitles = {
            "Macro":         "Automate your workflow",
            "Settings":      "Configure behavior",
            "Webhook":       "Send notifications",
            "Customization": "Rearrange tabs and widgets",
            "Credits":       "About this tool",
        }
        self.tab_pages           = {}
        self.tab_content_layouts = {}

        for name in DEFAULT_TABS:
            pg = QWidget(); pg.setObjectName("content")
            pg_lay = QVBoxLayout(pg); pg_lay.setContentsMargins(0,0,0,0); pg_lay.setSpacing(0)
            pg_lay.addWidget(section_header(name, subtitles[name]))

            if name == "Customization":
                self._custom_container = QWidget()
                self._custom_container.setObjectName("content")
                self._custom_container.setStyleSheet(f"background: {BG};")
                self._custom_lay = QVBoxLayout(self._custom_container)
                self._custom_lay.setContentsMargins(0,0,0,0); self._custom_lay.setSpacing(0)
                pg_lay.addWidget(self._custom_container)
                self._refresh_custom_panel()
            else:
                scroll = QScrollArea(); scroll.setWidgetResizable(True)
                scroll.setFrameShape(QFrame.NoFrame)
                inner = QWidget(); inner.setObjectName("content")
                inner.setStyleSheet(f"background: {BG};")
                ilay = QVBoxLayout(inner); ilay.setContentsMargins(20,16,20,20); ilay.setSpacing(12)
                scroll.setWidget(inner)
                pg_lay.addWidget(scroll)
                self.tab_content_layouts[name] = ilay

            self.tab_pages[name] = pg
            self.stack.addWidget(pg)

        self._rebuild_all_tab_contents()

    def _rebuild_all_tab_contents(self):
        for tab_name, ilay in self.tab_content_layouts.items():
            while ilay.count():
                item = ilay.takeAt(0)
                if item.widget(): item.widget().setParent(None)
            for entry in WIDGET_REGISTRY:
                if self.widget_placement.get(entry["id"]) == tab_name:
                    entry["builder"](ilay)
            ilay.addStretch()

    # ── Topbar ────────────────────────────────────────────────────────────────
    def _mk_topbar(self):
        bar = QWidget(); bar.setObjectName("topbar"); bar.setFixedHeight(40)
        bar.mousePressEvent = lambda e: (
            setattr(self, '_drag_pos', e.globalPos() - self.frameGeometry().topLeft())
            if e.button() == Qt.LeftButton else None
        )
        bar.mouseMoveEvent = lambda e: (
            self.move(e.globalPos() - self._drag_pos)
            if e.buttons() == Qt.LeftButton and self._drag_pos else None
        )
        lay = QHBoxLayout(bar); lay.setContentsMargins(16,0,8,0); lay.setSpacing(0)
        dot = QLabel("◆"); dot.setObjectName("logo_dot"); dot.setFixedWidth(18)
        ttl = QLabel("ECLIPSUM"); ttl.setObjectName("logo_text")
        self._ver_badge = QLabel("v2.0"); self._ver_badge.setObjectName("ver_badge")
        for w in (dot, ttl): lay.addWidget(w); lay.addSpacing(8)
        lay.addWidget(self._ver_badge)
        ai = QLabel("⚡"); ai.setStyleSheet(f"color: {PRIMARY}55; font-size: 12px;")
        ai.setToolTip("Async event loop active"); lay.addSpacing(8); lay.addWidget(ai)
        lay.addStretch()
        min_b = QPushButton("—"); min_b.setObjectName("wc_btn")
        min_b.setCursor(QCursor(Qt.PointingHandCursor)); min_b.clicked.connect(self.showMinimized)
        cls_b = QPushButton("✕"); cls_b.setObjectName("close_btn")
        cls_b.setCursor(QCursor(Qt.PointingHandCursor)); cls_b.clicked.connect(self._close)
        lay.addWidget(min_b); lay.addSpacing(2); lay.addWidget(cls_b)
        return bar

    # ── Sidebar ───────────────────────────────────────────────────────────────
    def _mk_sidebar(self):
        sb = QWidget(); sb.setObjectName("sidebar"); sb.setFixedWidth(152)
        lay = QVBoxLayout(sb); lay.setContentsMargins(10,16,10,14); lay.setSpacing(2)
        nav_lbl = QLabel("NAVIGATE")
        nav_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 9px; font-weight: 700; letter-spacing: 2px; padding: 0 4px 10px 4px;")
        lay.addWidget(nav_lbl)
        self._sb_layout = lay; self._sb_start = 1
        self._rebuild_sidebar_btns()
        lay.addStretch()
        info = QLabel("ECLIPSUM ENGINE")
        info.setStyleSheet(f"color: {TEXT_DIM}; font-size: 9px; letter-spacing: 0.3px; padding: 2px 4px 0 4px;")
        lay.addWidget(info)
        return sb

    def _rebuild_sidebar_btns(self):
        for btn in self.nav_buttons.values(): btn.setParent(None)
        self.nav_buttons = {}
        insert_at = self._sb_start
        for name in self.tab_order:
            label = self.tab_labels.get(name, name)
            btn = QPushButton(label); btn.setObjectName("nav_btn")
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.clicked.connect(lambda _, n=name: self._show_tab(n))
            self._sb_layout.insertWidget(insert_at, btn)
            self.nav_buttons[name] = btn; insert_at += 1

    # ── Status bar ────────────────────────────────────────────────────────────
    def _mk_statusbar(self):
        bar = QWidget(); bar.setObjectName("statusbar"); bar.setFixedHeight(24)
        lay = QHBoxLayout(bar); lay.setContentsMargins(14,0,14,0); lay.setSpacing(6)
        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet(f"color: {PRIMARY}; font-size: 8px;")
        self.status_label = QLabel("LOADING"); self.status_label.setObjectName("status_label")
        lay.addWidget(self.status_dot); lay.addWidget(self.status_label); lay.addStretch()
        build = QLabel("STEVE BUILD  ·  PYSIDE6  ·  ASYNCIO")
        build.setStyleSheet(f"color: {TEXT_DIM}; font-size: 9px; letter-spacing: 0.5px;")
        lay.addWidget(build); return bar

    def set_status(self, text: str): self.status_label.setText(text)

    # ── Tab switching ─────────────────────────────────────────────────────────
    def _show_tab(self, name):
        self.active_tab = name
        if name in self.tab_pages: self.stack.setCurrentWidget(self.tab_pages[name])
        for n, btn in self.nav_buttons.items():
            obj = "nav_btn_active" if n == name else "nav_btn"
            btn.setObjectName(obj); btn.style().unpolish(btn); btn.style().polish(btn)
        self.set_status(self.tab_labels.get(name, name).upper())

    # ── Customization panel ───────────────────────────────────────────────────
    def _refresh_custom_panel(self):
        while self._custom_lay.count():
            item = self._custom_lay.takeAt(0)
            if item.widget(): item.widget().setParent(None)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        inner = QWidget(); inner.setObjectName("content")
        inner.setStyleSheet(f"background: {BG};")
        ilay = QVBoxLayout(inner); ilay.setContentsMargins(20,16,20,20); ilay.setSpacing(14)

        ilay.addWidget(field_label("Tab Order & Names"))
        tabs_card = card(); tcl = QVBoxLayout(tabs_card)
        tcl.setContentsMargins(12,8,12,8); tcl.setSpacing(4)
        self._tab_order_rows = []
        for idx, name in enumerate(self.tab_order):
            row = QWidget(); row.setStyleSheet("background: transparent;")
            rl = QHBoxLayout(row); rl.setContentsMargins(4,4,4,4); rl.setSpacing(8)
            num = QLabel(f"{idx+1:02d}")
            num.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; font-weight: 700; min-width: 20px;")
            entry = QLineEdit(self.tab_labels[name]); entry.setFixedHeight(28)
            up = QPushButton("↑"); up.setObjectName("secondary_btn")
            up.setFixedSize(28, 28); up.setCursor(QCursor(Qt.PointingHandCursor))
            up.clicked.connect(lambda _, i=idx: self._tab_move_up(i))
            dn = QPushButton("↓"); dn.setObjectName("secondary_btn")
            dn.setFixedSize(28, 28); dn.setCursor(QCursor(Qt.PointingHandCursor))
            dn.clicked.connect(lambda _, i=idx: self._tab_move_dn(i))
            rl.addWidget(num); rl.addWidget(entry); rl.addWidget(up); rl.addWidget(dn)
            tcl.addWidget(row); self._tab_order_rows.append((name, entry))
        ilay.addWidget(tabs_card)

        ilay.addWidget(field_label("Widget Placement"))
        hint = QLabel("Drag widgets between tabs — changes apply when you hit Apply.")
        hint.setStyleSheet(f"font-size: 10px; color: {TEXT_DIM};")
        hint.setWordWrap(True)
        ilay.addWidget(hint)

        wcard = card(); wcl = QVBoxLayout(wcard)
        wcl.setContentsMargins(12,8,12,8); wcl.setSpacing(0)
        self._widget_placement_combos = {}

        for i, entry in enumerate(WIDGET_REGISTRY):
            row = QWidget(); row.setStyleSheet("background: transparent;")
            rl = QHBoxLayout(row); rl.setContentsMargins(4,9,4,9); rl.setSpacing(10)
            info_col = QVBoxLayout(); info_col.setSpacing(1)
            name_lbl = QLabel(entry["label"])
            name_lbl.setStyleSheet(f"font-size: 12px; font-weight: 500; color: {TEXT};")
            tab_lbl  = QLabel(f"Default: {entry['tab']}")
            tab_lbl.setStyleSheet(f"font-size: 10px; color: {TEXT_DIM};")
            info_col.addWidget(name_lbl); info_col.addWidget(tab_lbl)
            combo = QComboBox(); combo.setFixedWidth(128); combo.setFixedHeight(30)
            for tab in self.tab_order:
                combo.addItem(self.tab_labels.get(tab, tab), tab)
            current = self.widget_placement.get(entry["id"], entry["tab"])
            idx_c = next((j for j in range(combo.count()) if combo.itemData(j) == current), 0)
            combo.setCurrentIndex(idx_c)
            self._widget_placement_combos[entry["id"]] = combo
            rl.addLayout(info_col); rl.addStretch(); rl.addWidget(combo)
            wcl.addWidget(row)
            if i < len(WIDGET_REGISTRY) - 1: wcl.addWidget(h_line())
        ilay.addWidget(wcard)

        btn_row = QHBoxLayout(); btn_row.setSpacing(8)
        apply_b = QPushButton("✓  Apply Changes"); apply_b.setObjectName("primary_btn")
        apply_b.setCursor(QCursor(Qt.PointingHandCursor))
        apply_b.clicked.connect(lambda: run_async(self._apply_custom()))
        reset_b = QPushButton("↺  Reset Defaults"); reset_b.setObjectName("secondary_btn")
        reset_b.setCursor(QCursor(Qt.PointingHandCursor))
        reset_b.clicked.connect(lambda: run_async(self._reset_custom()))
        btn_row.addWidget(apply_b); btn_row.addWidget(reset_b)
        ilay.addLayout(btn_row); ilay.addStretch()

        scroll.setWidget(inner); self._custom_lay.addWidget(scroll)

    def _tab_move_up(self, idx):
        if idx > 0:
            self.tab_order[idx], self.tab_order[idx-1] = self.tab_order[idx-1], self.tab_order[idx]
            self._refresh_custom_panel()

    def _tab_move_dn(self, idx):
        if idx < len(self.tab_order) - 1:
            self.tab_order[idx], self.tab_order[idx+1] = self.tab_order[idx+1], self.tab_order[idx]
            self._refresh_custom_panel()

    async def _apply_custom(self):
        for name, entry in self._tab_order_rows:
            v = entry.text().strip()
            self.tab_labels[name] = v if v else name
        for wid, combo in self._widget_placement_combos.items():
            self.widget_placement[wid] = combo.currentData()
        self._rebuild_sidebar_btns()
        self._rebuild_all_tab_contents()
        self._show_tab(self.active_tab)
        self._refresh_custom_panel()
        await async_save_prefs({
            "tab_order":        self.tab_order,
            "tab_labels":       self.tab_labels,
            "widget_placement": self.widget_placement,
        })
        self.set_status("SAVED")

    async def _reset_custom(self):
        self.tab_order        = list(DEFAULT_TABS)
        self.tab_labels       = {t: t for t in DEFAULT_TABS}
        self.widget_placement = {w["id"]: w["tab"] for w in WIDGET_REGISTRY}
        self._rebuild_sidebar_btns()
        self._rebuild_all_tab_contents()
        self._refresh_custom_panel()
        self._show_tab(self.tab_order[0])
        await async_save_prefs({
            "tab_order":        self.tab_order,
            "tab_labels":       self.tab_labels,
            "widget_placement": self.widget_placement,
        })
        self.set_status("RESET TO DEFAULTS")

    # ── Close ─────────────────────────────────────────────────────────────────
    def _close(self):
        run_async(self._async_close())

    async def _async_close(self):
        await async_save_prefs({
            "tab_order":        self.tab_order,
            "tab_labels":       self.tab_labels,
            "widget_placement": self.widget_placement,
        })
        self.close()


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    w = EclipsumApp()
    w.show()
    with loop:
        loop.run_forever()

if __name__ == "__main__":
    main()
