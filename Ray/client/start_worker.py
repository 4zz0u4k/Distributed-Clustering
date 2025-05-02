# start_worker.py
import ray

# Connect to Ray head node (your machine IP)
ray.init(address='ray://192.168.1.1:10001')  # Adjust IP and port as shown on your head node
print("Worker node connected.")
