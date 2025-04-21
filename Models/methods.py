import numpy as np
import pandas as pd

def random_clustering(df, K, random_state=None):
    
    if random_state is not None:
        np.random.seed(random_state)

    data = df.values

    indices = np.random.choice(len(data), K, replace=False)
    centers = data[indices]

    distances = np.linalg.norm(data[:, np.newaxis] - centers, axis=2)
    cluster_assignments = np.argmin(distances, axis=1)

    return cluster_assignments, centers
