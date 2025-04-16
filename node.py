from clustering_system import start_instance, run_algorithm

# Replace with your server's IP address (the hotspot host)
SERVER_IP = '192.168.1.100'  

# Connect to the server
node_instance = start_instance(is_server=False, server_address=SERVER_IP)

# This will wait for jobs and process them
run_algorithm(node_instance)

