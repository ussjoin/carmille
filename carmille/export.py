"""
carmille.export: Takes an array of Slack message dicts and exports them as a file.
"""

import json
import logging
import time
import re
import markdown

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

async def make_archive(channel_name, start_time, end_time, messages, users_dict):
    """
    Construct a JSON archive of Slack messages.

    channel_name: the human-readable Slack channel name. Used for file naming.
    start_time: the `time.struct_time` representing the beginning of the messages.
    end_time: the `time.struct_time` representing the end of the messages.
    messages: the array of message dicts as formatted by carmille.fetch.
    users_dict: a nested dict object in the format 
        userid: {'display_name': display_name, 'icon_url': icon_url} .
    """

    logging.debug("I have begun the dump process.")
    filename = f"tmp/{channel_name} {time.strftime('%Y-%m-%d-%H-%M',start_time)} to {time.strftime('%Y-%m-%d-%H-%M',end_time)}.json"
    with open(filename, "w") as file:
        json.dump({'users': users_dict, 'messages': messages}, file, indent=4)
    logging.debug("I have finished the dump process.")
    return filename

def make_html(channel_name, start_time, end_time, messages, users_dict):
    """
    Construct an HTML archive of Slack messages.

    channel_name: the human-readable Slack channel name. Used for file naming.
    start_time: the `time.struct_time` representing the beginning of the messages.
    end_time: the `time.struct_time` representing the end of the messages.
    messages: the array of message dicts as formatted by carmille.fetch.
    users_dict: a nested dict object in the format 
        userid: {'display_name': display_name, 'icon_url': icon_url}
    """
    
    # TODO Actually use the filename
    
    #filename = f"tmp/{channel_name} {time.strftime('%Y-%m-%d-%H-%M',start_time)} to {time.strftime('%Y-%m-%d-%H-%M',end_time)}.html"
    filename = "tmp/dumb.html"
    with open(filename, "w") as file:
        file.write(HTML_HEADER_STRING)
        for message in messages:
            file.write(__render_one_message(message, users_dict))
        file.write(HTML_FOOTER_STRING)
    
    
def __render_one_message(message, users_dict):
    """
    Renders one message to HTML and returns the string.
    Private method.
    
    users_dict: a nested dict object in the format 
        userid: {'display_name': display_name, 'icon_url': icon_url}
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
    # TODO: Use the requesting user's local time
    message_time = time.localtime(int(float(message['ts'])))
    
    ret += f"<span class='timestamp'>{time.strftime('%Y-%m-%d %H:%M %z', message_time)}</span>"
    
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
        ret += __render_one_message(thread_message, users_dict)
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
        ret += "<span class='";
        
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
    
    # {
    #     "title": "Brendan O'Connor",
    #     "title_link": "https://ussjoin.com/",
    #     "text": "This is the CV and resume for Brendan O'Connor. If you'd like to talk about ways we could work together, please contact me: <mailto:bfo@ussjoin.com|bfo@ussjoin.com>.",
    #     "fallback": "Brendan O'Connor",
    #     "from_url": "https://ussjoin.com/",
    #     "service_icon": "https://ussjoin.com/apple-touch-icon.png",
    #     "service_name": "ussjoin.com",
    #     "id": 1,
    #     "original_url": "https://ussjoin.com"
    # }
    # {
    #     "fallback": "<https://twitter.com/JoBurford_|@JoBurford_>: Just spotted <https://twitter.com/MarksLarks|@MarksLarks> on the tele! Media law legend on Secrets of the Royals :clap::clap::clap: <https://pbs.twimg.com/media/ErUbN_lXcAARkoj.jpg>",
    #     "ts": 1610226461,
    #     "author_name": "Jo Burford",
    #     "author_link": "https://twitter.com/JoBurford_/status/1348013599533490177",
    #     "author_icon": "https://pbs.twimg.com/profile_images/1313011195545358337/lFRiBwde_normal.jpg",
    #     "author_subname": "@JoBurford_",
    #     "text": "Just spotted <https://twitter.com/MarksLarks|@MarksLarks> on the tele! Media law legend on Secrets of the Royals :clap::clap::clap: <https://pbs.twimg.com/media/ErUbN_lXcAARkoj.jpg>",
    #     "service_name": "twitter",
    #     "service_url": "https://twitter.com/",
    #     "from_url": "https://twitter.com/JoBurford_/status/1348013599533490177",
    #     "image_url": "https://pbs.twimg.com/media/ErUbN_lXcAARkoj.jpg",
    #     "image_width": 900,
    #     "image_height": 1200,
    #     "image_bytes": 143292,
    #     "id": 1,
    #     "original_url": "https://twitter.com/JoBurford_/status/1348013599533490177",
    #     "footer": "Twitter",
    #     "footer_icon": "https://a.slack-edge.com/80588/img/services/twitter_pixel_snapped_32.png"
    # }
    
    
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
