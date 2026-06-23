from PyQt5 import QtWidgets, QtCore


class OverlayWindow(QtWidgets.QWidget):
    def __init__(self, data_provider):
        super().__init__()

        self.data_provider = data_provider

        self.drag_position = None
        self.drag_locked = False

        self.setWindowOpacity(0.93)
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        self.setGeometry(100, 100, 320, 210)

        self.label = QtWidgets.QLabel(self)
        self.label.setGeometry(0, 0, 320, 210)

        self.label.setStyleSheet("""
            color: white;
            background-color: rgba(18, 18, 18, 180);
            border: 2px solid rgba(0, 255, 180, 140);
            border-radius: 12px;

            padding-top: 2px;
            padding-bottom: 10px;
            padding-left: 10px;
            padding-right: 10px;

            font-family: Consolas;
            font-size: 13px;
         """)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(1000)

    def color(self, value):
        if value < 60:
            return "#00ff88"
        elif value < 80:
            return "#ffaa00"
        return "#ff3355"

    def update_data(self):
        data = self.data_provider()
        gpu = data.get("gpu") or {}

        cpu = data.get("cpu", 0)
        cpu_t = data.get("cpu_temp", 0)

        gpu_u = gpu.get("usage", 0)
        gpu_t = gpu.get("temp", 0)

        ram = data["ram"]
        net = data["network"]

        text = f"""
🖥 CPU
Usage: {cpu}% | Temp: {cpu_t}°C

🎮 GPU
Usage: {gpu_u}% | Temp: {gpu_t}°C

🧠 RAM
{ram['used']} / {ram['total']} GB

🌐 Network
↓ {net['download']:.1f} Mbps | ↑ {net['upload']:.1f} Mbps | Ping {net['ping']} ms
"""

        self.label.setText(text)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.drag_position = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.drag_locked:
            return

        if self.drag_position:
            self.move(self.pos() + event.globalPos() - self.drag_position)
            self.drag_position = event.globalPos()

    def mouseDoubleClickEvent(self, event):
        self.drag_locked = not self.drag_locked