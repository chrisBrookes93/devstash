import logging
import time

from langchain_community.document_loaders import PyPDFLoader

import devstash

devstash.activate()

start = time.time()

# Set DEBUG logging so that we can see what devstash is up to
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("devstash").setLevel(logging.DEBUG)


loader = PyPDFLoader("nke-10k-2023.pdf")
docs = loader.load()  # @devstash

print(f"Number of docs: {len(docs)}")

print("Program execution time: {:.2f} seconds".format(time.time() - start))
