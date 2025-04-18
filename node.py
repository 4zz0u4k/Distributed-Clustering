import socket
import threading
import json
import time
import pandas as pd
import sys
import signal

# Server connection settings
SERVER_IP = '192.168.137.1'
PORT = 5000

# Message types for protocol
MSG_TYPE_DATA = "DATA"
MSG_TYPE_COMMAND = "CMD"
MSG_TYPE_ACK = "ACK"
MSG_TYPE_INFO = "INFO"

# Global variables
data_received = False
keep_running = True
received_data = None

def signal_handler(sig, frame):
    """Handle Ctrl+C to gracefully exit"""
    global keep_running
    print("\n[*] Shutting down client...")
    keep_running = False
    sys.exit(0)

def send_message(sock, msg_type, content):
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
        sock.sendall(length_prefix + serialized)
        return True
    except Exception as e:
        print(f"[!] Error sending message: {e}")
        return False

def receive_message(sock):
    """Receive a message with proper framing"""
    try:
        # Get message length
        length_bytes = sock.recv(4)
        if not length_bytes:
            return None
            
        msg_length = int.from_bytes(length_bytes, byteorder='big')
        
        # Get message content in chunks
        chunks = []
        bytes_received = 0
        while bytes_received < msg_length:
            chunk = sock.recv(min(4096, msg_length - bytes_received))
            if not chunk:
                return None
            chunks.append(chunk)
            bytes_received += len(chunk)
            
        message_data = b''.join(chunks)
        return json.loads(message_data.decode())
    except Exception as e:
        print(f"[!] Error receiving message: {e}")
        return None

def process_data_chunk(data_json):
    """Process received data chunk"""
    global data_received, received_data
    
    try:
        df = pd.read_json(data_json, orient='split')
        print(f"\n[✓] Received DataFrame with shape {df.shape}")
        print(df.head())
        
        # Store the data
        data_received = True
        received_data = df
        return True
    except Exception as e:
        print(f"[!] Error processing data: {e}")
        return False

def handle_server_messages(sock):
    """Handle incoming messages from the server"""
    global keep_running
    
    while keep_running:
        try:
            message = receive_message(sock)
            if not message:
                print("[!] Connection to server lost")
                keep_running = False
                break
                
            msg_type = message.get('type')
            content = message.get('content')
            
            if msg_type == MSG_TYPE_DATA:
                print("[*] Receiving data from server...")
                if process_data_chunk(content):
                    # Acknowledge receipt
                    send_message(sock, MSG_TYPE_ACK, "Data received successfully")
                    print("[*] Data processing complete")
                
            elif msg_type == MSG_TYPE_COMMAND:
                if content == "shutdown":
                    print("[!] Server is shutting down")
                    keep_running = False
                    break
                
            elif msg_type == MSG_TYPE_INFO:
                print(f"[i] Server: {content}")
                
        except Exception as e:
            print(f"[!] Error: {e}")
            keep_running = False
            break

def input_commands(sock):
    """Handle user input for commands"""
    global keep_running, data_received
    
    print("[*] Client commands:")
    print("  'status' - Check connection status")
    print("  'data' - Show data summary if received")
    print("  'exit' - Disconnect from server")
    
    while keep_running:
        cmd = input("Command > ")
        
        if cmd.lower() == 'status':
            print(f"[i] Connected to server: {keep_running}")
            print(f"[i] Data received: {data_received}")
            
        elif cmd.lower() == 'data':
            if data_received and received_data is not None:
                print(f"\n[i] Data summary:")
                print(f"  - Shape: {received_data.shape}")
                print(f"  - Columns: {received_data.columns.tolist()}")
                print(received_data.head())
            else:
                print("[!] No data received yet")
                
        elif cmd.lower() == 'exit':
            print("[*] Disconnecting from server...")
            keep_running = False
            break
        
        else:
            print("[!] Unknown command")

def main():
    """Main client function"""
    global keep_running
    
    # Set up signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    client_name = input("Your name: ")
    
    # Connect to server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        print(f"[*] Connecting to server at {SERVER_IP}:{PORT}...")
        client_socket.connect((SERVER_IP, PORT))
        print("[✓] Connected to server")
        
        # Send connection message
        send_message(client_socket, MSG_TYPE_INFO, f"{client_name} is connected")
        
        # Start message handler thread
        msg_thread = threading.Thread(target=handle_server_messages, args=(client_socket,))
        msg_thread.daemon = True
        msg_thread.start()
        
        # Start command input thread
        cmd_thread = threading.Thread(target=input_commands, args=(client_socket,))
        cmd_thread.daemon = True
        cmd_thread.start()
        
        # Keep main thread alive
        while keep_running:
            time.sleep(0.1)
            
    except ConnectionRefusedError:
        print("[!] Connection refused. Make sure the server is running.")
    except Exception as e:
        print(f"[!] Error: {e}")
    finally:
        if client_socket:
            client_socket.close()
        print("[*] Client shutdown complete")

if __name__ == "__main__":
    main()