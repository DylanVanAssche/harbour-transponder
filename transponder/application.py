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

import transponder.util as util
import logging

PROVIDERS_FILE = "providers.json"

__all__ = ("Application")

class Application:
    """ Application contains all the application APIs of Transponder. """
    
    def __init__(self):
        """Initialize an Application instance."""
        self._logger = logging.getLogger(__name__)
        providers = util.read_json(PROVIDERS_FILE)
        
        
        self._logger.debug("Application instance created")