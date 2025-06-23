import socket
import threading

def connect_to_server(ip, port=5000):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip, port))
    return s

def send_message(sock, message):
    try:
        sock.send(message.encode("utf-8"))
    except Exception as e:
        print(f"Error enviando mensaje: {e}")

def start_listening(sock, on_message_callback):
    def listen():
        while True:
            try:
                data = sock.recv(1024).decode("utf-8")
                if not data:
                    break
                on_message_callback(data)
            except Exception as e:
                print(f"Error en recepción: {e}")
                break
    thread = threading.Thread(target=listen, daemon=True)
    thread.start()
    return thread

def close_connection(sock):
    try:
        sock.close()
    except:
        pass