import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import pairwise_distances

class KMeansCustom:
    def __init__(self, n_clusters=8, random_state=None):
        """
        Simple wrapper around sklearn's KMeans
        
        Parameters:
        -----------
        n_clusters : int, default=8
            Number of clusters
        random_state : int, default=None
            Random seed for reproducibility
        """
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.model = KMeans(n_clusters=n_clusters, random_state=random_state)
        
    def fit(self, X):
        """Fit the model to data"""
        self.model.fit(X)
        self.cluster_centers_ = self.model.cluster_centers_
        self.labels_ = self.model.labels_
        return self
    
    def predict(self, X):
        """Predict cluster labels for samples in X"""
        return self.model.predict(X)
    
    def fit_predict(self, X):
        """Fit the model and predict cluster labels"""
        self.fit(X)
        return self.labels_


class KMedoidsCustom:
    def __init__(self, n_clusters=8, max_iter=100, random_state=None):
        """
        Simple K-medoids implementation
        
        Parameters:
        -----------
        n_clusters : int, default=8
            Number of clusters
        max_iter : int, default=100
            Maximum number of iterations
        random_state : int, default=None
            Random seed for reproducibility
        """
        self.n_clusters = n_clusters
        self.max_iter = max_iter
        self.random_state = random_state
        self.medoid_indices_ = None
        self.labels_ = None
        
    def fit(self, X):
        """Fit the model to data"""
        if isinstance(X, pd.DataFrame):
            X = X.values
            
        n_samples = X.shape[0]
        
        # Set random seed
        if self.random_state is not None:
            np.random.seed(self.random_state)
        
        # Calculate distance matrix (this is the most computationally expensive part)
        distance_matrix = pairwise_distances(X)
        
        # Initialize medoids randomly
        self.medoid_indices_ = np.random.choice(n_samples, self.n_clusters, replace=False)
        
        # Initialize labels
        self.labels_ = np.zeros(n_samples, dtype=int)
        
        # Main loop
        for _ in range(self.max_iter):
            # Store old medoid indices for convergence check
            old_medoid_indices = self.medoid_indices_.copy()
            
            # Assign points to nearest medoid
            self.labels_ = np.argmin(distance_matrix[:, self.medoid_indices_], axis=1)
            
            # Update medoids
            for i in range(self.n_clusters):
                # Get points in this cluster
                cluster_indices = np.where(self.labels_ == i)[0]
                
                if len(cluster_indices) > 0:
                    # Calculate total distance from each point to all others in the cluster
                    cluster_distances = distance_matrix[cluster_indices][:, cluster_indices]
                    total_distances = cluster_distances.sum(axis=1)
                    # The point with minimum total distance becomes the new medoid
                    new_medoid_idx_in_cluster = np.argmin(total_distances)
                    self.medoid_indices_[i] = cluster_indices[new_medoid_idx_in_cluster]
            
            # Check for convergence
            if np.all(old_medoid_indices == self.medoid_indices_):
                break
                
        return self
    
    def predict(self, X):
        """Predict cluster labels for samples in X"""
        if self.medoid_indices_ is None:
            raise ValueError("Model not fitted yet.")
            
        if isinstance(X, pd.DataFrame):
            X = X.values
            
        # Calculate distances to medoids
        medoids = X[self.medoid_indices_]
        distances = pairwise_distances(X, medoids)
        
        # Assign to nearest medoid
        return np.argmin(distances, axis=1)
    
    def fit_predict(self, X):
        """Fit the model and predict cluster labels"""
        self.fit(X)
        return self.labels_