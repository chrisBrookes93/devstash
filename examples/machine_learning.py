import logging
import time

from sklearn.datasets import fetch_openml
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline

import devstash

devstash.activate()
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("devstash").setLevel(logging.DEBUG)

start = time.time()

X, y = fetch_openml("mnist_784", version=1, return_X_y=True, as_frame=False, parser="liac-arff")  # @devstash
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)  # @devstash
pipe = make_pipeline(PCA(n_components=50), LogisticRegression(max_iter=2000))
pipe.fit(X_train, y_train)  # @devstash
acc = pipe.score(X_test, y_test)  # @devstash

print(f"Accuracy: {acc:.3f}")
print("Program execution time: %.2f s" % (time.time() - start))

# Output from the second run when the cache is warm:
# Accuracy: 0.908
# Program execution time: 29.67 s

# Output from the second run when the cache is warm:
# Accuracy: 0.908
# Program execution time: 0.68 s
