import ray
import pandas as pd
import numpy as np
from clustering_methods import KMeansCustom,KMedoidsCustom

ray.init(_node_ip_address='192.168.137.1')

@ray.remote
def remote_cluster(data_chunk):
    # Run K-means clustering
    k = 10
    kmeans = KMeansCustom(n_clusters=k, random_state=5555)
    kmeans.fit_predict(data_chunk)
    kmeans_centroids = kmeans.cluster_centers_
    return kmeans_centroids

DATA_PATH = './Data/data.csv'
data_df = pd.read_csv(DATA_PATH)
# number of workers
nodes_info = ray.nodes()
num_workers = sum(1 for node in ray.nodes() if 'node:__internal_head__' not in node['Resources'])
print(f"[!] Number of workers : {num_workers}")
# data spitting
data_chunks = np.array_split(data_df, num_workers)
# worker's clustering
futures = [remote_cluster.remote(chunk) for chunk in data_chunks]
intermediate_results = ray.get(futures)
print(f"[+] Intermediate reulsts : (Kmeans) \n {intermediate_results}")

