import socket
import threading

def create_connection(ip, port=5000):
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((ip, port))
    conn.timeout(3)
    return conn

def send_data(connection, message):
    try:
        connection.send(message.encode("utf-8"))
    except Exception as e:
        print(f"Error sending message: {e}")

def start_receiving(connection, message_handler):
    def listen():
        while True:
            try:
                data = connection.recv(1024).decode("utf-8")
                if not data:
                    break
                message_handler(data)
            except Exception as e:
                print(f"Error receiving data: {e}")
                break
    thread = threading.Thread(target=listen, daemon=True)
    thread.start()
    return thread

def close_connection(connection):
    try:
        connection.close()
    except:
        pass