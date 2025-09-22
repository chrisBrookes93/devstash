# devstash

**devstash** is a development-time utility for **persistent caching** of function return values and variable assignments across multiple program executions.  

When you’re iterating on code, you often hit the same **slow lines** (e.g. heavy computations, file parsing, data processing) or **expensive lines** (e.g. LLM requests that cost tokens/money). With devstash, you can mark those lines once and cache the results on disk — so the next run reuses the cached values instead of re-executing them.  

That means:
- 🚀 **Faster iteration** while debugging or prototyping  
- 💸 **Save money** by skipping repeated LLM/API calls  
- 🧘 **No wasted time** waiting for recomputation during development  
- 🌐 **Offline development** after the first run, since cached API/web results are replayed without needing network access  
- 🧪 **Deterministic results** for easier debugging — results are identical every run  
- 🧰 **Mock-friendly cache files** that can be reused as test data, eliminating the need to hit real APIs or recompute fixtures  
- 🔍 **Transparent storage** in a `.devstash_cache/` folder — easy to inspect, clear, or share  
- 👥 **Team-ready**: share cached results across machines to save setup time  

---

## ⚡ Quickstart

Install and run in seconds:

```bash
pip install devstash
```

```python
import time
import devstash

devstash.activate()  # ✅ enable caching for this run

def slow_function(x):
    print("Running slow_function...")
    time.sleep(10)
    return x * 2

val = slow_function(10)  # @devstash
print(val)
```

💡 First run: prints *“Running slow_function…”* and caches the result.  
💡 Subsequent runs: instantly reuses the cached value without executing the function.  

---

## ✨ Features

- **Cache function return values** with a simple inline marker (`# @devstash`)  
- **Cache variable assignments** persistently across runs  
- **Transparent disk storage** in a `./.devstash_cache/` folder  
- **Automatic restore**: cached values are re-injected into your program on the next run  
- **Logging integration**: view caching activity with Python’s logging system  
- **Zero dependencies** (just Python stdlib)  
- **Optional TTL (time-to-live)** to expire cache after a given time (e.g. `30m`, `2h`, `1d`, `1w`)
- **Argument-sensitive caching**: separate cache files are created for different function arguments, so `foo(1, 2)` and `foo(2, 3)` won’t overwrite each other’s results.

---

## 🔥 Use Cases

### 🧑‍🔬 Expensive LLM calls
```python
from openai import OpenAI
import devstash

devstash.activate()

client = OpenAI()
prompt = "Summarize War and Peace in 3 sentences."

summary = client.chat.completions.create(  # @devstash
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}]
)
print(summary.choices[0].message["content"])
```

### 📊 Large file parsing
```python
from langchain_community.document_loaders import PyPDFLoader
import devstash

devstash.activate()

loader = PyPDFLoader("A_LARGE_PDF_DOCUMENT.pdf")
docs = loader.load()  # @devstash

print(f"Number of docs: {len(docs)}")
```

### 🧮 Machine learning preprocessing
```python
from sklearn.model_selection import train_test_split
import numpy as np
import devstash

devstash.activate()

data = np.random.randn(1_000_000, 10)
labels = np.random.randint(0, 2, 1_000_000)

X_train, X_test, y_train, y_test = train_test_split(  # @devstash
    data, labels, test_size=0.2
)
print(X_train.shape, X_test.shape)
```

### 💾 API responses
```python
import requests
import devstash

devstash.activate()

url = "https://api.github.com/repos/langchain-ai/langchain"
resp = requests.get(url)  # @devstash
repo_info = resp.json()

print(repo_info["stargazers_count"])
```

### ⏳ Cache with Time-To-Live (TTL)
You can add an optional `ttl` parameter to your `# @devstash` marker.  
TTL values can be expressed in **seconds (s), minutes (m), hours (h), days (d), or weeks (w)**.  
Examples: `30m`, `2h`, `1d`, `1w`.

```python
import devstash, requests

devstash.activate()

url = "https://api.github.com/repos/langchain-ai/langchain"

# Cache result for 1 day, then refresh
resp = requests.get(url)  # @devstash ttl=1d
print(resp.json()["stargazers_count"])
```

- First run: makes the API call and caches the result.  
- Subsequent runs within 1 day: loads directly from cache.  
- After 1 day: re-fetches and updates the cache automatically.  

---

## 🛠️ How It Works

devstash works by transforming your program at runtime:

1. **Explicit activation**: When you call `devstash.activate()`, it reads your main script (the entrypoint in `sys.argv[0]`).  
2. **Build an AST**: The code is parsed into an Abstract Syntax Tree (AST), a structured representation of your Python source.  
3. **Rewrite annotated lines**: Calls or assignments marked with `# @devstash` are rewritten to wrap them with the persistent cache helper.  
4. **Compile and exec**: The rewritten AST is compiled back into Python bytecode and executed in a fresh `__main__` namespace.  
5. **Persistent storage**: Values are stored on disk using pickle, and automatically restored on subsequent runs.  
6. **TTL support**: Before reading a cache file, devstash checks its last-modified time. If the file is older than the specified TTL, the cache is refreshed.  

👉 If you don’t want rewriting in a certain environment, set:  
```bash
export DEVSTASH_SKIP_REWRITE=1
```

---

## 📚 Related Work

There are several existing Python libraries that provide caching or mocking functionality, but **devstash** takes a different approach designed for day-to-day development convenience.

- **[persist-cache](http://pypi.org/project/persist-cache/)**  
  A simple decorator-based persistent cache for Python functions.  
  ✅ Easy to apply with decorators.  
  ❌ Requires decorating functions, not inline caching with markers. Has the limitation that you can't add decorators to library functions.

- **[joblib](https://joblib.readthedocs.io/)**  
  Provides a `Memory.cache()` decorator to persist function results on disk.  
  ✅ Great for machine learning pipelines.  
  ❌ Requires wrapping or decorating functions explicitly.  

- **[diskcache](http://www.grantjenks.com/docs/diskcache/)**  
  A disk-backed caching library with dictionary-like APIs and function decorators.  
  ✅ Powerful and flexible.  
  ❌ Boilerplate needed to integrate into code.  

- **[vcrpy](https://github.com/kevin1024/vcrpy)**  
  Records HTTP requests and replays them later for tests.  
  ✅ Excellent for offline API testing.  
  ❌ Only works for HTTP calls, not arbitrary function results.  

- **[pytest-cache](https://docs.pytest.org/en/7.1.x/how-to/cache.html)**  
  Lets you persist values across pytest runs.  
  ✅ Useful in test environments.  
  ❌ Limited to pytest, not general development.  

### 🔑 How devstash is different
Unlike the above, **devstash** focuses on *zero-boilerplate caching during development*.  
- Just add `# @devstash` to a line of code.  
- No decorators, wrappers, or test frameworks required.  
- Works with any function return value or assignment that is pickle-serializable.  
- Optimized for saving time and cost during *iterative coding*, not for production.  

---

## ⚠️ Notes & Limitations

- devstash is designed for **development/debugging only**, not for production caching.  
- Cached objects must be **pickle-serializable**.  
- Cache invalidation: delete `.devstash_cache/` if values become stale.  
- Currently, cache keys are based on **function/variable names** (argument-sensitive caching may be added in future).  
- Function chaining is **not supported**.  
  E.g. to avoid an API call in `requests.get(url).json()` you must split the `.json()` onto a separate line and apply the marker to the `.get()` call.  
- **TTL support**: you can specify cache expiry with `ttl=...` in the marker (`# @devstash ttl=30m`). Invalid TTL formats will raise an error. Cache freshness is determined using the **file’s last modified time**.  
- **Execution context support**: devstash currently only supports being run with the **main Python executable** (e.g. `python script.py`) or through package manager wrappers like **uv** (`uv run script.py`) or **poetry** (`poetry run python script.py`).  
  Other **runner-style tools** such as `flask run`, `uvicorn`, or `gunicorn` are **not yet supported** because they import your application as a module instead of executing it as the entrypoint.  
  Support for these wrappers is planned for the future. For now, always run your scripts directly with `python` (or `uv run` / `poetry run`).  

---

## 🤝 Contributing

Contributions, feedback, and ideas are very welcome!

- 🐛 **Found a bug?** Please open an issue with details so we can fix it.  
- 💡 **Have a feature idea?** Share it in the issues or discussions.  
- 🔧 **Want to contribute code?** Fork the repo, create a branch, and open a pull request.  
- 📖 **Improve documentation?** Edits and clarifications are always appreciated.  

### 🔨 Development Setup

This project uses [uv](https://github.com/astral-sh/uv) and [Ruff](https://docs.astral.sh/ruff/) for dependency management and linting.

Install dependencies:

```bash
uv sync
```

Run tests:

```bash
uv run pytest
```

Run Ruff checks:

```bash
uv run ruff check .
```

Automatically fix issues:

```bash
uv run ruff check . --fix
```

Format code:

```bash
uv run ruff format .
```

---

devstash is still evolving, and community input will help shape its direction. Whether it’s catching rough edges, improving performance, or adding new caching strategies — we’d love your help!
