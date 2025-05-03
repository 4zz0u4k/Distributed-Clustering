import ray
import pandas as pd
import numpy as np
from clustering_methods import KMeansCustom,KMedoidsCustom
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
from scipy.spatial.distance import cdist
from sklearn.metrics import silhouette_score
from sklearn.metrics import normalized_mutual_info_score

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
n = data_df.shape[0]
# number of workers
nodes_info = ray.nodes()
num_workers = sum(1 for node in ray.nodes() if 'node:__internal_head__' not in node['Resources'])
# Computing diffrent Ks
alpha = 10   
k = int(input("Enter K (final number of clusters): "))
k1  = alpha * k
k2  = k * np.log(n)         
k3  = np.sqrt(n)     
k4  = n ** (1/3)  
k5 = n / k   
k6  = k * np.log(n / k)
print("\nChoose a strategy for computing k_kmeans:")
print("1. k1 = alpha * k")
print("2. k2 = k * log(n)")
print("3. k3 = sqrt(n)")
print("4. k4 = n ** (1/3)")
print("5. k5 = n / k")
print("6. k6 = k * log(n / k)")
choice = input("Enter your choice (1-6): ")
if choice == '1':
    k_kmeans = k1
elif choice == '2':
    k_kmeans = k2
elif choice == '3':
    k_kmeans = k3
elif choice == '4':
    k_kmeans = k4
elif choice == '5':
    k_kmeans = k5
elif choice == '6':
    k_kmeans = k6
else:
    print("Invalid choice.")
    k_kmeans = None
k_kmeans = int(round(k_kmeans))
if k_kmeans is not None:
    print(f"\nk_kmeans (K-means pre-clustering K): {k_kmeans}")
# data spitting
data_chunks = np.array_split(data_df, num_workers)
# worker's clustering
futures = [remote_cluster.remote(chunk,k_kmeans) for chunk in data_chunks]
intermediate_results = ray.get(futures)
# data unification
kmeans_centroids = [centroid for centroid in intermediate_results]
kmeans_centroids_df = pd.DataFrame(np.vstack([centroid for centroid in kmeans_centroids]))
# head clustering
kmedoids = KMedoidsCustom(n_clusters=k, random_state=7777)
kmedoids_labels = kmedoids.fit_predict(kmeans_centroids_df)
kmedoids_indices = kmedoids.medoid_indices_
kmedoids_points = kmeans_centroids_df.iloc[kmedoids_indices].values
distances = cdist(data_df.values, kmedoids_points)
labels = np.argmin(distances, axis=1)
print(f"K-medoids points:\n{kmedoids_points}")
print(f"K-medoids indices: {kmedoids_indices}")
# [*] 
sil_score = silhouette_score(data_df.values, labels)
print(f"Silhouette Score: {sil_score:.4f}")
# [*] PCA and visualizations
pca = PCA(n_components=2)
data_pca = pca.fit_transform(data_df) 
print(f"PCA explained variance ratio: {pca.explained_variance_ratio_}")
print(f"Total variance explained: {sum(pca.explained_variance_ratio_):.2%}")
plt.figure(figsize=(10, 8))
n_clusters = len(kmedoids_points)
for i in range(n_clusters):
    mask = labels == i
    cluster_points = data_pca[mask]
    plt.scatter(cluster_points[:, 0], cluster_points[:, 1], s=50, alpha=0.5)
kmedoids_pca = pca.transform(kmedoids_points)
plt.scatter(kmedoids_pca[:, 0], kmedoids_pca[:, 1], s=200, c='red', marker='*')
plt.tight_layout()
plt.show()

# [!] Specifically for this example only (we have labeled data)
RESPONSE_PATH = './Data/response.csv'
respopnse_df = pd.read_csv(RESPONSE_PATH)
true_labels = respopnse_df['Response'].values
nmi_score = normalized_mutual_info_score(true_labels, labels)
print(f"NMI Score: {nmi_score:.4f}")

