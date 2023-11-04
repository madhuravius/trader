from math import dist
from typing import List

from loguru import logger

from trader.client.waypoint import Waypoint
from trader.roles.common import Common


class Navigator(Common):
    """
    This role doesn't do much in terms of moving/actions on ships, but plots courses of various sorts.

    Its sole purpose is to generate routes for other roles to consume and act on. Some routes are generated
    dynamically and on the fly (mining activity), while others are predetermined for individual ships/squads
    to consume (exploration and market refresh circuits).
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

