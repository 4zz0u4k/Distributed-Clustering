import socket
import threading
from Data.data_loader import load_data

HOST = '0.0.0.0'
PORT = 5000

active_connections = set()
connections_lock = threading.Lock()

def distribute_data():
    with connections_lock:
        connected_nodes = len(active_connections)
        conns = list(active_connections.items())

    data_chunks = load_data(connected_nodes)
    
    for idx, (addr, conn) in enumerate(conns):
        try:
            chunk = data_chunks[idx]
            conn.sendall(chunk.encode())
            print(f"[>] Sent chunk to {addr}")
        except Exception as e:
            print(f"[!] Error sending to {addr}: {e}")

    
def handle_client(conn, addr):
    with connections_lock:
        active_connections[addr] = conn  # Save socket

    print(f"[+] {addr} connected. Total: {len(active_connections)}")

    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            print(f"[{addr}] Sent: {data.decode()}")
    except ConnectionResetError:
        pass
    finally:
        with connections_lock:
            if addr in active_connections:
                del active_connections[addr]
        print(f"[-] {addr} disconnected. Total: {len(active_connections)}")
        conn.close()

# Input listener to handle diffrent server commands
def input_listener():
    while True:
        cmd = input()
        if cmd.lower() == 'c':
            with connections_lock:
                print(f"[INFO] Active connections: {len(active_connections)}")
        elif cmd.lower() == 's':
            distribute_data()

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
