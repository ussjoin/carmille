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

# @app.event("app_mention")
# async def event_test(body, say, logger):
#     logger.info(body)
#     await say("What's up?")

@app.command("/carmille")
async def command(ack, body, respond):
    await ack()
    
    user_tz_offset = await get_tz_offset(body['user_id'])
    
    initial_end_time = time.time() + user_tz_offset # Unix seconds
    initial_start_time = initial_end_time - 3600 # An hour earlier
    
    
    # Start Times
    st = time.gmtime(initial_start_time)
    ui_block[2]['accessory']['initial_date'] = f"{st[0]}-{st[1]}-{st[2]}"
    ui_block[3]['accessory']['initial_time'] = f"{st[3]}:{st[4]}"
    
    # #
    # # End Times
    et = time.gmtime(initial_end_time)
    ui_block[5]['accessory']['initial_date'] = f"{et[0]}-{et[1]}-{et[2]}" # '1990-04-28'
    ui_block[6]['accessory']['initial_time'] = f"{et[3]}:{et[4]}" # '13:37'
    
    await respond(blocks = ui_block)
    #await respond(f"Hi <@{body['user_id']}>!")


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
    res = await app.client.conversations_history(channel=channel_id, oldest=time.mktime(start_time), latest=time.mktime(end_time), limit=5)
    
    # 

async def make_archive(channel_name, start_time, end_time, messages):
    print("foo")

@app.error
async def global_error_handler(error, body, logger):
    await logger.exception(error)
    await logger.info(body)

if __name__ == "__main__":
    app.start(8000)