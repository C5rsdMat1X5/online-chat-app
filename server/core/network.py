import socket
import threading
import re


class ServerNetwork:
    def __init__(self, host="0.0.0.0", port=5000):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)
        self.clients = {}
        self.clients_lock = threading.Lock()

        self.on_message = None
        self.on_typing = None
        self.on_client_disconnect = None

    def set_callbacks(self, on_message, on_typing, on_client_disconnect):
        self.on_message = on_message
        self.on_typing = on_typing
        self.on_client_disconnect = on_client_disconnect

    def start_accepting(self, new_connection_callback):
        def accept_loop():
            while True:
                try:
                    conn, addr = self.server_socket.accept()
                    with self.clients_lock:
                        self.clients[conn] = f"Cliente-{addr[1]}"
                    new_connection_callback(conn, addr)
                    threading.Thread(target=self.listen_peer, args=(conn,), daemon=True).start()
                except Exception:
                    break
        threading.Thread(target=accept_loop, daemon=True).start()

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
                    if self.on_message:
                        self.on_message(f"🗣️ {old} cambió su nombre a {new_name}")

                elif "#writing#" in data:
                    writing = data.replace("#writing#", "")
                    with self.clients_lock:
                        for c in self.clients:
                            c.send(f"#writing#{writing}".encode())
                    if self.on_typing:
                        self.on_typing(f"{writing} está escribiendo...")

                elif "#nowriting#" in data:
                    with self.clients_lock:
                        for c in self.clients:
                            c.send(data.encode())
                    if self.on_typing:
                        self.on_typing("")

                else:
                    try:
                        user = re.search(r"#(.*?)#", data).group(1)
                        msg = re.sub(r"#.*?#", "", data).strip()
                        with self.clients_lock:
                            for c in self.clients:
                                c.send(f"#other#{user}: {msg}".encode())
                        if self.on_message:
                            self.on_message(f"{user}: {msg}")
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
            if self.on_message:
                self.on_message("❌ Un cliente se ha desconectado.")
            if self.on_client_disconnect:
                self.on_client_disconnect()

    def send_to_all(self, message):
        with self.clients_lock:
            for conn in self.clients:
                try:
                    conn.send(message.encode())
                except:
                    pass

    def kick_client(self, conn):
        with self.clients_lock:
            try:
                conn.close()
                if conn in self.clients:
                    del self.clients[conn]
            except:
                pass

    def shutdown(self):
        with self.clients_lock:
            for conn in list(self.clients):
                try:
                    conn.close()
                except:
                    pass
        try:
            self.server_socket.close()
        except:
            pass