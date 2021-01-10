# Import the async app instead of the regular one
from slack_bolt.async_app import AsyncApp
import time
import logging

from . import export

app = AsyncApp()

async def get_message_archive(channel_id, channel_name, start_time, end_time):
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
    messages_group.sort(key=fetchMessageTimestampForSort)
    
    # OK! Now we've retrieved all the main-channel messages; however, we need to go get thread replies, because of course Slack makes that hard.
    
    # https://api.slack.com/methods/conversations.replies
    for m in messages_group:
        if 'thread_ts' in m:
            # This means it's part of a thread. We have to do the whole same song and dance now.
            ts = m['ts'] # Unique identifier used to identify any message. We only care for start of thread.
            res = await app.client.conversations_replies(channel=channel_id, ts=ts, oldest=time.mktime(start_time), latest=time.mktime(end_time), limit=2)
    
            # Deleting the very first one because it'll be a duplicate of the thread topper.
            tmessages_group = res['messages'][1:]
    
            thas_more = res['has_more']
    
            if res.get('response_metadata', None) and res['response_metadata'].get('next_cursor', None):
                tnew_cursor = res['response_metadata']['next_cursor']
    
            while thas_more:
                res = await app.client.conversations_replies(channel=channel_id, ts=ts, oldest=time.mktime(start_time), latest=time.mktime(end_time), limit=2, cursor=tnew_cursor)
        
                # Deleting the very first one because it'll be a duplicate of the thread topper.
                tmessages_group.extend(res['messages'][1:])
        
                thas_more = res['has_more']
    
                if res.get('response_metadata', None) and res['response_metadata'].get('next_cursor', None):
                    tnew_cursor = res['response_metadata']['next_cursor']
            
            # Finally, drop the replies into the message object above.
            tmessages_group.sort(key=fetchMessageTimestampForSort)
            m['replies'] = tmessages_group
    
    logging.debug(f"done! I retrieved {len(messages_group)} messages, including the thread replies.")
    
    return await export.make_archive(channel_name, start_time, end_time, messages_group)

# Given an (opaque) user ID, get their integer timezone offset (UTC + offset = usertime, so it can be negative)
async def get_tz_offset(user_id):
    # https://api.slack.com/methods/users.info
    res = await app.client.users_info(user=user_id)
    return res['user']['tz_offset']

def fetchMessageTimestampForSort(m):
    return float(m['ts'])
