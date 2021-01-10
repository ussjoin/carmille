"""
carmille.fetch: Interacts with the Slack API and grabs message archives.
"""

import time
import logging
from slack_bolt.async_app import AsyncApp

from . import export # Go get the export.py file so we can use it

app = AsyncApp()

async def get_message_archive(channel_id, channel_name, start_time, end_time):
    """
    Fetch, construct, and return a JSON archive of Slack messages.

    channel_id: the human-opaque Slack channel identifier.
    channel_name: the human-readable Slack channel name. Used for file naming.
    start_time: the `time.struct_time` representing the beginning of the messages.
    end_time: the `time.struct_time` representing the end of the messages.
    """
    # https://api.slack.com/methods/conversations.history

    # OK, so here's the deal. We need to handle pagination.
    # We're going to page through, `limit` at a time, until the `has_more` property
    # of the response becomes false.
    # Once we have all the messages, we hand them off to the next thing.

    # Recommended limit value is 200.
    # Set to 5 to ensure pagination works correctly, but that'll make the Slack API hate you.

    res = await app.client.conversations_history(channel=channel_id, oldest=time.mktime(start_time), latest=time.mktime(end_time), limit=200)

    messages_group = res['messages']

    has_more = res['has_more']

    if res.get('response_metadata', None) and res['response_metadata'].get('next_cursor', None):
        new_cursor = res['response_metadata']['next_cursor']
    while has_more:
        res = await app.client.conversations_history(channel=channel_id, oldest=time.mktime(start_time), latest=time.mktime(end_time), limit=200, cursor=new_cursor)

        messages_group.extend(res['messages'])

        has_more = res['has_more']

        if res.get('response_metadata', None) and res['response_metadata'].get('next_cursor', None):
            new_cursor = res['response_metadata']['next_cursor']
    messages_group.sort(key=__message_timestamp_sort)

    # OK! Now we've retrieved all the main-channel messages; however, we need to go get thread replies, because of course Slack makes that hard.

    # https://api.slack.com/methods/conversations.replies
    for message in messages_group:
        if 'thread_ts' in message:
            # This means it's part of a thread. We have to do the whole same song and dance now.
            timestamp = message['ts'] # Unique identifier used to identify any message. We only care for start of thread.
            res = await app.client.conversations_replies(channel=channel_id, ts=timestamp, oldest=time.mktime(start_time), latest=time.mktime(end_time), limit=2)

            # Deleting the very first one because it'll be a duplicate of the thread topper.
            tmessages_group = res['messages'][1:]

            thas_more = res['has_more']

            if res.get('response_metadata', None) and res['response_metadata'].get('next_cursor', None):
                tnew_cursor = res['response_metadata']['next_cursor']

            while thas_more:
                res = await app.client.conversations_replies(channel=channel_id, ts=timestamp, oldest=time.mktime(start_time), latest=time.mktime(end_time), limit=2, cursor=tnew_cursor)

                # Deleting the very first one because it'll be a duplicate of the thread topper.
                tmessages_group.extend(res['messages'][1:])

                thas_more = res['has_more']

                if res.get('response_metadata', None) and res['response_metadata'].get('next_cursor', None):
                    tnew_cursor = res['response_metadata']['next_cursor']

            # Finally, drop the replies into the message object above.
            tmessages_group.sort(key=__message_timestamp_sort)
            message['replies'] = tmessages_group

    logging.debug(f"done! I retrieved {len(messages_group)} messages, including the thread replies.")

    return await export.make_archive(channel_name, start_time, end_time, messages_group)

async def get_tz_offset(user_id):
    """
    Retrieve the (seconds as an integer) time zone offset from UTC for a user.
    Outputs an integer in the range [-43200, 43200]. (-12h, +12h.)

    user_id: the human-opaque Slack user identifier.
    """
    # https://api.slack.com/methods/users.info
    res = await app.client.users_info(user=user_id)
    return res['user']['tz_offset']

def __message_timestamp_sort(message):
    """
    Returns the Slack message timestamp for a single message.
    Used to sort Slack message arrays by time.
    Private function.

    m: A single Slack message dict.
    """

    return float(message['ts'])
