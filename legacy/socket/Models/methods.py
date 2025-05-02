import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from matplotlib.animation import FuncAnimation
from sklearn_extra.cluster import KMedoids

# # Load and prepare data
# df = pd.read_csv("../Data/data.csv")  # Make sure this file path is correct
# df = df.dropna()  # Drop rows with missing values

# # Number of clusters and random seed
# K = 5
# random_state = 42

# --- Clustering Methods ---
def random_clustering(data, k):
    """
    Perform random clustering on the data.
    
    Args:
        data: Either a DataFrame or a list of existing cluster centers
        k: Number of clusters to create
    
    Returns:
        numpy.ndarray: Array of k cluster centers
    """
    # Case 1: If we have a DataFrame, create k random centers
    if hasattr(data, 'shape') and hasattr(data, 'columns'):  # It's a DataFrame
        # Get numeric columns only
        numeric_cols = data.select_dtypes(include=np.number).columns.tolist()
        if not numeric_cols:
            print("[!] No numeric columns found in data")
            return np.zeros((k, 2))  # Default fallback
            
        # Use numeric data to generate random centers
        numeric_data = data[numeric_cols].values
        
        # Choose k random data points as initial centers
        if len(numeric_data) < k:
            # Generate synthetic centers if not enough data points
            centers = np.random.rand(k, len(numeric_cols))
        else:
            # Choose k random data points as initial centers
            indices = np.random.choice(len(numeric_data), k, replace=False)
            centers = numeric_data[indices]
            
        return centers  # Return as numpy array
        
    # Case 2: If we have a list of existing cluster centers, combine them
    elif isinstance(data, list) and all(isinstance(x, np.ndarray) for x in data):
        # Combine all centers from sub-clusters
        all_centers = np.vstack(data)
        
        # If we have fewer centers than k, just return what we have
        if len(all_centers) <= k:
            return all_centers
            
        # Otherwise, pick k random centers from the combined set
        indices = np.random.choice(len(all_centers), k, replace=False)
        return all_centers[indices]  # Return as numpy array
    
    # Case 3: Handle unexpected input
    else:
        print(f"[!] Unexpected data type for clustering: {type(data)}")
        # Return default centers
        return np.zeros((k, 2))  # Default fallback


def kmeans_clustering(df, K, random_state=None):
    model = KMeans(n_clusters=K, random_state=random_state, n_init='auto')
    model.fit(df.values)
    return model.labels_, model.cluster_centers_

def kmedoids_clustering(df, K, random_state=None):
    model = KMedoids(n_clusters=K, random_state=random_state, method='pam')
    model.fit(df.values)
    centers = df.values[model.medoid_indices_]
    return model.labels_, centers


def animate_clustering(df, centers_list, save_path='clustering_animation.mp4'):
    # Project data to 2D using PCA
    pca = PCA(n_components=2)
    projected_data = pca.fit_transform(df.values)

    # Project all sets of centers to 2D
    projected_centers_list = [pca.transform(np.array(centers)) for centers in centers_list]

    # Set up the figure and axis
    fig, ax = plt.subplots(figsize=(8, 6))
    scatter = ax.scatter(projected_data[:, 0], projected_data[:, 1], c='lightgray', s=10, label='Data Points')
    centers_plot = ax.scatter([], [], c='red', marker='x', s=100, label='Centroids')
    
    ax.set_title("Clustering Animation")
    ax.set_xlabel("PCA Component 1")
    ax.set_ylabel("PCA Component 2")
    ax.legend()
    ax.grid(True)

    def update(frame):
        centers = projected_centers_list[frame]
        centers_plot.set_offsets(centers)
        return centers_plot,

    ani = FuncAnimation(fig, update, frames=len(projected_centers_list), blit=True, repeat=False)

    # Save animation as MP4
    ani.save(save_path, fps=2)  # Adjust fps as needed
    plt.close()
    print(f"Animation saved to {save_path}")

# # Run clustering
# random_labels, random_centers = random_clustering(df, K, random_state)
# kmeans_labels, kmeans_centers = kmeans_clustering(df, K, random_state)
# kmedoids_labels, kmedoids_centers = kmedoids_clustering(df, K, random_state)

# # PCA projection
# pca = PCA(n_components=2)
# projected_data = pca.fit_transform(df.values)
# random_proj_centers = pca.transform(random_centers)
# kmeans_proj_centers = pca.transform(kmeans_centers)
# kmedoids_proj_centers = pca.transform(kmedoids_centers)

# # Plotting
# plt.figure(figsize=(12, 8))
# plt.scatter(projected_data[:, 0], projected_data[:, 1], c='lightgray', s=10, label='Data Points')

# plt.scatter(random_proj_centers[:, 0], random_proj_centers[:, 1], 
#             c='blue', marker='x', s=100, label='Random Centers')

# plt.scatter(kmeans_proj_centers[:, 0], kmeans_proj_centers[:, 1], 
#             c='red', marker='o', s=100, label='KMeans Centers')

# plt.scatter(kmedoids_proj_centers[:, 0], kmedoids_proj_centers[:, 1], 
#             c='green', marker='s', s=100, label='KMedoids Medoids')

# plt.title("2D PCA Projection with Cluster Centers")
# plt.xlabel("PCA Component 1")
# plt.ylabel("PCA Component 2")
# plt.legend()
# plt.grid(True)
# plt.tight_layout()
# plt.show()
