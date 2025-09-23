import logging
import time

import numpy as np
from sklearn.model_selection import train_test_split

import devstash

devstash.activate()

# Set DEBUG logging so that we can see what devstash is up to
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("devstash").setLevel(logging.DEBUG)

start = time.time()

# Create a large synthetic dataset (1M rows × 200 features)
X = np.random.randn(1_000_000, 200)
y = np.random.randint(0, 2, size=1_000_000)

# First run: very slow (scaling + PCA on big data)
# Later runs: instant (cached arrays restored)
X_train, X_test, y_train, y_test = train_test_split(  # @devstash
    X, y, test_size=0.2, random_state=42
)

print("Program execution time: {:.2f} seconds".format(time.time() - start))
