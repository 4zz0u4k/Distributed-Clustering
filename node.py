import socket

SERVER_IP = '192.168.137.1' 
PORT = 5000

data_to_send = "cluster_result: [1, 0, 0, 1, 2]"

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((SERVER_IP, PORT))
client_socket.sendall(data_to_send.encode())
client_socket.close()
