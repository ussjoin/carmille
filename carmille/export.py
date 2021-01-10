"""
carmille.export: Takes an array of Slack message dicts and exports them as a file.
"""

import json
import logging
import time

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
    }
    
    .reactji {
    }
    
    .timestamp {
        font-size: 12px;
        color: rgba(var(--sk_foreground_max_solid,97,96,97),1);
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

def make_html(channel_name, start_time, end_time, messages):
    """
    Construct an HTML archive of Slack messages.

    channel_name: the human-readable Slack channel name. Used for file naming.
    start_time: the `time.struct_time` representing the beginning of the messages.
    end_time: the `time.struct_time` representing the end of the messages.
    messages: the array of message dicts as formatted by carmille.fetch.
    """
    
    # TODO Actually use the filename
    
    #filename = f"tmp/{channel_name} {time.strftime('%Y-%m-%d-%H-%M',start_time)} to {time.strftime('%Y-%m-%d-%H-%M',end_time)}.html"
    filename = "tmp/dumb.html"
    with open(filename, "w") as file:
        file.write(HTML_HEADER_STRING)
        for message in messages:
            file.write(__render_one_message(message))
        file.write(HTML_FOOTER_STRING)
    
    
def __render_one_message(message):
    """
    Renders one message to HTML and returns the string.
    Private method.
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
    ret += f"<span class='username'>{message['user']}</span>"
    
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
        ret += f"{message['text']}\n"
    
    # Optional components
    if message.get('replies', None):
        for thread_message in message['replies']:
            ret += __render_one_message(thread_message)
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
        # TODO: There's likely another kind of linktype block that has a different display name.
        ret += f"<a href={element.get('url', '')}>{element.get('url', '')}</a>"
    
    else:
        ret += f"I don't understand how to render an element type of {element_type}, halp!"
    return ret