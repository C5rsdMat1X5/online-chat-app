from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QLabel, QListWidget, QMessageBox
)
from PySide6.QtCore import Signal, QObject, QTimer
from utils.styles import load_custom_css
from core.network import ChatServer
import socket

class Communicator(QObject):
    message_received = Signal(str)

class ChatServerControlPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chat Server Control Panel")
        self.setGeometry(100, 100, 700, 400)

        self.username = "Servidor"
        self.comm = Communicator()
        self.comm.message_received.connect(self.display_message)

        self.network = ChatServer()
        self.network.start_listening(self.new_connection)

        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        left_layout = QVBoxLayout()
        self.chat_display = QTextEdit(readOnly=True)
        self.username_input = QLineEdit(placeholderText="Server name")
        self.username_input.returnPressed.connect(self.change_username)
        self.username_btn = QPushButton("Update name")
        self.username_btn.clicked.connect(self.change_username)

        self.typing_label = QLabel("")
        self.message_input = QLineEdit(placeholderText="Type a message...")
        self.message_input.textEdited.connect(self.notify_typing)
        self.message_input.returnPressed.connect(self.send_message)

        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_message)

        left_layout.addWidget(QLabel("Active chat:"))
        left_layout.addWidget(self.chat_display)
        left_layout.addWidget(self.typing_label)
        left_layout.addWidget(self.username_input)
        left_layout.addWidget(self.username_btn)
        left_layout.addWidget(self.message_input)
        left_layout.addWidget(self.send_btn)

        right_layout = QVBoxLayout()
        self.clients_list = QListWidget()
        self.kick_btn = QPushButton("Kick selected client")
        self.kick_btn.clicked.connect(self.kick_client)

        self.shutdown_btn = QPushButton("Shut down server")
        self.shutdown_btn.clicked.connect(self.shutdown_server)

        self.info_label = QLabel("Active clients: 0\nCPU usage: -")
        self.info_label.setStyleSheet("font-size: 12px;")
        self.ip_label = QLabel("Server IP:")
        self.ip_btn = QPushButton("Show local IP")
        self.ip_btn.clicked.connect(self.get_local_ip)

        right_layout.addWidget(self.ip_label)
        right_layout.addWidget(self.ip_btn)
        right_layout.addWidget(QLabel("Connected clients:"))
        right_layout.addWidget(self.clients_list)
        right_layout.addWidget(self.kick_btn)
        right_layout.addStretch()
        right_layout.addWidget(QLabel("Server status:"))
        right_layout.addWidget(self.info_label)
        right_layout.addWidget(self.shutdown_btn)

        main_layout.addLayout(left_layout, 3)
        main_layout.addLayout(right_layout, 1)

        self.setStyleSheet(load_custom_css())
        
        self.network.set_callbacks(
            on_message=self.comm.message_received.emit,
            on_typing=self.typing_label.setText,
            on_client_disconnect=self.refresh_client_list
        )

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(2000)

    def update_stats(self):
        import psutil
        cpu = psutil.cpu_percent()
        with self.network.clients_lock:
            active = len(self.network.client_names)
        self.info_label.setText(f"Active clients: {active}\nCPU usage: {cpu:.1f}%")

    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            self.ip_label.setText(f"Server IP: {ip}")
        except Exception as e:
            self.ip_label.setText(f"Error {e}")

    def new_connection(self, conn, addr):
        self.comm.message_received.emit(f"🔌 New connection from {addr}")
        self.refresh_client_list()

    def refresh_client_list(self):
        self.clients_list.clear()
        with self.network.clients_lock:
            for name in self.network.client_names:
                self.clients_list.addItem(name)

    def display_message(self, msg):
        self.chat_display.append(msg)

    def notify_typing(self):
        self.typing_label.setText(f"{self.username} is typing...")
        with self.network.clients_lock:
            for conn in self.network.client_names.values():
                try:
                    conn.send(f"#writing#{self.username}".encode())
                except:
                    pass

    def change_username(self):
        self.username = self.username_input.text()
        with self.network.clients_lock:
            for conn in self.network.client_names.values():
                try:
                    conn.send(f"#usern#{self.username}".encode())
                except:
                    pass

    def send_message(self):
        msg = self.message_input.text().strip()
        self.typing_label.setText("")
        if msg:
            with self.network.clients_lock:
                for conn in self.network.client_names.values():
                    try:
                        conn.send("#nowriting#".encode())
                    except:
                        pass

                clean_msg = (
                    msg.replace("#usern#", "")
                    .replace("#writing#", "")
                    .replace("#nowriting#", "")
                )
                for conn in self.network.client_names.values():
                    conn.send(f"{clean_msg}\n".encode())
            self.chat_display.append(f"{self.username}: {clean_msg}")
            self.message_input.clear()
            if msg.upper() == "STOP":
                self.shutdown_server()

    def kick_client(self):
        selected = self.clients_list.currentItem()
        if not selected:
            return
        target = selected.text()
        with self.network.clients_lock:
            for name, conn in list(self.network.client_names.items()):
                if name == target:
                    self.network.kick_client(name)
                    self.comm.message_received.emit(f"⚠️ Client {target} was kicked.")
                    break
        self.refresh_client_list()

    def shutdown_server(self):
        confirm = QMessageBox.question(
            self,
            "Shut down server",
            "Are you sure you want to shut down the server?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            self.network.shutdown()
            self.close()

    def closeEvent(self, event):
        self.shutdown_server()
        event.accept()