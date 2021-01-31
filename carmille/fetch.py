"""
carmille.fetch: Interacts with the Slack API and grabs message archives.
"""

import time
import logging
import re

from . import export # Go get the export.py file so we can use it

async def get_message_archive(client, channel_id, channel_name, start_time, end_time, tz_offset):
    """
    Fetch, construct, and return a JSON archive of Slack messages.

    client: the client from the context object.
    channel_id: the human-opaque Slack channel identifier.
    channel_name: the human-readable Slack channel name. Used for file naming.
    start_time: the `time.struct_time` representing the beginning of the messages.
    end_time: the `time.struct_time` representing the end of the messages.
    tz_offset: the requesting user's local time offset from UTC, in integer seconds.
    """
    # https://api.slack.com/methods/conversations.history

    # OK, so here's the deal. We need to handle pagination.
    # We're going to page through, `limit` at a time, until the `has_more` property
    # of the response becomes false.
    # Once we have all the messages, we hand them off to the next thing.

    # Recommended limit value is 200.
    # Set to 5 to ensure pagination works correctly, but that'll make the Slack API hate you.

    res = await client.conversations_history(channel=channel_id, oldest=time.mktime(start_time), latest=time.mktime(end_time), inclusive=True, limit=200)

    messages_group = res['messages']

    has_more = res['has_more']

    all_users = []
    all_emoji = []

    users_dict = {}

    if res.get('response_metadata', None) and res['response_metadata'].get('next_cursor', None):
        new_cursor = res['response_metadata']['next_cursor']
    while has_more:
        res = await client.conversations_history(channel=channel_id, oldest=time.mktime(start_time), latest=time.mktime(end_time), inclusive=True, limit=200, cursor=new_cursor)

        messages_group.extend(res['messages'])

        has_more = res['has_more']

        if res.get('response_metadata', None) and res['response_metadata'].get('next_cursor', None):
            new_cursor = res['response_metadata']['next_cursor']
    messages_group.sort(key=__message_timestamp_sort)

    # OK! Now we've retrieved all the main-channel messages. Now there are things the Slack API
    # forces us to retrieve on an inefficient, per-message basis.

    for message in messages_group:

        all_users.extend(get_users_in_message(message))
        #all_emoji.extend(get_emoji_in_message(message)) # See TODO in __fetch_emoji_urls

        # This block looks for and, if necessary, fetches thread replies to a message, adding them to the JSON.
        # https://api.slack.com/methods/conversations.replies
        if 'thread_ts' in message:
            # This means it's part of a thread. We have to do the whole same song and dance now.
            timestamp = message['ts'] # Unique identifier used to identify any message. We only care for start of thread.
            res = await client.conversations_replies(channel=channel_id, ts=timestamp, oldest=time.mktime(start_time), latest=time.mktime(end_time), inclusive=True, limit=200)

            # Deleting the very first one because it'll be a duplicate of the thread topper.
            tmessages_group = res['messages'][1:]

            thas_more = res['has_more']

            if res.get('response_metadata', None) and res['response_metadata'].get('next_cursor', None):
                tnew_cursor = res['response_metadata']['next_cursor']

            while thas_more:
                res = await client.conversations_replies(channel=channel_id, ts=timestamp, oldest=time.mktime(start_time), latest=time.mktime(end_time), inclusive=True, limit=200, cursor=tnew_cursor)

                # Deleting the very first one because it'll be a duplicate of the thread topper.
                tmessages_group.extend(res['messages'][1:])

                thas_more = res['has_more']

                if res.get('response_metadata', None) and res['response_metadata'].get('next_cursor', None):
                    tnew_cursor = res['response_metadata']['next_cursor']

            # Sort them by time, ascending.
            tmessages_group.sort(key=__message_timestamp_sort)
            for tmessage in tmessages_group:
                # Add their users and emoji to the big list.
                all_users.extend(get_users_in_message(tmessage))
                #all_emoji.extend(get_emoji_in_message(tmessage)) # See TODO in __fetch_emoji_urls

            # Finally, drop the replies into the message object above.
            message['replies'] = tmessages_group

        # Another block would look for and fetch emoji reactions (reactji) to a message.
        # https://api.slack.com/methods/reactions.get
        # ...actually at the moment it looks like these are being retrieved as part of the normal work.
        # For now we'll leave this comment here, but not do anything.

        # Go fetch the users and turn them into a dict.
        users_dict = await __fetch_user_names_and_icons(client, all_users)

    logging.debug(f"done! I retrieved {len(messages_group)} messages, including any thread replies to them.")

    return await export.make_archive(channel_name, start_time, end_time, messages_group, users_dict, tz_offset)

def get_emoji_in_message(message):
    """
    Scan a message for any emoji or reactji.
    Returns an array of emoji names, no order or uniqueness guarantees.

    message: a single message dict.
    """

    # Emoji come in several ways:
    # reactji: Found in the "reactions" group
    # In-text: found by searching text for :something: groups.

    emojilist = []

    for reaction in message.get('reactions', None):
        emojilist.append(reaction['name'])

    for emoji in re.findall(r':([^:\s]+):', message['text']):
        emojilist.append(emoji)

    return emojilist

async def __fetch_emoji_urls(emojis):
    """
    Get the URLs at which to find emoji images.
    Returns a dict.
    Keys are emoji names, values are URLs.

    TODO: This method currently doesn't work. The reason is that the Slack
    API does not support bot users (like Carmille) getting emoji.
    See the big warning on https://api.slack.com/methods/emoji.list .

    emojis: a list of emoji names. Uniqueness not required.
    """

    eset = set(emojis)

    results = {}

    return results

def get_users_in_message(message):
    """
    Scan a message for any user identifiers.
    Returns an array of user IDs, no order or uniqueness guarantees.

    message: a single message dict.
    """

    # We're going to look in two places:
    # - the "user" identifier in the message
    # - the text for strings like <@U01J94AFNTX> (can also start with W)

    userlist = [message['user']]

    for user in re.findall(r'<@([UW][A-Z0-9]+)>', message['text']):
        userlist.append(user)


    return userlist

async def __fetch_user_names_and_icons(client, users):
    """
    Get user display names and icon URLs for a list of users.
    Returns a dict structure:
    userid: {'display_name': display_name, 'icon_url': icon_url}

    client: the client from the context object.
    users: a list of userids. Uniqueness not required.
    """

    uset = set(users)

    results = {}

    for user in uset:
        # https://api.slack.com/methods/users.info
        res = await client.users_info(user=user)
        results[user] = {
            'display_name': res['user']['profile']['display_name_normalized'],
            'icon_url': res['user']['profile']['image_72']
            }

    return results

async def get_tz_offset(client, user_id):
    """
    Retrieve the (seconds as an integer) time zone offset from UTC for a user.
    Outputs an integer in the range [-43200, 43200]. (-12h, +12h.)

    client: the client from the context object.
    user_id: the human-opaque Slack user identifier.
    """
    # https://api.slack.com/methods/users.info
    res = await client.users_info(user=user_id)
    return res['user']['tz_offset']

def __message_timestamp_sort(message):
    """
    Returns the Slack message timestamp for a single message.
    Used to sort Slack message arrays by time.
    Private function.

    m: A single Slack message dict.
    """

    return float(message['ts'])
