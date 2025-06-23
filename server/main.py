import sys
from PySide6.QtWidgets import QApplication
from ui.widgets import ChatServerControlPanel

if __name__ == "__main__":
    app = QApplication(sys.argv)
    server_ui = ChatServerControlPanel()
    server_ui.show()
    sys.exit(app.exec())