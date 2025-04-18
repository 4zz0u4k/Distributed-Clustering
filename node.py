import socket

SERVER_IP = '192.168.137.1' 
PORT = 5000

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((SERVER_IP, PORT))

# Optional: initial message to say hello
client_socket.sendall("ready".encode())

try:
    while True:
        data = client_socket.recv(1024)
        if not data:
            break
        print(f"[SERVER] Sent: {data.decode()}")
finally:
    client_socket.close()
