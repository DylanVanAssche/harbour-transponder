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

import logging
from transponder import util

class Provider:
    def __init__(self, app, name, sdk):
        """Initialize an Provider instance.

		Attributes:
			id          Object ID integer
			user        Contact object of the user
			name        Name of the provider string
			contacts    List of all contacts for this provider
			sdk         Holds the process of the Python provider SDK
        """
        self.id = util.generate_id()
        self.app = app
        self.user = None
        self.name = name
        self.contacts = []
        self.sdk = sdk
        self._logger = logging.getLogger(__name__)
        self._logger.debug("Provider instance created")

    def login(self, username, password):
        self.user = "test" # Needs User obj
