"""
Carmille (the module) handles the use of the Slack API for Carmille (the Slack application).

Major chunks include:
  fetch: Responsible for interactions with the Slack API, like downloading messages and fetching
    user information.
  export: Responsible for taking the objects retrieved by fetch and excreting them into zip files.
  ui: Holds prewritten Slack UI blocks to send as messages.
"""

from . import fetch
from . import export
from . import ui
