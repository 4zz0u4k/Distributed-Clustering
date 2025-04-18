import socket
import threading

HOST = '0.0.0.0'  # Listen on all interfaces
PORT = 5000       # Any free port

def handle_client(conn, addr):
    print(f"[+] Connected: {addr}")
    data = conn.recv(1024).decode()
    print(f"[{addr}] Sent data: {data}")
    conn.close()

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(5)

print(f"[*] Server listening on {HOST}:{PORT}")

while True:
    conn, addr = server_socket.accept()
    thread = threading.Thread(target=handle_client, args=(conn, addr))
    thread.start()
