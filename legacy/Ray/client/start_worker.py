# start_worker.py
import ray
SERVER_IP = '192.168.137.1'
PORT = 5000
ADDRESS = f'ray://{SERVER_IP}:{PORT}'
# Connect to Ray head node (your machine IP)
ray.init(address=ADDRESS)  # Adjust IP and port as shown on your head node
print("Worker node connected.")
