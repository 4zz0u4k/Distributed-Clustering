import socket
import threading
import json
import time
from Data.data_loader import load_data
import warnings
from Models.methods import random_clustering
import numpy as np

warnings.filterwarnings("ignore")
HOST = '0.0.0.0'
PORT = 5000
CLUSTERING_TIMEOUT = 60

global data_sent 
data_sent = False
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
    global data_sent
    
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
    
    data_sent = True
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
    print("  'count'   - Show connection count")
    print("  'send'    - Distribute data to all nodes")
    print("  'cluster' - Show clustering options")
    print("  'quit'    - Quit server")
    
    while True:
        cmd = input("Command > ")
        if cmd.lower() == 'count':
            with connections_lock:
                nodes = len(active_connections)
                print(f"[INFO] Active connections: {nodes}")
                for addr in active_connections:
                    print(f"    - {addr}")
        elif cmd.lower() == 'send':
            distribute_data()
        elif cmd.lower() == 'cluster':
            if data_sent:
                show_clustering_menu()
            else:
                print("Must send data before clustering")
        elif cmd.lower() == 'quit':
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

def show_clustering_menu():
    print("\n[*] Clustering options:")
    print("  1. Purely random (default)")
    print("  0. Back to main menu")
    
    choice = input("Select option > ")
    clusters = cluster(choice)

def cluster(choice):
    k = input("[>] Enter K : ")
    k = int(k)
    if k <= 0:
        print("[!] K must be a positive integer")
        return
    if choice == '1':
        pure_random_clustering(k)
    elif choice == '0':
        return
    else:
        print("[!] Invalid option")

def pure_random_clustering(k):
    """Execute distributed random clustering using connected nodes"""
    try:
            
        with connections_lock:
            if len(active_connections) == 0:
                print("[!] No connected nodes to perform clustering")
                return
            node_conns = list(active_connections.items())
        
        print(f"[*] Initiating random clustering with K={k} across {len(node_conns)} nodes...")
        
        # Send command to all nodes to perform random clustering
        cluster_command = {
            "method": "random_clustering",
            "k": k
        }
        
        # Track nodes that successfully received the command
        active_nodes = []
        for addr, conn in node_conns:
            try:
                if send_message(conn, MSG_TYPE_COMMAND, cluster_command):
                    active_nodes.append((addr, conn))
                    print(f"[>] Sent clustering command to {addr}")
            except Exception as e:
                print(f"[!] Failed to send command to {addr}: {e}")
        
        if not active_nodes:
            print("[!] No nodes received clustering command")
            return
            
        # Collect sub-cluster centers from nodes
        print(f"[*] Waiting for results from {len(active_nodes)} nodes...")
        sub_clusters = []
        
        for addr, conn in active_nodes:
            try:
                # Wait for response with timeout
                start_time = time.time()
                while time.time() - start_time < CLUSTERING_TIMEOUT:  # 60-second timeout
                    message = receive_message(conn)
                    if not message:
                        print(f"[!] Lost connection to {addr}")
                        break
                        
                    if message.get('type') == MSG_TYPE_DATA and "cluster_centers" in message.get('content', {}):
                        centers_data = message.get('content')
                        centers = np.array(centers_data["cluster_centers"])
                        print(f"[✓] Received {len(centers)} centers from {addr}")
                        sub_clusters.append(centers)
                        break
            except Exception as e:
                print(f"[!] Error receiving centers from {addr}: {e}")
        
        if not sub_clusters:
            print("[!] No sub-clusters received from nodes")
            return
            
        # Combine sub-clusters using the random_clustering method
        print(f"[*] Combining {sum(len(sc) for sc in sub_clusters)} centers from {len(sub_clusters)} nodes...")
        final_clusters = random_clustering(sub_clusters, k)
        
        print(f"[✓] Clustering complete! Final cluster count: {len(final_clusters)}")
        print(f"[*] Final cluster centers:")
        for i, center in enumerate(final_clusters):
            print(f"  Cluster {i+1}: {center}")
            
        # Notify nodes of completion
        for addr, conn in active_nodes:
            try:
                send_message(conn, MSG_TYPE_INFO, "Clustering complete")
            except:
                pass
                
        return final_clusters
        
    except ValueError:
        print("[!] Invalid K value - must be an integer")
    except Exception as e:
        print(f"[!] Error in clustering process: {e}")
        return None

    
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