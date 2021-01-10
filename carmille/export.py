"""
carmille.export: Takes an array of Slack message dicts and exports them as a file.
"""

import json
import logging
import time

async def make_archive(channel_name, start_time, end_time, messages):
    """
    Construct a JSON archive of Slack messages.

    channel_name: the human-readable Slack channel name. Used for file naming.
    start_time: the `time.struct_time` representing the beginning of the messages.
    end_time: the `time.struct_time` representing the end of the messages.
    messages: the array of message dicts as formatted by carmille.fetch.
    """

    logging.debug("I have begun the dump process.")
    filename = f"tmp/{channel_name} {time.strftime('%Y-%m-%d-%H-%M',start_time)} to {time.strftime('%Y-%m-%d-%H-%M',end_time)}.json"
    with open(filename, "w") as file:
        json.dump(messages, file, indent=4)
    logging.debug("I have finished the dump process.")
    return filename
