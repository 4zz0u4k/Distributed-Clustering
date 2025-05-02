# controller.py
import ray
import pandas as pd
from cluster.clustering import method1, method2
from sklearn.datasets import make_blobs

# 1. Connect to Ray (you are already the head node)
ray.init(address='auto')

# 2. Generate dummy data
X, _ = make_blobs(n_samples=1000, centers=3, n_features=4)
df = pd.DataFrame(X)

# 3. Split the data into chunks (one per worker, say 4)
chunks = [df.iloc[i:i+250] for i in range(0, len(df), 250)]

# 4. Send clustering tasks (choose method1 or method2)
futures = [method1.remote(chunk) for chunk in chunks]  # or method2.remote(chunk)

# 5. Collect results
results = ray.get(futures)

# 6. Process results (just printing here)
for r in results:
    print(f"Received from worker: {r}")
