import json
import logging
import time

async def make_archive(channel_name, start_time, end_time, messages):
    logging.debug("I have begun the dump process.")
    filename = f"tmp/{channel_name} {time.strftime('%Y-%m-%d-%H-%M',start_time)} to {time.strftime('%Y-%m-%d-%H-%M',end_time)}.json"
    with open(filename, "w") as f:
        json.dump(messages, f, indent=4)
    logging.debug("I have finished the dump process.")
    return filename