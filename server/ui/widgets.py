from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QLabel, QListWidget, QMessageBox
)
from PySide6.QtCore import Signal, QObject, QTimer
from utils.styles import custom_css
from core.network import ServerNetwork
import socket

class Communicator(QObject):
    message_received = Signal(str)

class ChatServerUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Centro de Control del Servidor de Chat")
        self.setGeometry(100, 100, 700, 400)

        self.username = "Servidor"
        self.comm = Communicator()
        self.comm.message_received.connect(self.display_message)

        self.network = ServerNetwork()
        self.network.start_accepting(self.new_connection)

        # UI Setup
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # Left layout
        left_layout = QVBoxLayout()
        self.chat_display = QTextEdit(readOnly=True)
        self.username_input = QLineEdit(placeholderText="Nombre del servidor")
        self.username_input.returnPressed.connect(self.change_username)
        self.username_btn = QPushButton("Actualizar nombre")
        self.username_btn.clicked.connect(self.change_username)

        self.typing_label = QLabel("")
        self.message_input = QLineEdit(placeholderText="Escribe un mensaje...")
        self.message_input.textEdited.connect(self.notify_typing)
        self.message_input.returnPressed.connect(self.send_message)

        self.send_btn = QPushButton("Enviar")
        self.send_btn.clicked.connect(self.send_message)

        left_layout.addWidget(QLabel("Chat activo:"))
        left_layout.addWidget(self.chat_display)
        left_layout.addWidget(self.typing_label)
        left_layout.addWidget(self.username_input)
        left_layout.addWidget(self.username_btn)
        left_layout.addWidget(self.message_input)
        left_layout.addWidget(self.send_btn)

        # Right layout
        right_layout = QVBoxLayout()
        self.clients_list = QListWidget()
        self.kick_btn = QPushButton("Expulsar cliente seleccionado")
        self.kick_btn.clicked.connect(self.kick_client)

        self.shutdown_btn = QPushButton("Cerrar servidor")
        self.shutdown_btn.clicked.connect(self.shutdown_server)

        self.info_label = QLabel("Clientes activos: 0\nUso de CPU: -")
        self.info_label.setStyleSheet("font-size: 12px;")
        self.ip_label = QLabel("IP del servidor:")
        self.ip_btn = QPushButton("Mostrar IP local")
        self.ip_btn.clicked.connect(self.get_local_ip)

        right_layout.addWidget(self.ip_label)
        right_layout.addWidget(self.ip_btn)
        right_layout.addWidget(QLabel("Clientes conectados:"))
        right_layout.addWidget(self.clients_list)
        right_layout.addWidget(self.kick_btn)
        right_layout.addStretch()
        right_layout.addWidget(QLabel("Estado del servidor:"))
        right_layout.addWidget(self.info_label)
        right_layout.addWidget(self.shutdown_btn)

        main_layout.addLayout(left_layout, 3)
        main_layout.addLayout(right_layout, 1)

        self.setStyleSheet(custom_css())
        
        self.network.set_callbacks(
            on_message=self.comm.message_received.emit,
            on_typing=self.typing_label.setText,
            on_client_disconnect=self.refresh_client_list
        )

        # Timer to update stats
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(2000)

    def update_stats(self):
        import psutil
        cpu = psutil.cpu_percent()
        with self.network.clients_lock:
            active = len(self.network.clients)
        self.info_label.setText(f"Clientes activos: {active}\nUso de CPU: {cpu:.1f}%")

    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            self.ip_label.setText(f"IP del servidor: {ip}")
        except Exception as e:
            self.ip_label.setText(f"Error {e}")

    def new_connection(self, conn, addr):
        self.comm.message_received.emit(f"🔌 Nueva conexión desde {addr}")
        self.refresh_client_list()

    def refresh_client_list(self):
        self.clients_list.clear()
        with self.network.clients_lock:
            for conn in self.network.clients:
                try:
                    ip, port = conn.getpeername()
                    self.clients_list.addItem(f"{ip}:{port}")
                except:
                    continue

    def display_message(self, msg):
        self.chat_display.append(msg)

    def notify_typing(self):
        self.typing_label.setText(f"{self.username} está escribiendo...")
        with self.network.clients_lock:
            for conn in self.network.clients:
                try:
                    conn.send(f"#writing#{self.username}".encode())
                except:
                    pass

    def change_username(self):
        self.username = self.username_input.text()
        with self.network.clients_lock:
            for conn in self.network.clients:
                try:
                    conn.send(f"#usern#{self.username}".encode())
                except:
                    pass

    def send_message(self):
        msg = self.message_input.text().strip()
        self.typing_label.setText("")
        if msg:
            with self.network.clients_lock:
                for conn in self.network.clients:
                    try:
                        conn.send("#nowriting#".encode())
                    except:
                        pass

                clean_msg = (
                    msg.replace("#usern#", "")
                    .replace("#writing#", "")
                    .replace("#nowriting#", "")
                )
                for conn in self.network.clients:
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
            for conn in list(self.network.clients):
                try:
                    ip, port = conn.getpeername()
                    if f"{ip}:{port}" == target:
                        self.network.kick_client(conn)
                        self.comm.message_received.emit(f"⚠️ Cliente {target} fue expulsado.")
                        break
                except:
                    continue
        self.refresh_client_list()

    def shutdown_server(self):
        confirm = QMessageBox.question(
            self,
            "Cerrar servidor",
            "¿Seguro que deseas apagar el servidor?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            self.network.shutdown()
            self.close()

    def closeEvent(self, event):
        self.shutdown_server()
        event.accept()