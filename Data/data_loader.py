import pandas as pd
import numpy as np

DATA_PATH = 'data.csv'

def load_data(chunks_number : int):
    df = pd.read_csv(DATA_PATH)
    chunks = np.array_split(df, chunks_number)
    return chunks
