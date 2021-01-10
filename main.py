import logging
logging.basicConfig(level=logging.DEBUG)
import time
# Import the async app instead of the regular one
from slack_bolt.async_app import AsyncApp

import carmille as carmille

app = AsyncApp()


@app.command("/carmille")
async def command(ack, body, respond):
    await ack()
    
    user_tz_offset = await carmille.fetch.get_tz_offset(body['user_id'])
    
    initial_end_time = time.time() + user_tz_offset # Unix seconds
    initial_start_time = initial_end_time - 3600 # An hour earlier
    
    ui_block = carmille.ui.datetime_selection_block
    
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
        
    user_tz_offset = await carmille.fetch.get_tz_offset(body['user']['id'])
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
    message_archive_url = await carmille.fetch.get_message_archive(channel_id, channel_name, start_time, end_time)
    await respond(text=f"This archive is done, and you can pick it up at `{message_archive_url}`. Have a nice day!")
    
@app.error
async def global_error_handler(error, body, logger):
    logger.exception(error)
    logger.info(body)

if __name__ == "__main__":
    app.start(8000)