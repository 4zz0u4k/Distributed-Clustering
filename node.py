import socket
import pandas as pd

SERVER_IP = '192.168.137.1' 
PORT = 5000

client_name = input("Your name : ")

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((SERVER_IP, PORT))

client_socket.sendall(f"{client_name} : Am ready".encode())

try:
    full_data = b""  # To collect all incoming chunks
    while True:
        data = client_socket.recv(4096)
        if not data:
            break
        full_data += data  # Append each chunk

    # Once all data is received
    json_str = full_data.decode()
    df = pd.read_json(json_str, orient='split')
    print(f"\n[✓] Received DataFrame with shape {df.shape}")
    print(df.head())
finally:
    client_socket.close()