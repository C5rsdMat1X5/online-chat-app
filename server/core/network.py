import socket
import threading
import re


class ChatServer:
    def __init__(self, host="0.0.0.0", port=5000):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)
        self.client_names = {}
        self.clients_lock = threading.Lock()

        self.on_message = None
        self.on_typing = None
        self.on_client_disconnect = None

    def set_callbacks(self, on_message, on_typing, on_client_disconnect):
        self.on_message = on_message
        self.on_typing = on_typing
        self.on_client_disconnect = on_client_disconnect

    def start_listening(self, on_new_connection):
        def accept_loop():
            while True:
                try:
                    client_socket, addr = self.server_socket.accept()
                    with self.clients_lock:
                        self.client_names[client_socket] = f"Cliente-{addr[1]}"
                    on_new_connection(client_socket, addr)
                    threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()
                except Exception:
                    break
        threading.Thread(target=accept_loop, daemon=True).start()

    def handle_client(self, client_socket):
        try:
            while True:
                data = client_socket.recv(1024).decode()
                if not data:
                    break

                if "#usern#" in data:
                    new_name = data.replace("#usern#", "")
                    with self.clients_lock:
                        old = self.client_names.get(client_socket, "Unknown")
                        self.client_names[client_socket] = new_name
                        for c in self.client_names:
                            c.send(f"🗣️ {old} changed their name to {new_name}".encode())
                    if self.on_message:
                        self.on_message(f"🗣️ {old} changed their name to {new_name}")

                elif "#writing#" in data:
                    writing = data.replace("#writing#", "")
                    with self.clients_lock:
                        for c in self.client_names:
                            c.send(f"#writing#{writing}".encode())
                    if self.on_typing:
                        self.on_typing(f"{writing} is typing...")

                elif "#nowriting#" in data:
                    with self.clients_lock:
                        for c in self.client_names:
                            c.send(data.encode())
                    if self.on_typing:
                        self.on_typing("")

                else:
                    try:
                        user = re.search(r"#(.*?)#", data).group(1)
                        msg = re.sub(r"#.*?#", "", data).strip()
                        with self.clients_lock:
                            for c in self.client_names:
                                c.send(f"#other#{user}: {msg}".encode())
                        if self.on_message:
                            self.on_message(f"{user}: {msg}")
                    except AttributeError:
                        continue

                if data.strip().upper().endswith("STOP"):
                    break

        except Exception as e:
            print(f"Error in handle_client: {e}")
        finally:
            with self.clients_lock:
                if client_socket in self.client_names:
                    del self.client_names[client_socket]
            client_socket.close()
            if self.on_message:
                self.on_message("❌ A client has disconnected.")
            if self.on_client_disconnect:
                self.on_client_disconnect()

    def send_to_all(self, message):
        with self.clients_lock:
            for client_socket in self.client_names:
                try:
                    client_socket.send(message.encode())
                except:
                    pass

    def kick_client(self, client_socket):
        with self.clients_lock:
            try:
                client_socket.close()
                if client_socket in self.client_names:
                    del self.client_names[client_socket]
            except:
                pass

    def shutdown(self):
        with self.clients_lock:
            for client_socket in list(self.client_names):
                try:
                    client_socket.close()
                except:
                    pass
        try:
            self.server_socket.close()
        except:
            pass