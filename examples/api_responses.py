import logging

import requests

import devstash

devstash.activate()

# Set DEBUG logging so that we can see what devstash is up to
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("devstash").setLevel(logging.DEBUG)


url = "https://api.github.com/repos/langchain-ai/langchain"

# First run: actual GitHub API call
# Later runs: cached JSON
resp = requests.get(url)  # @devstash
repo_info = resp.json()

print(repo_info["stargazers_count"])
