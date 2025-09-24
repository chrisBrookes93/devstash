import logging

from openai import OpenAI

import devstash

devstash.activate()

# Set DEBUG logging so that we can see what devstash is up to
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("devstash").setLevel(logging.DEBUG)


client = OpenAI()

docs = [
    "Artificial intelligence is transforming software development.",
    "Caching results can save time and money during prototyping.",
    "OpenAI provides high-quality embedding models.",
]

# First run: calls OpenAI API for embeddings (costs tokens)
# Later runs: instantly reloads cached embeddings (0 tokens)
response = client.embeddings.create(  # @devstash
    model="text-embedding-3-small", input=docs
)

embeddings = [item.embedding for item in response.data]
print("Number of embeddings:", len(embeddings))
print("First vector dimensions:", len(embeddings[0]))
