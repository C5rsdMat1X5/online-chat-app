# 🗨️ Online Chat App

A clean and simple **client-server chat application** built in Python using sockets and PySide6 GUI. Supports multiple users chatting in real-time with username changes, typing indicators, and server-side client management.

---

## 🚀 Features

- 💬 Multi-client chat with real-time messaging  
- 🆔 Dynamic username management (change your nickname anytime)  
- ⌨️ Typing notifications to see who’s typing  
- 🔒 Server controls to kick clients and monitor connections  
- 🖥️ GUI built with PySide6 for both client and server  
- 🌍 Cross-platform support (macOS, Windows, Linux)  
- 🧵 Thread-safe client handling using threads and locks  

---

## 📂 Project Structure

online-chat-app/
├── client/               # Client-side code and UI
│   ├── core/             # Networking functions (create_connection, send_data, start_receiving)
│   ├── ui/               # Client GUI (ChatClient, ServerConnectionDialog)
│   └── main.py           # Client app entry point
├── server/               # Server-side code and UI
│   ├── core/             # Server networking (ChatServer class)
│   ├── ui/               # Server GUI (ChatServerControlPanel)
│   └── main.py           # Server app entry point
├── utils/                # Shared utilities (e.g., load_custom_css for styles)
└── README.md             # This README file

---

## ⚙️ Requirements

- Python 3.8 or higher  
- PySide6  
- psutil (for server CPU monitoring)  

---

## 🛠️ Installation

1. Clone the repo:

   ```bash
   git clone https://github.com/yourusername/online-chat-app.git
   cd online-chat-app
   ```

2. (Optional) Create and activate a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate      # macOS/Linux
   venv\Scripts\activate         # Windows
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

   If no requirements.txt is provided:

   ```bash
   pip install PySide6 psutil
   ```

---

▶️ Running the Server

```bash
python server/main.py
```

- Starts the ChatServerControlPanel GUI.
- Shows connected clients, CPU usage, and lets you kick clients or shut down the server.

---

▶️ Running the Client

```bash
python client/main.py
```

- Opens the ServerConnectionDialog window to input the server IP.
- After connecting, opens the ChatClient GUI for chatting, username changes, and typing notifications.

---

🔍 How It Works

- The ChatServer runs a multi-threaded TCP socket server managing multiple clients with threads and locks.
- Clients communicate with the server using TCP sockets, sending messages with special prefixes (e.g., #usern# for username changes, #writing# for typing indicators).
- The GUIs update in real-time to show messages, typing status, and client connection state.
- Server can kick clients and safely handle disconnects.

---

🤝 Contributing

Contributions are welcome! Please follow Python best practices, keep UI consistent, and add tests when possible.

---

📄 License

MIT License — see the LICENSE file for details.

---