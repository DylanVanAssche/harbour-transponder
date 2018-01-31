# -*- coding: utf-8 -*-
#
#   This file is part of Transponder.
#
#   Transponder is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   Transponder is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with Transponder.  If not, see <http://www.gnu.org/licenses/>.

"""
Transponder is a Sailfish OS application that provide access to different 
messaging providers using Python plugins.
"""

__version__ = "0.1-1"

import logging
_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)
_logger.info("Logging setup done")

try:
    import pyotherside
except ImportError:
    import sys
    # Allow testing Python backend alone.
    print("PyOtherSide not found, continuing anyway!", file=sys.stderr)
    class pyotherside:
        def atexit(*args): pass
        def send(*args): pass
    sys.modules["pyotherside"] = pyotherside()

from transponder.application import Application

def main():
    """Initialize application."""
    global app
    app = Application()
    return True
