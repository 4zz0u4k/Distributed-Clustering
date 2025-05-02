# start_head_node.py
import ray
SERVER_IP = '192.168.137.1'
# Start Ray as HEAD node
ray.init(address='192.168.137.1:5000')  
print("Ray head node is running. Share this with friends:")
print(ray.init().address_info["redis_address"])
