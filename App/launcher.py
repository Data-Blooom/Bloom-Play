import threading
import uvicorn
from PyQt5 import QtWidgets
from api.server import app
from overlay.main_window import MainWindow


def start_api():
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="warning"
    )


def main():

    api_thread = threading.Thread(
        target=start_api,
        daemon=True
    )
    api_thread.start()

    qt_app = QtWidgets.QApplication([])

    window = MainWindow()
    window.show()

    qt_app.exec_()


if __name__ == "__main__":
    main()