"""
Carmille (the module) handles the use of the Slack API for Carmille (the Slack application).

Major chunks include:
  fetch: Responsible for interactions with the Slack API, like downloading messages and fetching
    user information.
  export: Responsible for taking the objects retrieved by fetch and excreting them into zip files.
"""

from . import fetch
from . import export
