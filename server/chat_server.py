import sys
import socket
import threading
import os
import re
import psutil
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QLineEdit,
    QPushButton,
    QLabel,
    QListWidget,
    QMessageBox,
)
from PySide6.QtCore import Signal, QObject, QTimer

os.environ["QT_LOGGING_RULES"] = "qt.gui.icc=false"


class Communicator(QObject):
    message_received = Signal(str)


class ChatServer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Centro de Control del Servidor de Chat")
        self.setGeometry(100, 100, 700, 400)

        self.username = "Servidor"
        self.clients = {}
        self.clients_lock = threading.Lock()

        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

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

        self.setStyleSheet("""
        QWidget { background-color: #1e1e1e; color: #f0f0f0; font-family: "Arial", "Ubuntu", sans-serif; font-size: 14px; }
        QLabel { color: #f0f0f0; font-weight: bold; }
        QTextEdit, QLineEdit, QListWidget {
            background-color: #2a2a2a; color: #f0f0f0;
            border: 1px solid #444; border-radius: 5px; padding: 6px;
        }
        QPushButton {
            background-color: #3a9ff5; color: white;
            border: none; border-radius: 4px; padding: 6px; font-weight: bold;
        }
        QPushButton:hover { background-color: #61afef; }
        QPushButton:pressed { background-color: #1f71c2; }
        QPushButton#shutdown_btn, QPushButton#kick_btn { background-color: #e06c75; }
        QPushButton#shutdown_btn:hover, QPushButton#kick_btn:hover { background-color: #be4c56; }
        QPushButton#username_btn { background-color: #98c379; }
        QPushButton#username_btn:hover { background-color: #7fbf5e; }
        QScrollBar:vertical {
            border: none; background: transparent; width: 10px; margin: 4px 0;
        }
        QScrollBar::handle:vertical {
            background: #3a9ff5; min-height: 20px; border-radius: 2px;
        }
        QScrollBar::handle:vertical:hover { background: #61afef; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0; background: none; border: none;
        }
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
        """)

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(("0.0.0.0", 5000))
        self.server_socket.listen(5)
        self.chat_display.append("Servidor escuchando conexiones entrantes...")

        self.comm = Communicator()
        self.comm.message_received.connect(self.display_message)

        self.accept_thread = threading.Thread(
            target=self.accept_connections, daemon=True
        )
        self.accept_thread.start()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(2000)

    def update_stats(self):
        cpu = psutil.cpu_percent()
        with self.clients_lock:
            active = len(self.clients)
        self.info_label.setText(f"Clientes activos: {active}\nUso de CPU: {cpu:.1f}%")

    def accept_connections(self):
        while True:
            try:
                conn, addr = self.server_socket.accept()
                with self.clients_lock:
                    self.clients[conn] = f"Cliente-{addr[1]}"
                self.clients_list.addItem(f"{addr[0]}:{addr[1]}")
                self.comm.message_received.emit(f"🔌 Nueva conexión desde {addr}")
                threading.Thread(
                    target=self.listen_peer, args=(conn,), daemon=True
                ).start()
            except:
                break

    def notify_typing(self):
        self.typing_label.setText(f"{self.username} está escribiendo...")
        with self.clients_lock:
            for conn in self.clients:
                try:
                    conn.send(f"#writing#{self.username}".encode())
                except:
                    pass

    def change_username(self):
        self.username = self.username_input.text()
        with self.clients_lock:
            for conn in self.clients:
                try:
                    conn.send(f"#usern#{self.username}".encode())
                except:
                    pass

    def send_message(self):
        msg = self.message_input.text().strip()
        self.typing_label.setText("")
        if msg:
            with self.clients_lock:
                for conn in self.clients:
                    try:
                        conn.send("#nowriting#".encode())
                    except:
                        pass

                clean_msg = (
                    msg.replace("#usern#", "")
                    .replace("#writing#", "")
                    .replace("#nowriting#", "")
                )
                for conn in self.clients:
                    conn.send(f"{clean_msg}\n".encode())
            self.chat_display.append(f"{self.username}: {clean_msg}")
            self.message_input.clear()
            if msg.upper() == "STOP":
                self.shutdown_server()

    def listen_peer(self, conn):
        try:
            while True:
                data = conn.recv(1024).decode()
                if not data:
                    break
                if "#usern#" in data:
                    new_name = data.replace("#usern#", "")
                    with self.clients_lock:
                        old = self.clients.get(conn, "Desconocido")
                        self.clients[conn] = new_name
                        for c in self.clients:
                            c.send(f"🗣️ {old} cambió su nombre a {new_name}".encode())
                    self.comm.message_received.emit(
                        f"🗣️ {old} cambió su nombre a {new_name}"
                    )
                elif "#writing#" in data:
                    writing = data.replace("#writing#", "")
                    with self.clients_lock:
                        for c in self.clients:
                            c.send(f"#writing#{writing}".encode())
                    self.typing_label.setText(f"{writing} está escribiendo...")
                elif "#nowriting#" in data:
                    with self.clients_lock:
                        for c in self.clients:
                            c.send(data.encode())
                    self.typing_label.setText("")
                else:
                    try:
                        user = re.search(r"#(.*?)#", data).group(1)
                        msg = re.sub(r"#.*?#", "", data).strip()
                        with self.clients_lock:
                            for c in self.clients:
                                c.send(f"#other#{user}: {msg}".encode())
                        self.comm.message_received.emit(f"{user}: {msg}")
                    except AttributeError:
                        continue
                if data.strip().upper().endswith("STOP"):
                    break
        except Exception as e:
            print(f"Error en listen_peer: {e}")
        finally:
            with self.clients_lock:
                if conn in self.clients:
                    del self.clients[conn]
            conn.close()
            self.comm.message_received.emit("❌ Un cliente se ha desconectado.")
            self.refresh_client_list()

    def refresh_client_list(self):
        self.clients_list.clear()
        with self.clients_lock:
            for conn in self.clients:
                try:
                    ip, port = conn.getpeername()
                    self.clients_list.addItem(f"{ip}:{port}")
                except:
                    continue

    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            self.ip_label.setText(f"IP del servidor: {ip}")
        except Exception as e:
            self.ip_label.setText(f"Error {e}")

    def kick_client(self):
        selected = self.clients_list.currentItem()
        if not selected:
            return
        target = selected.text()
        with self.clients_lock:
            for conn in list(self.clients):
                try:
                    ip, port = conn.getpeername()
                    if f"{ip}:{port}" == target:
                        conn.close()
                        del self.clients[conn]
                        self.comm.message_received.emit(
                            f"⚠️ Cliente {target} fue expulsado."
                        )
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
            with self.clients_lock:
                for conn in list(self.clients):
                    try:
                        conn.close()
                    except:
                        pass
            self.server_socket.close()
            self.close()

    def display_message(self, msg):
        self.chat_display.append(msg)

    def closeEvent(self, event):
        self.shutdown_server()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    server_ui = ChatServer()
    server_ui.show()
    sys.exit(app.exec())
