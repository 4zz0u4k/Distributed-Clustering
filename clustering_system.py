from .Models import random
import multiprocessing,multiprocessing.managers as managers
import socket
import numpy as np
import time
import uuid

class NodeManager(managers.BaseManager):
    pass

# For the server (global node)
def create_server(port=50000):
    # Shared objects to hold data and results
    job_queue = multiprocessing.Queue()
    result_queue = multiprocessing.Queue()
    nodes_registry = {}  # To keep track of connected nodes
    
    # Register these objects with the manager
    NodeManager.register('get_job_queue', callable=lambda: job_queue)
    NodeManager.register('get_result_queue', callable=lambda: result_queue)
    NodeManager.register('register_node', callable=lambda node_id, ip: nodes_registry.update({node_id: ip}))
    NodeManager.register('get_nodes', callable=lambda: nodes_registry)
    
    # Create and start the server
    manager = NodeManager(address=('', port), authkey=b'clustering_secret')
    server = manager.get_server()
    return server, job_queue, result_queue, nodes_registry


# For the clients (worker nodes)
def connect_to_server(server_address, port=50000):
    NodeManager.register('get_job_queue')
    NodeManager.register('get_result_queue')
    NodeManager.register('register_node')
    
    manager = NodeManager(address=(server_address, port), authkey=b'clustering_secret')
    manager.connect()
    
    # Generate a unique ID for this node
    node_id = str(uuid.uuid4())
    local_ip = socket.gethostbyname(socket.gethostname())
    
    # Register this node with the server
    manager.register_node(node_id, local_ip)
    
    return manager, node_id

def start_instance(is_server=False, server_address=None, port=50000):
    """
    Start either a server or client instance
    """
    if is_server:
        server, job_queue, result_queue, nodes = create_server(port)
        print(f"Server started on port {port}")
        return {
            'server': server,
            'job_queue': job_queue,
            'result_queue': result_queue,
            'nodes': nodes
        }
    else:
        if not server_address:
            raise ValueError("Server address is required for client instances")
        manager, node_id = connect_to_server(server_address, port)
        print(f"Connected to server at {server_address}:{port} as node {node_id}")
        return {
            'manager': manager,
            'node_id': node_id,
            'job_queue': manager.get_job_queue(),
            'result_queue': manager.get_result_queue()
        }

def run_algorithm(instance, data_partition=None, params=None):
    """
    Run the clustering algorithm on this node
    """
    if 'server' in instance:  # This is the server
        # Distribute data to nodes
        nodes = instance['nodes']
        if not nodes:
            print("No nodes connected. Cannot distribute work.")
            return
            
        # Split the data for each node
        # For simplicity, assuming data is a numpy array
        if data_partition is None:
            # Create sample data for testing
            data_partition = np.random.rand(1000, 10)
        
        parts = np.array_split(data_partition, len(nodes))
        
        # Add jobs to the queue
        for i, (node_id, _) in enumerate(nodes.items()):
            instance['job_queue'].put({
                'node_id': node_id,
                'data': parts[i],
                'params': params
            })
        
        # Wait for all results
        print(f"Waiting for results from {len(nodes)} nodes...")
        
    else:  # This is a client
        # Get a job from the queue
        job_queue = instance['job_queue']
        result_queue = instance['result_queue']
        node_id = instance['node_id']
        
        while True:
            try:
                job = job_queue.get(block=True, timeout=5)
                
                # Check if this job is for this node
                if job['node_id'] == node_id:
                    # Process the data
                    data = job['data']
                    params = job['params']
                    
                    # Run the clustering algorithm
                    start_time = time.time()
                    result = random(data, params)
                    elapsed_time = time.time() - start_time
                    
                    # Send the result back
                    result_queue.put({
                        'node_id': node_id,
                        'result': result,
                        'processing_time': elapsed_time
                    })
                    print(f"Node {node_id} completed processing. Time: {elapsed_time:.2f} seconds")
                    break
            except Exception as e:
                print(f"Error in node {node_id}: {e}")
                break

def unify_solution(instance):
    """
    Unify the results from all nodes
    """
    if 'server' not in instance:
        raise ValueError("This function must be called on the server instance")
    
    result_queue = instance['result_queue']
    nodes = instance['nodes']
    
    # Collect all results
    all_results = []
    for _ in range(len(nodes)):
        try:
            result = result_queue.get(block=True, timeout=60)
            all_results.append(result)
        except Exception as e:
            print(f"Error collecting results: {e}")
    
    # Combine the results
    # This depends on your specific clustering algorithm and how you want to combine results
    combined_result = []
    for node_result in all_results:
        combined_result.append(node_result['result'])
    
    # Here you'd implement the logic to combine cluster centers or whatever
    # is appropriate for your custom clustering algorithm
    
    print(f"Unified results from {len(all_results)} nodes")
    return combined_result
