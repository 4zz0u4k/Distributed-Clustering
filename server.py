import socket
import threading
import json
import time
from Data.data_loader import load_data
import warnings

warnings.filterwarnings("ignore")
HOST = '0.0.0.0'
PORT = 5000

active_connections = {}
connections_lock = threading.Lock()

# Message types for protocol
MSG_TYPE_DATA = "DATA"
MSG_TYPE_COMMAND = "CMD"
MSG_TYPE_ACK = "ACK"
MSG_TYPE_INFO = "INFO"

def send_message(conn, msg_type, content):
    """Send a message with proper framing and protocol"""
    message = {
        "type": msg_type,
        "content": content,
        "timestamp": time.time()
    }
    
    # Serialize and add length prefix for proper framing
    serialized = json.dumps(message).encode()
    length_prefix = len(serialized).to_bytes(4, byteorder='big')
    
    try:
        conn.sendall(length_prefix + serialized)
        return True
    except Exception as e:
        print(f"[!] Error sending message: {e}")
        return False

def receive_message(conn):
    """Receive a message with proper framing"""
    try:
        # Get message length
        length_bytes = conn.recv(4)
        if not length_bytes:
            return None
            
        msg_length = int.from_bytes(length_bytes, byteorder='big')
        
        # Get message content in chunks
        chunks = []
        bytes_received = 0
        while bytes_received < msg_length:
            chunk = conn.recv(min(4096, msg_length - bytes_received))
            if not chunk:
                return None
            chunks.append(chunk)
            bytes_received += len(chunk)
            
        message_data = b''.join(chunks)
        return json.loads(message_data.decode())
    except Exception as e:
        print(f"[!] Error receiving message: {e}")
        return None

def distribute_data():
    """Distribute data chunks to all connected nodes"""
    with connections_lock:
        connected_nodes = len(active_connections)
        conns = list(active_connections.items())
    
    if connected_nodes == 0:
        print("[!] No nodes connected")
        return
        
    print(f"[*] Loading data for {connected_nodes} nodes...")
    data_chunks = load_data(connected_nodes)
    
    success_count = 0
    for idx, (addr, conn) in enumerate(conns):
        try:
            chunk_json = data_chunks[idx].to_json(orient='split')
            if send_message(conn, MSG_TYPE_DATA, chunk_json):
                success_count += 1
                print(f"[>] Sent chunk {idx+1}/{connected_nodes} to {addr}")
        except Exception as e:
            print(f"[!] Error sending to {addr}: {e}")
    
    print(f"[*] Data distribution complete: {success_count}/{connected_nodes} successful")

def handle_client(conn, addr):
    """Handle client connection and messages"""
    client_name = "Unknown"
    
    with connections_lock:
        active_connections[addr] = conn
    
    print(f"[+] New connection from {addr}")
    
    try:
        while True:
            message = receive_message(conn)
            if not message:
                break
                
            msg_type = message.get('type')
            content = message.get('content')
            
            if msg_type == MSG_TYPE_INFO and "connected" in content:
                client_name = content.split(" is connected")[0]
                print(f"[+] {client_name} ({addr}) connected")
                send_message(conn, MSG_TYPE_INFO, f"Welcome {client_name}, connected to data distribution server")
                
            elif msg_type == MSG_TYPE_ACK:
                print(f"[✓] {client_name} ({addr}) acknowledged: {content}")
                
            else:
                print(f"[?] Message from {client_name} ({addr}): {content}")
                
    except ConnectionResetError:
        print(f"[!] Connection reset by {client_name} ({addr})")
    except Exception as e:
        print(f"[!] Error handling {client_name} ({addr}): {e}")
    finally:
        with connections_lock:
            if addr in active_connections:
                del active_connections[addr]
        print(f"[-] {client_name} ({addr}) disconnected")
        conn.close()

# Input listener to handle different server commands
def input_listener():
    print("[*] Server commands:")
    print("  'c' - Show connection count")
    print("  's' - Distribute data to all nodes")
    print("  'q' - Quit server")
    
    while True:
        cmd = input("Command > ")
        if cmd.lower() == 'c':
            with connections_lock:
                nodes = len(active_connections)
                print(f"[INFO] Active connections: {nodes}")
                for addr in active_connections:
                    print(f"    - {addr}")
        elif cmd.lower() == 's':
            distribute_data()
        elif cmd.lower() == 'q':
            print("[*] Shutting down server...")
            # Notify all clients before shutdown
            with connections_lock:
                for addr, conn in active_connections.items():
                    try:
                        send_message(conn, MSG_TYPE_COMMAND, "shutdown")
                    except:
                        pass
            break
        else:
            print("[!] Unknown command")

def start_server():
    """Initialize and start the server"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Allow reuse of address
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen(10)
        print(f"[*] Server started at {HOST}:{PORT}")
        
        # Start command handler thread
        cmd_thread = threading.Thread(target=input_listener, daemon=True)
        cmd_thread.start()
        
        # Accept incoming connections
        while True:
            conn, addr = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.daemon = True
            client_thread.start()
            
    except KeyboardInterrupt:
        print("[*] Server shutting down...")
    except Exception as e:
        print(f"[!] Server error: {e}")
    finally:
        server_socket.close()

if __name__ == "__main__":
    start_server()