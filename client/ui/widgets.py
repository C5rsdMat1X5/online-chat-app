from PySide6.QtWidgets import (
    QWidget, QMainWindow, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QLabel, QMessageBox
)
from PySide6.QtGui import QTextCursor
from utils.styles import load_custom_css
from core.network import create_connection, send_data, start_receiving

class ServerConnectionDialog(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Connect to Server")
        self.setFixedSize(300, 150)
        self.client_socket = None

        layout = QVBoxLayout()
        self.title = QLabel("Enter the server IP address:")

        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("e.g., 111.111.1.1")
        self.address_input.returnPressed.connect(self.create_connection)

        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.create_connection)

        layout.addWidget(self.title)
        layout.addWidget(self.address_input)
        layout.addWidget(self.connect_button)
        self.setLayout(layout)

        self.setStyleSheet(load_custom_css())

    def create_connection(self):
        ip = self.address_input.text().strip()
        if ip:
            try:
                self.client_socket = create_connection(ip)
                self.hide()
                self.chat_window = ChatClient(ip, self.client_socket)
                self.chat_window.show()
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Connection Error",
                    f"Could not connect to the server at {ip}:\n{e}",
                )


class ChatClient(QMainWindow):
    def __init__(self, server_ip, client_socket):
        super().__init__()
        self.setWindowTitle("Chat Client")
        self.resize(420, 380)

        self.server_ip = server_ip
        self.username = "Client"
        self.server_username = "Server"
        self.client_socket = client_socket

        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.returnPressed.connect(self.change_username)

        self.username_button = QPushButton("Change")
        self.username_button.clicked.connect(self.change_username)

        username_layout = QHBoxLayout()
        username_layout.addWidget(self.username_input)
        username_layout.addWidget(self.username_button)

        self.current_user_label = QLabel(f"Connected as: {self.username}")
        self.server_writing = QLabel("")
        self.server_writing.setStyleSheet("font-style: italic; color: #4e88ff;")

        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("Message")
        self.input_line.textEdited.connect(self.notify_writing)
        self.input_line.returnPressed.connect(self.send_message)

        self.send_button = QPushButton("Send")
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

        self.setStyleSheet(load_custom_css())
        self.setup_connection()

    def setup_connection(self):
        self.chat_area.append(f"✅ Connected to server {self.server_ip}.")
        self.listen_thread = start_receiving(self.client_socket, self.process_server_message)

    def change_username(self):
        new_username = self.username_input.text().strip()
        if new_username:
            self.username = new_username
            try:
                send_data(self.client_socket, "#usern#" + self.username)
                self.chat_area.append(f"🔄 Username changed to: {self.username}")
            except Exception as e:
                self.chat_area.append(f"Error sending username change: {e}")
            self.current_user_label.setText(f"Connected as: {self.username}")
        self.username_input.setPlaceholderText(self.username)
        self.username_input.clear()

    def notify_writing(self):
        try:
            send_data(self.client_socket, "#writing#" + self.username)
        except Exception as e:
            print(f"Error sending writing status: {e}")

    def send_message(self):
        msg = self.input_line.text()

        try:
            send_data(self.client_socket, "#nowriting#")
        except Exception as e:
            self.chat_area.append(f"Error: could not send '#nowriting#'. {e}")
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
                send_data(self.client_socket, f"#{self.username}#{clean_msg}\n")
                if clean_msg.upper() == "STOP":
                    self.close()
            except Exception as e:
                self.chat_area.append(f"Error: could not send the message. {e}")

        self.input_line.clear()

    def process_server_message(self, data):
        data_stripped = data.strip()

        if "#usern#" in data_stripped:
            new_server_name = data_stripped.replace("#usern#", "")
            if new_server_name != self.server_username:
                self.chat_area.append(f"🗣️ The {self.server_username} changed their name to {new_server_name}")
            self.server_username = new_server_name
        elif "#writing#" in data_stripped:
            writing_user = data_stripped.replace("#writing#", "")
            self.server_writing.setText(f"{writing_user} is typing...")
        elif "#nowriting#" in data_stripped:
            self.server_writing.setText("")
        elif "#other#" in data_stripped:
            message_content = data_stripped.replace("#other#", "")
            self.chat_area.append(f"{message_content}")
        else:
            self.chat_area.append(f"{self.server_username}: {data_stripped}")

        self.chat_area.moveCursor(QTextCursor.End)

        if (not data_stripped.startswith("#other#") and data_stripped.upper() == "STOP"):
            self.chat_area.append("🛑 The server has ended the connection.")
            self.input_line.setEnabled(False)
            self.send_button.setEnabled(False)
            self.username_input.setEnabled(False)
            self.username_button.setEnabled(False)

    def closeEvent(self, event):
        try:
            send_data(self.client_socket, "Goodbye folks")
        except:
            pass
        finally:
            try:
                self.client_socket.close()
            except:
                pass
        event.accept()