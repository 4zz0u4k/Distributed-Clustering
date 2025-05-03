import ray
import pandas as pd
import numpy as np
from clustering_methods import KMeansCustom,KMedoidsCustom
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
from scipy.spatial.distance import cdist

ray.init(_node_ip_address='192.168.137.1')

@ray.remote
def remote_cluster(data_chunk,k=100):
    # Run K-means clustering
    kmeans = KMeansCustom(n_clusters=k, random_state=5555)
    kmeans.fit_predict(data_chunk)
    kmeans_centroids = kmeans.cluster_centers_
    return kmeans_centroids

DATA_PATH = './Data/data.csv'
data_df = pd.read_csv(DATA_PATH)
# number of workers
nodes_info = ray.nodes()
num_workers = sum(1 for node in ray.nodes() if 'node:__internal_head__' not in node['Resources'])
k = input("Enter K : ")
# data spitting
data_chunks = np.array_split(data_df, num_workers)
# worker's clustering
futures = [remote_cluster.remote(chunk) for chunk in data_chunks]
intermediate_results = ray.get(futures)
# data unification
kmeans_centroids = [centroid for centroid in intermediate_results]
kmeans_centroids_df = pd.DataFrame(np.vstack([centroid for centroid in kmeans_centroids]))
# head clustering
kmedoids = KMedoidsCustom(n_clusters=4, random_state=7777)
kmedoids_labels = kmedoids.fit_predict(kmeans_centroids_df)
kmedoids_indices = kmedoids.medoid_indices_
kmedoids_points = kmeans_centroids_df.iloc[kmedoids_indices].values
print(f"K-medoids points:\n{kmedoids_points}")
print(f"K-medoids indices: {kmedoids_indices}")
# [*] PCA and visualizations
pca = PCA(n_components=2)
data_pca = pca.fit_transform(data_df) 
print(f"PCA explained variance ratio: {pca.explained_variance_ratio_}")
print(f"Total variance explained: {sum(pca.explained_variance_ratio_):.2%}")
plt.figure(figsize=(10, 8))
distances = cdist(data_df.values, kmedoids_points)
labels = np.argmin(distances, axis=1)
n_clusters = len(kmedoids_points)
for i in range(n_clusters):
    mask = labels == i
    cluster_points = data_pca[mask]
    plt.scatter(cluster_points[:, 0], cluster_points[:, 1], s=50, alpha=0.5)
kmedoids_pca = pca.transform(kmedoids_points)
plt.scatter(kmedoids_pca[:, 0], kmedoids_pca[:, 1], s=200, c='red', marker='*')
plt.tight_layout()
plt.show()

