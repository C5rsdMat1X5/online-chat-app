from PySide6.QtWidgets import (
    QWidget, QMainWindow, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QLabel, QMessageBox
)
from PySide6.QtGui import QTextCursor
from utils.styles import custom_css
from core.network import connect_to_server, send_message, start_listening

class ServerConnectionDialog(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Conectarse al Servidor")
        self.setFixedSize(300, 150)
        self.client_socket = None

        layout = QVBoxLayout()
        self.title = QLabel("Ingrese la dirección IP del servidor:")

        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("Por ejemplo: 111.111.1.1")
        self.address_input.returnPressed.connect(self.connect_to_server)

        self.connect_button = QPushButton("Conectar")
        self.connect_button.clicked.connect(self.connect_to_server)

        layout.addWidget(self.title)
        layout.addWidget(self.address_input)
        layout.addWidget(self.connect_button)
        self.setLayout(layout)

        self.setStyleSheet(custom_css())

    def connect_to_server(self):
        ip = self.address_input.text().strip()
        if ip:
            try:
                self.client_socket = connect_to_server(ip)
                self.hide()
                self.chat_window = ChatClient(ip, self.client_socket)
                self.chat_window.show()
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error de conexión",
                    f"No se pudo conectar al servidor en {ip}:\n{e}",
                )


class ChatClient(QMainWindow):
    def __init__(self, server_ip, client_socket):
        super().__init__()
        self.setWindowTitle("Cliente Chat")
        self.resize(420, 380)

        self.server_ip = server_ip
        self.usern = "Cliente"
        self.server_usern = "Servidor"
        self.client_socket = client_socket

        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Nombre de usuario")
        self.username_input.returnPressed.connect(self.change_username)

        self.usern_button = QPushButton("Cambiar")
        self.usern_button.clicked.connect(self.change_username)

        username_layout = QHBoxLayout()
        username_layout.addWidget(self.username_input)
        username_layout.addWidget(self.usern_button)

        self.current_user_label = QLabel(f"Conectado como: {self.usern}")
        self.server_writing = QLabel("")
        self.server_writing.setStyleSheet("font-style: italic; color: #4e88ff;")

        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("Mensaje")
        self.input_line.textEdited.connect(self.notify_writing)
        self.input_line.returnPressed.connect(self.send_message)

        self.send_button = QPushButton("Enviar")
        self.send_button.clicked.connect(self.send_message)

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_line)
        input_layout.addWidget(self.send_button)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        layout.addWidget(self.current_user_label)
        layout.addLayout(username_layout)
        layout.addWidget(self.chat_area)
        layout.addWidget(self.server_writing)
        layout.addLayout(input_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.setStyleSheet(custom_css())
        self.setup_connection()

    def setup_connection(self):
        self.chat_area.append(f"✅ Conectado al servidor {self.server_ip}.")
        self.listen_thread = start_listening(self.client_socket, self.process_server_message)

    def change_username(self):
        new_username = self.username_input.text().strip()
        if new_username:
            self.usern = new_username
            try:
                send_message(self.client_socket, "#usern#" + self.usern)
                self.chat_area.append(f"🔄 Nombre cambiado a: {self.usern}")
            except Exception as e:
                self.chat_area.append(f"Error al enviar cambio de nombre: {e}")
            self.current_user_label.setText(f"Conectado como: {self.usern}")
        self.username_input.setPlaceholderText(self.usern)
        self.username_input.clear()

    def notify_writing(self):
        try:
            send_message(self.client_socket, "#writing#" + self.usern)
        except Exception as e:
            print(f"Error enviando estado de escritura: {e}")

    def send_message(self):
        msg = self.input_line.text()

        try:
            send_message(self.client_socket, "#nowriting#")
        except Exception as e:
            self.chat_area.append(f"Error: no se pudo enviar '#nowriting#'. {e}")
            return

        if msg:
            clean_msg = (
                msg.replace("#usern#", "")
                .replace("#writing#", "")
                .replace("#nowriting#", "")
                .replace("#other#", "")
                .replace("#", "")
            )
            try:
                send_message(self.client_socket, f"#{self.usern}#{clean_msg}\n")
                if clean_msg.upper() == "STOP":
                    self.close()
            except Exception as e:
                self.chat_area.append(f"Error: no se pudo enviar el mensaje. {e}")

        self.input_line.clear()

    def process_server_message(self, data):
        data_stripped = data.strip()

        if "#usern#" in data_stripped:
            new_server_name = data_stripped.replace("#usern#", "")
            if new_server_name != self.server_usern:
                self.chat_area.append(f"🗣️ El {self.server_usern} cambió su nombre a {new_server_name}")
            self.server_usern = new_server_name
        elif "#writing#" in data_stripped:
            writing_user = data_stripped.replace("#writing#", "")
            self.server_writing.setText(f"{writing_user} está escribiendo...")
        elif "#nowriting#" in data_stripped:
            self.server_writing.setText("")
        elif "#other#" in data_stripped:
            message_content = data_stripped.replace("#other#", "")
            self.chat_area.append(f"{message_content}")
        else:
            self.chat_area.append(f"{self.server_usern}: {data_stripped}")

        self.chat_area.moveCursor(QTextCursor.End)

        if (not data_stripped.startswith("#other#") and data_stripped.upper() == "STOP"):
            self.chat_area.append("🛑 El servidor finalizó la conexión.")
            self.input_line.setEnabled(False)
            self.send_button.setEnabled(False)
            self.username_input.setEnabled(False)
            self.usern_button.setEnabled(False)

    def closeEvent(self, event):
        try:
            send_message(self.client_socket, "Chaito pesaitos")
        except:
            pass
        finally:
            try:
                self.client_socket.close()
            except:
                pass
        event.accept()