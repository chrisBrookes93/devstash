import logging
import time

import devstash

devstash.activate()

logging.basicConfig(
    level=logging.INFO,  # Change to DEBUG to see the devstash logs
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger()


function_ret_vals = ("alpha", "bravo", "charlie", "delta", "echo")
hit_count = 0


def function_to_cache():
    logger.info("function_to_cache has been called!")
    global hit_count
    ret_val = function_ret_vals[hit_count]
    hit_count += 1
    return ret_val


logger.info("We're going to call the cache function 15 times in a loop with a 5 second sleep.")
logger.info(
    "Each time the function is called it will return the next phonetic alphabet word, e.g. alpha, bravo, charlie"
)
logger.info("The TTL is 12s, therefore, we expect to see each phonetic printed 3 times")
expected = [val for val in function_ret_vals for _ in range(3)]
actual = []
for _ in range(0, 15):
    ret = function_to_cache()  # @devstash ttl=12s
    actual.append(ret)
    logger.info(ret)
    time.sleep(5)
assert expected == actual, "Unexpected output"
