import logging
logging.basicConfig(level=logging.DEBUG)
import json
import time
# Import the async app instead of the regular one
from slack_bolt.async_app import AsyncApp


ui_block = [
    {
    	'type': 'section',
    	'text': {
    		'type': 'mrkdwn',
    		'text': 'Bonjour! I am happy to archive part of this channel\'s history for you.\n\n *Please select start and end times below (in your time zone):*'
    	}
    },
    {
    	'type': 'divider'
    },
    {
    	'type': 'section',
        'block_id': 'start-date',
    	'text': {
    		'type': 'mrkdwn',
    		'text': 'Archive Start Date:'
    	},
    	'accessory': {
    		'type': 'datepicker',
    		'initial_date': '1990-04-28',
    		'placeholder': {
    			'type': 'plain_text',
    			'text': 'Select a date',
    			'emoji': True
    		},
    		'action_id': 'start-date'
    	}
    },
    {
    	'type': 'section',
        'block_id': 'start-time',
    	'text': {
    		'type': 'mrkdwn',
    		'text': 'Archive Start Time:'
    	},
    	'accessory': {
    		'type': 'timepicker',
    		'initial_time': '13:37',
    		'placeholder': {
    			'type': 'plain_text',
    			'text': 'Select time'
    		},
    		'action_id': 'start-time'
    	}
    },
    {
    	'type': 'divider'
    },
    {
    	'type': 'section',
        'block_id': 'end-date',
    	'text': {
    		'type': 'mrkdwn',
    		'text': 'Archive End Date:'
    	},
    	'accessory': {
    		'type': 'datepicker',
    		'initial_date': '1990-04-28',
    		'placeholder': {
    			'type': 'plain_text',
    			'text': 'Select a date'
    		},
    		'action_id': 'end-date'
    	}
    },
    {
    	'type': 'section',
        'block_id': 'end-time',
    	'text': {
    		'type': 'mrkdwn',
    		'text': 'Archive End Time:'
    	},
    	'accessory': {
    		'type': 'timepicker',
    		'initial_time': '13:37',
    		'placeholder': {
    			'type': 'plain_text',
    			'text': 'Select time'
    		},
    		'action_id': 'end-time'
    	}
    },
    {
    	'type': 'divider'
    },
    {
    	'type': 'actions',
    	'elements': [
    		{
    			'type': 'button',
    			'text': {
    				'type': 'plain_text',
    				'text': 'Archive!'
    			},
    			'value': 'make_archive',
                'action_id': 'make_archive'
    		}
    	]
    },
    {
    	'type': 'divider'
    }
]


app = AsyncApp()


@app.command("/carmille")
async def command(ack, body, respond):
    await ack()
    
    user_tz_offset = await get_tz_offset(body['user_id'])
    
    initial_end_time = time.time() + user_tz_offset # Unix seconds
    initial_start_time = initial_end_time - 3600 # An hour earlier
    
    
    # Start Times
    st = time.gmtime(initial_start_time)
    ui_block[2]['accessory']['initial_date'] = f"{st[0]:04}-{st[1]:02}-{st[2]:02}"
    ui_block[3]['accessory']['initial_time'] = f"{st[3]:02}:{st[4]:02}"

    # End Times
    et = time.gmtime(initial_end_time)
    ui_block[5]['accessory']['initial_date'] = f"{et[0]:04}-{et[1]:02}-{et[2]:02}" # '1990-04-28'
    ui_block[6]['accessory']['initial_time'] = f"{et[3]:02}:{et[4]:02}" # '13:37'
    
    await respond(blocks = ui_block)

# These actions are for when you select start/end times/dates; we need to have
# an endpoint here for Slack to hit, but we're not gonna do anything.
@app.action("start-time")
@app.action("end-time")
@app.action("start-date")
@app.action("end-date")
@app.action("channel-selection")
async def action_do_nothing(body, ack, respond):
    # Acknowledge the action
    await ack()

# This endpoint gets hit when you click the "Archive" button.
@app.action("make_archive")
async def action_make_archive(body, ack, respond):
    # Acknowledge the action
    await ack()
        
    user_tz_offset = await get_tz_offset(body['user']['id'])
    tz_off_min = user_tz_offset / 60 # Truncating division but that's fine, this is seconds
    tz_off_h = int(tz_off_min / 60) # Truncating again to get two-digit hour
    tz_off_m = int(tz_off_min % 60) # Getting two-digit minutes
    
    # Getting + or - correct for the TZ offset (like the - in "-0800")
    tz_off_dir = '+'
    if tz_off_h < 0:
        tz_off_dir = '-'
        tz_off_h = -tz_off_h
    
    tz_str = f"{tz_off_dir}{tz_off_h:02}{tz_off_m:02}"
    
    
    start_date_str = body['state']['values']['start-date']['start-date']['selected_date']
    end_date_str = body['state']['values']['end-date']['end-date']['selected_date']
    start_time_str = body['state']['values']['start-time']['start-time']['selected_time']
    end_time_str = body['state']['values']['end-time']['end-time']['selected_time']
    
    start_time = time.strptime(f"{start_date_str} {start_time_str} {tz_str}", "%Y-%m-%d %H:%M %z")
    end_time = time.strptime(f"{end_date_str} {end_time_str} {tz_str}", "%Y-%m-%d %H:%M %z")
    
    channel_id = body['channel']['id']
    channel_name = body['channel']['name']
    
    await respond(text=f"I've received your request! I'll archive channel *#{channel_name}* from *{time.strftime('%Y-%m-%d %H:%M',start_time)}* to *{time.strftime('%Y-%m-%d %H:%M',end_time)}*, all times local to you. Exciting!")
    message_archive_url = await get_message_archive(channel_id, channel_name, start_time, end_time)
    await respond(text=f"This archive is done, and you can pick it up at `{message_archive_url}`. Have a nice day!")
    
# Given an (opaque) user ID, get their integer timezone offset (UTC + offset = usertime, so it can be negative)
async def get_tz_offset(user_id):
    # https://api.slack.com/methods/users.info
    res = await app.client.users_info(user=user_id)
    return res['user']['tz_offset']
    
    

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
    
    return await make_archive(channel_name, start_time, end_time, messages_group)
        

async def make_archive(channel_name, start_time, end_time, messages):
    logging.debug("I have begun the dump process.")
    filename = f"tmp/{channel_name} {time.strftime('%Y-%m-%d-%H-%M',start_time)} to {time.strftime('%Y-%m-%d-%H-%M',end_time)}.json"
    with open(filename, "w") as f:
        json.dump(messages, f, indent=4)
    logging.debug("I have finished the dump process.")
    return filename

def fetchMessageTimestampForSort(m):
    return float(m['ts'])

@app.error
async def global_error_handler(error, body, logger):
    logger.exception(error)
    logger.info(body)

if __name__ == "__main__":
    app.start(8000)