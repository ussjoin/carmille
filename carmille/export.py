"""
carmille.export: Takes an array of Slack message dicts and exports them as a file.
"""

import json
import logging
import datetime
import time
import re
import os
import string
import shutil
import random
import markdown
import boto3
from botocore.exceptions import ClientError
from dateutil import tz

utctzobject = tz.tzutc()

HTML_HEADER_STRING="""
<!DOCTYPE html>
<html>
<head>
<style>
    body {
        font-family: Slack-Lato,appleLogo,sans-serif;
        font-size: 15px;
        font-weight: 400;
        color: rgba(var(--sk_primary_foreground,29,28,29),1);
        font-variant-ligatures: common-ligatures;
        -moz-osx-font-smoothing: grayscale;
        -webkit-font-smoothing: antialiased;
        line-height: 1.46668;
    }
    div {
        display: block;
    }
    
    a {
        text-decoration: none;
    }
    
    .message {
        flex: 1 1 0;
        min-width: 0;
        padding: 8px;
        padding-left: 16px;
        
    }
    
    .reply {
        padding-left: 32px;
    }
    
    .reactji-block {
        height: 36px;
    }
    
    .reactji {
        max-width: 64px;
        border: 2px solid #666666;
        border-radius: 5px;
    }
    
    .reactji-word {
        font-weight: bold;
    }
    
    .reactji-icon {
        width: 24px;
        height: 24px;
    }
    
    .reactji-count {
        font-weight: bold;
        padding-left: 4px;
    }
    
    .attachment {
        border-left: 4px solid lightgrey;
        padding-left: 8px;
    }
    
    .timestamp {
        font-size: 12px;
        color: rgba(var(--sk_foreground_max_solid,97,96,97),1);
        padding-left: 12px;
    }
    
    .username {
        font-weight: 900;
        word-break: break-word;
    }
    
    .bold {
        font-weight: bold;
    }
    
    .italic {
        font-style: italic;
    }
    
    .strike {
        text-decoration: line-through;
    }
    
    .code {
        font-family: monospace;
    }
    
</style>
</head>
<body>
"""

HTML_FOOTER_STRING="""
</body>
</html>
"""

async def upload_archive(directory, filename):
    """
    Push a file to a configured S3 bucket.
    filename: the local filename (and local path) to the file in question.

    Note: relies on the following environment variables:
    S3_API_ENDPOINT -- e.g., us-east-1.linodeobjects.com
    S3_BUCKET -- the name of the bucket
    S3_ACCESS_KEY -- your S3 access key
    S3_SECRET_KEY -- your S3 secret key
    """
    S3_API_ENDPOINT = os.environ.get('S3_API_ENDPOINT')
    S3_BUCKET = os.environ.get('S3_BUCKET')
    S3_ACCESS_KEY = os.environ.get('S3_ACCESS_KEY')
    S3_SECRET_KEY = os.environ.get('S3_SECRET_KEY')


    cfg = {
        "aws_access_key_id": S3_ACCESS_KEY,
        "aws_secret_access_key": S3_SECRET_KEY,
        "endpoint_url": f"https://{S3_API_ENDPOINT}",
    }

    s3_client = boto3.client('s3', **cfg)
    try:
        s3_client.upload_file(f"{directory}/{filename}", S3_BUCKET, filename, ExtraArgs={'ACL': 'public-read'})
    except ClientError as errormessage:
        logging.error(errormessage)
        return False
    return True


async def make_archive(channel_name, start_time, end_time, messages, users_dict, tz_offset):
    """
    Construct a zip file of Slack messages containing a JSON and an HTML representation.

    channel_name: the human-readable Slack channel name. Used for file naming.
    start_time: the `time.struct_time` representing the beginning of the messages.
    end_time: the `time.struct_time` representing the end of the messages.
    messages: the array of message dicts as formatted by carmille.fetch.
    users_dict: a nested dict object in the format
        userid: {'display_name': display_name, 'icon_url': icon_url} .
    tz_offset: the requesting user's local time offset from UTC, in integer seconds.

    Note: relies on the following environment variables:
    S3_WEBSITE_PREFIX -- the entire string to put before the object name to get a place to download the file. e.g., https://carmille.supercoolhost.net
    """

    logging.debug("Entering the archive process.")
    S3_WEBSITE_PREFIX = os.environ.get('S3_WEBSITE_PREFIX')

    letters = string.ascii_lowercase
    randstr = ''.join(random.choice(letters) for i in range(5))
    os.mkdir(f"tmp/{randstr}")

    user_tz = tz.tzoffset(None, tz_offset)

    start_datetime = datetime.datetime.fromtimestamp(time.mktime(start_time)).astimezone(user_tz)
    end_datetime = datetime.datetime.fromtimestamp(time.mktime(end_time)).astimezone(user_tz)

    # Has extensions added to it
    filepart = f"{channel_name}_{start_datetime.strftime('%Y-%m-%d-%H-%M')}_to_{end_datetime.strftime('%Y-%m-%d-%H-%M')}"

    filename = f"tmp/{randstr}/{filepart}"
    zipfilename = f"tmp/{filepart}"

    await make_json(filename, messages, users_dict)
    # Only make_html needs user_tz, because it's the one that tries to do "human_readable" stuff.
    await make_html(filename, messages, users_dict, user_tz)

    shutil.make_archive(zipfilename, "zip", f"tmp/{randstr}")
    shutil.rmtree(f"tmp/{randstr}")
    logging.debug("Finished the archive process.")

    upload_result = await upload_archive("tmp", f"{filepart}.zip")
    if upload_result:
        logging.debug("Finished upload process.")
        os.remove(f"tmp/{filepart}.zip")
        return f"{S3_WEBSITE_PREFIX}/{filepart}.zip"
    else:
        return "Unfortunately, the archive failed. Look at the logs. Sorry!"


async def make_json(filename, messages, users_dict):
    """
    Construct a JSON archive of Slack messages.

    channel_name: the human-readable Slack channel name. Used for file naming.
    start_time: the `time.struct_time` representing the beginning of the messages.
    end_time: the `time.struct_time` representing the end of the messages.
    messages: the array of message dicts as formatted by carmille.fetch.
    users_dict: a nested dict object in the format
        userid: {'display_name': display_name, 'icon_url': icon_url} .
    """

    logging.debug("I have begun the JSON dump process.")
    filename = f"{filename}.json"
    with open(filename, "w") as file:
        json.dump({'users': users_dict, 'messages': messages}, file, indent=4)
    logging.debug("I have finished the JSON dump process.")
    return filename

async def make_html(filename, messages, users_dict, user_tz):
    """
    Construct an HTML archive of Slack messages.

    channel_name: the human-readable Slack channel name. Used for file naming.
    start_time: the `time.struct_time` representing the beginning of the messages.
    end_time: the `time.struct_time` representing the end of the messages.
    messages: the array of message dicts as formatted by carmille.fetch.
    users_dict: a nested dict object in the format
        userid: {'display_name': display_name, 'icon_url': icon_url}
    user_tz: a tzinfo object with the requesting user's timezone set.
    """

    logging.debug("I have begun the HTML dump process.")
    filename = f"{filename}.html"
    with open(filename, "w") as file:
        file.write(HTML_HEADER_STRING)
        for message in messages:
            file.write(__render_one_message(message, users_dict, user_tz))
        file.write(HTML_FOOTER_STRING)
    logging.debug("I have finished the HTML dump process.")
    return filename

def __render_one_message(message, users_dict, user_tz):
    """
    Renders one message to HTML and returns the string.
    Private method.

    users_dict: a nested dict object in the format
        userid: {'display_name': display_name, 'icon_url': icon_url}
    user_tz: a tzinfo object with the requesting user's timezone set.
    """
    #print(message)
    classes = "message"

    if message.get('thread_ts', None) and message.get('thread_ts', None) != message.get('ts', None):
        # Then it's a reply in a thread.
        # (If they're the same, then it's the head of a thread.)
        classes += " reply"

    ret = f"<div class='{classes}' id=\"{message['ts']}\">\n"

    # Message headers
    ret += "<div class='header'>"
    # Username
    ret += f"<span class='username'>@{users_dict[message['user']]['display_name']}</span>"

    # Timezone math
    # This line takes an epoch timestamp that's passed as a string float.
    # It converts it to a float, then to an integer, to drop the sub-second bit.
    # It then parses it into a UTC datetime object.
    # Finally, it excretes it into the user's timezone.
    # utctzobject is made once, at the top of this file, to avoid having to
    # construct it on every single message.
    message_time = datetime.datetime.fromtimestamp(int(float(message['ts'])),utctzobject).astimezone(user_tz)

    ret += f"<span class='timestamp'>{message_time.strftime('%Y-%m-%d %H:%M %z')}</span>"

    ret += "</div>" # End of class='header'

    # Main body of the message

    if message.get('blocks', None):
        for block in message['blocks']:
            ret += __render_one_block(block)
    else:
        mod_text = re.sub(r'<@([UW][A-Z0-9]+)>',
            lambda x: "<span class='username'>@"+users_dict[x.group(1)]['display_name']+"</span>",
            message['text'])
        ret += f"{mod_text}\n"

    # Optional components
    for thread_message in message.get('replies', []):
        ret += __render_one_message(thread_message, users_dict, user_tz)
    for attachment in message.get('attachments', []):
        ret += __render_one_attachment(attachment)
    if message.get('reactions', None):
        ret += __render_all_reactions(message.get('reactions', []))

    ret += "</div>\n"

    return ret

def __render_one_block(block):
    """
    Takes a message block and renders it to a string, which it returns.
    Private method.
    """
    ret = ""
    block_type = block.get('type', None)
    if block_type == "rich_text":
        # A rich_text block will have a series of element section blocks.
        # Those blocks will be of type rich_text_section or rich_text_preformatted.
        # I interpret those as calls for a <p> element or a <pre> element.
        # Hilariously, either way they'll then contain a subarray of elements.
        # So they get passed on.

        for rtelement in block['elements']:
            rt_type = rtelement.get('type', None)
            if rt_type == "rich_text_section":
                # Then it'll have a series of small elements.
                ret += "<p>"
                for rtselement in rtelement['elements']:
                    ret += __render_one_rtsec_element(rtselement)
                ret += "</p>"
            elif rt_type == "rich_text_preformatted":
                ret += "<pre>"
                for rtselement in rtelement['elements']:
                    ret += __render_one_rtsec_element(rtselement)
                ret += "</pre>"
            else:
                ret += f"ERROR: rich_text block element type {rt_type}: unknown"
    else:
        ret += f"ERROR: block element type {block_type}: unknown"
    return ret

def __render_one_rtsec_element(element):
    """
    Takes a message block rich text section element and renders it to a string, which it returns.
    Private method.
    """
    ret = ""
    element_type = element.get('type', None)
    if element_type == "text":
        # This can contain an optional style block that contains a hash with keys that are useful, and values that are true.
        ret += "<span class='"

        formats = element.get('style', {})
        ret += " ".join(formats.keys())
        ret += "'>"

        ret += element.get('text', '')
        ret += "</span>"
    elif element_type == "link":
        ret += f"<a href={element.get('url', 'ERROR: link element contains no URL')}>{element.get('text', element.get('url', 'ERROR: link element contains no URL or text'))}</a>"
    else:
        ret += f"ERROR: rich_text_section element type {element_type}: unknown"
    return ret

def __render_one_attachment(attachment):
    """
    Takes a message attachment block and tries to render it to a string, which it returns.
    Private method.
    """

    ret = "<div class='attachment'>"

    mrkdown = attachment['text']
    mrkdown = re.sub(r"<([^|]+)\|([^>]+)>", r"[\2](\1)", mrkdown)

    ret += markdown.markdown(mrkdown)

    if attachment.get('image_url', None):
        ret += f"<img src='{attachment.get('image_url', None)}' height=200 />"

    ret += "</div>"
    return ret

def __render_all_reactions(reactions):
    """
    Takes a reaction emoji block and tries to render it to a string, which it returns.
    Private method.
    """

    ret = "<div class='reactji-block'>"
    for reaction in reactions:
        ret += "<div class='reactji'>"

        # ret += f"<img class='reactji-icon' src='reactji/{reaction['name']}'/>"
        # TODO: Due to emoji listing not being supported by Slack bots (see warning
        # at https://api.slack.com/methods/emoji.list), this renderer lists emoji
        # names instead.

        ret += f"<span class='reactji-word'>:{reaction['name']}:</span>"

        ret += f"<span class='reactji-count'>{reaction['count']}</span>"
        ret += "</div>"
    ret += "</div>"

    return ret
