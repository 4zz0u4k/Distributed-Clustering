# start_head_node.py
import ray

# Start Ray as HEAD node
ray.init(address='auto', _node_ip_address="192.168.1.1")  # Replace with your hotspot IP
print("Ray head node is running. Share this with friends:")
print(ray.init().address_info["redis_address"])
