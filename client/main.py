import sys
from PySide6.QtWidgets import QApplication
from ui.widgets import ServerConnectionDialog

if __name__ == "__main__":
    app = QApplication(sys.argv)
    connection_dialog = ServerConnectionDialog()
    connection_dialog.show()
    sys.exit(app.exec())