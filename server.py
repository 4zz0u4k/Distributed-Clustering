import ray
import pandas as pd
import numpy as np

ray.init(_node_ip_address='192.168.137.1')

# Assume this is your clustering function
def cluster_chunk(df):
    pass  # you implement this

@ray.remote
def remote_cluster(data_chunk):
    return cluster_chunk(data_chunk)

DATA_PATH = './Data/data.csv'
data_df = pd.read_csv(DATA_PATH)
# number of workers
nodes_info = ray.nodes()
num_workers = sum(1 for node in ray.nodes() if 'node:__internal_head__' not in node['Resources'])
# data spitting
data_chunks = np.array_split(data_df, num_workers)
for chunk in data_chunks:
    print(chunk.head())
    
# 4. Send to workers
futures = [remote_cluster.remote(chunk) for chunk in data_chunks]
partial_results = ray.get(futures)

# 5. Final clustering step (on head node)
final_result = cluster_chunk(data_df)
print(final_result)
