import logging

from openai import OpenAI

import devstash

devstash.activate()

# Set DEBUG logging so that we can see what devstash is up to
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("devstash").setLevel(logging.DEBUG)

client = OpenAI()
prompt = "Summarize War and Peace in 3 sentences."

summary = client.chat.completions.create(  # @devstash
    model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}]
)
print(summary.choices[0].message.content)
