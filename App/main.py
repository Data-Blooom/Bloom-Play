import sys
import threading
from PyQt5 import QtWidgets

from engine import get_all_stats
from overlay.window import OverlayWindow
from collectors.logger import SystemLogger
from collectors.gpu import init_gpu
from collectors.network import start_ping_thread


def run():
    init_gpu()
    start_ping_thread()

    app = QtWidgets.QApplication(sys.argv)

    window = OverlayWindow(get_all_stats)
    window.show()

    logger = SystemLogger(get_all_stats)
    threading.Thread(target=logger.start, daemon=True).start()

    sys.exit(app.exec_())


if __name__ == "__main__":
    run()