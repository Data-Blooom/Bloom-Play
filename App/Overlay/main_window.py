import time
import webbrowser

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import QThread, pyqtSignal, QSettings

import api.state

from engine import get_all_stats
from utils.ip import get_local_ip
from utils.qr import create_qr

from collectors.hardware import get_hardware_info


class StatsWorker(QThread):
    """Worker thread for fetching system stats"""
    stats_ready = pyqtSignal(dict)
    
    def run(self):
        try:
            data = get_all_stats()
            self.stats_ready.emit(data)
        except Exception:
            self.stats_ready.emit({})


class MainWindow(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        
        self.settings = QSettings("BloomPlay", "Settings")
        self.show_hardware = self.settings.value("show_hardware", False, type=bool)
        
        try:
            self.ip = get_local_ip()
            self.url = f"http://{self.ip}:8000"
        except Exception:
            self.ip = "127.0.0.1"
            self.url = "http://127.0.0.1:8000"

        try:
            self.hardware = get_hardware_info()
        except Exception:
            self.hardware = {}

        try:
            self.qr_path = create_qr(self.url)
        except Exception:
            self.qr_path = None

        self.cached_stats = {}
        self.stats_worker = None
        
        self.setup_window()
        self.setup_tray()
        self.setup_ui()
        self.setup_timer()

    def setup_window(self):
        self.setWindowTitle("BloomPlay")
        self.setFixedSize(700, 420)

        self.setStyleSheet("""
            QWidget {
                background-color: qlineargradient(
                    x1:0, y1:0,
                    x2:1, y2:1,
                    stop:0 #0a0e1a,
                    stop:1 #111827
                );
                color: #ffffff;
                font-family: 'Inter', 'Segoe UI', sans-serif;
            }

            QPushButton {
                background-color: #1f2937;
                color: #ffffff;
                border: 1px solid #2a3a55;
                border-radius: 12px;
                padding: 10px;
                font-size: 13px;
                font-weight: 600;
                font-family: 'Inter', 'Segoe UI', sans-serif;
            }

            QPushButton:hover {
                background-color: #2a3a55;
                border-color: #3b5a8a;
            }

            QPushButton:pressed {
                background-color: #374151;
            }
            
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            
            QScrollBar:vertical {
                background-color: #0f1729;
                width: 8px;
                border-radius: 4px;
                margin: 2px;
            }
            
            QScrollBar::handle:vertical {
                background: #2a3a55;
                border-radius: 4px;
                min-height: 30px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: #3b5a8a;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
                border: none;
            }
            
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
        """)

    def setup_ui(self):
        root = QtWidgets.QVBoxLayout(self)

        content = QtWidgets.QHBoxLayout()
        content.setSpacing(12)

        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #0f1729;
                border: 1px solid #1a2840;
                border-radius: 16px;
            }
        """)

        self.stats_label = QtWidgets.QLabel()
        self.stats_label.setAlignment(
            QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft
        )
        self.stats_label.setTextFormat(
            QtCore.Qt.RichText
        )
        self.stats_label.setWordWrap(True)
        self.stats_label.setStyleSheet("""
            background-color: transparent;
            padding: 16px;
            font-size: 13px;
            font-family: 'Inter', 'Segoe UI', sans-serif;
            line-height: 1.6;
            color: #ffffff;
        """)
        
        self.scroll_area.setWidget(self.stats_label)

        # ===== QR =====
        qr_frame = QtWidgets.QFrame()

        qr_frame.setStyleSheet("""
            QFrame {
                background-color: #0f1729;
                border: 1px solid #1a2840;
                border-radius: 16px;
            }
        """)

        qr_layout = QtWidgets.QVBoxLayout(qr_frame)

        title = QtWidgets.QLabel("📱 Scan to Connect")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 14px;
            font-weight: 700;
            color: #ffffff;
            font-family: 'Inter', 'Segoe UI', sans-serif;
        """)

        qr_label = QtWidgets.QLabel()

        if self.qr_path:
            pixmap = QtGui.QPixmap(self.qr_path)
            qr_label.setPixmap(
                pixmap.scaled(
                    180,
                    180,
                    QtCore.Qt.KeepAspectRatio,
                    QtCore.Qt.SmoothTransformation
                )
            )
        else:
            qr_label.setText("QR Code\nNot Available")

        qr_label.setAlignment(QtCore.Qt.AlignCenter)

        self.ip_label = QtWidgets.QLabel(self.url)
        self.ip_label.setAlignment(QtCore.Qt.AlignCenter)
        self.ip_label.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.ip_label.setToolTip("🖱 Click to copy IP address")
        self.ip_label.setStyleSheet("""
            color: #60a5fa;
            font-size: 12px;
            font-weight: 600;
            font-family: 'Inter', 'Segoe UI', sans-serif;
        """)
        self.ip_label.mousePressEvent = self.copy_ip_to_clipboard

        self.phone_status = QtWidgets.QLabel("🔴 Disconnected")
        self.phone_status.setAlignment(QtCore.Qt.AlignCenter)
        self.phone_status.setStyleSheet("""
            background-color: rgba(248, 113, 113, 0.05);
            border: 1px solid rgba(248, 113, 113, 0.15);
            border-radius: 10px;
            color: #f87171;
            padding: 10px;
            font-size: 12px;
            font-weight: bold;
            font-family: 'Inter', 'Segoe UI', sans-serif;
        """)

        qr_layout.addWidget(title)
        qr_layout.addWidget(qr_label)
        qr_layout.addWidget(self.ip_label)
        qr_layout.addSpacing(8)
        qr_layout.addWidget(self.phone_status)

        content.addWidget(self.scroll_area, 2)
        content.addWidget(qr_frame, 1)

        root.addLayout(content)

        # ===== Bottom Buttons =====
        bottom = QtWidgets.QHBoxLayout()
        bottom.setSpacing(10)

        self.creator_btn = QtWidgets.QPushButton("🌸 Data Bloom")
        self.creator_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0,
                    x2:1, y2:0,
                    stop:0 rgba(167, 139, 250, 0.12),
                    stop:1 rgba(244, 114, 182, 0.12)
                );
                color: #a78bfa;
                border: 1px solid rgba(167, 139, 250, 0.2);
                border-radius: 12px;
                padding: 10px;
                font-size: 13px;
                font-weight: 600;
                font-family: 'Inter', 'Segoe UI', sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0,
                    x2:1, y2:0,
                    stop:0 rgba(167, 139, 250, 0.2),
                    stop:1 rgba(244, 114, 182, 0.2)
                );
                border-color: rgba(167, 139, 250, 0.35);
            }
            QPushButton:pressed {
                background: qlineargradient(
                    x1:0, y1:0,
                    x2:1, y2:0,
                    stop:0 rgba(167, 139, 250, 0.3),
                    stop:1 rgba(244, 114, 182, 0.3)
                );
            }
        """)
        self.creator_btn.clicked.connect(
            lambda: webbrowser.open("https://linktr.ee/Data_Bloom")
        )

        self.hardware_btn = QtWidgets.QPushButton("💻 Hardware Info")
        self.hardware_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0,
                    x2:1, y2:0,
                    stop:0 rgba(34, 211, 167, 0.12),
                    stop:1 rgba(96, 165, 250, 0.12)
                );
                color: #22d3a7;
                border: 1px solid rgba(34, 211, 167, 0.2);
                border-radius: 12px;
                padding: 10px;
                font-size: 13px;
                font-weight: 600;
                font-family: 'Inter', 'Segoe UI', sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0,
                    x2:1, y2:0,
                    stop:0 rgba(34, 211, 167, 0.2),
                    stop:1 rgba(96, 165, 250, 0.2)
                );
                border-color: rgba(34, 211, 167, 0.35);
            }
            QPushButton:pressed {
                background: qlineargradient(
                    x1:0, y1:0,
                    x2:1, y2:0,
                    stop:0 rgba(34, 211, 167, 0.3),
                    stop:1 rgba(96, 165, 250, 0.3)
                );
            }
        """)
        self.hardware_btn.clicked.connect(self.toggle_hardware)

        bottom.addWidget(self.creator_btn)
        bottom.addWidget(self.hardware_btn)

        root.addLayout(bottom)

        self.update_stats()

    def copy_ip_to_clipboard(self, event):
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(self.url)
        
        original_text = self.ip_label.text()
        self.ip_label.setText("✅ Copied!")
        self.ip_label.setStyleSheet("""
            color: #22d3a7;
            font-size: 12px;
            font-weight: 600;
            font-family: 'Inter', 'Segoe UI', sans-serif;
        """)
        
        QtCore.QTimer.singleShot(1500, lambda: self.restore_ip_label(original_text))

    def restore_ip_label(self, original_text):
        self.ip_label.setText(original_text)
        self.ip_label.setStyleSheet("""
            color: #60a5fa;
            font-size: 12px;
            font-weight: 600;
            font-family: 'Inter', 'Segoe UI', sans-serif;
        """)

    def setup_timer(self):
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.fetch_stats_async)
        self.timer.start(1000)

    def fetch_stats_async(self):
        if not self.show_hardware:
            if self.stats_worker is None or not self.stats_worker.isRunning():
                self.stats_worker = StatsWorker()
                self.stats_worker.stats_ready.connect(self.display_stats)
                self.stats_worker.start()

    def display_stats(self, data):
        if data:
            self.cached_stats = data
            self.update_stats()

    def setup_tray(self):
        self.tray = QtWidgets.QSystemTrayIcon(self)
        icon = self.style().standardIcon(QtWidgets.QStyle.SP_ComputerIcon)
        self.tray.setIcon(icon)

        menu = QtWidgets.QMenu()
        show_action = menu.addAction("Show")
        exit_action = menu.addAction("Exit")
        show_action.triggered.connect(self.show_window)
        exit_action.triggered.connect(QtWidgets.qApp.quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.on_tray_click)
        self.tray.show()

    def get_color(self, value, warning=70, critical=85):
        try:
            value = float(value)
        except Exception:
            return "#ffffff"

        if value >= critical:
            return "#f87171"
        if value >= warning:
            return "#fbbf24"
        return "#22d3a7"

    def update_phone_status(self):
        connected = (
            time.time() - api.state.last_client_seen
        ) < 10

        if connected:
            self.phone_status.setText("🟢 Connected")
            self.phone_status.setStyleSheet("""
                background-color: rgba(34, 211, 167, 0.05);
                border: 1px solid rgba(34, 211, 167, 0.2);
                border-radius: 10px;
                color: #22d3a7;
                padding: 10px;
                font-size: 12px;
                font-weight: bold;
                font-family: 'Inter', 'Segoe UI', sans-serif;
            """)
        else:
            self.phone_status.setText("🔴 Disconnected")
            self.phone_status.setStyleSheet("""
                background-color: rgba(248, 113, 113, 0.05);
                border: 1px solid rgba(248, 113, 113, 0.15);
                border-radius: 10px;
                color: #f87171;
                padding: 10px;
                font-size: 12px;
                font-weight: bold;
                font-family: 'Inter', 'Segoe UI', sans-serif;
            """)

    def toggle_hardware(self):
        self.show_hardware = not self.show_hardware
        self.settings.setValue("show_hardware", self.show_hardware)

        if self.show_hardware:
            self.hardware_btn.setText("📊 Live Stats")
        else:
            self.hardware_btn.setText("💻 Hardware Info")

        self.update_stats()

    def update_stats(self):
        self.update_phone_status()

        if self.show_hardware:
            try:
                cpu = self.hardware.get("cpu", {})
                gpu = self.hardware.get("gpu", {})
                ram = self.hardware.get("ram", {})
                system = self.hardware.get("system", {})
                bios = self.hardware.get("bios", {})

                disk_total = self.hardware.get("total_storage", "Unknown")
                disks = self.hardware.get("disk", [])

                disk_parts = []
                for i, d in enumerate(disks):
                    emoji = ["💿", "📀", "💾", "🖴"][i % 4]
                    total = d.get('total', 0)
                    used = d.get('used', 0)
                    pct = d.get('percent', 0)
                    disk_type = d.get('type', '')
                    
                    disk_parts.append(
                        f"├ {emoji} <b>{d['name']}</b> "
                        f"<span style='color:#ffffff;'>{used}GB / {total}GB</span> "
                        f"<span style='color:{self.get_color(pct)}; font-weight:bold;'>"
                        f"({pct}%)</span>"
                        f" <span style='color:#ffffff;font-size:11px;'>{disk_type}</span>"
                    )
                
                disk_text = "<br>".join(disk_parts) if disk_parts else "├ No drives detected"

                cpu_clock = cpu.get('base_clock', 0)
                clock_text = f"{cpu_clock} GHz" if cpu_clock > 0 else "Unknown"

                self.stats_label.setText(f"""
<b style='color:#60a5fa;'>🖥 Processor</b>
<br>
<span style='color:#ffffff;font-weight:600;'>{cpu.get('name','Unknown')}</span>
<br>
<span style='color:#ffffff;'>
├ Brand: {cpu.get('brand','Unknown')}<br>
├ Cores: {cpu.get('cores','?')}<br>
├ Threads: {cpu.get('threads','?')}<br>
├ Base Clock: {clock_text}<br>
├ Cache: {cpu.get('cache','Unknown')}<br>
└ Architecture: {cpu.get('architecture','Unknown')}
</span>

<br><br>

<b style='color:#a78bfa;'>🎮 Graphics</b>
<br>
<span style='color:#ffffff;font-weight:600;'>{gpu.get('name','Unknown')}</span>
<br>
<span style='color:#ffffff;'>
├ Vendor: {gpu.get('vendor','Unknown')}<br>
├ VRAM: {gpu.get('memory','Unknown')}<br>
└ Driver: {gpu.get('driver','Unknown')}
</span>

<br><br>

<b style='color:#f472b6;'>🧠 Memory</b>
<br>
<span style='color:#ffffff;font-weight:600;'>{ram.get('size','Unknown')}</span>
<br>
<span style='color:#ffffff;'>
├ Type: {ram.get('type','Unknown')}<br>
├ Speed: {ram.get('speed','Unknown')} MHz<br>
├ Brand: {ram.get('brand','Unknown')}<br>
├ Form Factor: {ram.get('form_factor','Unknown')}<br>
└ Slots: {ram.get('slots','?')} Module(s)
</span>

<br><br>

<b style='color:#fbbf24;'>💾 Storage</b>
<br>
<span style='color:#ffffff;'>Total Capacity: {disk_total}</span>
<br>
<span style='color:#ffffff;'>
{disk_text}
</span>

<br><br>

<b style='color:#fb923c;'>🔧 Motherboard</b>
<br>
<span style='color:#ffffff;'>{bios.get('board','Unknown')}</span>
<br>
<span style='color:#ffffff;'>
└ BIOS: {bios.get('bios','Unknown')}
</span>

<br><br>

<b style='color:#22d3ee;'>🪟 System</b>
<br>
<span style='color:#ffffff;'>{system.get('os','Unknown')}</span>
<br>
<span style='color:#ffffff;'>
├ Hostname: {system.get('hostname','Unknown')}<br>
├ Architecture: {system.get('arch','Unknown')}<br>
└ Kernel: {system.get('kernel','Unknown')}
</span>
""")
            except Exception as e:
                self.stats_label.setText(f"Error loading hardware info: {str(e)}")
            return

        data = self.cached_stats if self.cached_stats else get_all_stats()

        gpu = data.get("gpu") or {}
        ram = data.get("ram") or {}
        net = data.get("network") or {}
        battery = data.get("battery") or {}

        cpu = data.get("cpu", 0)
        cpu_temp = data.get("cpu_temp", 0)

        gpu_usage = gpu.get("usage", 0)
        gpu_temp = gpu.get("temp", 0)

        ram_percent = ram.get("percent", 0)

        ping = net.get("ping", "Offline")

        ping_color = "#ffffff"

        if isinstance(ping, (int, float)):
            if ping < 80:
                ping_color = "#22d3a7"
            elif ping < 150:
                ping_color = "#fbbf24"
            else:
                ping_color = "#f87171"

        self.stats_label.setText(f"""
<b style='color:#60a5fa;'>🖥 CPU</b><br>
<span style='color:#ffffff;'>Usage:</span>
<span style='color:{self.get_color(cpu)};font-weight:700;'>{cpu}%</span>
<span style='color:#ffffff;'>  •  Temp:</span>
<span style='color:{self.get_color(cpu_temp)};font-weight:700;'>{cpu_temp}°C</span>

<br><br>

<b style='color:#a78bfa;'>🎮 GPU</b><br>
<span style='color:#ffffff;'>Usage:</span>
<span style='color:{self.get_color(gpu_usage)};font-weight:700;'>{gpu_usage}%</span>
<span style='color:#ffffff;'>  •  Temp:</span>
<span style='color:{self.get_color(gpu_temp)};font-weight:700;'>{gpu_temp}°C</span>
<br>
<span style='color:#ffffff;'>VRAM:</span>
<span style='color:#ffffff;font-weight:600;'>{gpu.get('vram_used', 0)} / {gpu.get('vram_total', 0)} GB</span>

<br><br>

<b style='color:#f472b6;'>🧠 RAM</b><br>
<span style='color:#ffffff;'>Usage:</span>
<span style='color:{self.get_color(ram_percent)};font-weight:700;'>
{ram.get('used', 0)} / {ram.get('total', 0)} GB ({ram_percent}%)
</span>

<br><br>

<b style='color:#22d3ee;'>🌐 Network</b><br>
<span style='color:#ffffff;'>Download:</span>
<span style='color:#ffffff;font-weight:600;'>↓ {net.get('download', 'Offline')} Mbps</span>
<span style='color:#ffffff;'>  •  Upload:</span>
<span style='color:#ffffff;font-weight:600;'>↑ {net.get('upload', 'Offline')} Mbps</span>
<br>
<span style='color:#ffffff;'>Ping:</span>
<span style='color:{ping_color};font-weight:700;'>{ping} ms</span>

<br><br>

<b style='color:#fbbf24;'>🔋 Battery</b><br>
<span style='color:#ffffff;'>Charge:</span>
<span style='color:#ffffff;font-weight:600;'>{battery.get('percent', 'N/A')}%</span>
<br>
<span style='color:#ffffff;'>Health:</span>
<span style='color:#ffffff;font-weight:600;'>{battery.get('health', 'Unknown')}</span>
""")

    def hide_to_tray(self):
        self.hide()
        self.tray.showMessage(
            "BloomPlay",
            "Running in background",
            QtWidgets.QSystemTrayIcon.Information,
            2000
        )

    def show_window(self):
        self.showNormal()
        self.activateWindow()

    def on_tray_click(self, reason):
        if reason == QtWidgets.QSystemTrayIcon.Trigger:
            self.show_window()

    def closeEvent(self, event):
        event.ignore()
        self.hide_to_tray()