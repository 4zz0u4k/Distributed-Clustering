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

# Custom JSON encoder to handle NumPy arrays
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()  # Convert NumPy arrays to lists
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        return json.JSONEncoder.default(self, obj)

def send_message(conn, msg_type, content):
    """Send a message with proper framing and protocol"""
    message = {
        "type": msg_type,
        "content": content,
        "timestamp": time.time()
    }
    
    # Serialize and add length prefix for proper framing
    serialized = json.dumps(message, cls=NumpyEncoder).encode()  # Use custom encoder
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
            
        # Collect sub-cluster centers from nodes with improved timeout and debugging
        print(f"[*] Waiting for results from {len(active_nodes)} nodes...")
        sub_clusters = []
        responses_received = 0
        
        # Use non-blocking approach with overall timeout
        overall_start_time = time.time()
        remaining_nodes = active_nodes.copy()
        
        while remaining_nodes and (time.time() - overall_start_time < CLUSTERING_TIMEOUT):
            # Check each node without blocking for too long
            for i, (addr, conn) in enumerate(remaining_nodes[:]):  # Create a copy to allow removal during iteration
                try:
                    # Non-blocking check for response
                    conn.settimeout(60.0)  # Increase timeout to 3 seconds for each check
                    message = receive_message(conn)
                    
                    if message:
                        print(f"[D] Received message from {addr}: {message.get('type')}")
                        
                        if message.get('type') == MSG_TYPE_DATA:
                            content = message.get('content', {})
                            if isinstance(content, dict) and "cluster_centers" in content:
                                centers_data = content
                                # Convert to numpy array and ensure proper shape
                                centers = np.array(centers_data["cluster_centers"])
                                if len(centers.shape) == 1:  # Ensure 2D array
                                    centers = centers.reshape(1, -1)
                                print(f"[✓] Received {len(centers)} centers from {addr}")
                                sub_clusters.append(centers)
                                responses_received += 1
                                # Remove from remaining nodes as we got a response
                                remaining_nodes.remove((addr, conn))
                                # Send acknowledgment
                                send_message(conn, MSG_TYPE_ACK, "Cluster centers received")
                            else:
                                print(f"[!] Received DATA message from {addr} but missing 'cluster_centers' or invalid format")
                        elif message.get('type') == MSG_TYPE_ACK:
                            print(f"[i] ACK from {addr}: {message.get('content')}")
                            
                except socket.timeout:
                    # Expected timeout, just continue to the next node
                    pass
                except Exception as e:
                    print(f"[!] Error receiving from {addr}: {e}")
                    # Remove problematic nodes
                    if (addr, conn) in remaining_nodes:
                        remaining_nodes.remove((addr, conn))
            
            # Short sleep to prevent CPU overuse
            time.sleep(0.1)
            
            # Print status update every 5 seconds
            elapsed = time.time() - overall_start_time
            if int(elapsed) % 5 == 0 and int(elapsed) > 0:
                print(f"[*] Still waiting... ({responses_received}/{len(active_nodes)} responses, {int(elapsed)}s elapsed)")
        
        # Reset socket timeout to blocking for future operations
        for addr, conn in active_nodes:
            try:
                conn.settimeout(None)
            except Exception as e:
                print(f"[!] Error resetting timeout for {addr}: {e}")
        
        if not sub_clusters:
            print("[!] No sub-clusters received from nodes")
            if remaining_nodes:
                print(f"[!] {len(remaining_nodes)} nodes did not respond in time")
            return
            
        # Combine sub-clusters using the random_clustering method
        print(f"[*] Combining {sum(len(sc) for sc in sub_clusters)} centers from {len(sub_clusters)} nodes...")
        
        try:
            final_clusters = random_clustering(sub_clusters, k)
            
            if final_clusters is None or len(final_clusters) == 0:
                print("[!] Clustering failed to produce valid clusters")
                return
                
            print(f"[✓] Clustering complete! Final cluster count: {len(final_clusters)}")
            print(f"[*] Final cluster centers:")
            for i, center in enumerate(final_clusters):
                print(f"  Cluster {i+1}: {center}")
                
            # Notify nodes of completion
            for addr, conn in active_nodes:
                try:
                    # Use an INFO message instead of another command
                    send_message(conn, MSG_TYPE_INFO, "Clustering complete")
                except Exception as e:
                    print(f"[!] Error notifying {addr} of completion: {e}")
                    
            return final_clusters
        except Exception as e:
            print(f"[!] Error combining cluster centers: {e}")
            import traceback
            traceback.print_exc()
            return None
            
    except ValueError as ve:
        print(f"[!] Invalid K value - must be an integer: {ve}")
    except Exception as e:
        print(f"[!] Error in clustering process: {e}")
        import traceback
        traceback.print_exc()  # Print full stack trace for better debugging
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