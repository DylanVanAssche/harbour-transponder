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
from transponder.application import Application

try:
    import pyotherside
except ImportError:
    import sys
    # Allow testing Python backend alone.
    print("PyOtherSide not found, continuing anyway!")
    class pyotherside:
        def atexit(*args): pass
        def send(*args): pass
    sys.modules["pyotherside"] = pyotherside()
    
_logger = logging.getLogger(__name__)
#_logger.setLevel(logging.DEBUG)
_logger.info("Logging setup done")

def main():
    """Initialize application."""
    # Globals app is a pointer equivalent to easily connect between the Application class in Python and QML
    # Only 1 Application instance is allowed
    global app
    app = Application()

# Launch main() when module is imported
main()
