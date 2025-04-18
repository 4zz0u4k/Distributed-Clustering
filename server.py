import socket
import threading

HOST = '0.0.0.0'
PORT = 5000

active_connections = set()
connections_lock = threading.Lock()

def handle_client(conn, addr):
    with connections_lock:
        active_connections.add(addr)
    print(f"[+] {addr} connected. Total: {len(active_connections)}")

    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break  # Client disconnected
            print(f"[{addr}] Sent: {data.decode()}")
    except ConnectionResetError:
        pass
    finally:
        with connections_lock:
            active_connections.discard(addr)
        print(f"[-] {addr} disconnected. Total: {len(active_connections)}")
        conn.close()

def input_listener():
    while True:
        cmd = input()
        if cmd.lower() == 'c':
            with connections_lock:
                print(f"[INFO] Active connections: {len(active_connections)}")

# Start input listener in background
threading.Thread(target=input_listener, daemon=True).start()

# Start server
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(5)

print(f"[*] Server listening on {HOST}:{PORT}")

while True:
    conn, addr = server_socket.accept()
    thread = threading.Thread(target=handle_client, args=(conn, addr))
    thread.start()
