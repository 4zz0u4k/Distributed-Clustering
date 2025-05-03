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
# data spitting
data_chunks = np.array_split(data_df, num_workers)
# worker's clustering
futures = [remote_cluster.remote(chunk) for chunk in data_chunks]
intermediate_results = ray.get(futures)
# data unification
kmeans_centroids = [centroid for centroid in intermediate_results]
kmeans_centroids_df = pd.DataFrame(np.vstack([centroid for centroid in kmeans_centroids]))
# head clustering
kmedoids = KMedoidsCustom(n_clusters=3, random_state=7777)
kmedoids_labels = kmedoids.fit_predict(kmeans_centroids_df)
kmedoids_indices = kmedoids.medoid_indices_
kmedoids_points = kmeans_centroids_df.iloc[kmedoids_indices].values
print(f"K-medoids points:\n{kmedoids_points}")
print(f"K-medoids indices: {kmedoids_indices}")
